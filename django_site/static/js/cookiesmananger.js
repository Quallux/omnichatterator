/**
 * Creates new cookie.
 *
 * @param cname{string} name of the cookie
 * @param cvalue{string} value of the cookie
 * @param exdays{string} duration of the cookie
 */
function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

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
 * Remove the cookie by its name.
 *
 * @param cname
 */
function deleteCookie(cname) {
    document.cookie = cname + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}

document.getElementById("logout-all").addEventListener("click", async () => {
    deleteCookie(PLATFORMS[0])
    deleteCookie(PLATFORMS[1])
    deleteCookie(PLATFORMS[2])
    await DB.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME).clear()
    await fetch(window.location.origin + "/logout/")
});

Array.from(document.getElementsByClassName("confirm-logout")).forEach(
    a => {
        a.addEventListener("click", (ev) => {
            const value = ev.currentTarget.id.split("-")[0]
            deleteCookie(value)
            const url = new URL(window.location.origin + "/logout/?" + new URLSearchParams(
                {"platform": value}
            ))
            fetch(url).then(
                (res) => {
                    if (res.ok) {
                        const cookies = [getCookie(PLATFORMS[0]), getCookie(PLATFORMS[1]), getCookie(PLATFORMS[2])]
                        for (let i = 0; i<cookies.length;i++)
                        {
                            if (cookies[i]==="")
                            {
                                const objectStore = DB.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME)
                                objectStore.index("platform").getAllKeys(PLATFORMS[i]).onsuccess = (event)=>{
                                    Array.from(event.target.result).forEach(a=>{
                                        objectStore.delete(Number(a))
                                    })
                                    objectStore.transaction.commit()
                                }
                            }
                        }
                  if (cookies.some((elem)=>elem!=="")) {
                            window.location.reload()
                        } else {
                            window.location.href = window.location.origin + "/login/"
                        }
                    }
                }
            )
        })
    }
)
