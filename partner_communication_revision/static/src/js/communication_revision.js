odoo.define('partner_communication_revision.communication_revision', function (require) {
    'use strict';

    // display debug message if set to true
    const DEBUG = false;
    // max retry if needed buttons not found in page
    const TIMEOUT_LIMIT = 5;

    if (DEBUG) console.log('Begin...');

    var ListView = require('web.ListView');
    ListView.include({
        start: function() {
            if (DEBUG) console.log('starting ...');

            var timeoutCount = TIMEOUT_LIMIT;

            // do a virtual click on the refresh button
            function refreshButtonAction () {
                if (DEBUG) console.log('Refresh');

                var refreshButton = document.getElementsByClassName('sht_refresh_button')[0];
                $(refreshButton)
                    .click()
                    .blur();

                // re-create custom click event (listView reload on every click)
                $('table.o_list_view').on("remove",function (){
                    if (DEBUG) console.log('change !');
                    attachEvents();
                });
            }

            // Attach event to toggle if tags buttons
            function attachEvents() {
                if (DEBUG) console.log("Event attached");

                var buttons = document.getElementsByTagName('button');
                var refreshButton = document.getElementsByClassName('sht_refresh_button')[0];
                var btnFound = false;

                for (var idx=0; idx < buttons.length; idx++) {
                    var button = buttons[idx];
                    if (button.className.indexOf('o_icon_button') !== -1) {
                        $(button)
                            .off("click")
                            .on("click", refreshButtonAction);

                        btnFound = true;
                    }
                }
                // if needed buttons not found, retry 500 ms after until TIMEOUT_LIMIT is reach
                if (!btnFound || !refreshButton) {
                    if (DEBUG) console.log("Buttons not found");
                    if (timeoutCount > 0) {
                        setTimeout(attachEvents, 500);

                        timeoutCount -= 1;
                    } else {
                        if (DEBUG) console.log("Buttons never found. Timeout limit reach.");
                    }
                }
            }

            attachEvents();
        }
    });

    if (DEBUG) console.log('End...')
});
