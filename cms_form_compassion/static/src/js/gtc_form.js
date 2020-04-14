$(document).ready(function () {
    $(".gtc-link").each(function () {
        var $elem = $(this);
        $elem.click(function (event) {
            // Do not scroll to the top of the page
            event.preventDefault();
            // Toggle gtc text
            $(".gtc").toggle();
        });
    });
});
