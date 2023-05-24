"""bagitobjecttransfer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import PasswordResetView
from django.urls import include, path

from bagitobjecttransfer.settings.base import USE_AZURE_AD_LOGIN

urlpatterns = [
    path('admin/django_rq/', include('django_rq.urls')),
    path('admin/', admin.site.urls),
    path('', include('recordtransfer.urls')),
    # HTML email is set to None by default, so we set html_email_template_name here
    path('accounts/password_reset/', PasswordResetView.as_view(
        email_template_name='registration/password_reset_email.txt',
        html_email_template_name='registration/password_reset_email.html',
    )),
    path('accounts/', include('django.contrib.auth.urls')),
]

if USE_AZURE_AD_LOGIN:
    # If using Microsoft login.
    urlpatterns += [
        path("azure-signin/", include("azure_signin.urls", namespace="azure_signin")),
    ]

