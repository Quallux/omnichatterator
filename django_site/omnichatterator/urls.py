from django.contrib import admin
from django.urls import path
from . import view
from . import messenger_login_verification

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', view.default_page),
    path('login/', view.login),
    path('welcome/',view.welcome_page),
    path('get_authorization_url/', view.get_authorization_url),  # only for post request from login.js
    path('conversation/', view.get_conversation),
    path('recieve_msg/', view.recieve_messages),
    path('send_msg/', view.send_message),
    path('logout/', view.logout),
    path('check-messenger-login-status/', messenger_login_verification.check_messenger_login_status),
    path('messenger_choose_page/', view.messenger_choose_page),
    path('gmail_exchange_token/', view.gmail_exchange_tokens)
]
