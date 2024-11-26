odoo.define('sbc_translation.translation_letter_counting', function(require) {
    'use strict'

    function refreshCounting() {
        const rpc = require("web.rpc");
        const modelId = (new URLSearchParams(window.location.hash.substr(1))).get("id");
        rpc.query({
            model: "translation.letter.counting.wizard",
            method: "search_read",
            domain: [["id", "=?", modelId]],
            fields: ["start_of_counting", "counting"],
        }).then(function(result) {
            if(result.length > 0 && 'counting' in result[0]) {
                document.getElementsByName("counting")[0].innerHTML = result[0].counting;
            }
        })
    }
    window.setInterval(function(){
        if(document.getElementsByName("counting").length == 1) {
            refreshCounting();
        }
    }, 5000);

});