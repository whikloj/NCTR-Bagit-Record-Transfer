# Generated by Django 3.2.11 on 2023-02-16 18:27
import logging

from dbtemplates.models import Template
from django.conf import settings
from django.contrib.auth.models import Group, Permission
import django.contrib.auth.validators
from django.contrib.auth.management import create_permissions
from django.contrib.sites.models import Site
from django.db import migrations, models
import django.utils.timezone
import recordtransfer.models
import recordtransfer.storage
import uuid

LOGGER = logging.getLogger(__name__)


def create_groups(apps, schema_editor):
    # Able to transfer
    group, created = Group.objects.get_or_create(name='transfer_user')
    if created:
        LOGGER.info('transfer_user Group created')

    # Archivist
    group, created = Group.objects.get_or_create(name='archivist_user')
    if created:
        LOGGER.info('archivist_user Group created')


def update_local_site(apps, schema_editor):
    local_domain = '127.0.0.1:8000'

    Site.objects.update_or_create(
        pk=1,
        defaults={
            'domain': local_domain,
            'name': 'Record Transfer'
        }
    )


def populate_permissions(apps, schema_editor):
    ''' Add default archivist staff '''
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None
    # emit_post_migrate_signal(1, False, 'default')
    group = Group.objects.get(name='archivist_user')
    existing_permissions = group.permissions.all()

    for codename in (
        # Job
        'add_job',
        'change_job',
        'view_job',
        # UploadedFile
        'view_uploadedfile',
        # UploadSession
        'view_uploadsession',
        # User
        'add_user',
        'change_user',
        'view_user',
        # Appraisal
        'add_appraisal',
        'change_appraisal',
        'view_appraisal',
        # Submission
        'change_submission',
        'view_submission',
    ):
        permission = Permission.objects.get(codename=codename)
        if permission not in existing_permissions:
            group.permissions.add(permission)


RECORDTRANSFER_PREFIX = 'recordtransfer'


def populate_templates(apps, schema_editor):
    ''' Add default editable templates to database '''

    for name, description in (
            ('about', (
                'Page for information relating to the application.'
            )),
            ('activationcomplete', (
                'Page user is re-directed to after activating their account.'
            )),
            ('activationinvalid', (
                'Page user is re-directed to if their account could not be '
                'activated.'
            )),
            ('activationsent', (
                'Page user is re-directed to after submitting their info in '
                'the sign-up form.'
            )),
            ('banner', (
                'Banner displayed at top of every page of site.'
            )),
            ('base', (
                'Base template used for every page of site. Includes the head '
                'so that the title, scripts, meta tags, etc. can be edited.'
            )),
            ('footer', (
                'Footer displayed on every page of site.'
            )),
            ('header', (
                'Navigation header displayed on every page of site.'
            )),
            ('home', (
                'Main homepage or "index" page.'
            )),
            ('transfersent', (
                'Page user is re-directed to after submitting a transfer.'
            )),
            ('transferform_legal', (
                'First page of transfer form that contains legal copy defining '
                'the legal parameters that apply to the transfer. Legal copy '
                'should be defined the form_explanation block.'
            )),
        ):
        template_name = RECORDTRANSFER_PREFIX + '/' + name + '.html'
        template, _ = Template.objects.get_or_create(
            name=template_name,
            description=description,
        )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('gets_bag_email_updates', models.BooleanField(default=False)),
                ('confirmed_email', models.BooleanField(default=False)),
                ('gets_notification_emails', models.BooleanField(default=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='BagGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('description', models.TextField(default='')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UploadSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=32)),
                ('started_at', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='UploadedFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='-', max_length=256, null=True)),
                ('file_upload', models.FileField(null=True, storage=recordtransfer.storage.UploadedFileStorage, upload_to=recordtransfer.models.session_upload_location)),
                ('session', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='recordtransfer.uploadsession')),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submission_date', models.DateTimeField()),
                ('title', models.CharField(max_length=255, null=True)),
                ('review_status', models.CharField(choices=[('NR', 'Not Reviewed'), ('RS', 'Review Started'), ('RC', 'Review Complete')], default='NR', max_length=2)),
                ('uuid', models.UUIDField(default=uuid.uuid4)),
                ('bag_name', models.CharField(max_length=256, null=True)),
                ('part_of_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='recordtransfer.baggroup')),
                ('upload_session', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='recordtransfer.uploadsession')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField(null=True)),
                ('name', models.CharField(max_length=256, null=True)),
                ('description', models.TextField(null=True)),
                ('job_status', models.CharField(choices=[('NS', 'Not Started'), ('IP', 'In Progress'), ('CP', 'Complete'), ('FD', 'Failed')], default='NS', max_length=2)),
                ('attached_file', models.FileField(blank=True, null=True, storage=recordtransfer.storage.OverwriteStorage, upload_to='jobs/zipped_bags')),
                ('submission', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='job', to='recordtransfer.submission')),
                ('user_triggered', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Appraisal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appraisal_type', models.CharField(choices=[('AP', 'Archival Appraisal'), ('MP', 'Monetary Appraisal')], max_length=2)),
                ('appraisal_date', models.DateTimeField(auto_now=True)),
                ('statement', models.TextField()),
                ('note', models.TextField(default='', null=True)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appraisals', to='recordtransfer.submission')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
