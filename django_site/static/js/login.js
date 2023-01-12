function select_messenger_login() {
    const cookie = getCookie("csrftoken");
    let headers = new Headers();
    headers.append('X-CSRFToken', cookie);

    fetch(window.location.origin+"/get_authorization_url/",
        {
            method: 'POST',
            headers: headers,
            body: JSON.stringify( {'platform': "messenger"} ),
            credentials: "include"
    }).then (
        (response) => {
            if (response.ok){
                response.json().then((res) => {
                    let element = document.getElementById("select-twitter-form");
                    element.classList.add("hidden");

                    element = document.getElementById("log-in-with-text");
                    element.classList.add("hidden");

                    element = document.getElementById("logging-in-with-text");
                    element.classList.remove("hidden");

                    element = document.getElementById("messenger-selected");
                    element.classList.remove("hidden");

                    element = document.getElementById("messenger-link")
                    element.setAttribute("href", res["verification_uri"])

                    element = document.getElementById("messenger-code")
                    let user_code = document.createTextNode(res["user_code"]);
                    element.appendChild(user_code);
                    setInterval(function() { checkMessengerLoginStatus(res["code"]); }, res["interval"] * 1000 + 150)
                })
            } else {
                throw new Error()
            }
        }
    ).catch(
        (error)=>{console.log(error)}
    )
}

function copyMessengerCodeToClipboard() {
    let messengerCodeInputElement = document.getElementById("messenger-code");
    window.getSelection().selectAllChildren(messengerCodeInputElement);
    document.execCommand("Copy")
    window.getSelection().empty()

    let element = document.getElementById("copied-popup")
    element.classList.remove("hidden")
    setTimeout(() => element.classList.add("hidden"), 2000)
}

function select_gmail_login() {

    const cookie = getCookie("csrftoken");
    let headers = new Headers();
    headers.append('X-CSRFToken', cookie);
    fetch(window.location.origin+"/get_authorization_url/",
        {
            method: 'POST',
            headers: headers,
            body: JSON.stringify( {'platform': "gmail"} ),
            credentials: "include"
    }).then (
        (response)=>{
            if (response.ok)
            {
                response.json().then((res)=>{
                    console.log(res["login"])
                    if (res["login"]!="false")
                    {
                        let a = document.createElement('a');
                        let link = document.createTextNode("Get Auth from Gmail");
                        a.appendChild(link)
                        a.title = "Get Auth from Gmail";
                        a.href =  res["login"];
                        //a.target = "_blank";
                        a.classList.add("get-authorization-url-link")

                        let element = document.getElementById("twitter_url");
                        element.appendChild(a);
                        const div = document.createElement("div")
                        div.classList.add("margin-top-10px")
                        a = document.createElement("a")
                        a.classList.add("back-link")
                        div.classList.add("center")
                        a.innerText = "go back"
                        a.href = window.location.origin+"/login/"
                        div.appendChild(a)
                        element.parentElement.appendChild(div)

                        element = document.getElementById("log-in-with-text");
                        element.classList.add("hidden");

                        element = document.getElementById("select-twitter-form");
                        element.classList.add("hidden");

                        element = document.getElementById("gmail-selected-logo");
                        element.classList.remove("hidden");

                        element = document.getElementById("logging-in-with-text");
                        element.classList.remove("hidden");

                        element = document.getElementById("go-back");
                        element.classList.remove("hidden");



                        element = document.getElementById("error");
                        if (element != null) {
                            element.classList.add("hidden");
                        }
                    }
                    else {
                        window.location.href = window.location.origin + "/login/"
                    }
                })
            }
             else{
                throw new Error('Could not fetch URL /get_authorization_url/')
            }
        }
    ).catch(
        (error)=>{console.log(error)}
    )
}

function select_twitter_login() {

    const cookie = getCookie("csrftoken");
    let headers = new Headers();
    headers.append('X-CSRFToken', cookie);

    fetch(window.location.origin+"/get_authorization_url/",
        {
            method: 'POST',
            headers: headers,
            body: JSON.stringify( {'platform': "twitter"} ),
            credentials: "include"
        })
        .then(
            response => {
                if (response.status === 200) {
                    response.json().then(
                        value => {
                            let a = document.createElement('a');
                            let link = document.createTextNode("Get authorization PIN");
                            a.appendChild(link)
                            a.title = "Get authorization PIN";
                            a.href =  value["authorization_url"];
                            a.target = "_blank";
                            a.classList.add("get-authorization-url-link")

                            let element = document.getElementById("twitter_url");
                            element.appendChild(a);

                            element = document.getElementById("auth_id");
                            element.setAttribute("value",value["auth_id"]);

                            element = document.getElementById("log-in-with-text");
                            element.classList.add("hidden");

                            element = document.getElementById("select-twitter-form");
                            element.classList.add("hidden");

                            element = document.getElementById("twitter-selected-logo");
                            element.classList.remove("hidden");

                            element = document.getElementById("login-form");
                            element.classList.remove("hidden");

                            element = document.getElementById("logging-in-with-text");
                            element.classList.remove("hidden");

                            element = document.getElementById("error");
                            if (element != null) {
                                element.classList.add("hidden");
                            }
                        }
                    )
                }
            })
        .catch(
            error => console.error(error)
        )
}

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

function checkMessengerLoginStatus(verificationCode) {
    const cookie = getCookie("csrftoken");
    let headers = new Headers();
    headers.append('X-CSRFToken', cookie);

    fetch(window.location.origin+"/check-messenger-login-status/",
        {
            method: 'POST',
            headers: headers,
            body: JSON.stringify( {'verification_code': verificationCode} ),
            credentials: "include"
    }).then (
        (response) => {
            if (response.ok){
                response.json().then((res) => {
                    if (res["status_code"] === 0) {
                        // USER HAS SUCCESSFULLY AUTHORIZED
                        window.location.href = window.location.origin + "/messenger_choose_page/" // redirect
                    } else if (res["status_code"] === 463) {
                        // VERIFICATION CODE EXPIRED
                        window.location.href = window.location.origin + "/login/" // redirect
                    }
                });
            } else {
                throw new Error()
            }
        }
    ).catch(
        (error)=>{console.log(error)}
    )
}

function setUpLoginButtons() {
    let twitterCookie = getCookie("twitter")
    let messengerCookie = getCookie("messenger")
    let gmailCookie = getCookie("gmail")

    if (!twitterCookie) {
        let element = document.getElementById("twitter-done")
        element.classList.add("hidden")
        element = document.getElementById("twitter-button")
        element.classList.add("clickable")
        document.getElementById("twitter-button").addEventListener("click", select_twitter_login)
    }
    if (!messengerCookie) {
        let element = document.getElementById("messenger-done")
        element.classList.add("hidden")
        element = document.getElementById("messenger-button")
        element.classList.add("clickable")
        document.getElementById("messenger-button").addEventListener("click", select_messenger_login)
    }
    if (!gmailCookie) {
        let element = document.getElementById("gmail-done")
        element.classList.add("hidden")
        element = document.getElementById("gmail-button")
        element.classList.add("clickable")
        document.getElementById("gmail-button").addEventListener("click", select_gmail_login)
    }
}

setUpLoginButtons()
