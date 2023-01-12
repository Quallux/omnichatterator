
Array.from(document.querySelectorAll(".usr_page")).forEach(a=>{
    a.addEventListener("click", (ev)=>{
        func(ev.currentTarget)
})})


function func(elem) {
    const cookie = getCookie("csrftoken");
    let headers = new Headers();
    headers.append('X-CSRFToken', cookie);
    const url = new URL(window.location.origin + "/messenger_choose_page/")
    const res = {"page_choice":elem.id}
    console.log(url)
    fetch(url,
    {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(res),
            credentials: "same-origin"
        }).then(response=>{
            if(response.ok) {
                window.location.href = window.location.origin

            } else {
                throw new Error("Failed to send selected page");

            }
        }).catch(Error=>{console.error(Error)})
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