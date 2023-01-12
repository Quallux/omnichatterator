/**
 * Selects only the contact element with id value given in the param and fetch conversation history with given user.
 *
 * @param elem{HTMLElement} selected ID of user
 */
function selectContact(elem) {

    let id = elem.getElementsByClassName("contact-id")[0].textContent
    //search through all contact elements
    for (let i = 0; i < document.getElementsByClassName("contact").length; i++) {
        const contact = document.getElementsByClassName("contact")[i]
        //clear elem off all select classes
        if (contact.classList.contains("contact-selected")) {
            contact.classList.remove("contact-selected")
        } else {
            contact.classList.remove("contact-not-selected")
        }
        //if there is a contact with wanted id, select that contact and edit convo history
        if (contact.getElementsByClassName("contact-id")[0].innerText === id) {
            getAndCreateConversationHistory(contact)
            contact.classList.add("contact-selected")
            Array.from(contact.querySelector(".contact-values").children).forEach((a) => {
                a.classList.remove("new-message-arrived")
            })
        } else {
            contact.classList.add("contact-not-selected")
        }
    }
}

/**
 *
 * @param messages
 * @param contact
 * @param convoHistory
 * @param id
 * @returns {boolean}
 */
function appendConvoHistory(messages, contact, convoHistory, id) {
       const divMessage = createNewConvoMessage(messages, id);
     appendAttachment(messages, divMessage)
    if (contact.querySelector(".contact-id").innerText !==
        document.querySelector(".contact-selected").querySelector(".contact-id").innerText) {
        return false;
    }
    convoHistory.appendChild(divMessage)
    return true;
}

/**
 *
 * @param res
 * @param platform
 * @param id
 * @private
 */
function _putToDatabase(res, platform, id){
      res["messageList"].sort((a, b) => (a["timeStamp"] > b["timeStamp"]) ? -1 : ((b["timeStamp"] > a["timeStamp"]) ? 1 : 0))
                                const message = {
                                    "userId":id,
                                    "platform": platform,
                                    "messageList": res["messageList"]
                                }
                                DB.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME).put(message).onerror = (e)=>{
          console.error(e.target.error);
                                }
}

/**
 * Fetch conversation history of contact.
 *
 * @param contact{HTMLElement} selected contact element
 */
