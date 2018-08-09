odoo.define('cms_form_compassion.gtc_form', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');

    animation.registry.modal_form = animation.Class.extend({
        selector: ".gtc-link",
        start: function () {
            // Show GTC text
            this.$el.click(function () {
                $(".gtc").toggle();
            });
        },
    });
});
