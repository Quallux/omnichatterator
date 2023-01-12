import requests, time, datetime, os, copy
from .logger.logger import log
from .logger.logger_sink import LoggerSink
from threading import Thread, Event, Lock

APP_ID = os.environ["MESS_APP_ID"]                            #app id, secret and client token for meta omnichatterator app
APP_SECRET = os.environ["MESS_APP_SECRET"]
CLIENT_TOKEN = os.environ["MESS_CLIENT_TOKEN"]
API_URL = "https://graph.facebook.com/v15.0/"

"""     //original terminal login

payload = { "access_token": APP_ID+"|"+CLIENT_TOKEN, "scope":"pages_show_list,pages_messaging,public_profile"} #json payload to be send to api login request
response = requests.post(API_URL+"device/login",json = payload).json() #get auth code and uri
interval = int(response["interval"])    #getting auth status polling interval from response
wait = int(response["expires_in"])      #getting time in which we can authorize the user, after that the code will no longer be valid
payload = { "access_token": APP_ID+"|"+CLIENT_TOKEN, "code": response["code"]}  #payload for login_status api request
usr_at = None
print("go here: " +response["verification_uri"]+" and put this code there "+response["user_code"])
while wait>0:               #polling only till the time runs out
    wait = wait - interval
    response = requests.post(API_URL+"device/login_status",json = payload).json() #get auth status
    usr_at = response.get("access_token")
    if usr_at != None:                      #WE GOT IN!
        response = requests.get(API_URL+"me",params={"access_token":usr_at,"fields":"name,picture.width(200)"}).json()     #get info about logged in user such as photo and name
        print("successfully logged in as "+response["name"]+" photo: "+response["picture"]["data"]["url"])
        break
    print(response["error"]["error_user_title"])    #we didnt get in yet, we keep trying and we print the status
    if response["error"]["code"] == "463":      #the code is already invalid, there is gonna be another code generation needed
        exit()
    time.sleep(interval)
if usr_at == None:      #time ran out and no access token was given, there is gonna be another code generation needed
    exit()
response = requests.get(API_URL+"me/accounts",params={"access_token":usr_at,"fields":"name,picture.width(200),access_token"}).json() #get pages of the user
if len(response["data"]) == 0:      #if there are no pages then there is no point to life :)
    print("no pages... byeeeeee!")
    exit()
print("user's pages:")
for page in response["data"]:   #showing the list of pages
    print("\t"+page["name"]+"\t"+page["id"]+"\t"+page["picture"]["data"]["url"])
index = int(input("which page?\n"))
print("you selected page '"+response["data"][index]["name"]+"'")
glob_access_token = response["data"][index]["access_token"]           #get access token for selected page from the list  //using this in other functions for now
print(glob_access_token)
"""

#hardcoded omnichatterator page
def get_omnichatter_page():
    user_at = None #no more hardcoded token for u!
    response = requests.get(API_URL+"me/accounts",params={"access_token":user_at}).json()
    for page in response["data"]:
        if page["id"]=="108586122082160":   #omnichatterator page id
            return page["access_token"]
    return 0
#glob_access_token = get_omnichatter_page()      #get hardcoded access token for omnichatterator page  //using this in other functions for now


#-------------------------------------start of login flow---------------

def get_auth(app_id,client_token):
    payload = {"access_token": app_id+"|"+client_token, "scope":"pages_show_list,pages_messaging,public_profile"} #json payload to be send to api login request
    return requests.post(API_URL+"device/login",json = payload).json() #get auth codes, times and uri
    #returns json:
    """
    {
        "interval" : int,       //how long to wait between polling in seconds
        "expires_in" : int,     //for how long to try polling auth_status in seconds
        "code" : str,           //sort of auth_id, use this to poll for auth_status
        "user_code" : str,      //code for the user to put in the verification website
        "verification_uri" : str    //verification website uri
    } 
    """

