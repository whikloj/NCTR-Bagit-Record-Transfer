import json
import logging
import smtplib
import zipfile
from io import BytesIO
from datetime import timedelta

import django_rq
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import slugify
from django.template.loader import render_to_string

from recordtransfer.caais import convert_transfer_form_to_meta_tree
from recordtransfer.models import Bag, BagGroup, UploadedFile, UploadSession, User, Job, Submission
from recordtransfer.settings import DO_NOT_REPLY_USERNAME, ARCHIVIST_EMAIL, BAG_CHECKSUMS
from recordtransfer.tokens import account_activation_token
from recordtransfer.utils import html_to_text, zip_directory


LOGGER = logging.getLogger('rq.worker')


def _get_admin_recipient_list(subject):
    LOGGER.info(msg='Finding Users to send "{0}" email to'.format(subject))
    recipients = User.objects.filter(gets_bag_email_updates=True)
    if not recipients:
        LOGGER.warning(msg='There are no users configured to receive transfer update emails.')
        return
    user_list = list(recipients)
    LOGGER.info(msg=('Found {0} Users(s) to send email to: {1}'.format(len(user_list), user_list)))
    return [str(e) for e in recipients.values_list('email', flat=True)]


@django_rq.job
def bag_user_metadata_and_files(form_data: dict, user_submitted: User):
    ''' Create database models and BagIt bag on file system for the submitted form. Sends an email
    to the submitting user and the staff members who receive submission email updates.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form.
        user_submitted (User): The user who submitted the data and files.
    '''
    LOGGER.info(msg='Creating a submission and bag from the transfer submitted by {0}'.format(
        str(user_submitted))
    )

    token = form_data['session_token']
    LOGGER.info(msg=('Fetching session with the token {0}'.format(token)))
    upload_session = UploadSession.objects.filter(token=token).first()

    LOGGER.info(msg='Creating serializable CAAIS metadata from form data')
    caais_metadata = convert_transfer_form_to_meta_tree(form_data)

    title = form_data['accession_title']
    abbrev_title = title if len(title) <= 20 else title[0:20]
    bag_name = '{username}_{datetime}_{title}'.format(
        username=slugify(user_submitted),
        datetime=timezone.localtime(timezone.now()).strftime(r'%Y%m%d-%H%M%S'),
        title=slugify(abbrev_title))

    LOGGER.info(msg=('Created name for bag: "{0}"'.format(bag_name)))

    new_bag = Bag(
        user=user_submitted,
        bag_name=bag_name,
        caais_metadata=json.dumps(caais_metadata),
        upload_session=upload_session,
    )
    new_bag.save()

    LOGGER.info(msg='Creating bag on filesystem')
    bagging_result = new_bag.make_bag(
        algorithms=BAG_CHECKSUMS,
        file_perms='644',
        move_files=True,
        logger=LOGGER,
    )

    if bagging_result['bag_created']:
        LOGGER.info('The BagIt bag was created successfully')
        LOGGER.info('Creating Submission object linked to new bag')
        new_submission = Submission(
            submission_date=bagging_result['time_created'],
            user=user_submitted,
            bag=new_bag,
        )
        new_submission.save()

        group_name = form_data['group_name']
        if group_name != 'No Group':
            if group_name == 'Add New Group':
                new_group_name = form_data['new_group_name']
                description = form_data['group_description']
                group, created = BagGroup.objects.get_or_create(name=new_group_name,
                                                                description=description,
                                                                created_by=user_submitted)
                if created:
                    LOGGER.info(msg='Created "{0}" BagGroup'.format(new_group_name))
            else:
                group = BagGroup.objects.get(name=group_name, created_by=user_submitted)

            if group:
                LOGGER.info(msg='Associating Bag with "{0}" BagGroup'.format(group.name))
                new_bag.part_of_group = group
                new_bag.save()
            else:
                LOGGER.warning(msg='Could not find "{0}" BagGroup'.format(group.name))

        LOGGER.info('Sending transfer success email to administrators')
        send_bag_creation_success.delay(form_data, new_submission)
        LOGGER.info('Sending thank you email to user')
        send_thank_you_for_your_transfer.delay(form_data, new_submission)
    else:
        LOGGER.error('bagger reported that the bag was NOT created successfully')
        LOGGER.info('Sending transfer failure email to administrators')
        send_bag_creation_failure.delay(form_data, user_submitted)
        LOGGER.info('Sending transfer issue email to user')
        send_your_transfer_did_not_go_through.delay(form_data, user_submitted)

