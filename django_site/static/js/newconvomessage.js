/**
 *
 *
 * @param messageObj
 * @param id
 * @returns {HTMLDivElement}
 */

function createNewConvoMessage(messageObj, id)
{
    const divContainer = document.createElement("div")
    const divMessage = document.createElement("div")
    divContainer.classList.add('conversation-message-container', 'max-width', 'flex-container')
    divMessage.classList.add('conversation-message')
    const contact = document.querySelector(".contact-selected");
    const isOwn = id !== messageObj["senderId"];
    divMessage.classList.add(isOwn?"mine":"his");
    if (!isOwn)
    {
         const profilePhoto = document.createElement("img")
         profilePhoto.classList.add("conversation-profile-photo")
    profilePhoto.src = contact.querySelector(".contact-avatar").src
            divContainer.appendChild(profilePhoto)
    }
      divContainer.appendChild(divMessage)
    //TODO modify for attachments
    divMessage.innerText = messageObj["message"]
    return divContainer
}

/**
 *
 *
 * @param msg
 * @param msgContainer
 */
function appendAttachment(msg, msgContainer) {
    if (Object.keys(msg["attachments"]).length !== 0) {
        //TODO: not my creative moment, need to rephrase the text
        const attachMsg = "-----\n This message contains a HTML element shared in a message body. For displaying" +
            " the full link, click on the link below.\n\n"
        const link = document.createElement("a")
        const urlAddr = window.location.origin + "/" + msg["messageId"] + "/"
        const linkText = document.createTextNode(urlAddr)
        link.appendChild(linkText)
        const innerMessageContainer = msgContainer.querySelector(".conversation-message");
       innerMessageContainer.innerText = innerMessageContainer.innerText.concat(attachMsg)
       innerMessageContainer.append(link)
       innerMessageContainer.querySelector("a").addEventListener("click", () => {
            const newTab = window.open(urlAddr, "_blank")
            if (!newTab) {
                console.error(`Could not open the address ${urlAddr}.`)
            }
            newTab.document.open()
            newTab.document.write(msg["attachments"])
            newTab.document.close()
        })
    }
    else{
        const innerMessageContainer = msgContainer.querySelector(".conversation-message");
        if (innerMessageContainer.innerText.length<=0)
        {
            innerMessageContainer.innerText = "-----\n\n This message has unsupported format.\n\n"
        }
    }
}