"""
The "code" parameter is from the response from response = get_auth();  response["code"]
"""
def chceck_auth_status(app_id: str, clien_token: str, code: str):
    payload = { "access_token": app_id+"|"+clien_token, "code": code}
    return requests.post(API_URL+"device/login_status",json = payload).json()
    #on completed auth send json:               //more here: https://developers.facebook.com/docs/facebook-login/for-devices#tech-step3
    """ RESPONSE MESSAGE EXAMPLES HERE
    {
        "access_token": str,    //USER access_token
        "expires_in": int       //how long the token will last in seconds
    }
    
    #or:
    
    {
        "error": {
            "message": str,
            "code": int,            //if this code is 463, then the code is already expired and front-end should stop this polling
            "error_subcode": int,
            "error_user_title": str,
            "error_user_msg": str
        }
    }
    """

"""LIST USER PAGES TO CHOOSE FROM"""
def get_pages(access_token: str):   #access_token - USER access token
    response = requests.get(API_URL+"me/accounts",params={"access_token":access_token,"fields":"name,picture.width(200)"}).json()
    check_response(response)
    return response
    """ RESPONSE MESSAGE EXAMPLES HERE
    returns json:

    {
        "data": [
            {
                "name": str,
                "picture": {
                    "data": {
                        "height": 200,
                        "is_silhouette": bool,
                        "url": str,
                        "width": 200
                    }
                },
                "id": str
            },
            {
                //page2...
            },
            {
                //page3...
            }
        ]
    }
   """

"""GET ACCESS TO CHOSEN PAGE"""
def get_page_access(page_id: str,access_token: str):    #access_token - PAGE access token
    response = requests.get(API_URL+"oauth/access_token",params={"grant_type":"fb_exchange_token","client_id":APP_ID,"client_secret":APP_SECRET,"fb_exchange_token":access_token}).json()
    check_response(response)
    long_token = response["access_token"]
    response = requests.get(API_URL+"me/accounts",params={"access_token":long_token,"fields":"name,picture.width(200),access_token"}).json()
    #log("response with long-lived token:\n"+str(response),LoggerSink.MESSENGER)
    for page in response["data"]:
        if page["id"]== page_id:
            return page
    return False
    """ RESPONSE MESSAGE EXAMPLES HERE
    returns json:

    {
        "access_token": str,    //PAGE access token
        "name": str,
        "picture": {
            "data": {
                "height": 200,
                "is_silhouette": bool,
                "url": str,
                "width": 200
            }
        },
        "id": str
    }

    or returns False
    """

#--------------------------------------end of login flow----------------

#following methods work with PAGE access token!

