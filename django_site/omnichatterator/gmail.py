import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pickle
import os,traceback
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request 
import json
from .logger.logger_sink import LoggerSink
from .logger.logger import log
import socket
from contextlib import closing
import datetime
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError


# https://www.codersarts.com/post/how-to-integrate-gmail-api-with-django
# https://console.cloud.google.com/apis/credentials?authuser=3&project=omnichatterator 
# https://console.cloud.google.com/iam-admin/iam?authuser=3&project=omnichatterator
# https://console.cloud.google.com/apis/credentials/consent?authuser=3&orgonly=true&project=omnichatterator&supportedpurview=organizationId


SCOPES = ['https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/gmail.readonly']
CLIENT_SECRET_FILE = 'unsecured-user-data/client_secret.json'
APPLICATION_NAME = 'Omnichatterator' #'Gmail API Python Send Email'
REDIRECT_URI = "https://omnichatterator.pythonanywhere.com/"

THREAD_IDS = {}
THREAD_SENDER = {}
MESSAGES = {}

def exchange_tokens(authorization_code):
    flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, ' '.join(SCOPES))
    flow.redirect_uri = REDIRECT_URI
    try:
        creds = flow.step2_exchange(authorization_code)
        
        # Save the credentials for the next run
        with open(f'unsecured-user-data/.credentials/{creds.client_id}-token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            log("FILE SAVED!", LoggerSink.GMAIL)
        
        return creds
    except Exception as e:
        log(f"Error exchanging codes: {e}", LoggerSink.GMAIL)
        return False

def gmail_login():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    flow = InstalledAppFlow.from_client_secrets_file(
        os.path.join(base_dir, CLIENT_SECRET_FILE), SCOPES)
    
    #creds = flow.run_local_server(port=empty_port,prompt="consent")

    flow.redirect_uri = REDIRECT_URI #+ "gmail_exchange_token/"
    url, _ = flow.authorization_url(prompt="consent")
    
    return url

def verify_creds(creds):
    return creds.expired

def refresh_creds(creds):
    log("get_creds(): Credentials nonexistant or expired! - REFRESHING", LoggerSink.GMAIL)
    # If there are no (valid) credentials available, let the user log in.
    new_creds = False
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                new_creds = creds
            except:
                pass
    return new_creds   

def get_creds(client_id):
    creds = False
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    if client_id != None:
        if os.path.exists(f'unsecured-user-data/.credentials/{client_id}-token.pickle'):
            with open(f'unsecured-user-data/.credentials/{client_id}-token.pickle', 'rb') as token:
                creds = pickle.load(token)
            
            if creds.invalid == True:
                log(f"get_creds(): Creds invalid, refreshing...", LoggerSink.GMAIL)
                # If there are no (valid) credentials available, let the user log in.
                #if not creds or not creds.valid:
                creds.refresh(Request())
    return creds
   
def get_service(creds):
    service = build('gmail', 'v1', credentials=creds)
    return service

def send_message(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id,
                body=message).execute()

        #print('Message Id: {}'.format(message['id']))

        return message
    except Exception as e:
        log(f'An error occurred: {e}',LoggerSink.GMAIL)
        raise e
    
def create_message_with_attachment(sender, to, subject, message_text, message_id):
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    message['References'] = message_id
    message['In-Reply-To'] = message_id

    msg = MIMEText(message_text)
    message.attach(msg)

    raw_message = \
        base64.urlsafe_b64encode(message.as_string().encode('utf-8'))
    return {'raw': raw_message.decode('utf-8')}
    
def sendingMessage(msgto,message,creds,subject):
    service = get_service(creds)
    convo_owner = getProfile(service)
    
    # append to messages
    print(THREAD_IDS)
    thread_id = THREAD_IDS[convo_owner][subject][0]

    convo = getConversation(service,None,thread_id)[0]
    
    messageId = convo["message-id"]
    subject = convo["subject"]
    user_id = 'me'
    msg = create_message_with_attachment('me', msgto, subject, message, messageId)
    data = send_message(service, user_id, msg)
    
    # append to messages
    print(MESSAGES)
    MESSAGES[convo_owner][subject].append(message)
    
    log(f"MESSAGES ({subject}): " + str(MESSAGES[convo_owner][subject]))
    
    return {"message_id":data["id"]}

def getThreads(service):
    """Display threads with long conversations(>=  X messages)
    Return: None
    """

    try:
        # pylint: disable=maybe-no-member
        # pylint: disable:R1710
        threads = service.users().threads().list(userId='me').execute().get('threads', [])
        for thread in threads:
            tdata = service.users().threads().get(userId='me', id=thread['id']).execute()
            nmsgs = len(tdata['messages'])

            # skip if <3 msgs in thread
            if nmsgs > 0:
                msg = tdata['messages'][0]['payload']
                subject = ''
                for header in msg['headers']:
                    if header['name'] == 'Subject':
                        subject = header['value']
                        break
                if subject:  # skip if no Subject line
                    print(F'- {subject}, {nmsgs}')
        return threads

    except Exception as error:
        print(F'An error occurred: {error}')
        
def getProfile(service):
    return service.users().getProfile(userId="me").execute()['emailAddress']

def getContacts(service):
    result = []
    
    log("CALLING GET CONTACTS",LoggerSink.GMAIL)
    
    thread_receiver = getProfile(service)
    
    threads = service.users().threads().list(userId='me', maxResults=40).execute().get('threads', [])
    for thread in threads:
        tdata = service.users().threads().get(userId='me', id=thread['id']).execute()
        
        sender = ""
        receiver = ""
        when = ""
        thread_id = thread["id"]
        subject = ""
        
        for msg in tdata['messages'][-1]['payload']['headers']:
            if msg['name'].lower() == 'subject':
                subject = msg['value'].replace("Re: ","")
            
                
            if msg["name"].lower() == "date":
                try:
                    when = msg["value"].strip().replace("  "," ").split(" ")[1:6] #.split(" +")[0]
                    when = " ".join(when)
                    when = str(int(datetime.datetime.strptime(when,"%d %b %Y %H:%M:%S %z").timestamp()*1000))
                except:
                    pass     
                
        
        for message in tdata['messages']:
            for msg in message['payload']['headers']:
                
                if msg["name"].lower() == "from":
                    try:
                        sender = msg["value"].split("<")[1].replace(">","")
                    except:
                        sender = msg["value"].replace(">","")
                if msg["name"].lower() == "from":
                    try:
                        receiver = msg["value"].split("<")[1].replace(">","")
                    except:
                        receiver = msg["value"].replace(">","")
                
                if sender != "":
                    if sender != thread_receiver:
                        break
                    
                if receiver != "":
                    if receiver != thread_receiver:
                        break
                    
        if THREAD_SENDER.get(thread_receiver) == None:
            THREAD_SENDER[thread_receiver] = {}     
        if THREAD_SENDER[thread_receiver].get(subject) == None:
            if sender != thread_receiver and sender != "":
                THREAD_SENDER[thread_receiver][subject] = sender
            if receiver != thread_receiver and receiver != "":
                THREAD_SENDER[thread_receiver][subject] = sender


        if THREAD_IDS.get(thread_receiver) == None:
            THREAD_IDS[thread_receiver] = {}
        if THREAD_IDS[thread_receiver].get(subject) == None:
            THREAD_IDS[thread_receiver][subject] = []
            
        
        result.append({ 
            "id": sender+"|"+ subject,
            "name": sender, #display_name,
            "timeStamp": when,
            "lastMessage": subject,
            "platform":"gmail",
            "thread_id" : thread_id
        })
        if thread_id not in THREAD_IDS[thread_receiver][subject]:
            THREAD_IDS[thread_receiver][subject].append(thread_id)
            
    # Remove duplicates     
    res = {}
    for th in result:
        if res.get(th['lastMessage']) == None and th['name'] != thread_receiver:
            res[th['lastMessage']] = th
    result = list(res.values())
    
    # Set correct senders
    for th in result:
        th['id'] = THREAD_SENDER[thread_receiver][th['lastMessage']] + "|" + th['lastMessage']
        
    return result

""" RETURN VALUE EXAMPLE:

    {   "thread_id" : "029310432423",
        "subject" : "Hello motherfucker",
        "messages": [{
            "from": "mikepavlis@gmail.com", 
            "to" : "tate@cobratate.com", 
            "message" : "cau kokot", 
            "timeStamp" : "32143523523522"
            },
            {
            "from": "tate@cobratate.com", 
            "to" : "1mikepavlis@gmail.com", 
            "message" : "nebud vulgarny", 
            "timeStamp" : "32143523523522"
            }]
    }
"""
def getConversation(service,param_subject,thr_id):
    
    convo_owner = getProfile(service)
    
    # od koho, komu, sprava, kedy, subject
    new_thread = {'thread_id': param_subject, "messages":[]}
    try:
        count = 0
        
        iterate_over = []
        
        if param_subject != None:
            print("PARAM SUBJECT: " + str(param_subject))
            print("THREAD IDS: " + str(THREAD_IDS))
            iterate_over = THREAD_IDS[convo_owner][param_subject]
        else:
            iterate_over.append(thr_id)
            
        for thread_id in iterate_over:
            thread = service.users().threads().get(userId='me', id=thread_id).execute() 
            messages = thread['messages']
            thread_subject = ""
                        
            # GET DATA FOR REPLYING
            if count == 0:     
                for headers in messages[-1]['payload']['headers']:
                    if headers['name'].lower() == 'message-id':
                        new_thread["message-id"] = headers["value"]
            count = 1
            
            for msg in messages:
                
                sender = ""
                when = msg["internalDate"]
                display_name = ""
                new_message = ""
                
                if param_subject == None:
                    subject = ""
                receiver = ""
                msg_id = msg["id"]
                mime_type = msg['payload']['mimeType']
                
                for part in msg['payload']['headers']:
                        
                    if param_subject == None:
                        if part['name'].lower() == 'subject':
                            subject = part['value']
                            subject = subject.replace("Re: ","")
                            new_thread["subject"] = subject
                            new_thread['thread_id'] = thread['id']
                            
                    if part['name'].lower() == 'subject':
                        thread_subject = part['value']
                        thread_subject = thread_subject.replace("Re: ","")
                        
                    if part['name'].lower() == 'from':
                        try:
                            sender = part["value"].split("<")[1].replace(">","")
                        except:
                            sender = part["value"]
                        
                    #print(part)
                    if part['name'].lower() == 'to':
                        try:
                            receiver = part["value"].split("<")[1].replace(">","")
                        except:
                            receiver = part["value"]
                        #print(receiver)
                try:
                    
                    if msg['payload'].get('parts') == None:
                        data = msg['payload']['body']['data']
                        new_message = base64.urlsafe_b64decode(data).decode() 
                        
                        # PROCESSING OF MSG HISTORY
                        new_message = new_message.split("\n")
                        new_new_message = []
                        for th in new_message:
                            ok = True
                            if len(th) > 0:
                                if ">" == th[0] or th == ">":
                                    ok = False

                                if ok == True:
                                    if f"<{sender}>" in th or f"<{receiver}>" in th:
                                        ok = False

                                if ok == True:
                                    new_new_message.append(th)

                        new_message = "\n".join(new_new_message)
                        new_message = new_message.strip()
                    else:
                        for part in msg['payload']['parts']:
                            if part["partId"] == "0":
                                mime_type = part['mimeType']
                                data = part['body']['data']
                                new_message = base64.urlsafe_b64decode(data).decode()

                                # PROCESSING OF MSG HISTORY
                                new_message = new_message.split("\n")
                                new_new_message = []
                                for th in new_message:
                                    ok = True
                                    if len(th) > 0:
                                        if ">" == th[0] or th == ">":
                                            ok = False

                                        if ok == True:
                                            if f"<{sender}>" in th or f"<{receiver}>" in th:
                                                ok = False

                                        if ok == True:
                                            new_new_message.append(th)

                                new_message = "\n".join(new_new_message)
                                new_message = new_message.strip()
                except Exception as e:
                    log(str(e),LoggerSink.GMAIL)
                    traceback.print_exc()
                    
                    
                # Add messages using in new thread filtering bug
                if MESSAGES.get(convo_owner) == None:
                    MESSAGES[convo_owner] = {}
                if MESSAGES[convo_owner].get(thread_subject) == None:
                    MESSAGES[convo_owner][thread_subject] = []
                

                MESSAGES[convo_owner][thread_subject].append(new_message)
                
                adding = {
                    "from" : sender,
                    "to" : receiver,
                    "message" : new_message,
                    "timeStamp" : when,
                    "mime_type" : mime_type,
                    "id" : msg_id
                }
                new_thread["messages"].append(adding)  
 

    except Exception as e:
        log("Error in getConversation(): ", LoggerSink.GMAIL)
        log(str(e), LoggerSink.GMAIL)
        log(traceback.print_exc(), LoggerSink.GMAIL)
        return False
            
    if param_subject != None:
        new_thread["subject"] = param_subject
        # REMOVE IF DOESNT WORK
        new_thread['thread_id'] = param_subject
    
    return [new_thread]

def getNewThreads(service,timestamp):
    result_threads = []
    subject = ""
    
    thread_receiver = getProfile(service)    

    try:
        threads = service.users().threads().list(userId='me', maxResults=10).execute().get('threads', [])
        for thread in threads:
            thread_add = 0
            thread = service.users().threads().get(userId='me', id=thread['id']).execute() 
            messages = thread['messages']
 
            
            new_thread = {'thread_id': thread['id'], 'messages':[], 'subject':""}
            
            for msg in thread['messages'][-1]['payload']['headers']:
                if msg['name'].lower() == 'subject':
                    subject = msg['value'].replace("Re: ","")
                    new_thread['subject'] = subject
                    
                
            
            for msg in messages:
                if int(msg["internalDate"]) > int(timestamp):
                    sender = ""
                    when = msg['internalDate']
                    message = ""
                    receiver = ""
                    message_id = msg["id"]
                    mime_type = msg['payload']['mimeType']
                    
                    for part in msg['payload']['headers']:
                        
                        if part['name'].lower() == 'from':
                            try:
                                sender = part["value"].split("<")[1].replace(">","")
                            except:
                                sender = part["value"]
                            
                        if part['name'].lower() == 'to':
                            try:
                                receiver = part["value"].split("<")[1].replace(">","")
                            except:
                                receiver = part["value"]
                                
                        if sender != "":
                            if sender != thread_receiver:
                                break
                            
                        if receiver != "":
                            if receiver != thread_receiver:
                                break
                            
                        if new_thread['subject'] == "":
                            if part['name'].lower() == 'subject':
                                subject = part['value']
                                subject = subject.replace("Re: ","")
                                new_thread['subject'] = subject

                    try:
                        if msg['payload'].get('parts') == None:
                            data = msg['body']['data']
                            new_message = base64.urlsafe_b64decode(data).decode()

                            # PROCESSING OF MSG HISTORY
                            new_message = new_message.split("\n")
                            new_new_message = []
                            for th in new_message:
                                ok = True
                                if len(th) > 0:
                                    if ">" == th[0] or th == ">":
                                        ok = False

                                    if ok == True:
                                        if f"<{sender}>" in th or f"<{receiver}>" in th:
                                            ok = False

                                    if ok == True:
                                        new_new_message.append(th)

                            new_message = "\n".join(new_new_message)
                            new_message = new_message.strip()
                        else:
                            for part in msg['payload']['parts']:
                                if part["partId"] == "0":
                                    mime_type = part['mimeType']
                                    data = part['body']['data']
                                    new_message = base64.urlsafe_b64decode(data).decode()

                                    # PROCESSING OF MSG HISTORY
                                    new_message = new_message.split("\n")
                                    new_new_message = []
                                    for th in new_message:
                                        ok = True
                                        if len(th) > 0:
                                            if ">" == th[0] or th == ">":
                                                ok = False

                                            if ok == True:
                                                if f"<{sender}>" in th or f"<{receiver}>" in th:
                                                    ok = False

                                            if ok == True:
                                                new_new_message.append(th)

                                    new_message = "\n".join(new_new_message)
                                    new_message = new_message.strip()
                    except Exception as e:
                        log(str(e),LoggerSink.GMAIL)
                        traceback.print_exc()
                        
                    log(new_message,LoggerSink.GMAIL)
                    
                    if MESSAGES.get(thread_receiver) == None:
                        MESSAGES[thread_receiver] = {}
                    thread_messages = MESSAGES[thread_receiver].get(new_thread["subject"])
                    
                    if THREAD_SENDER.get(thread_receiver) == None:
                        THREAD_SENDER[thread_receiver] = {}
                    if THREAD_SENDER[thread_receiver].get(subject) == None:
                        if sender != thread_receiver and sender != "":
                            THREAD_SENDER[thread_receiver][subject] = sender
                        if receiver != thread_receiver and receiver != "":
                            THREAD_SENDER[thread_receiver][subject] = sender
                        
                    if thread_messages == None or new_message not in thread_messages:
                        thread_add = 1
                        adding = {
                            "from" : sender,
                            "to" : receiver,
                            "message" : new_message,
                            "mime_type" : mime_type,
                            "timeStamp" : when,
                            "id" : message_id
                        }
                        new_thread["messages"].append(adding)
                        
                        if MESSAGES[thread_receiver].get(new_thread["subject"]) == None:
                            MESSAGES[thread_receiver][new_thread["subject"]] = []
                        MESSAGES[thread_receiver][new_thread["subject"]].append(new_message)
                        log("ADDING",LoggerSink.GMAIL) 
                    else:
                        log("NOT ADDING",LoggerSink.GMAIL)
                    
            if thread_add == 1:
                result_threads.append(new_thread)
                
            # REMOVE IF DOESNT WORK
            new_thread['thread_id'] = subject

    except Exception as error:
        print(F'Error in getNewThreads(): {error}')
        print(traceback.print_exc())
        return False
    
    return result_threads
