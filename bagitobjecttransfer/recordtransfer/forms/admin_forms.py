''' Forms specific to the recordtransfer admin site '''
from django import forms
from django.utils.translation import gettext

from recordtransfer.models import BagGroup, Submission, UploadSession, UploadedFile, User


class RecordTransferModelForm(forms.ModelForm):
    ''' Adds disabled_fields to forms.ModelForm
    '''

    disabled_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk and self.disabled_fields:
            # Disable fields
            for field in self.disabled_fields:
                if field in self.fields:
                    self.fields[field].disabled = True


class UploadedFileForm(RecordTransferModelForm):
    class Meta:
        model = UploadedFile
        fields = (
            'name',
            'session',
            'file_upload'
        )

    exists = forms.BooleanField()


class InlineUploadedFileForm(RecordTransferModelForm):
    class Meta:
        model = UploadedFile
        fields = (
            'name',
        )

    exists = forms.BooleanField()


class UploadSessionForm(RecordTransferModelForm):
    ''' For for vieweing UploadSessions. This form should not be used to provide edit
    capabilities in-line for UploadSessions.
    '''

    class Meta:
        model = UploadSession
        fields = (
            'token',
            'started_at'
        )

    number_of_files_uploaded = forms.IntegerField(required=False)


class SubmissionForm(RecordTransferModelForm):
    ''' Form for editing Submissions. Adds a help_text to the submission with a link to the submission, if the
    submission exists.
    '''

    class Meta:
        model = Submission
        fields = (
            'submission_date',
            'title',
            'extent_statement',
            'user',
            'review_status',
            'part_of_group',
        )

    disabled_fields = ['submission_date', 'title', 'user', 'extent_statement', 'part_of_group']


class InlineSubmissionForm(RecordTransferModelForm):
    ''' Form for viewing Submissions in-line. This form should not be used to provide edit
    capabilities in-line for Submissions.
    '''
    class Meta:
        model = Submission
        fields = (
            'submission_date',
            'title',
            'review_status',
        )
    disabled_fields = ['submission_date']


class InlineBagGroupForm(RecordTransferModelForm):
    ''' Form used to view BagGroups in-line. This form should not be used to provide edit
    capabilities in-line for a BagGroup.
    '''

    class Meta:
        model = BagGroup
        fields = (
            'name',
            'description',
        )

    number_of_bags_in_group = forms.IntegerField(required=False)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'gets_notification_emails',
            'gets_bag_email_updates',
        )
        widgets = {
            'gets_notification_emails': forms.CheckboxInput(),
            'gets_bag_email_updates': forms.CheckboxInput(),
        }
        labels = {
            'gets_notification_emails': 'Gets notification emails',
            'gets_bag_email_updates': 'Gets bag email updates for new bags and bag updates (staff only)',
        }