@django_rq.job
def create_downloadable_bag(bag: Bag, user_triggered: User):
    ''' Create a zipped bag that a user can download using a Job model.

    Args:
        bag (Bag): The bag to zip up for users to download
        user (User): The user who triggered this new Job creation
    '''
    LOGGER.info(msg='Creating zipped bag from {0}'.format(str(bag.location)))

    description = (
        '{user} triggered this job to generate a download link for the bag '
        '{name}'
    ).format(user=str(user_triggered), name=bag.bag_name)

    new_job = Job(
        name=f'Generate Download Link for {str(bag)}',
        description=description,
        start_time=timezone.now(),
        user_triggered=user_triggered,
        job_status=Job.JobStatus.NOT_STARTED)
    new_job.save()

    zipf = None
    try:
        new_job.job_status = Job.JobStatus.IN_PROGRESS
        new_job.save()

        LOGGER.info(msg='Zipping directory to an in-memory file ...')
        zipf = BytesIO()
        zipped_bag = zipfile.ZipFile(zipf, 'w', zipfile.ZIP_DEFLATED, False)
        zip_directory(bag.location, zipped_bag)
        zipped_bag.close()
        LOGGER.info(msg='Zipped directory successfully')

        file_name = f'{bag.user.username}-{bag.bag_name}.zip'
        LOGGER.info(msg='Saving zip file as {0} ...'.format(file_name))
        new_job.attached_file.save(file_name, ContentFile(zipf.getvalue()), save=True)
        LOGGER.info(msg='Saved file succesfully')

        new_job.job_status = Job.JobStatus.COMPLETE
        new_job.end_time = timezone.now()
        new_job.save()

        LOGGER.info('Downloadable bag created successfully')
    except Exception as exc:
        new_job.job_status = Job.JobStatus.FAILED
        new_job.save()
        LOGGER.error(msg=('Creating zipped bag failed: {0}'.format(str(exc))))
    finally:
        if zipf is not None:
            zipf.close()

@django_rq.job
def send_bag_creation_success(form_data: dict, submission: Submission):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    were no errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        submission (Submission): The new submission that was created.
    '''
    subject = 'New Transfer Ready for Review'
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)
    submission_url = 'http://{domain}/{change_url}'.format(
        domain=domain.rstrip(' /'),
        change_url=submission.get_admin_change_url().lstrip(' /')
    )
    LOGGER.info(msg='Generated submission change URL: {0}'.format(submission_url))

    recipient_emails = _get_admin_recipient_list(subject)

    user_submitted = submission.user
    send_mail_with_logs(
        recipients=recipient_emails,
        from_email=from_email,
        subject=subject,
        template_name='recordtransfer/email/bag_submit_success.html',
        context={
            'user': user_submitted,
            'form_data': form_data,
            'submission_url': submission_url,
        }
    )

@django_rq.job
def send_bag_creation_failure(form_data: dict, user_submitted: User):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    WERE errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        user_submitted (User): The user that tried to create the submission.
    '''
    subject = 'Bag Creation Failed'
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)

    recipient_emails = _get_admin_recipient_list(subject)

    send_mail_with_logs(
        recipients=recipient_emails,
        from_email=from_email,
        subject=subject,
        template_name='recordtransfer/email/bag_submit_failure.html',
        context={
            'user': user_submitted,
            'form_data': form_data,
        }
    )

@django_rq.job
def send_thank_you_for_your_transfer(form_data: dict, submission: Submission):
    ''' Send a transfer success email to the user who submitted the transfer.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        submission (Submission): The new submission that was created.
    '''
    if submission.user.gets_notification_emails:
        domain = Site.objects.get_current().domain
        from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)

        user_submitted = submission.user
        send_mail_with_logs(
            recipients=[user_submitted.email],
            from_email=from_email,
            subject='Thank You For Your Transfer',
            template_name='recordtransfer/email/transfer_success.html',
            context={
                'user': user_submitted,
                'form_data': form_data,
                'archivist_email': ARCHIVIST_EMAIL,
            }
        )

