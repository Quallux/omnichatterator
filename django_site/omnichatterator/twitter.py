import tweepy
import datetime
import time
from threading import Thread, Event, Lock
import os
from .logger.logger import log
from .logger.logger_sink import LoggerSink

api_key = os.environ['API_KEY'] #rename to something like TWITTER_API_KEY
api_secret = os.environ['API_SECRET'] #rename to something like TWITTER_API_SECRET
access_token = None             #remove - not used
access_token_secret = None      #remove - not used

class MsgCache:
    """
    Retrieves messages from Twitter API for other functions
    to use and helps to conserve API requests.
    """

    class Suber:
        _subers = []
        _subersLock = Lock()

        def __init__(self,access_t,access_ts,api,mock=False):
            # log("Suber init(" + str(api) + ")", LoggerSink.TWITTER)
            with MsgCache.Suber._subersLock:
                found = False
                for suber in MsgCache.Suber._subers:
                    if suber.access_t == access_t and suber.access_ts == access_ts:
                        found = True
                        break
                if found:
                    raise Exception("suber already subscribed")
                try:
                        self.id_str = api.verify_credentials().id_str
                except:
                    raise Exception("bad api for suber")
                MsgCache.Suber._subers.append(self)

            self.access_t = access_t
            self.access_ts = access_ts
            self.api = api
            self.messagesLock = Lock()
            self.all_sents_cached = True
            self.recently_sent =[]
            self.messages =[]
            self.decay = -1
            self._stopEvent = Event()
            if mock:
                self._mockMsgId = 0
                self._pollingThread = Thread(target=self._mockUpdate)    
            else:
                self._pollingThread = Thread(target=self._update)    
            self._pollingThread.daemon = True
            log("starting"+(" mock" if mock else "")+" polling for user "+self.id_str, LoggerSink.TWITTER)
            self._pollingThread.start()
            
        
        def __str__(self):
            return "Suber object:\n\tid_str: "+self.id_str+"\n\tmessages: "+str(self.messages)+"\n\tdecay: "+str(self.decay)+"\n"

        class MockMsg:
            def __init__(self,json):
                self._json =json
                self.type = json["type"]
                self.id = json["id"]
                self.created_timestamp = json["created_timestamp"]
                self.message_create = json["message_create"]
            
            def __repr__(self):
                return "MockMsg(recipient_id: "+self.message_create['target']['recipient_id']+", SenderId: "+self.message_create['sender_id']+")"

        def _update(self):
            while not self._stopEvent.is_set():
                
                if self.decay < 5:
                    with self.messagesLock:
                        try:
                            self.messages = self.api.get_direct_messages(count=50)
                        except Exception as e:
                            log(f"error updating suber {e}",LoggerSink.TWITTER)
                            pass
                        self.all_sents_cached = False
                        if self.recently_sent:
                            log("removing from recently_sent",LoggerSink.TWITTER)
                            msg_ids = []
                            for msg in self.messages:
                                msg_ids.append(msg.id)
                            self.recently_sent = list(filter(
                                lambda msg: msg.id not in msg_ids,
                                self.recently_sent
                            ))
                    self.decay += 1
                else:
                    #stop suber
                    with MsgCache.Suber._subersLock:
                        MsgCache.Suber._subers.remove(self)
                    return
                
                self._stopEvent.wait(60)

        def _mockUpdate(self):
            mockUsers = ['1595050958555430913', '759883386974531584','1584904645855657985','1585654451737706502',
                         '1595050958555430913','1496091340823801859','1593591318231523329','1590798137320476672',
                         '1590800682491191311']
            spammerId = mockUsers[0]
            while not self._stopEvent.is_set():
                log("mockUpdate for " + str(self), LoggerSink.TWITTER)
                nowTime = int(time.time())
                if self._mockMsgId%5==0:
                    spammerId = mockUsers[(self._mockMsgId//5) % len(mockUsers)]
                msg = {
                    "type": "message_create",
                    "id": str(self._mockMsgId),
                    "created_timestamp": str(nowTime*1000),
                    "message_create": {
                        "target": {
                            "recipient_id": "" #every suber
                        },
                        "sender_id": str(spammerId),
                        "message_data": {
                            "text": "TestMessageuofejkfajpfjapkjafjpafjkafkjlfasjasfopfafjajafjopfas[fsa[klasfkfa[kaf[ksafk[asfpfsako[fk[q[fpwq[powqoioqwproiwqroiwrk;lflslcmcasm;lsksaflsfkl;fsaklfk;falskfoqir[qwrpqwriwqriropropwopwow[pwopewopewoeoepwp[w[ "+str(datetime.datetime.fromtimestamp(nowTime)),
                            "entities": {
                                "hashtags": [],
                                "symbols": [],
                                "urls": [],
                                "user_mentions": [],
                            },
                        }
                    }
                }
                self._mockMsgId += 1
                if self.decay < 60:
                    msg["message_create"]["target"]["recipient_id"]=self.id_str
                    msg=self.MockMsg(msg)
                    log(str(msg), LoggerSink.TWITTER)
                    with self.messagesLock:
                        self.messages.insert(0,msg)
                        self.messages = self.messages[-50:]
                    self.decay += 1
                else:
                    #stop suber
                    with MsgCache.Suber._subersLock:
                        MsgCache.Suber._subers.remove(self)
                    return

                self._stopEvent.wait(5)    
        
        def stopPolling(self):
            if self._pollingThread.is_alive():
                self._stopEvent.set()
            
    def get_messages(self,access_t,access_ts):
        with MsgCache.Suber._subersLock:
            for suber in MsgCache.Suber._subers:
                if suber.access_t==access_t and suber.access_ts==access_ts:
                    #log("getting messages for " + str(suber), LoggerSink.TWITTER)

                    while(suber.decay==-1):
                        pass
                    suber.decay =0
                    with suber.messagesLock:
                        if not suber.all_sents_cached and suber.recently_sent:
                            log("not all sents are cached!",LoggerSink.TWITTER)
                            msg_ids = []
                            for msg in suber.messages:
                                msg_ids.append(msg.id)
                            recent = list(filter(
                                lambda msg: msg.id not in msg_ids,
                                suber.recently_sent
                            ))
                            if recent:
                                log("caching:\n" +str(recent),LoggerSink.TWITTER)
                                suber.messages.extend(recent)
                                suber.messages.sort(key= lambda msg: msg.created_timestamp,reverse=True)
                                suber.messages = suber.messages[-50:]
                                suber.all_sents_cached = True
                        return suber.messages
        auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_t, access_ts
        )
        api = tweepy.API(auth)
        if self.subscribe(access_t,access_ts,api):
            return self.get_messages(access_t,access_ts)

    def update_recently_sent(self,access_t,access_ts,msg):
        with MsgCache.Suber._subersLock:
            for suber in MsgCache.Suber._subers:
                if suber.access_t==access_t and suber.access_ts==access_ts:
                    with suber.messagesLock:
                        log("updating recently_sent with "+str(msg),LoggerSink.TWITTER)
                        suber.recently_sent.append(msg)
                        suber.all_sents_cached = False
                    return
    
    def subscribe(self,access_t,access_ts,api):
        log("subscribing with api: " + str(api), LoggerSink.TWITTER)
        try:
            self.Suber(access_t,access_ts,api)     # use self.Suber(access_t,access_ts,api, True) for mocking message getting <-------------------------------------------!!!
            log("a user subscribed for polling", LoggerSink.TWITTER)
            return True
        except Exception as e:
            log(str(e), LoggerSink.TWITTER)
            return False

msgPoller = MsgCache()

def start_polling(access_token,access_token_secret):
    global msgPoller
    if access_token is None or access_token_secret is None:
        log("cannot send request with no creds! run 'get_access_creds()' to acquire them", LoggerSink.TWITTER)
        return None
    auth = tweepy.OAuth1UserHandler(
            api_key, api_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)
    sub_result = msgPoller.subscribe(access_token,access_token_secret,api)

    user = api.verify_credentials()
    user_Id= user.id_str
    user_photoUrl = user.profile_image_url_https.replace("_normal", "")
    #user_log(user_Id,f"Status: {sub_result}","start_polling()")
    return (user_Id,user_photoUrl)

def verify_creds(access_token,access_token_secret):
    if access_token is None or access_token_secret is None:
        log("cannot send request with no creds! run 'get_access_creds()' to acquire them", LoggerSink.TWITTER)
        return None
    try:
        auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_token_secret
        )
        api = tweepy.API(auth)

        user = api.verify_credentials()
        user_Id= user.id_str
        return True
    except:
        return False

