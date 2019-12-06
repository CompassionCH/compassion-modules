odoo.define('cms_form_compassion.gtc_form', function (require) {
    'use strict';

    var animation = require('website.content.snippets.animation');

    var gtc = animation.Class.extend({
        selector: '.gtc-link',

        /**
         * Called when widget is started
         */
        start: function () {
            this.$el.click(function (event) {
                // Do not scroll to the top of the page
                event.preventDefault();

                // Show GTC text
                $('.gtc').toggle();
            });
        },
    });
    animation.registry.gtc_form = gtc;
    return gtc;
});
