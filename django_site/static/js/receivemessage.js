/**
 * Array of timestamps for each platform.
 * @type {string[]}
 */
TIME_STAMP = [getTimeStamp(),getTimeStamp(), getTimeStamp()]
let contactListElement = ""
let newMessageContainer = ""
const img = ["/static/images/twitter.svg", "/static/images/messenger.svg", "/static/images/gmail.svg", "/static/images/close.svg"]
fetchResult()



async function fetchContactListElem()
{
     const fetchRes = await fetch(window.location.origin + "/static/tmpl/contact-list-element.html")
    return await fetchRes.text()
}



/**
 *
 * Fetch templates and saves them into global parameters in a form of String.
 *
 * @returns {Promise<void>}
 */

async function fetchResult() {
    contactListElement = await fetchContactListElem()
}

/**
 * Gets timestamp created from current time, minus one minute.
 *
 * @returns {string}
 */
function getTimeStamp() {
    return Date.now().toString()
}

/**
 *
 * Fetch new messages from server based on platform.
 *
 */
function sendReceiveMessageCall() {
    const cookie = getCookie("csrftoken");
    const request = {"timeStamps": {
            "twitter": TIME_STAMP[0],
            "messenger": TIME_STAMP[1],
            "gmail": TIME_STAMP[2]
        }}
    let headers = new Headers();
    headers.append('Accept', 'application/json')
    headers.append('Content-Type', 'application/json')
    headers.append('X-CSRFToken', cookie);
    fetch("/recieve_msg/",
        {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(request),
            credentials: "same-origin"
        })
        .then(
            response => {
                if (response.status === 200) {
                    response.json().then(
                        value => {
                            validateJSONInput(value)
                            for (const valueElement of value["messageList"]) {
                                let x = valueElement["messages"].reverse()[0]["timeStamp"]
                                let y = valueElement["platform"]
                                for (let i = 0; i<PLATFORMS.length;i++)
                                {
                                    if (y===PLATFORMS[i] && TIME_STAMP[i]<x)
                                    {
                                        TIME_STAMP[i]=x
                                        break
                                    }
                                }
                            }
                        }
                    )
                } else {
                    if (response.status === 204) {
                        console.log("No new messages.")
                    } else {
                        throw new Error(`Server responded with status code ${response.status}:${response.statusText}`)
                    }
                }

            })
        .catch(
            error => console.error(error)
        )
}

/**
 * Validate input from json response for receiving messages and render the default page correspondingly.
 *
 * @param jsonBody body of JSON response
 *
 */
function validateJSONInput(jsonBody)
{
     if (DB === null) {
        console.error(`Error while getting database reference for database ${DB_NAME}. Database is probably not yet opened or is corrupted.`)
    }
    for (const msgList of jsonBody["messageList"]) {
        for (const msg of msgList["messages"].reverse()) {
            const dbTransaction = DB.transaction(STORE_NAME, "readwrite")
            const objStore = dbTransaction.objectStore(STORE_NAME)
            const getTransaction = objStore.index("ID").get(msg["senderId"])
            getTransaction.onsuccess = (event) => {
                if (event.target.result === undefined) {
                    const msgList = {
                        "userId": msg["senderId"],
                        "platform": msg["platform"],
                        "messageList": Array.of(msg)
                    }
                   objStore.add(msgList).onsuccess =()=>{dbTransaction.commit()}
                } else {
                    const newMsgList = event.target.result["messageList"]
                    newMsgList.unshift(msg)
                    newMsgList.sort((a, b) => (a["timeStamp"] > b["timeStamp"]) ? -1 : ((b["timeStamp"] > a["timeStamp"]) ? 1 : 0))
                    const newList = {
                        "userId": event.target.result["userId"],
                        "platform": event.target.result["platform"],
                        "messageList": newMsgList
                    }
                    objStore.index("ID").getKey(msg["senderId"]).onsuccess = (ev)=> {
                        console.log(ev.target.result)
                        const result = objStore.put(newList, ev.target.result)
                        result.onsuccess = (event) => {
                            dbTransaction.commit()
                        }
                    }
                }
            }
            dbTransaction.oncomplete = () => {
                Array.from(document.querySelectorAll(".contact-id")).filter(a => a.innerText === msg["senderId"]).forEach((a) => {
                    const contactMessage = a.parentElement.querySelector(".contact-message")
                    if (a.parentElement.querySelector(".contact-platform").innerText!=="gmail")
                contactMessage.innerText =
                    msg["message"].length >= MESSAGE_CONTACT_MAX_LENGTH ? msg["message"].slice(0, MESSAGE_CONTACT_MAX_LENGTH - 1) + "..." : msg["message"]
            else contactMessage.innerText =
                msg["senderId"].split("|")[1].length>= MESSAGE_CONTACT_MAX_LENGTH ? msg["senderId"].split("|")[1].slice(0, MESSAGE_CONTACT_MAX_LENGTH-1)+"..."
                : msg["senderId"].split("|")[1]
                    a.parentElement.querySelector(".contact-name").classList.add("new-message-arrived")
                    a.parentElement.querySelector(".contact-message").classList.add("new-message-arrived")
                    // following 3 lines of code move contact with a new message on top of contact list
                    let contactElementToMoveToTop = a.parentElement.parentElement.parentElement;
                    let firstContactElementToMoveBefore = document.getElementsByClassName("contact")[0]
                    firstContactElementToMoveBefore.parentElement.insertBefore(contactElementToMoveToTop, firstContactElementToMoveBefore)
                })
                addNewContactOnTop(msg, msgList["platform"])
                const convoHistory = document.getElementById("conversation-history")
                const selectedElem = document.querySelector(".contact-selected")
                if (msg["senderId"] === selectedElem.querySelector(".contact-id").innerText) {
                    const container = createNewConvoMessage(msg, msg["senderId"]);
                    appendAttachment(msg, container)
                    convoHistory.insertBefore(container, convoHistory.children[0])
                }
            }
        }
    }
}


