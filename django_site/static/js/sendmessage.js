/**
 * Create listeners for sending messages.
 */
function addMessageListener() {
    document.getElementById("send-message-button").addEventListener("click", (e) => {
        e.preventDefault()
        sendMessage(document.querySelector(".contact-selected").querySelector(".contact-platform").innerText)
    })
    document.addEventListener("keypress", ev => {
        const key = ev.key
        if (key === "Enter") {
            ev.preventDefault()
            ev.stopPropagation()
            sendMessage(document.querySelector(".contact-selected").querySelector(".contact-platform").innerText)
        }
    })
}

/**
 *
 * Evaluate the send-message form and send message on the server.
 *
 * @param platform{string} platform from which is the message sent
 */
function sendMessage(platform) {
    //Check if local database is already loaded
    if (DB === null) {
        console.error(`Error while getting database reference for database ${DB_NAME}. Database is probably not yet opened or is corrupted.`)
    }
    //Process the form for sending messages
    const form = document.forms["send-message"]
    if (form != null) {
        for (let i = 0; i < document.getElementsByClassName("contact").length; i++) {
        }
        const id = document.getElementsByClassName("contact-selected")[0].getElementsByClassName("contact-id")[0].innerText

        // following 3 lines of code move contact that the user is sending message to on top of contact list
        let firstContactElementToMoveBefore = document.getElementsByClassName("contact")[0];
        let contactElementToMoveToTop = document.getElementsByClassName("contact-selected")[0];
        firstContactElementToMoveBefore.parentElement.insertBefore(contactElementToMoveToTop, firstContactElementToMoveBefore)

        const message = form.elements["message"].value
        //If message is empty, do not proceed further
        if (message.length <= 0) {
            window.alert("You can't send empty messages.")
            return
        }
        //prepare headers and client window before fetch on server
        document.getElementById("send-message").reset()
        const cookie = getCookie("csrftoken")
        const headers = new Headers()
        headers.append('Content-Type', 'application/json')
        headers.append('X-CSRFToken', cookie);
        const request = {
            "senderId": id,
            "platform": platform,
            "message": message
        }
        fetch(window.location.origin + "/send_msg/",
            {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(request),
                credentials: "include"
            }).then(response => {
            if (response.ok) {
                response.json().then(
                    (res) => {
                        //If response from server was successful, commit search in every platform implemented, if it finds a match, proceed
                        PLATFORMS.forEach(a => {
                            if (PLATFORMS.find((e) => e === a) === undefined) {
                                return
                            }
                            const newConvoHistoryMessage = {
                                "messageId": res["messageId"] ? res["messageId"] : "",
                                "timeStamp": getTimeStamp(),
                                "senderId": getCookie(PLATFORMS[PLATFORMS.indexOf(a)]),
                                "senderName": "",
                                "avatar": "",
                                "message": message,
                                "attachments": {}
                            }
                            //create new database transaction
                            const dbTransaction = DB.transaction(STORE_NAME, "readwrite")
                            const objStore = dbTransaction.objectStore(STORE_NAME)
                            //find record with selected ID
                            objStore.index("ID").get(id).onsuccess = (event) => {
                                if (event.target.result === undefined) {
                                    throw new Error(`Could not find ID ${id} in the local database.`)
                                } else {
                                    const newMsgList = event.target.result["messageList"]
                                    newMsgList.unshift(newConvoHistoryMessage)
                                    newMsgList.sort((a, b) => (a["timeStamp"] > b["timeStamp"]) ? -1 : ((b["timeStamp"] > a["timeStamp"]) ? 1 : 0))
                                    const newList = {
                                        "userId": event.target.result["userId"],
                                        "platform": event.target.result["platform"],
                                        "messageList": newMsgList
                                    }
                                    //find the primary key for our record and update its value
                                    objStore.index("ID").getKey(id).onsuccess = (ev) => {
                                        if (platform === PLATFORMS[PLATFORMS.indexOf(a)]) {
                                            objStore.put(newList, ev.target.result).onsuccess = () => {
                                                dbTransaction.commit()
                                                //fill conversation history
                                                appendToConversationHistory(message, typeof message, true, false)
                                                //scroll to bottom of the page
                                                document.querySelector("#conversation-history").scrollTo({
                                                        top: document.querySelector("#conversation-history").scrollHeight,
                                                        behavior: "smooth"
                                                    }
                                                )
                                                if (platform!=="gmail") {
                                                    document.querySelector(".contact-selected").querySelector(".contact-message").innerText =
                                                        message.length > MESSAGE_CONTACT_MAX_LENGTH ?
                                                            message.slice(0, MESSAGE_CONTACT_MAX_LENGTH - 1) + "..." : message
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        })
                    })
            } else {
                if (response.status === 511) {
                    deleteCookie("twitter")
                    deleteCookie("messenger")
                    deleteCookie("gmail")
                    fetch(window.location.origin).then(Promise.resolve)
                } else {
                    throw new Error(`Server responded with status code ${response.status}:${response.statusText}`)
                }
            }
        }).catch((error) => {
            console.error("Error while sending message: " + error)
            window.alert("Could not send message.")
        })

    }
}

/**
 *@deprecated
 *
 * Create and animate new message status pop-up.
 *
 * @param messageClass{string} type of class the pop-up is associated with
 * @param message{string} innerText value
 */
function createMessageStatusPopUp(messageClass, message) {
    const chatContent = document.getElementById("message-status-container")
    if (chatContent.getElementsByClassName("popup").length > 0) {
        document.querySelectorAll(".popup").forEach(elem => {
            elem.getAnimations().forEach(animation => animation.finish())
            elem.remove()
        })
    }
    const newDiv = document.createElement("div")
    newDiv.classList.add(messageClass)
    newDiv.classList.add("popup")
    newDiv.innerText = message
    chatContent.append(newDiv)
    const animationOpacity = [
        {
            opacity: 0, transform: 'scale(0.55)', offset: 0, easing: 'ease-in'
        },
        {
            opacity: 0.7, transform: 'scale(0.85)', offset: 0.45, easing: 'ease-out'
        },
        {
            opacity: 1, transform: 'scale(1)', offset: 1
        }
    ]
    const propertiesOpacity = {
        duration: 250,
        iterations: 1,
        easing: "ease-in",
    }
    if (document.getElementsByClassName("popup")[0] !== null) {
        document.getElementsByClassName("popup")[0].animate(animationOpacity, propertiesOpacity)
        setTimeout(function () {
                const timeout = 1000;
                const animationRemove = [
                    {
                        opacity: 1, easing: 'ease-out', transform: 'scale(1)'
                    },
                    {
                        opacity: 0, transform: 'scale(0.90)'
                    }
                ]
                const propertiesRemove = {
                    duration: timeout,
                    iterations: 1,
                    easing: "ease-out"
                }
                if (document.getElementsByClassName("popup")[0] != null) {
                    document.getElementsByClassName("popup")[0].animate(animationRemove, propertiesRemove)
                    setTimeout(function () {
                        if (document.getElementsByClassName("popup").length > 0) {
                            document.getElementById("message-status-container").removeChild(document.getElementsByClassName("popup")[0])
                        }
                    }, timeout)
                }
            }
            , 4000)
    }
}


/**
 *From the parameter message creates new conversation message with content type based on its type parameter and passes it into conversation history.
 *
 *
 * @param message content of the message, either as String, parsed JSON object or attachment object/arrays
 * @param type{string} type of the message (passed as typeof)
 * @param isOurOwn{boolean} either if it is our sent message or received message
 * @param isJson{boolean} if the parameter is JSON object
 */
function appendToConversationHistory(message, type, isOurOwn, isJson) {
    const messageContent = isJson ? message["message"] : message
    const convoHistory = document.getElementById("conversation-history")
    const divContainer = document.createElement("div")
    const divMessage = document.createElement("div")
    //add classes to elements
    divContainer.classList.add('conversation-message-container', 'max-width', 'flex-container')
    divMessage.classList.add('conversation-message')
    divContainer.appendChild(divMessage)
    //TODO switch message value based on type for each type (text, image etc.)
    switch (type) {
        case "string":
        case "String": {
            divMessage.innerText = messageContent
            break;
        }
        default: {
            console.error("wrong format")
            throw new Error('The new message is not in allowed format.')
        }
    }
    //add classes based if either it is our own message or not
    divMessage.classList.add(isOurOwn ? "mine" : "his");
    //TODO edit if order is wrong
    convoHistory.insertBefore(divContainer, convoHistory.children[0])
}


addMessageListener()




