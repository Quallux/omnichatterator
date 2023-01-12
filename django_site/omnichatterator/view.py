from . import twitter
from . import gmail
from . import messenger

import tweepy

from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.http import JsonResponse
import json
import os
import time, datetime
import traceback
from django.conf import settings
from .logger.logger import log
from .logger.logger_sink import LoggerSink


def welcome_page(request):
    return render(request,"welcome.html")

def default_page(request):    
    
    # GMAIL LOGIN HANDLING
    if request.method == "GET" and request.GET.get("code") != None:
        response = redirect(login)
        response["Location"] += f"?code={request.GET.get('code')}"
        return response
    
    connected = []
    auth_check = verify_login(request,"all")
    if auth_check["authed"] == False:
        return redirect(welcome_page)
    else:
        twitter_auth = auth_check["platforms"].get("twitter")
        if twitter_auth:
            connected.append("twitter")
        gmail_auth = auth_check["platforms"].get("gmail")
        if gmail_auth:
            connected.append("gmail")
        messenger_auth = auth_check["platforms"].get("messenger")
        if messenger_auth:
            connected.append("messenger")

    log("connected: "+str(connected),LoggerSink.VIEW)

    user_ids = {}
    contacts = []
    profile_pics = {}
    
    if gmail_auth == True:
        try:
            user_token = request.session["GM_ACCESS_T"]
            gmail_service = gmail.get_service(gmail.get_creds(user_token))
            gm_contacts = gmail.getContacts(gmail_service)
            log("gmail contacts:\n"+str(gm_contacts),LoggerSink.VIEW)
            contacts.extend(gm_contacts)
        except Exception as e:
            log(f"Failed getting gmail contacts, not sending them to frontend", LoggerSink.VIEW)
            log(f"Failed getting gmail contacts:\n{e}", LoggerSink.PLATFORM_ERRS)
        # CREATE GMAIL COOKIE
        profile_pics["gmail"] = "a"  # it needs to have any non empty value if logged with gmail; used in template condition
        try:
            if "gmail" not in request.COOKIES:
                #log("Creating gmail cookie", LoggerSink.VIEW)
                user_ids["gmail"] = gmail.getProfile(gmail_service)
        except Exception as e:
            log(f"Failed getting gmail logged user info, not sending it to frontend", LoggerSink.VIEW)
            log(f"Failed getting gmail logged user info:\n{e}", LoggerSink.PLATFORM_ERRS)
            messenger_auth = False
    
    
    # START POLLING & GET CONTACTS AND PIC FOR TWIITER
    if twitter_auth == True:
        try:
            polling_result = twitter.start_polling(
                request.session['TW_ACCESS_T'],
                request.session["TW_ACCESS_T_SECRET"]
            )
            profile_pics["twitter"] = polling_result[1]
            if "twitter" not in request.COOKIES:
                user_ids["twitter"] = str(polling_result[0])
        except Exception as e:
            log(f"Failed getting twitter logged user info, not sending it to frontend", LoggerSink.VIEW)
            log(f"Failed getting twitter logged user info:\n{e}", LoggerSink.PLATFORM_ERRS)
            messenger_auth = False
        try:
            tw_contacts = twitter.get_contacts(
                None,
                request.session['TW_ACCESS_T'],
                request.session["TW_ACCESS_T_SECRET"]
            )
            contacts.extend(tw_contacts)
        except Exception as e:
            log(f"Failed getting twitter contacts, not sending them to frontend", LoggerSink.VIEW)
            log(f"Failed getting twitter contacts:\n{e}", LoggerSink.PLATFORM_ERRS)
    
    #GET CONTACTS AND PIC FOR MESSENGER
    if messenger_auth == True:
        try:
            ms_contacts = messenger.get_contacts(
                request.session['MS_ACCESS_T'],
            )
            contacts.extend(ms_contacts)
        except Exception as e:
            log(f"Failed getting messenger contacts, not sending them to frontend", LoggerSink.VIEW)
            log(f"Failed getting messenger contacts:\n{e}", LoggerSink.PLATFORM_ERRS)
        try:
            ms_me = messenger.get_myself(
                request.session['MS_ACCESS_T'],
            )
            profile_pics["messenger"] = ms_me[1]
            if "messenger" not in request.COOKIES:
                user_ids["messenger"] = str(ms_me[0])
        except Exception as e:
            log(f"Failed getting messenger logged user info, not sending it to frontend", LoggerSink.VIEW)
            log(f"Failed getting messenger logged user info:\n{e}", LoggerSink.PLATFORM_ERRS)
            messenger_auth = False
    
    contacts.sort(key= lambda elem: elem["timeStamp"],reverse=True)
    for contact in contacts:
        if len(contact["lastMessage"])>25:
            contact["lastMessage"] = contact["lastMessage"][:25]+"..."
        if len(contact["name"]) > 20:
            contact["name"] = contact["name"][:20]+"..."
    log("contacts:\n"+str(contacts),LoggerSink.VIEW)

    response = render(
        request,
        'default_page.html',
        {
            'contacts': contacts,
            'twitter_profile_pic':profile_pics.get("twitter"),
            'messenger_profile_pic':profile_pics.get("messenger"),
            'gmail_profile_pic':profile_pics.get("gmail"),
            'connected_platforms':connected
        }
    )
    
    if twitter_auth == True and "twitter" not in request.COOKIES:
        response.set_cookie('twitter', user_ids["twitter"])
    if gmail_auth == True and "gmail" not in request.COOKIES:
        response.set_cookie('gmail', user_ids["gmail"])
    if messenger_auth == True and "messenger" not in request.COOKIES:
        response.set_cookie('messenger', user_ids["messenger"])
        
    return response