class MsgCache:
    """
    Retrieves convos from Messenger API for other functions
    to use and helps to conserve API requests.
    """

    class Suber:
        _subers = []
        _subersLock = Lock()

        def __init__(self,access_t):
            # log("Suber init(" + str(api) + ")", LoggerSink.TWITTER)
            with MsgCache.Suber._subersLock:
                found = False
                for suber in MsgCache.Suber._subers:
                    if suber.access_t == access_t:
                        found = True
                        break
                if found:
                    raise Exception("suber already subscribed")
                try:
                        get_myself(access_t)
                except:
                    raise Exception("bad token")
                MsgCache.Suber._subers.append(self)

            self.access_t = access_t
            self.messagesLock = Lock()
            self.all_sents_cached = True
            self.recently_sent =[]
            self.messages =[]
            self.decay = -1
            self._stopEvent = Event()
            
            self._pollingThread = Thread(target=self._update)    
            self._pollingThread.daemon = True
            log("starting polling for messenger page", LoggerSink.MESSENGER)
            self._pollingThread.start()
            
        
        def __str__(self):
            return "Suber object:\n\tmessages: "+str(self.messages)+"\n\tdecay: "+str(self.decay)+"\n"

        def _update(self):
            while not self._stopEvent.is_set():
                
                if self.decay < 30:
                    with self.messagesLock:
                        try:
                            self.messages = try_request(API_URL+"me/conversations",params={"fields":"participants,messages{message,from,to,created_time}","access_token":self.access_t}).json()
                            #log("updated suber messages: "+str(self.messages),LoggerSink.MESSENGER)
                        except Exception as e:
                            log(f"error updating suber - {e}",LoggerSink.PLATFORM_ERRS)
                            self.decay += 1
                            self._stopEvent.wait(10)
                            continue
                        self.all_sents_cached = False
                        if self.recently_sent:
                            log("removing from recently_sent",LoggerSink.MESSENGER)
                            msg_ids = []
                            for convo in self.messages["data"]:
                                for msg in convo["messages"]["data"]:
                                    msg_ids.append(msg["id"])
                            self.recently_sent = list(filter(
                                lambda msg: msg["message_id"] not in msg_ids,
                                self.recently_sent
                            ))
                    self.decay += 1
                else:
                    #stop suber
                    with MsgCache.Suber._subersLock:
                        MsgCache.Suber._subers.remove(self)
                    return
                
                self._stopEvent.wait(10)

        
        def stopPolling(self):
            if self._pollingThread.is_alive():
                self._stopEvent.set()
            
    def get_messages(self,access_t):
        with MsgCache.Suber._subersLock:
            for suber in MsgCache.Suber._subers:
                if suber.access_t==access_t:
                    #log("getting messages for " + str(suber), LoggerSink.MESSENGER)

                    while(suber.decay==-1):
                        pass
                    suber.decay =0
                    with suber.messagesLock:
                        if not suber.all_sents_cached and suber.recently_sent:
                            log("not all sents are cached!",LoggerSink.MESSENGER)
                            msg_ids = []
                            try:
                                for convo in suber.messages["data"]:
                                    for msg in convo["messages"]["data"]:
                                        msg_ids.append(msg["id"])
                            except:
                                raise ValueError("failed getting cached suber messages")
                            recent = list(filter(
                                lambda msg: msg["message_id"] not in msg_ids,
                                suber.recently_sent
                            ))
                            if recent:
                                log("caching:\n" +str(recent),LoggerSink.MESSENGER)
                                for msg in recent:
                                    try:
                                        msg = try_request(API_URL+msg["message_id"],params={"fields":"message,from,to,created_time,thread_id","access_token":access_token}).json
                                        for thread in suber.messages["data"]:
                                            if thread["id"]==msg["thread_id"]:
                                                thread["messages"]["data"].insert(0,msg)
                                                break
                                    except Exception as e:
                                        log(f"failed getting cached recent message: {e}",LoggerSink.PLATFORM_ERRS)
                                        continue
                                suber.all_sents_cached = True
                        return copy.deepcopy(suber.messages)
        
        if self.subscribe(access_t):
            return self.get_messages(access_t)

    def update_recently_sent(self,access_t,msg):
        with MsgCache.Suber._subersLock:
            for suber in MsgCache.Suber._subers:
                if suber.access_t==access_t:
                    with suber.messagesLock:
                        log("updating recently_sent with "+str(msg),LoggerSink.MESSENGER)
                        suber.recently_sent.append(msg)
                        suber.all_sents_cached = False
                    return
    
    def subscribe(self,access_t):
        log("subscribing messenger page", LoggerSink.MESSENGER)
        try:
            self.Suber(access_t)
            log("a user subscribed for polling", LoggerSink.MESSENGER)
            return True
        except Exception as e:
            log("messenger page not subscribed - "+str(e), LoggerSink.PLATFORM_ERRS)
            return False

msgPoller = MsgCache()

#Richard    psid 6128056210561978 -scope: Omnichatterator
def send_msg(msg: str, user_psid: int, access_token: str):
    """Sends a direct message to the user."""
    if access_token is None:
        log("cannot send request with no access token!", LoggerSink.MESSENGER)
        return None
    payload = {
        "recipient": {
            "id": user_psid
        },
        "messaging_type": "RESPONSE",
        "message": {
            "text": msg
        },
        "access_token":access_token
    }

    msg = requests.post(API_URL+"me/messages",json = payload).json()
    try:
        check_response(msg)
        update_recently_sent(access_token,msg)
    except:
        pass

    return msg

