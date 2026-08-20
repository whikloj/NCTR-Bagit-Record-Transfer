''' Custom administration code for the admin site '''
import logging
from pathlib import Path

from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, path
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from django.views.decorators.debug import sensitive_post_parameters

from recordtransfer.forms import InlineBagGroupForm, SubmissionForm, \
    InlineSubmissionForm, UploadSessionForm, \
    UploadedFileForm, InlineUploadedFileForm
from recordtransfer.jobs import send_user_account_updated, send_user_activation_email, create_downloadable_bag
from recordtransfer.models import User, UploadSession, UploadedFile, BagGroup, \
    Submission, Job
from recordtransfer.settings import ALLOW_BAG_CHANGES

from bagitobjecttransfer.settings.base import MEDIA_ROOT

LOGGER = logging.getLogger(__name__)


def linkify(field_name):
    ''' Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    '''
    def _linkify(obj):
        try:
            linked_obj = getattr(obj, field_name)
            if not linked_obj:
                return '-'

            app_label = linked_obj._meta.app_label
            model_name = linked_obj._meta.model_name
            view_name = f'admin:{app_label}_{model_name}_change'
            link_url = reverse(view_name, args=[linked_obj.pk])
            return format_html('<a href="{}">{}</a>', link_url, linked_obj)

        except AttributeError:
            return '-'

    _linkify.short_description = field_name.replace('_', ' ') # Sets column name
    return _linkify


@receiver(pre_delete, sender=Job)
def job_file_delete(sender, instance, **kwargs):
    """ FileFields are not deleted automatically after Django 1.11, instead this receiver does it."""
    instance.attached_file.delete(False)


@receiver(post_delete, sender=Submission)
def submission_delete_metadata(sender, instance, **kwargs):
    """ Submissions have a ForeignKey to the Upload Session. It is not deleted when the
    Submission is deleted. This receiver causes the Upload Session (and all subsequent parts to be deleted).
    It is post_delete because otherwise we get an error (possibly a recursive loop)."""
    instance.upload_session.delete(False)


class ReadOnlyAdmin(admin.ModelAdmin):
    ''' A model admin that does not allow any editing/changing/ or deletions

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    '''
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + \
               [field.name for field in obj._meta.fields] + \
               [field.name for field in obj._meta.many_to_many]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UploadedFile)
class UploadedFileAdmin(ReadOnlyAdmin):
    ''' Admin for the UploadedFile model

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    '''
    class Media:
        js = ("recordtransfer/js/hideMediaLink.js",)

    change_form_template = 'admin/readonly_change_form.html'

    form = UploadedFileForm

    actions = [
        'clean_temp_files',
    ]

    list_display = [
        'name',
        'exists',
        linkify('session'),
    ]

    ordering = [
        '-session',
        'name'
    ]

    def clean_temp_files(self, request, queryset):
        ''' Remove temporary files stored on the file system by the uploaded
        files
        '''
        for uploaded_file in queryset:
            uploaded_file.remove()
    clean_temp_files.short_description = gettext('Remove temp files on filesystem')


class UploadedFileInline(admin.TabularInline):
    ''' Inline admin for the UploadedFile model. Used to view the files
    associated with an upload session

    Permission:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    '''
    form = InlineUploadedFileForm
    model = UploadedFile
    max_num = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UploadSession)
