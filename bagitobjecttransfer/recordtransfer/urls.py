from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views
from . import forms
from . import settings

app_name = 'recordtransfer'
urlpatterns = [
    path('', views.Index.as_view(), name='index'),

    path('transfer/', login_required(views.TransferFormWizard.as_view([
        ('acceptlegal', forms.AcceptLegal),
        ('grouptransfer', forms.GroupTransferForm),
        ('uploadfiles', forms.UploadFilesForm),
    ])), name='transfer'),
    path('transfer/checkfile/', login_required(views.accept_file), name='checkfile'),
    path('transfer/uploadfile/', login_required(views.uploadfiles), name='uploadfile'),
    path('transfer/error/', login_required(views.SystemErrorPage.as_view()), name="systemerror"),
    path('transfer/sent/', views.TransferSent.as_view(), name='transfersent'),

    path('about/', views.About.as_view(), name='about'),
    path('profile/', login_required(views.UserProfile.as_view()), name='userprofile'),
]

if settings.SIGN_UP_ENABLED:
    urlpatterns.extend([
        path('createaccount/', views.CreateAccount.as_view(), name='createaccount'),
        path('createaccount/sent/', views.ActivationSent.as_view(), name='activationsent'),
        path('createaccount/complete/', views.ActivationComplete.as_view(), name='accountcreated'),
        path('createaccount/invalid/', views.ActivationInvalid.as_view(), name='activationinvalid'),
        re_path(('createaccount/'
                'activate/'
                r'(?P<uidb64>[0-9A-Za-z_\-]+)/'
                r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'),
            views.activate_account, name='activateaccount')
    ])