def get_contacts(access_token: str):
    response = msgPoller.get_messages(access_token)
    #log(f"get contacts - access token used: {access_token}",LoggerSink.MESSENGER)
    contacts= []
    #log("get contacts response: "+str(response),LoggerSink.MESSENGER)
    for convo in response["data"]:
        contact = get_user(convo["participants"]["data"][0]["id"],access_token)
        contacts.append({
                "id": str(contact["id"]),
                "name": contact["name"],
                "profile_image_url_https": contact["picture"]["data"]["url"],
                "timeStamp": str(int(datetime.datetime.strptime(convo["messages"]["data"][0]["created_time"], "%Y-%m-%dT%H:%M:%S%z").timestamp()*1000)),
                "lastMessage": convo["messages"]["data"][0]["message"],
                "platform":"messenger"
        })
    return contacts

def get_myself(access_token: str):
    response = requests.get(API_URL+"me",params={"fields":"picture.width(200),name","access_token":access_token}).json()
    check_response(response)
    return (response["id"],response["picture"]["data"]["url"],response["name"])

def get_user(psid:str,access_token:str):
    response = requests.get(API_URL+psid,params={"fields":"name,picture.width(200)","access_token":access_token}).json()
    check_response(response)
    return response
    """
    returns json:

    {
        "name": "str,
        "picture": {
            "data": {
                "height": 200,
                "is_silhouette": bool,
                "url": str,
                "width": 200
            }
        },
        "id": str
    }
    """

def get_messages(since:str,including_mine: bool, access_token: str, psid:str=None):
    #log(f"get messages - access token used: {access_token}",LoggerSink.MESSENGER)
    response = msgPoller.get_messages(access_token)
    #log("get messages response: "+str(response),LoggerSink.MESSENGER)
    if psid:
        found = None
        for convo in response["data"]:
            if convo["participants"]["data"][0]["id"]==psid:
                found = convo
                break
        if found:
            response["data"] = [found]
            #log("get messages psid response: "+str(response),LoggerSink.MESSENGER)
        else:
            raise Exception("could not find conversation with provided user")
    if since == "0" and including_mine:
        return response
    meId = requests.get(API_URL+"me",params={"access_token":access_token}).json()["id"]
    since = datetime.datetime.fromtimestamp(int(since)/1000, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    for convo in response["data"]:
        convo["messages"]["data"] = list(filter(
            lambda msg: msg["created_time"]>since and (including_mine or msg["to"]["data"][0]["id"]==meId),
            convo["messages"]["data"]
        ))
    return response
    """
    returns json:

    {
        "data": [   //list of conversations - starting with latest
            {
                "messages": {
                    "data": [   //list of messages - starting with latest from the conversation
                        {
                            "from": {
                                "name": str,
                                "email": str,
                                "id": str   //psid(page scoped id) of the user
                            },
                            "to": {
                                "data": [   //list of recipients of the message - always only one element
                                    {
                                        "name": str,
                                        "email": str,
                                        "id": str
                                    }
                                ]
                            },
                            "message": str,
                            "created_time": "str"
                            "id": str   //id of the message
                        },
                        {
                            //another message...
                        }
                    ],
                },
                "id": str   //id of the conversation
            },
            {
                //another conversation...
            }
        ]
    }
    """

def check_response(response):
    if response.get("error"):
        raise ValueError(f"API responded with error:\n{response}")

def try_request(url,params):
    tries = 5
    order_strs = ["1st","2nd","3rd","4th"]
    while(tries>0):
        tries =tries-1
        try:
           response = requests.get(url,params=params)
           #log(f"try request response:\n{response}",LoggerSink.MESSENGER)
           check_response(response.json())
           return response
        except Exception as e:
            if tries<=0:
                raise e
            else:
                log(f"(no biggie){order_strs[4-tries]}/5 messenger request try failed with error - {e}",LoggerSink.PLATFORM_ERRS)
                time.sleep(0.1)
    raise Exception("try request code rly shouldn't get here :| ... this is very bad, you should stop doing what you are doing cuz u are breaking the spacetime continuum")