def send_message(request):
    if request.method == 'POST':

        if request.content_type != 'application/json':
            log("not json!",LoggerSink.VIEW)
            return HttpResponse(status=400)
        reqJson = json.loads(request.body.decode('utf-8'))
        log("DATA HERE:", LoggerSink.VIEW)
        log(str(reqJson), LoggerSink.VIEW)
        if 'message' not in reqJson or 'senderId' not in reqJson or 'platform' not in reqJson:
            log("something missing form json",LoggerSink.VIEW)
            return HttpResponse(status=400)

        message = reqJson['message']
        sender_id = reqJson['senderId']
        platform = reqJson['platform'].lower()
        log(sender_id, LoggerSink.VIEW)
        result = None
        try:
            if platform == "twitter":
                result = twitter.send_msg(
                    message,
                    sender_id,
                    request.session['TW_ACCESS_T'],
                    request.session["TW_ACCESS_T_SECRET"]
                )

                if not hasattr(result,"id"):
                    raise Exception(f"unexpected result:\n{result}")

                result = result.id

            elif platform == "messenger":
                result = messenger.send_msg(
                    message,
                    int(sender_id),
                    request.session['MS_ACCESS_T']
                ).get("message_id")
                
                if not result:
                    raise Exception(f"unexpected result:\n{result}")
                    
            elif platform == "gmail":
                #TODO GMAIL: send gmail 'message' to 'senderId'
                result = gmail.sendingMessage(
                    sender_id.split("|")[0],
                    message,
                    gmail.get_creds(request.session["GM_ACCESS_T"]),
                    sender_id.split("|")[1]
                ).get("message_id")

                if not result:
                    raise Exception(f"unexpected result:\n{result}")
            else:
                log("Unknown platform '"+platform+"'", LoggerSink.VIEW)
                return HttpResponse(status=400)
        except Exception as e:
            log(f"Error sending message: {e}", LoggerSink.VIEW)
            if not verify_login(request,platform).get("authed"):
                log(platform+" user not authed, requesting front-end logout", LoggerSink.VIEW)
                return HttpResponse(status=511)
            return HttpResponse(status=500)
    else:
        log("not post!",LoggerSink.VIEW)
        return HttpResponse(status=400)
    log("send result:\n"+str(result), LoggerSink.VIEW)
    return JsonResponse(
            {
                "message_id": result
            }
        )