"""
 Michal  id 759883386974531584
 Richard id 1584904645855657985
 Omni    id 1585654451737706502
 Miso    id 1595050958555430913
 Samo1   id 1496091340823801859
 Samo2   id 1593591318231523329
 Bezos   id 1590798137320476672
 West    id 1590800682491191311
"""

def send_msg(msg: str, user_id: int, access_token: str, access_token_secret: str):
    """Sends a direct message to the user."""
    if access_token is None or access_token_secret is None:
        log("cannot send request with no creds! run 'get_access_creds()' to acquire them", LoggerSink.TWITTER)
        return None
    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)

    msg = api.send_direct_message(recipient_id=user_id, text=msg)

    #caching the sent message, since it doesnt show up in messages right away
    msgPoller.update_recently_sent(access_token,access_token_secret,msg)

    return msg


def get_userId(screen_name: str) -> int:     #screen_name is twitter @ 'name'
    """Returns id of a single user."""
    auth = tweepy.OAuth2AppHandler(
        api_key, api_secret,
    )
    api = tweepy.API(auth)

    return api.get_user(screen_name=screen_name).id


def get_messages(since: str,including_mine: bool, access_token, access_token_secret):
    """Returns messages previously collected by msgCache class."""
    if access_token is None or access_token_secret is None:
        log("cannot send request with no creds! run 'get_access_creds()' to acquire them", LoggerSink.TWITTER)
        return None
    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )

    api = tweepy.API(auth)
    result = []
    messages = msgPoller.get_messages(access_token,access_token_secret)

    meId = ""
    for suber in MsgCache.Suber._subers:
        if suber.access_t == access_token and suber.access_ts == access_token_secret:
            meId = suber.id_str
            break

    for dm in messages:
        #log("BEFORE " + str(datetime.datetime.fromtimestamp(int(dm.created_timestamp)/1000)) + " recipient: " + str(dm.message_create["target"]["recipient_id"]) + " me: " + str(meId), LoggerSink.TWITTER)
        if int(dm.created_timestamp) > int(since):
            if including_mine:
                result.append(dm)
            else:
                if dm.message_create["target"]["recipient_id"] == meId:
                    # log("AFTER " + str(dm.created_timestamp))
                    result.append(dm)
        else:
            break
    log("zmakol som get_messages", LoggerSink.TWITTER)

    return result


