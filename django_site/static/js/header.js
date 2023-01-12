
document.addEventListener("DOMContentLoaded", () => {
    const perfEntries = String(performance.getEntriesByType("navigation")[0].type)
    const navigation = document.getElementById("navigation")
    const chatWindow = document.getElementById("chat-window")
    if (perfEntries === "navigate") {
        const logo = navigation.querySelector("#image-container")
        editContent(navigation, chatWindow, true)
        logo.animate([
            {
                transform: "rotateY(0)"
            },
            {
                transform: "rotateY(180deg)"
            }
        ], {
            easing: "ease-out",
            duration: 1000,
            iterations: 1,
            delay: 0.5
        }).onfinish = () => {
            navigation.animate(
                [
                    {
                        transform: "translateX(40vw)"
                    },
                    {
                        transform: "translateX(0%)"
                    }

                ],
                {
                    easing: "ease-in-out",
                    duration: 2000,
                    iterations: 1
                }
            ).onfinish = () => {
                navigation.style.zIndex = "0"
                navigation.style.transform = "translateX(0)"
                editContent(navigation, chatWindow, false)
            }
        }
    }
    else {
        navigation.classList.add("reloaded")
        editContent(navigation, chatWindow, false)
    }

    if (getCookie("twitter")!=="")
    {
        document.getElementById("twitter-user").classList.remove("hidden")
    }
    if (getCookie("messenger")!=="")
    {

        document.getElementById("messenger-user").classList.remove("hidden")
    }
    if(getCookie("gmail")!=="")
    {
        document.getElementById("gmail-user").classList.remove("hidden")
    }
     window.history.forward()

})

/**
 *
 * Returns cookie value.
 *
 * @param cname{string} name of the cookie
 * @returns {string}
 */
function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

/**
 *
 * @param navigation{HTMLElement} id="navigation" element
 * @param chatWindow{HTMLElement} id="chat-window" element
 * @param remove{boolean} is added or removed
 */
function editContent(navigation, chatWindow, remove) {
    const keyframes = [
        {
            opacity: "0"
        },
        {
            opacity: "1"
        }
    ]
    const property = {
            easing: "ease-in-out",
        duration: 1000,
        iterations: 1
    }
    for (let i = 0; i < navigation.children.length; i++) {
        if (navigation.children[i].id === "image-container") {
            continue
        }
        if (remove) {
            navigation.children[i].classList.add("hidden")
            navigation.children[i].style.opacity = "0%"
        } else {
             navigation.children[i].classList.remove("hidden")
             navigation.children[i].style.opacity = "0"
             navigation.children[i].animate(keyframes, property).onfinish = ()=>{
                 navigation.children[i].style.opacity = "1"
                }
        }

    }
    for (let i = 0; i < chatWindow.children.length; i++) {
            if (remove) {
                chatWindow.children[i].classList.add("hidden")
                chatWindow.children[i].style.opacity = "0%"
            } else {
                chatWindow.children[i].classList.remove("hidden")
                chatWindow.children[i].style.opacity = "0"
                chatWindow.children[i].animate(keyframes, property).onfinish = ()=>{
                    chatWindow.children[i].style.opacity = "1"
                }
            }
    }
}