def transform_messages(messages,request):
    #check which platform are the messages from
    if type(messages) is type(dict()) and messages.get("data") != None:
        #transforming facebook messages
        log("transforming facebook messages",LoggerSink.VIEW)
        results =[]
        senderIds = set()
        senders = []
        for convo in messages["data"]:
            for msg in convo["messages"]["data"]:
                sender = None
                if str(msg["from"]['id']) not in senderIds:
                    try:
                        sender = messenger.get_user(
                            msg["from"]["id"],
                            request.session['MS_ACCESS_T']
                        )
                    except Exception as e:
                        log(f"Failed getting messenger user info, going with 'none' user", LoggerSink.VIEW)
                        log(f"Failed getting messenger user info:\n{e}", LoggerSink.PLATFORM_ERRS)
                        sender = {"id":0,"name":None,"picture":{"data":{"url":""}}}
                    senders.append(sender)
                    senderIds.add(str(msg["from"]["id"]))
                else:
                    for s in senders:
                        if str(s["id"]) == str(msg["from"]["id"]):
                            sender = s
                            break

                results.append({
                    #id of this message
                    "messageId": str(msg["id"]),
                    #timestamp of this message
                    "timeStamp": str(int(datetime.datetime.strptime(msg["created_time"], "%Y-%m-%dT%H:%M:%S%z").timestamp()*1000)),
                    #id of sender of this message
                    "senderId": str(sender["id"]),
                    #name of sender of this message
                    "senderName": sender["name"],
                    #profile pic of sender coded in base64
                    "avatar": sender["picture"]["data"]["url"],
                    #actual message
                    "message": msg["message"],
                    #adding also attachments for future use
                    "attachments": msg['attachments']['data'] if ('attachments' in msg) else {}
                })
        results.sort(key= lambda elem: elem["timeStamp"],reverse=True)
        return results
    elif not messages:  #messages empty - not transofrming
        return messages
    elif type(messages) is type(list()) and hasattr(messages[0],"message_create"):
        #transofrming twitter messges
        log("transforming twitter messages",LoggerSink.VIEW)
        results =[]
        senderIds = set()
        senders = []
        for msg in messages:
            sender = None
            if str(msg.message_create['sender_id']) not in senderIds:
                try:
                    sender = twitter.get_user(
                        msg.message_create['sender_id'],
                        request.session['TW_ACCESS_T'],
                        request.session["TW_ACCESS_T_SECRET"]
                    )
                except Exception as e:
                    log(f"Failed getting twitter user info, going with 'none' user", LoggerSink.VIEW)
                    log(f"Failed getting twitter user info:\n{e}", LoggerSink.PLATFORM_ERRS)
                    class NoneSender:
                        id=0
                        name = None
                        profile_image_url_https = ""
                    sender = NoneSender()
                senders.append(sender)
                senderIds.add(str(msg.message_create['sender_id']))
            else:
                for s in senders:
                    if str(s.id) == str(msg.message_create['sender_id']):
                        sender = s
                        break

            results.append({            #<<<<<------------------------------------------------------------established format for recieved messages
                #id of this message
                "messageId": str(msg.id),
                #timestamp of this message
                "timeStamp": msg.created_timestamp,
                #id of sender of this message
                "senderId": str(sender.id),
                #name of sender of this message
                "senderName": sender.name,
                #profile pic of sender coded in base64
                "avatar": sender.profile_image_url_https.replace("_normal", ""),
                #actual message
                "message": msg.message_create['message_data']['text'],
                #adding also attachments for future use
                "attachments": msg.message_create['message_data']['attachment'] if ('attachment' in msg.message_create['message_data']) else {}
            })
        return results
    elif type(messages) is type(list()) and messages[0].get("thread_id") != None:
        #transforming gmail messages
        log("transforming gmail messages",LoggerSink.VIEW)
        results =[]
        for convo in messages:
            log("convo:\n"+str(convo),LoggerSink.VIEW)
            for msg in convo["messages"]:
                results.append({
                    #id of this message
                    "messageId": msg["id"],
                    #timestamp of this message
                    "timeStamp": msg["timeStamp"],
                    #id of sender of this message
                    "senderId": msg["from"]+"|"+str(convo["thread_id"]),
                    #name of sender of this message
                    "senderName": msg["from"],
                    #profile pic of sender coded in base64
                    "avatar": None,
                    #actual message
                    "message": msg["message"] if msg.get("mime_type") != "text/html" else "",
                    #adding also attachments for future use
                    "attachments": {} if msg.get("mime_type") != "text/html" else msg["message"]
                })
        results.sort(key= lambda elem: elem["timeStamp"],reverse=True)
        return results
    else:
        log("unknown message format:\n" + str(messages),LoggerSink.VIEW)
        return None