def get_user(id: str, access_token, access_token_secret) -> int:
    """Returns the User class from Tweepy for selected user id."""
    if access_token is None or access_token_secret is None:
        log("cannot send request with no creds! run 'get_access_creds()' to acquire them", LoggerSink.TWITTER)
        return None
    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)

    return api.get_user(user_id=id)


def get_contact_ids(access_token,access_token_secret):
    """Returns message recipient and sender ids."""
    if access_token is None or access_token_secret is None :
        log("cannot send request with no creds! run 'get_access_creds()' to acquire them", LoggerSink.TWITTER)
        return

    contact_ids = set()
    messages = msgPoller.get_messages(access_token,access_token_secret)
    meId = ""
    for suber in MsgCache.Suber._subers:
        if suber.access_t == access_token and suber.access_ts == access_token_secret:
            meId = suber.id_str
            break

    for m in messages:
        recipient_id = m._json["message_create"]["target"]["recipient_id"]
        sender_id = m._json["message_create"]['sender_id']
        if(sender_id == meId):
            contact_ids.add(int(recipient_id))
        else:
            contact_ids.add(int(sender_id))

    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)
    #contact_ids.discard(api.verify_credentials().id_str) #discard current acc id -- comment this line of code if you want to be able to send messages to yourself
    return contact_ids

def get_last_messages(access_token,access_token_secret,ids):
    if access_token is None or access_token_secret is None :
        log("cannot send request with no creds! run 'get_access_creds()' to acquire them", LoggerSink.TWITTER)
        return
    #log("ids:\n"+str(ids),LoggerSink.TWITTER)
    lastMsgs = {}
    messages = msgPoller.get_messages(access_token,access_token_secret)
    meId = ""
    for suber in MsgCache.Suber._subers:
        if suber.access_t == access_token and suber.access_ts == access_token_secret:
            meId = suber.id_str
            break

    for msg in messages:
        sender = int(msg.message_create["sender_id"])
        recipient = int(msg.message_create["target"]["recipient_id"])
        #log(str(sender)+" -> "+str(recipient)+" : "+msg.message_create["message_data"]["text"] ,LoggerSink.TWITTER)
        if str(recipient)!=meId and recipient in ids:
            if str(recipient) not in lastMsgs:
                log("adding with recipient_id",LoggerSink.TWITTER)
                lastMsgs[str(recipient)] = (msg.created_timestamp,msg.message_create["message_data"]["text"])
        elif sender in ids:
            if str(sender) not in lastMsgs:
                log("adding with sender_id",LoggerSink.TWITTER)
                lastMsgs[str(sender)] = (msg.created_timestamp,msg.message_create["message_data"]["text"])
    return lastMsgs


def get_contacts(ids,access_token,access_token_secret):
    ids=None
    
    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)
    if ids is None:
        ids = get_contact_ids(access_token,access_token_secret)
    lastMsgs = get_last_messages(access_token,access_token_secret,ids)
    contacts = []
    if (len(ids)):
        contacts = api.lookup_users(user_id=ids)
    output_contacts = []
    for contact in contacts:
        contact_json = contact._json
        parsed = {k: str(contact_json[k]) for k in contact_json.keys() & {
            'id',
            'name',
            'profile_image_url_https'}}
        if str(contact_json["id"]) in lastMsgs:
            tup = lastMsgs[str(contact_json["id"])]
            parsed.update({"timeStamp":str(tup[0]),"lastMessage":tup[1],"platform":"twitter"})
        else:
            parsed.update({"timeStamp":"0","lastMessage":"","platform":"twitter"})
        output_contacts.append(parsed)

    output_contacts.sort(key= lambda elem: elem["timeStamp"],reverse=True)
    for oc in output_contacts:
        oc['profile_image_url_https'] = oc['profile_image_url_https'].replace("_normal", "")

    return output_contacts