class UploadSessionAdmin(ReadOnlyAdmin):
    ''' Admin for the UploadSession model

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    '''
    change_form_template = 'admin/readonly_change_form.html'

    form = UploadSessionForm

    inlines = [
        UploadedFileInline,
    ]

    list_display = [
        'token',
        'started_at',
        'number_of_files_uploaded'
    ]

    ordering = [
        '-started_at',
    ]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    ''' Admin for the Submission model. Adds a view to view the transfer report
    associated with the submission. The report view can be accessed at
    code:`submission/<id>/report/`

    Permissions:
        - add: Not allowed
        - change: Allowed
        - delete: Only by superusers
    '''
    change_form_template = 'admin/submission_change_form.html'

    form = SubmissionForm

    inlines = [
    ]

    actions = [
    ]

    search_fields = [
        'id',
        'title',
    ]

    list_display = [
        'title',
        'submission_date',
        'id',
        'review_status',
        linkify('user'),
        linkify('part_of_group')
    ]

    ordering = [
        '-submission_date',
    ]

    readonly_fields = [
        'extent_statement',
        'submission_date',
        'user',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser

    def get_urls(self):
        ''' Add report/ view to admin
        '''
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        report_url = [
            path('<path:object_id>/report/',
                 self.admin_site.admin_view(self.view_report),
                 name='%s_%s_report' % info),
        ]
        return report_url + urls

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        job = Job.objects.get_queryset().filter(Q(submission_id=object_id)).first()
        if extra_context is None:
            extra_context = {}
        extra_context['has_generated_bag'] = job is not None
        if job is not None:
            extra_context['generated_bag_url'] = job.get_admin_download_url()
        else:
            create_downloadable_bag.delay(Submission.objects.get(id=object_id), request.user)
        return super().changeform_view(request, object_id, form_url, extra_context)

    def view_report(self, request, object_id):
        ''' Redirect to the submission's report if the submission exists

        Args:
            request: The originating request
            object_id: The ID for the submission
        '''
        submission = Submission.objects.filter(id=object_id).first()
        if submission:
            return HttpResponse(submission.get_report())
        # Error response
        msg = gettext('Submission with ID “%(key)s” doesn’t exist. Perhaps it was deleted?') % {
            'key': object_id,
        }
        self.message_user(request, msg, messages.WARNING)
        url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def save_model(self, request, obj, form, change):
        ''' Update Bag in case the accession identifier or level of detail
        changes.
        '''

        if not change:
            # Do nothing because nothing changed.
            return
        super().save_model(request, obj, form, change)

        if not ALLOW_BAG_CHANGES:
            messages.warning(request, gettext(
                "A change was made to this submission that would have affected the Bag's "
                'submission-info.txt, but ALLOW_BAG_CHANGES is OFF, so no change was made to the Bag'
            ))

    def recreate_zipped_bag(self, request, object_id):
        """ Remove the existing submission for this submission and user, then recreate it.
        Args:
            request: The originating request
            object_id: The ID for the submission
        """

        job = Job.objects.filter(Q(submission_id=object_id)).first()
        if job:
            job.delete()
        return self.create_zipped_bag(request, object_id)

    def create_zipped_bag(self, request, object_id):
        ''' Start a background job to create a downloadable submission

        Args:
            request: The originating request
            object_id: The ID for the submission
        '''
        bag = Submission.objects.filter(id=object_id).first()
        if bag:
            job = Job.objects.filter(Q(submission_id=object_id) & Q(user_triggered=request.user)).first()
            if job:
                # You should not get here, reload the submission page.
                self.message_user(request, mark_safe(gettext(
                    'A downloadable submission already exists for you. Check the Submission page for links to download and '
                    'regenerate the submission.'
                )))
                return HttpResponseRedirect(bag.get_admin_change_url())
            create_downloadable_bag.delay(bag, request.user)
            self.message_user(request, mark_safe(gettext(
                'A downloadable submission is being generated. Check the Submission page for links access the submission.'
            )))
            url = reverse('admin:recordtransfer_submission_changelist', current_app=self.admin_site.name)
            return HttpResponseRedirect(url)
        # Error response
        msg = gettext('Bag with ID “%(key)s” doesn’t exist. Perhaps it was deleted?') % {
            'key': object_id,
        }
        self.message_user(request, msg, messages.WARNING)
        admin_url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(admin_url)

class SubmissionInline(admin.TabularInline):
    ''' Inline admin for the Appraisal model. Used to edit Appraisals associated
    with a Submission. Deletions are not allowed.

    Permissions:
        - add: Not allowed
        - change: Not allowed - go to Submission page for change ability
        - delete: Only by superusers
    '''
    model = Submission
    max_num = 0
    show_change_link = True
    form = InlineSubmissionForm

    ordering = ['-submission_date']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser


@admin.register(BagGroup)
class BagGroupAdmin(ReadOnlyAdmin):
    ''' Admin for the BagGroup model. Bags can be viewed in-line.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Only by superusers
    '''

    list_display = [
        'name',
        linkify('created_by'),
        'number_of_bags_in_group',
    ]

    search_fields = [
        'name',
        'uuid',
    ]

    ordering = [
        '-created_by',
    ]

    inlines = [
        SubmissionInline,
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return obj and (request.user.is_superuser or request.user.has_perm('recordtransfer.delete_baggroup'))


class BagGroupInline(admin.TabularInline):
    ''' Inline admin for the Appraisal model. Used to edit Appraisals associated
    with a Submission. Deletions are not allowed.

    Permissions:
        - add: Not allowed
        - change: Not allowed - go to BagGroup page for change ability
        - delete: Not allowed - go to BagGroup page for delete ability
    '''
    model = BagGroup
    max_num = 0
    show_change_link = True

    form = InlineBagGroupForm

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Job)
class JobAdmin(ReadOnlyAdmin):
    ''' Admin for the Job model. Adds a view to download the file associated
    with the job, if there is a file. The file download view can be accessed at
    code:`job/<id>/download/`

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Only if current user created job
    '''
    change_form_template = 'admin/job_change_form.html'

    list_display = [
        'name',
        'start_time',
        'user_triggered',
        'job_status',
    ]

    ordering = [
        '-start_time'
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return obj and (request.user == obj.user_triggered or request.user.is_superuser)

    def get_urls(self):
        ''' Add download/ view to admin
        '''
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        report_url = [
            path('<path:object_id>/download/',
                 self.admin_site.admin_view(self.download_file),
                 name='%s_%s_download' % info),
        ]
        return report_url + urls

    def download_file(self, request, object_id):
        ''' Download an application/x-zip-compressed file for the job, if the
        file and the job exist

        Args:
            request: The originating request
            object_id: The ID for the job
        '''
        job = Job.objects.filter(id=object_id).first()
        if job and job.attached_file:
            file_path = Path(MEDIA_ROOT) / job.attached_file.name
            file_handle = open(file_path, "rb")
            response = HttpResponse(file_handle, content_type='application/x-zip-compressed')
            response['Content-Disposition'] = f'attachment; filename="{file_path.name}"'
            return response
        if job:
            msg = gettext('Could not find a file attached to the Job with ID “%(key)s”') % {
                'key': object_id
            }
            self.message_user(request, msg, messages.WARNING)
            return HttpResponseRedirect('../')
        # Error response
        msg = gettext('Job with ID “%(key)s” doesn’t exist. Perhaps it was deleted?') % {
            'key': object_id,
        }
        self.message_user(request, msg, messages.WARNING)
        url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def get_fields(self, request, obj=None):
        ''' Hide the attached file field, the user is not allowed to interact
        directly with it. If a user wants this file, they should use the
        download/ view.
        '''
        fields = list(super().get_fields(request, obj))
        exclude_set = set()
        if obj:
            exclude_set.add('attached_file')
        return [f for f in fields if f not in exclude_set]


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ''' Admin for the User model.

    Permissions:
        - change: Allowed if editing own account, or if editor is a superuser
        - delete: Allowed by superusers
    '''

    change_form_template = 'admin/user_change_form.html'

    fieldsets = (
        *UserAdmin.fieldsets, # original form fieldsets, expanded
        (                     # New fieldset added on to the bottom
            'Email Updates',  # Group heading of your choice. set to None for a blank space
            {
                'fields': (
                    'gets_bag_email_updates',
                ),
            },
        ),
    )

    list_display = (
        *UserAdmin.list_display,  # Original user list display fields
        'is_active'  # Add on is_active field to display
    )

    inlines = [
        SubmissionInline,
        BagGroupInline,
    ]

    # Fields that would let a user change their own level of access
    permission_fields = ('is_staff', 'is_superuser', 'groups', 'user_permissions')

    def get_readonly_fields(self, request, obj=None):
        ''' Prevent a user from editing their own permission-related fields, even
        though they otherwise have permission to change their own account. Without
        this, a non-superuser could grant themselves extra groups/permissions.

        Also prevents any non-superuser from granting or revoking superuser status
        on any account, including their own.
        '''
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and 'is_superuser' not in readonly_fields:
            readonly_fields.append('is_superuser')
        if obj and obj == request.user and not request.user.is_superuser:
            readonly_fields += [
                field for field in self.permission_fields if field not in readonly_fields
            ]
        if obj and not request.user.is_superuser and 'user_permissions' not in readonly_fields:
            readonly_fields.append('user_permissions')
        return readonly_fields

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        if request.user.is_superuser or obj == request.user:
            return True
        if obj.is_superuser:
            return False
        return request.user.has_perm('recordtransfer.change_user')

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not obj:
            return request.user.has_perm('recordtransfer.delete_user')
        if obj.is_staff or obj.is_superuser or obj == request.user:
            return False
        return request.user.has_perm('recordtransfer.delete_user')

    @method_decorator(sensitive_post_parameters())
    def user_change_password(self, request, id, form_url=''):
        """ Send a notification email when a user's password is changed. """
        response = super().user_change_password(request, id, form_url)
        user = self.get_object(request, unquote(id))
        form = self.change_password_form(user, request.POST)
        if form.is_valid() and request.method == 'POST':
            context = {
                'subject': gettext("Password updated"),
                'changed_item': gettext("password"),
                'changed_status': gettext("updated")
            }
            send_user_account_updated.delay(user, context)
        return response

    def save_model(self, request, obj, form, change):
        ''' Enforce superuser permissions checks and send notification emails
        for other account updates
        '''
        if change and obj.is_superuser and not request.user.is_superuser:
            messages.set_level(request, messages.ERROR)
            msg = 'Non-superusers cannot modify superuser accounts.'
            self.message_user(request, msg, messages.ERROR)
        else:
            super().save_model(request, obj, form, change)
            if change and (not obj.is_active or "is_superuser" in form.changed_data or \
                           "is_staff" in form.changed_data):
                if not obj.is_active:
                    context = {
                        'subject': gettext("Account Deactivated"),
                        'changed_item': gettext("account"),
                        'changed_status': gettext("deactivated")
                    }
                else:
                    context = {
                        'subject': gettext("Account updated"),
                        'changed_item': gettext("account"),
                        'changed_status': gettext("updated"),
                        'changed_list': self._get_changed_message(form.changed_data, obj)
                    }

                send_user_account_updated.delay(obj, context)

    def _get_changed_message(self, changed_data: list, user: User):
        """ Generate a list of changed status message for certain account details. """
        message_list = []
        if "is_superuser" in changed_data:
            if user.is_superuser:
                message_list.append(
                    gettext("Superuser privileges have been added to your account.")
                )
            else:
                message_list.append(
                    gettext("Superuser privileges have been removed from your account.")
                )
        if "is_staff" in changed_data:
            if user.is_staff:
                message_list.append(
                    gettext("Staff privileges have been added to your account.")
                )
            else:
                message_list.append(
                    gettext("Staff privileges have been removed from your account.")
                )
        return message_list

    def get_urls(self):
        """
        Add new function urls to admin
        """
        return [
            path('<path:user_id>/resend_confirmation/',
                 self.admin_site.admin_view(self.resend_confirmation_email),
                 name='auth_user_resend_confirmation'),
        ] + super().get_urls()

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            user = User.objects.get(pk=object_id)
            if (request.user.is_superuser or request.user.is_staff) and not user.confirmed_email:
                if extra_context is None:
                    extra_context = {}
                if user is not None:
                    extra_context['resend_confirmation'] = user.get_resend_confirmation_uri()
        except User.DoesNotExist:
            pass
        return super().changeform_view(request, object_id, form_url, extra_context)

    def resend_confirmation_email(self, request, user_id):
        """ Resend the user confirmation email. """
        if request.user.is_superuser or request.user.is_staff:
            try:
                user = User.objects.get(pk=user_id)
                if not user.confirmed_email:
                    LOGGER.info(msg=f"Resending email confirmation to {user.email}")
                    messages.info(request, gettext("Email confirmation sent to user."))
                    send_user_activation_email(user)
                    return HttpResponseRedirect(
                        reverse(
                            "%s:%s_%s_change"
                            % (
                                self.admin_site.name,
                                user._meta.app_label,
                                user._meta.model_name,
                            ),
                            args=(user.pk,),
                        )
                    )
                else:
                    messages.warning(request, gettext("User has already confirmed their email."))
                    LOGGER.debug(msg=f"Requested resend link for user ID {user_id} who has already confirmed their " +
                                     "email or could not be found.")
            except User.DoesNotExist:
                messages.error(request, gettext("User does not exist."))
                LOGGER.warning(msg=f"User attempted to resend email confirmation to user id {user_id} which does not " +
                                   "exist.")
        else:
            messages.warning(request, gettext("You do not have permission to resend email confirmations."))
            LOGGER.warning(msg=f"User {request.user} attempted to resend email confirmation to user id {user_id}")

        return HttpResponseRedirect(
            reverse(
                "%s:%s_%s_change"
                % (
                    self.admin_site.name,
                    user._meta.app_label,
                    user._meta.model_name,
                ),
                args=(user.pk,),
            )
        )


admin.site.unregister(Group)


@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    ''' Admin for the Group model.

    Permissions:
        - change: Allowed, but non-superusers cannot edit the group's permissions
    '''

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and 'permissions' not in readonly_fields:
            readonly_fields.append('permissions')
        return readonly_fields