def get_conversation(request):
    if request.method == "GET":
        with_id = request.GET.get("with")
        platform = request.GET.get("platform")
        logouts =[]
        log("convo with: "+with_id,LoggerSink.VIEW)
        if not with_id or not platform:
            log("bad params!",LoggerSink.VIEW)
            return HttpResponse(status=400)
        try:
            if platform.lower() == "twitter":
                try:
                    messages = twitter.get_messages(
                        "0",
                        True,
                        request.session["TW_ACCESS_T"],
                        request.session["TW_ACCESS_T_SECRET"]
                    )
                    if messages is None:
                        return HttpResponse(status=400)
                    me2me = list(filter(
                        lambda msg: msg.message_create['sender_id']==with_id and msg.message_create["target"]["recipient_id"]==with_id,
                        messages
                    ))
                    if me2me:
                        messages = me2me
                    else:
                        messages = list(filter(
                            lambda msg: msg.message_create['sender_id']==with_id or msg.message_create["target"]["recipient_id"]==with_id,
                            messages
                        ))
                except Exception as e:
                    log(f"Failed getting twitter convo, verifing user login", LoggerSink.VIEW)
                    log(f"Failed getting twitter convo:\n{e}", LoggerSink.PLATFORM_ERRS)
                    #check if user auth is still valid
                    if not verify_login(request,"twitter").get("authed"):
                        log("twitter user not authed, requesting front-end logout", LoggerSink.VIEW)
                        logouts.append("twitter")
            elif platform.lower() in ["facebook","messenger"]:
                try:
                    messages = messenger.get_messages(
                        "0",
                        True,
                        request.session['MS_ACCESS_T'],
                        with_id
                    )
                except Exception as e:
                    log(f"Failed getting messenger convo, verifing user login", LoggerSink.VIEW)
                    log(f"Failed getting messenger convo:\n{e}", LoggerSink.PLATFORM_ERRS)
                    #check if user auth is still valid
                    if not verify_login(request,"messenger").get("authed"):
                        log("messenger user not authed, requesting front-end logout", LoggerSink.VIEW)
                        logouts.append("messenger")

            elif platform.lower() == "gmail":
                #TODO GMAIL: get gmail(messages from / conversation with) 'with_id'
                try:
                    messages = gmail.getConversation(
                        gmail.get_service(gmail.get_creds(request.session["GM_ACCESS_T"])),
                        with_id.split("|")[1],
                        None
                    )
                except Exception as e:
                    log(f"Failed getting gmail convo, verifing user login", LoggerSink.VIEW)
                    log(f"Failed getting gmail convo:\n{e}", LoggerSink.PLATFORM_ERRS)
                    #check if user auth is still valid
                    if not verify_login(request,"gmail").get("authed"):
                        log("gmail user not authed, requesting front-end logout", LoggerSink.VIEW)
                        logouts.append("gmail")
            else:
                log("Unknown platform '"+platform+"'",LoggerSink.VIEW)
                return HttpResponse(status=400) 
        except Exception as e:
            log(f"Error getting conversation: {e}", LoggerSink.VIEW)
            return HttpResponse(status=500)
        messages = transform_messages(messages,request)
        log("convo messages:\n"+str(messages),LoggerSink.VIEW)
        if messages is None:
            return HttpResponse(status=400)
        return JsonResponse(
            {
                #list of convo messages
                "messageList": messages,
                "logoutPlatforms": logouts
            }
        )              
    return HttpResponse(status=400)

