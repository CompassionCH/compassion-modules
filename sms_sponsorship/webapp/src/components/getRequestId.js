export default () => {
    let child_request_id = window.location.href.match(/child_request_id=([0-9]+)/);
    if (!child_request_id) {
        return false;
    }
    return child_request_id[1];
};