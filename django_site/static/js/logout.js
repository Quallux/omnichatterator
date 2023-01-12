// this document handles visualization of logout process, the core is located inside cookiesmanager.js

let screenCoverBox = document.getElementById("screen-cover-box");
let logoutPlatformElements = document.getElementsByClassName("logout-platform");
let noElements = document.getElementsByClassName("no");

Array.prototype.forEach.call(logoutPlatformElements, function (logoutPlatform) {
    logoutPlatform.addEventListener("click", () => {
        screenCoverBox.classList.remove("hidden");
    });
});

Array.prototype.forEach.call(noElements, function (no) {
    no.addEventListener("click", () => {
        let yesNoBoxElements = document.getElementsByClassName("yes-no-box");
        Array.prototype.forEach.call(yesNoBoxElements, function (yesNoBox) {
           yesNoBox.classList.add("hidden");
        });
        screenCoverBox.classList.add("hidden");
    });
});

// ALL PLATFORMS
let logoutAll = document.getElementById("logout");

if (logoutAll != null) {
    logoutAll.addEventListener("click", () => {
        screenCoverBox.classList.remove("hidden");
        let logoutAllBox = document.getElementById("logout-all-box");
        logoutAllBox.classList.remove("hidden");
    });
}

// TWITTER

let twitterUserImage = document.getElementById("twitter-user-image");
let twitterLogoutButton = document.getElementById("twitter-logout-button");

if (twitterUserImage != null && twitterLogoutButton != null) {
    let twitterLogoutBox = document.getElementById("twitter-logout-box");

    twitterLogoutButton.addEventListener("click", () => {
        twitterLogoutBox.classList.remove("hidden");
    })

    twitterUserImage.addEventListener("mouseenter", () => {
        twitterLogoutButton.classList.remove("hidden");
    });

    twitterUserImage.addEventListener("mouseleave", () => {
        twitterLogoutButton.classList.add("hidden");
    });

    twitterLogoutButton.addEventListener("mouseenter", () => {
        twitterLogoutButton.classList.remove("hidden");
    });

    twitterLogoutButton.addEventListener("mouseleave", () => {
        twitterLogoutButton.classList.add("hidden");
    });
}

// MESSENGER

let messengerUserImage = document.getElementById("messenger-user-image");
let messengerLogoutButton = document.getElementById("messenger-logout-button");

if (messengerUserImage != null && messengerLogoutButton != null) {
    let messengerLogoutBox = document.getElementById("messenger-logout-box");

    messengerLogoutButton.addEventListener("click", () => {
        messengerLogoutBox.classList.remove("hidden");
    })

    messengerUserImage.addEventListener("mouseenter", () => {
        messengerLogoutButton.classList.remove("hidden");
    });

    messengerUserImage.addEventListener("mouseleave", () => {
        messengerLogoutButton.classList.add("hidden");
    });

    messengerLogoutButton.addEventListener("mouseenter", () => {
        messengerLogoutButton.classList.remove("hidden");
    });

    messengerLogoutButton.addEventListener("mouseleave", () => {
        messengerLogoutButton.classList.add("hidden");
    });
}

// GMAIL

let gmailUserImage = document.getElementById("gmail-user-image");
let gmailLogoutButton = document.getElementById("gmail-logout-button");

if (gmailUserImage != null && gmailLogoutButton != null) {
    let gmailLogoutBox = document.getElementById("gmail-logout-box");

    gmailLogoutButton.addEventListener("click", () => {
        gmailLogoutBox.classList.remove("hidden");
    })

    gmailUserImage.addEventListener("mouseenter", () => {
        gmailLogoutButton.classList.remove("hidden");
    });

    gmailUserImage.addEventListener("mouseleave", () => {
        gmailLogoutButton.classList.add("hidden");
    });

    gmailLogoutButton.addEventListener("mouseenter", () => {
        gmailLogoutButton.classList.remove("hidden");
    });

    gmailLogoutButton.addEventListener("mouseleave", () => {
        gmailLogoutButton.classList.add("hidden");
    });
}