def recieve_messages(request):
    if request.method == 'POST':
        if request.content_type != 'application/json':
            return HttpResponse(status=400)
        reqJson = json.loads(request.body.decode('utf-8'))
        log(str(reqJson), LoggerSink.VIEW)
        if 'timeStamps' not in reqJson:
            return HttpResponse(status=400)
        timestamps = reqJson['timeStamps']
        #log("timestamp converted: "+str(datetime.datetime.fromtimestamp(int(timestamp)/1000)), LoggerSink.VIEW)
        # log("TIMESTAMP: " + timestamp)
        
        #twitter.user_log(recipientId,f"Got frontend call - {timestamp}","view.receiver_message()") #user,thing,tag
        
        results =[]
        logouts =[]
        try:
            if request.session.get("TW_ACCESS_T"):
                log("recieving for twitter",LoggerSink.VIEW)
                try:
                    messages = twitter.get_messages(
                        timestamps["twitter"],
                        False,
                        request.session["TW_ACCESS_T"],
                        request.session["TW_ACCESS_T_SECRET"]
                    )
                
                    #twitter.user_log(recipientId,f"TW_ACCESS_T - {request.session['TW_ACCESS_T']}","view.receiver_message()") #user,thing,tag
                    #twitter.user_log(recipientId,f"TW_ACCESS_T_SECRET - {request.session['TW_ACCESS_T_SECRET']}","view.receiver_message()") #user,thing,tag
                        
                    #if len(messages) > 0:
                        #twitter.user_log(recipientId,f"Last received message - {messages[-1]}","view.receiver_message()") #user,thing,tag
                    messages = transform_messages(messages,request)
                    if messages:
                        results.append({"platform":"twitter","messages": messages})
                except Exception as e:
                    log(f"Failed receiving twitter msgs, not sending", LoggerSink.VIEW)
                    log(f"Failed receiving twitter msgs:\n{e}", LoggerSink.PLATFORM_ERRS)


            if request.session.get("MS_ACCESS_T"):
                log("recieving for messenger",LoggerSink.VIEW)
                try:
                    messages = messenger.get_messages(
                        timestamps["messenger"],
                        False,
                        request.session['MS_ACCESS_T']
                    )
                    messages = transform_messages(messages,request)
                    if messages:
                        results.append({"platform":"messenger","messages": messages})
                except Exception as e:
                    log(f"Failed receiving messenger msgs, not sending", LoggerSink.VIEW)
                    log(f"Failed receiving messenger msgs:\n{e}", LoggerSink.PLATFORM_ERRS)
            
            if request.session.get("GM_ACCESS_T"):
                #TODO GMAIL: get gmail messages recieved since 'timestamp' AND append them to results
                try:
                    messages =  gmail.getNewThreads(
                        gmail.get_service(gmail.get_creds(request.session["GM_ACCESS_T"])),
                        timestamps["gmail"]
                    )
                    messages = transform_messages(messages,request)
                    #log("transformed:\n"+str(messages),LoggerSink.VIEW)
                    if messages:
                        results.append({"platform":"gmail","messages": messages})
                except Exception as e:
                    log(f"Failed receiving gmail msgs, not sending", LoggerSink.VIEW)
                    log(f"Failed receiving gmail msgs:\n{e}", LoggerSink.PLATFORM_ERRS)
            
            # log(str(results), LoggerSink.VIEW)
        except Exception as e:
            log(f"Error getting messages: {e}", LoggerSink.VIEW)
            traceback.print_exc()
            return HttpResponse(status=500)
        if len(results) == 0:
            return HttpResponse(status=204)
        return JsonResponse(
            {
                #list of all messages
                "messageList": results,
            }
        )
    return HttpResponse(status=400)

