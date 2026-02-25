''' Forms specific to transferring files with a new submission '''
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3
from django import forms
from django.utils.translation import gettext
from bagitobjecttransfer.settings.base import RECAPTCHA_PUBLIC_KEY, RECAPTCHA_PRIVATE_KEY


class TransferForm(forms.Form):
    required_css_class = 'required-field'


class AcceptLegal(TransferForm):
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data['agreement_accepted']:
            self.add_error('agreement_accepted', 'You must accept before continuing')

    agreement_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(),
        label=gettext('I accept these terms'),
    )


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


class CachedReCaptchaField(ReCaptchaField):
    """
    Wrapper around ReCaptchaField that stores successfully validated tokens
    on the current request object to avoid repeated remote verification when
    the formwizard re-validates steps during final submission. This is request-
    scoped, short-lived (lives only for the request) and avoids process-global
    state.
    """
    def _get_request_from_stack(self):
        # Walk the frame stack looking for a 'request' local, similar to what's
        # done elsewhere in this codebase and in the original ReCaptchaField.
        import sys
        f = sys._getframe()
        while f:
            request = f.f_locals.get('request')
            if request is not None:
                return request
            f = f.f_back
        return None

    def validate(self, value):
        # Try to find the current request; if found, use a per-request set to
        # remember validated tokens for the lifetime of the request.
        request = self._get_request_from_stack()
        if request is not None:
            token_set = getattr(request, '_recaptcha_validated_tokens', None)
            if token_set is not None and value in token_set:
                # Token already validated earlier in this request; skip external call
                return

        # Perform the normal validation (this will call client.submit)
        super().validate(value)

        # If validation succeeded, mark token as validated on the request.
        if request is not None:
            if not hasattr(request, '_recaptcha_validated_tokens'):
                setattr(request, '_recaptcha_validated_tokens', set())
            request._recaptcha_validated_tokens.add(value)


class UploadFilesForm(TransferForm):
    ''' The form where users upload their files and add a title '''
    submission_title = forms.CharField(
        required=True,
        min_length=4,
        widget=forms.TextInput(
            attrs={
                'placeholder': gettext('Example title'),
            }
        ),
        label=gettext('Submission title')
    )

    session_token = forms.CharField(
        required=True,
        widget=forms.HiddenInput(),
        label='hidden'
    )

    captcha = CachedReCaptchaField(
        widget=ReCaptchaV3(attrs={'data-callback': ''}),
        label='hidden',
        public_key=RECAPTCHA_PUBLIC_KEY,
        private_key=RECAPTCHA_PRIVATE_KEY
    )