@django_rq.job
def send_your_transfer_did_not_go_through(form_data: dict, user_submitted: User):
    ''' Send a transfer failure email to the user who submitted the transfer.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        user_submitted (User): The user that tried to create the submission.
    '''
    if user_submitted.gets_notification_emails:
        domain = Site.objects.get_current().domain
        from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)

        send_mail_with_logs(
            recipients=[user_submitted.email],
            from_email=from_email,
            subject='Issue With Your Transfer',
            template_name='recordtransfer/email/transfer_failure.html',
            context={
                'user': user_submitted,
                'form_data': form_data,
                'archivist_email': ARCHIVIST_EMAIL,
            }
        )

@django_rq.job
def send_user_activation_email(new_user: User):
    ''' Send an activation email to the new user who is attempting to create an account. The user
    must visit the link to activate their account.

    Args:
        new_user (User): The new user who requested an account
    '''
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)

    token = account_activation_token.make_token(new_user)
    LOGGER.info(msg='Generated token for activation link: {0}'.format(token))

    send_mail_with_logs(
        recipients=[new_user.email],
        from_email=from_email,
        subject='Activate Your Account',
        template_name='recordtransfer/email/activate_account.html',
        context = {
            'user': new_user,
            'base_url': domain,
            'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
            'token': token,
        }
    )


@django_rq.job
def send_user_account_updated(user_updated: User, context_vars: dict):
    """ Send a notice that the user's account has been updated.

    Args:
        user_updated (User): The user whose account was updated.
        context_vars (dict): Template context variables.
    """

    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)

    send_mail_with_logs(
        recipients=[user_updated.email],
        from_email=from_email,
        subject=context_vars['subject'],
        template_name='recordtransfer/email/account_updated.html',
        context=context_vars
    )


def send_mail_with_logs(recipients: list, from_email: str, subject, template_name: str,
                        context: dict):
    try:
        if Site.objects.get_current().domain == '127.0.0.1:8000':
            new_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, 'example.com')
            msg = 'Changing FROM email for local development. Using {0} instead of {1}'
            LOGGER.info(msg=msg.format(new_email, from_email))
            from_email = new_email
        elif ":" in Site.objects.get_current().domain:
            new_domain = Site.objects.get_current().domain.split(":")[0]
            new_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, new_domain)
            msg = 'Changing FROM email to remove port number. Using {0} instead of {1}'
            LOGGER.info(msg=msg.format(new_email, from_email))
            from_email = new_email

        LOGGER.info('Setting up new email:')
        LOGGER.info(msg='SUBJECT: {0}'.format(subject))
        LOGGER.info(msg='TO: {0}'.format(recipients))
        LOGGER.info(msg='FROM: {0}'.format(from_email))
        LOGGER.info(msg='Rendering HTML email from {0}'.format(template_name))
        context['site_domain'] = Site.objects.get_current().domain
        msg_html = render_to_string(template_name, context=context)
        LOGGER.info('Stripping tags from rendered HTML to create a plaintext email')
        msg_plain = html_to_text(msg_html)
        LOGGER.info('Sending...')
        send_mail(
            subject=subject,
            message=msg_plain,
            from_email=from_email,
            recipient_list=recipients,
            html_message=msg_html,
            fail_silently=False
        )
        num_recipients = len(recipients)
        if num_recipients == 1:
            LOGGER.info('1 email sent')
        else:
            LOGGER.info(msg='{0} emails sent'.format(num_recipients))
    except smtplib.SMTPException as exc:
        LOGGER.error(msg=('Error when sending email to user: {0}'.format(str(exc))))

@django_rq.job
def clean_undeleted_temp_files(hours=12):
    ''' Deletes every temp file tracked in the database older than a specified number of hours.

    Args:
        hours (int): The threshold number of hours in the past required to delete a file
    '''
    time_threshold = timezone.now() - timedelta(hours=hours)

    old_undeleted_files = UploadedFile.objects.filter(
        old_copy_removed=False
    ).filter(
        session__started_at__lt=time_threshold
    )

    LOGGER.info('Running cleaning')

    for upload in old_undeleted_files:
        upload.remove()