def login(request):
    
    try:
        del request.session["TMP_MSNGR_USR_TOKEN"]
        del request.session["TMP_MSNGR_USR_PAGES"]
    except:
        pass
    
    log("login", LoggerSink.VIEW)
    request.session.clear_expired()
    for key, value in request.session.items():
        log('{} => {}'.format(key, value), LoggerSink.VIEW)
        
    # GMAIL LOGIN HANDLING
    if request.method == 'GET':
        
        if request.GET.get("code"):
            log(f"Auth token: {request.GET.get('code')}",LoggerSink.VIEW)
            creds = gmail.exchange_tokens(request.GET.get("code"))
            
            if creds != False:
                request.session["GM_ACCESS_T"] = creds.client_id
                log(creds.client_id, LoggerSink.VIEW)
                
                return redirect(default_page)
                #return JsonResponse( { "login": "true" } )
            else:
                request.session["error"] = "Somethings smells fishy. Try again later."
                return redirect(login)
    
    # TWITTER LOGIN HANDLING
    if request.method == 'POST':
        
        # IF VERIFIER CORRECT
        try:
            verifier = str(request.POST['oauth']).replace(" ", "")

            oauth1_user_handler = oauth_handlers[int(request.POST['auth_id'])]
            access_token, access_token_secret = oauth1_user_handler.get_access_token(
                verifier
            )
            request.session['TW_ACCESS_T'] = access_token
            request.session['TW_ACCESS_T_SECRET'] = access_token_secret
            log(access_token, LoggerSink.VIEW)
            log(access_token_secret, LoggerSink.VIEW)

            log("\n\nSTARTED POLLING\n\n", LoggerSink.VIEW)
            polling_result = twitter.start_polling(
                access_token,
                access_token_secret
            )

            return redirect(default_page)

        # IF VERIFIER INCORRECT
        except Exception as e:
            log("twitter login failed, redirecting to login", LoggerSink.VIEW)
            log("twitter login failed:\n"+str(e), LoggerSink.PLATFORM_ERRS)
            request.session['error'] = "Incorrect authorization PIN for twitter login!"
            return redirect(login)

    auth = False
    auth = verify_login(request,"all")
    
    if auth['authed'] == True:                  # IF SUCCESFULLY AUTHED SOMEWHERE
        #return redirect(default_page)  //cannot log into multiple platforms if this redirect is here
        return render(request, 'login.html')    #for multiple platform
    else:                                       # IF UNSUCCESFULLY AUTHED
        log("NOT LOGGED IN", LoggerSink.VIEW)
        error = ""
        try:
            error = request.session['error']
        except:
            pass
        request.session['error'] = ""
        return render(request, 'login.html', {'error': error})

def logout(request):
    platform = request.GET.get("platform")
    
    print("PRINTING SESS VARS:")
    for key,val in request.session.items():
        print(key +" ===> "+ val)
    
    if platform:
        try:
            if platform.lower() == "twitter":
                del request.session['TW_ACCESS_T']
                del request.session['TW_ACCESS_T_SECRET']
                return HttpResponse(status=200)
            elif platform.lower() == "messenger":
                del request.session['MS_ACCESS_T']
                return HttpResponse(status=200)
            elif platform.lower() == "gmail":
                del request.session['GM_ACCESS_T']
                return HttpResponse(status=200)
            else:
                log("Unknown platform '"+platform+"'", LoggerSink.VIEW)
                return HttpResponse(status=400)
        except Exception as e:
            log(f"Logout failed: {e}",LoggerSink.VIEW)
            return HttpResponse(status=500)

    request.session.flush()
    
    return redirect(login)

