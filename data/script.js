document.addEventListener("DOMContentLoaded", function () {
    var video = document.querySelector("video");
    if (!video) {
        return;
    }

    video.addEventListener("play", function () {
        console.log("Video playback started");
    });
});