function getAndCreateConversationHistory(contact) {
    const id = contact.getElementsByClassName("contact-id")[0].innerText
    const convoHistory = document.getElementById("conversation-history")
    const platform = contact.querySelector(".contact-platform").innerText
    //remove all remaining children
    convoHistory.replaceChildren()
    if (DB === null) {
        console.error(`Error while getting database reference for database ${DB_NAME}. Database is probably not yet opened or is corrupted.`)
    }
    //create transaction from database and check for existence of the key in database
    const res = DB.transaction(STORE_NAME, "readonly").objectStore(STORE_NAME).index("ID").get(id)
    res.onsuccess = (event) => {
        const url = new URL(window.location.origin + "/conversation?" + new URLSearchParams(
                {
                    with: id,
                    platform: platform
                }))
        if (event.target.result === undefined) {
            fetch(url).then(
                (response) => {
                    if (response.ok) {
                        response.json().then(
                            (res) => {
                                _putToDatabase(res, platform, id)
                                if (contact.querySelector(".contact-id").innerText !==
                                    document.querySelector(".contact-selected").querySelector(".contact-id").innerText) {
                                    return
                                }
                                for (const newMessage of res["messageList"]) {
                                    if (!appendConvoHistory(newMessage, contact, convoHistory, contact.querySelector(".contact-id").innerText))
                                        return;
                                }
                            }
                        )
                    } else {
                        if (response.status===511)
                        {
                    deleteCookie("twitter")
                    deleteCookie("messenger")
                    deleteCookie("gmail")
                    fetch(window.location.origin).then(Promise.resolve)
                        }
                        else {
                            throw new Error(`Server responded with status code ${response.status}:${response.statusText}`)
                        }
                    }
                }
            ).catch(
                (error) => {
                    console.error(error)
                }
            )
        } else {
            //when conversation is already in database
            if (contact.querySelector(".contact-id").innerText !==
                document.querySelector(".contact-selected").querySelector(".contact-id").innerText) {
                return
            }

            const message = contact.querySelector(".contact-platform").innerText !== "gmail"?
                event.target.result["messageList"][0]["message"]:contact.querySelector(".contact-id").innerText.split("|")[1]
            contact.querySelector(".contact-message").innerText = message.length >= MESSAGE_CONTACT_MAX_LENGTH ? message.slice(0, MESSAGE_CONTACT_MAX_LENGTH - 1) + "..." : message
            //between choosing stupid or lengthy, i chose stupid
            for (const newMessage of event.target.result["messageList"]) {
                if (!appendConvoHistory(newMessage, contact, convoHistory, contact.querySelector(".contact-id").innerText))
                    return;
            }
            fetch(url).then(
                (response)=>{
                    if (response.ok)
                    {
                        //transaception
                        response.json().then((res)=>{
                            if (event.target.result["messageList"] === res["messageList"]) return
                            event.target.result["messageList"] = res["messageList"]
                            const transaction = DB.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME)
                                .index("ID").getKey(event.target.result["userId"])
                                transaction.onsuccess = (ev)=>{
                                    DB.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME).openCursor(ev.target.result).onsuccess = (ev)=>{
                                        ev.target.result.update(event.target.result).onerror = (ev)=>{
                                            console.error(ev.error)
                                        }
                                    }
                            }
                            transaction.onerror=(eventTrans)=>{
                                    console.log(eventTrans.target.error)
                            }
                        })
                    } else {
                        if (response.status===511)
                        {
                    deleteCookie("twitter")
                    deleteCookie("messenger")
                    deleteCookie("gmail")
                    fetch(window.location.origin).then(Promise.resolve)
                        }
                        else {
                            throw new Error(`Server responded with status code ${response.status}:${response.statusText}`)
                        }
                    }
                }
            )
                .catch(
                    (error)=>{console.error(error)}
                )
        }
    }
    res.onerror=(ev)=>{
        console.log(ev.target.errorCode)
    }
}

/**
 *
 * Create event listeners regarding contact element, while also
 * for usage of button-down and button-up for more interactive transition between contacts.
 *
 * **/
function addClickListeners() {
    window.addEventListener("load", () => {
        getAndCreateConversationHistory(document.querySelector(".contact-selected"))
    })

    let contactList = document.getElementsByClassName("contact")
    //add usability for regular clicking
    for (let i = 0; i < document.getElementsByClassName("contact").length; i++) {
        document.getElementsByClassName("contact")[i].addEventListener("click", (e) => {
            selectContact(e.currentTarget)
        })
    }
    //button down listener
    document.addEventListener("keydown", ev => {
            const key = ev.key
            let chosenId = 0;
            for (let i = 0; i < contactList.length; i++) {
                if (contactList[i].classList.contains("contact-selected")) {
                    chosenId = i;
                }
            }
            //arrow-down handling
            if (key === "ArrowDown") {
                ev.preventDefault()
                ev.stopPropagation()
                for (let i = 0; i < contactList.length; i++) {
                    if (i === chosenId) {
                        if (i + 1 >= contactList.length) {
                            selectContact(contactList[0])
                        } else {
                            selectContact(contactList[i + 1])
                        }
                        break
                    }
                }
            }
            //arrow-up handling
            if (key === "ArrowUp") {
                ev.preventDefault()
                ev.stopPropagation()
                for (let i = 0; i < contactList.length; i++) {
                    if (i === chosenId) {
                        contactList[i].classList.remove("contact-selected")
                        contactList[i].classList.add("contact-not-selected")
                        if (i - 1 < 0) {
                            selectContact(contactList[contactList.length - 1])
                        } else {
                            selectContact(contactList[i - 1])
                        }
                        break
                    }
                }
            }
        }
    )

}

addClickListeners()