/**
 * @deprecated
 *
 * Validate JSON response based on its id.
 *
 * @param jsonBody{Object} body of JSON response
 */
function validateJSONInputAndRender(jsonBody) {

    jsonBody["messageList"] = jsonBody["messageList"].reverse()
    if (jsonBody["recipientId"] === id) {
        for (let i = 0; i < jsonBody["messageList"].length; i++) {
            renderMessages(jsonBody["messageList"][i])
        }
    } else {
        throw new Error(`This response has been corrupted. Key data does not correspond with values sent by request.`)
    }
}

/**
 *
 * Based on message and its ID of sender value, checks if there already is duplicate value between contact list.
 * If false, create new contact Div element at the top of the contact list from the values passed in message.
 *
 * @param message{Object} new message
 * @param platform{string} platform from which message was received
 */
function addNewContactOnTop(message, platform) {
    const contactListElem = document.getElementsByClassName("contacts")[0]
    let containsContact = false;
    for (let x = 0; x < contactListElem.getElementsByClassName("contact").length; x++) {
        const y = contactListElem.getElementsByClassName("contact")[x].getElementsByClassName("contact-id")[0].innerText
        if (y === message["senderId"] || y === message["recipientId"]) {
            containsContact = true;
            break;
        }
    }
    if (!containsContact) {
        if (contactListElement != null) {
            const parser = new DOMParser()
            const newMessageTemplate = parser.parseFromString(contactListElement, "text/html")
            const clone = newMessageTemplate.body
            const cloneNode = clone.cloneNode(true)
            cloneNode.getElementsByClassName("contact-platform")[0].textContent = platform
            cloneNode.getElementsByClassName("contact-timestamp")[0].textContent = message["timeStamp"]
            if (platform!=="gmail") {
                cloneNode.getElementsByClassName("contact-avatar")[0].src = message["avatar"]
            }
            else
            {
                cloneNode.getElementsByClassName("contact-avatar")[0].src = "static/images/default_avatar.svg"
            }
            for (let i = 0;i<PLATFORMS.length;i++)
            {
                if (platform===PLATFORMS[i])
                {
                    cloneNode.getElementsByClassName("platform-logo-contact")[0].src=window.location.origin+img[i]
                }
            }
            cloneNode.getElementsByClassName("contact-name")[0].innerText = message["senderName"]
            if (platform!=="gmail")
                cloneNode.getElementsByClassName("contact-message")[0].innerText =
                    message["message"].length >= MESSAGE_CONTACT_MAX_LENGTH ? message["message"].slice(0, MESSAGE_CONTACT_MAX_LENGTH - 1) + "..." : message["message"]
            else cloneNode.getElementsByClassName("contact-message")[0].innerText =
                message["senderId"].split("|")[1].length>= MESSAGE_CONTACT_MAX_LENGTH ? message["senderId"].split("|")[1].slice(0, MESSAGE_CONTACT_MAX_LENGTH-1)+"..."
                    : message["senderId"].split("|")[1]
            cloneNode.getElementsByClassName("contact-id")[0].textContent= message["senderId"]
               cloneNode.getElementsByClassName("contact-name")[0].classList.add("new-message-arrived")
            cloneNode.getElementsByClassName("contact-message")[0].classList.add("new-message-arrived")
            const divParent = document.getElementsByClassName("contacts")[0]
            divParent.insertBefore(cloneNode, divParent.firstChild)
            const newlyInsertedDiv = document.getElementsByClassName("contacts")[0].getElementsByClassName("contact")[0]
            newlyInsertedDiv.addEventListener("click", (e) => {
                selectContact(e.currentTarget)
            })
        }
    }
}



/**
 *
 * Reverse the epoch time back to the readable date and time.
 *
 * @param timestamp{string} String containing timestamp in epoch time.
 * @returns {string}
 */
function reverseDateFromTimeStamp(timestamp) {
    let date = new Date(Number.parseInt(timestamp))
    const year = date.getFullYear()
    const month = date.getMonth() + 1
    const day = date.getDate()
    const hours = date.getHours() < 10 ? '0' + date.getHours() : date.getHours();
    const minutes = date.getMinutes() < 10 ? '0' + date.getMinutes() : date.getMinutes();
    return day + "." + month + "." + year + "  " + hours + ":" + minutes

}

setInterval(sendReceiveMessageCall, 5000);