def get_authorization_url(request):
    request.session['error'] = ""
    global oauth_handlers
    
    log("get_authorization_url()", LoggerSink.VIEW)
    
    oauth_id = 1
    try:
        oauth_id = max(oauth_handlers,key=oauth_handlers.get) + 1
    except Exception as e:
        oauth_handlers = {}
    
    if request.method == 'POST':
        
        reqJson = json.loads(request.body.decode('utf-8'))
        
        if reqJson["platform"] == "twitter":
            oauth1_user_handler = tweepy.OAuth1UserHandler(
                    os.environ["API_KEY"], os.environ["API_SECRET"],
                    callback="oob"
                )
            
            oauth_handlers.update({oauth_id:oauth1_user_handler})
            
            authorization_url = oauth1_user_handler.get_authorization_url(signin_with_twitter=True)
            return JsonResponse(
                {
                    "authorization_url": str(authorization_url),
                    "auth_id":str(oauth_id)
                }
            )
            
        elif reqJson["platform"] == "gmail":
            try:
                log("Calling gmail.gmail_login()", LoggerSink.VIEW)
                auth_url = gmail.gmail_login()
                
                return JsonResponse( { "login" : auth_url } )
                
                """
                if creds != False:
                    request.session["GM_ACCESS_T"] = creds.client_id
                    log(creds.client_id, LoggerSink.VIEW)
                    
                    #return JsonResponse( { "login": "FROG" } )
                    return JsonResponse( { "login": "true" } )
                else:
                    request.session["error"] = "Too many logins in progress. Try again later."
                    return JsonResponse( { "login" : "false" } )
                """
            
            except Exception as e:                    
                print(e)
                log("PROBLEM RETURNING GMAIL CREDS", LoggerSink.VIEW)
                log(str(e), LoggerSink.VIEW)
                request.session['error'] = "Gmail authorization failed!"
           
            return JsonResponse( { "login": "false" } )
        
        elif reqJson["platform"] == "messenger":
            try:
                log("getting authorization url", LoggerSink.MESSENGER_LOGIN)
                auth = messenger.get_auth(os.environ["MESS_APP_ID"], os.environ["MESS_CLIENT_TOKEN"])
                log("returning auth: " + str(auth), LoggerSink.MESSENGER_LOGIN)
                return JsonResponse(auth)
            except Exception as e:
                log("getting messenger auth url failed!", LoggerSink.VIEW)
                log(f"getting messenger auth url failed:\n{e}", LoggerSink.PLATFORM_ERRS)
                return httpResponse(status=500)

def messenger_choose_page(request):
    try:
        tmp_token = request.session["TMP_MSNGR_USR_TOKEN"]
        user = messenger.get_myself(tmp_token)
        pages = request.session["TMP_MSNGR_USR_PAGES"]
        #name = request.session["TMP_MSNGR_NAME"]
        #pic_url = request.session["TMP_MSNGR_PIC_URL"]
    except Exception as e:
        log(f"Messenger TMP user token/pages not found, redirecting to login page.", LoggerSink.VIEW)
        log(f"Messenger TMP user token/pages not found:\n{e}", LoggerSink.PLATFORM_ERRS)
        return redirect(login)
    
    if request.method == "POST":
        try:
            reqJson = json.loads(request.body.decode('utf-8'))
            page_id = reqJson["page_choice"]
            log(f"Page_id choice: {page_id}", LoggerSink.VIEW)
            response = page_access = messenger.get_page_access(page_id,tmp_token)
        except:
            log("Messenger page choice failed, redirecting to login page.", LoggerSink.VIEW)
            log("Messenger page choice failed:\n{e}", LoggerSink.PLATFORM_ERRS)
            return redirect(login)
        
        if response != False:
            del request.session["TMP_MSNGR_USR_TOKEN"]
            del request.session["TMP_MSNGR_USR_PAGES"]
            request.session['MS_ACCESS_T'] = response["access_token"]
            return redirect(default_page)    
        else:
            request.session["error"] = "Messenger authentification failed."
            redirect(login)
    
    return render(request,"choose_pages.html",{"pages":pages,"user_name":user[2],"user_pic":user[1]})

