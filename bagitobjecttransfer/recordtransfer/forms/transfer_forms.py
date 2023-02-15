''' Forms specific to transferring files with a new submission '''
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Invisible
from django import forms
from django.utils.translation import gettext

from recordtransfer.forms.metadata_forms import TransferForm


class GroupTransferForm(TransferForm):
    def __init__(self, *args, **kwargs):
        users_groups = kwargs.pop('users_groups')
        super().__init__(*args, **kwargs)
        self.fields['group_name'].choices = [
            ('No Group', gettext('-- None Selected --')),
            ('Add New Group', gettext('-- Add New Group --')),
            *[(x.name, x.name) for x in users_groups],
        ]
        self.allowed_group_names = [x[0] for x in self.fields['group_name'].choices]
        self.fields['group_name'].initial = 'No Group'

    def clean(self):
        cleaned_data = super().clean()
        group_name = cleaned_data['group_name']
        if group_name not in self.allowed_group_names:
            self.add_error('group_name', f'Group name "{group_name}" was not in list')
        if group_name == 'Add New Group' and not cleaned_data['new_group_name']:
            self.add_error('new_group_name', 'Group name cannot be empty')
        if group_name == 'Add New Group' and not cleaned_data['group_description']:
            self.add_error('group_description', 'Group description cannot be empty')
        return cleaned_data

    group_name = forms.ChoiceField(
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'reduce-form-field-width',
            }
        ),
        label=gettext('Assigned group')
    )

    new_group_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': gettext('e.g., My Group'),
            }
        ),
        label=gettext('New group name'),
    )

    group_description = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '2',
            'placeholder': gettext('e.g., this group represents all of the records from...'),
        }),
        label=gettext('New group description'),
    )


class UploadFilesForm(TransferForm):
    ''' The form where users upload their files and write any final notes '''
    general_note = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': gettext('Record any general notes you have about the records here '
                                   '(optional)')
        }),
        help_text=gettext('These should be notes that did not fit in any of the previous steps of '
                          'this form'),
        label=gettext('Other notes'),
    )

    session_token = forms.CharField(
        required=True,
        widget=forms.HiddenInput(),
        label='hidden'
    )

    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible, label='hidden')
