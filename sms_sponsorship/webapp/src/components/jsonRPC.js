export default (url, data, success) => {
    let xhr = new XMLHttpRequest();
    xhr.withCredentials = true;

    xhr.addEventListener("readystatechange", function() {
        if (this.readyState === 4) {
            success(this);
        }
    });

    xhr.open("POST", url);
    xhr.setRequestHeader("Content", "application/json");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Cache-Control", "no-cache");

    xhr.send(JSON.stringify(data));
}