def gmail_exchange_tokens(request):
    if request.method == 'GET':
        
        if request.get("code"):
            log(f"Auth token: {request.get('code')}",LoggerSink.VIEW)
            creds = gmail.exchange_tokens(request.get("code"))
            
            if creds != False:
                request.session["GM_ACCESS_T"] = creds.client_id
                log(creds.client_id, LoggerSink.VIEW)
                return JsonResponse( { "login": "true" } )
            else:
                request.session["error"] = "Somethings smells fishy. Try again later."
                return JsonResponse( { "login" : "false" } )

def verify_login(request,what):
    platforms = {}
    authed = False
    
    if what == "all" or what == "twitter":
        
        tw_api = None
        tw_user = None
        
        """VERIFY TWITTER APP AUTH"""
        try:
            token1 = os.environ["API_KEY"]
            token2 = os.environ["API_SECRET"]
            tw_api = True
        except:
            log("No TWITTER APP creds found in this session!", LoggerSink.VIEW)
            tw_api = False
            
            
        """VERIFY TWITTER USER AUTH"""
        try:
            token1 = request.session['TW_ACCESS_T']
            token2 = request.session['TW_ACCESS_T_SECRET']
            if not twitter.verify_creds(token1,token2):
                del request.session['TW_ACCESS_T']
                del request.session['TW_ACCESS_T_SECRET']
                raise ValueError("Oops! Ur tokens ain't valid no mo")
            tw_user = True
        except Exception as e:
            log("No TWITTER USER creds found in this session!", LoggerSink.VIEW)
            tw_user = False
        finally:
            if tw_api == True and tw_user == True:
                platforms["twitter"] = True
                authed = True
    
    if what == "all" or what == "gmail":
        gm_api = None
        gm_user = None
        
        """VERIFY GMAIL APP AUTH"""
        try:
            with open("unsecured-user-data/client_secret.json","r") as file:
                pass
            gm_api = True
        except Exception as e:
            log("No GMAIL APP creds found in this session!", LoggerSink.VIEW)
            gm_api = False

        """VERIFY GMAIL USER AUTH"""
        try:
            token1 = request.session['GM_ACCESS_T']
            log("TOKEN: " + str(token1),LoggerSink.GMAIL)
            try:
                if not gmail.get_creds(token1):
                    del request.session['GM_ACCESS_T']
                    raise ValueError("Oops! Cannot get ur creds homie")
            except:
                del request.session['GM_ACCESS_T']
                raise ValueError("Oops! Cannot get ur creds homie")
            gm_user = True
        except Exception as e:
            log("No GMAIL USER creds found in this session!", LoggerSink.VIEW)
            gm_user = False
        finally:
            if gm_api == True and gm_user == True:
                platforms["gmail"] = True
                authed = True
                
    if what =="all" or what == "messenger":
        ms_api = None
        ms_user = None
        
        """VERIFY MESS APP AUTH"""
        try:
            token1 = os.environ["MESS_APP_ID"]
            token2= os.environ["MESS_CLIENT_TOKEN"]
            ms_api = True
        except:
            log("No MESSENGER APP creds found in this session!", LoggerSink.VIEW)
            ms_api = False
            
        """VERIFY MESS USER AUTH"""
        try:
            token1 = request.session["MS_ACCESS_T"]
            try:
                if not messenger.get_myself(token1):
                    del request.session['MS_ACCESS_T']
                    raise ValueError("Oops! I dont get u")
            except:
                del request.session['MS_ACCESS_T']
                raise ValueError("Oops! I dont get u")
            ms_user = True
        except:
            log("No MESSENGER USER creds found in this session!", LoggerSink.VIEW)
            ms_user = False
        
        if ms_api == True and ms_user == True:
            platforms["messenger"] = True
            authed = True
        
    return {"authed":authed,"platforms":platforms}
