from .logger.logger import log
from .logger.logger_sink import LoggerSink
from . import messenger

from django.http import JsonResponse
import json
import os


def check_messenger_login_status(request):
    if request.method == "POST":
        json_from_request = json.loads(request.body.decode('utf-8'))
        verification_code = json_from_request["verification_code"]
        log(f"checking login status for verification_code: \'{verification_code}\'", LoggerSink.MESSENGER_LOGIN)

        auth_status = messenger.chceck_auth_status(
            os.environ["MESS_APP_ID"],
            os.environ["MESS_CLIENT_TOKEN"],
            verification_code
        )

        # DOCS https://developers.facebook.com/docs/facebook-login/for-devices#tech-step3
        if auth_status.get("access_token"):  # if user has successfully authorized the device
            successful_status_code = 0
            log(f"verification code: '{verification_code}'; user with access token '"
                + str(auth_status.get("access_token")) + f"' was successfully verified;"
                + f" status code: '{successful_status_code}'", LoggerSink.MESSENGER_LOGIN)
            setup_session_variables_on_successful_login(request, auth_status)
            return JsonResponse({"status_code": successful_status_code})
        else:
            log(f"verification status code for verification_code : '{verification_code}' is: '"
                + str(auth_status.get("error").get("code")) + "'", LoggerSink.MESSENGER_LOGIN)
            return JsonResponse({"status_code": auth_status.get("error").get("code")})
    else:
        log(f"unexpected \'{request.method}\' call for login status check", LoggerSink.MESSENGER_LOGIN)


def setup_session_variables_on_successful_login(request, auth_status):
    access_token = auth_status.get("access_token")
    log(f"setting up session variables for user with access token: \'{access_token}\'", LoggerSink.MESSENGER_LOGIN)

    try:
        pages = messenger.get_pages(access_token)
    except Exception as e:
        log("failed to get pages, not setting the session variables", LoggerSink.MESSENGER_LOGIN)
        log(f"failed to get messenger pages:\n{e}", LoggerSink.PLATFORM_ERRS)
        return

    request.session["TMP_MSNGR_USR_TOKEN"] = access_token
    request.session["TMP_MSNGR_USR_PAGES"] = pages["data"]

    log(f"session variables for user with access token: \'{access_token}\' were set", LoggerSink.MESSENGER_LOGIN)
