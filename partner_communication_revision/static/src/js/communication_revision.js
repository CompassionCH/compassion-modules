odoo.define('partner_communication_revision.edit_revision', function (require) {
'use strict';

    var ListView = require('web.ListView');


    ListView.include({
        events: {
            "click .toggle_condition": "your_function",
        },
        your_function: function () {
            console.log('Button Clicked')
        },
        render_buttons: function() {
            var self = this;
            this._super.apply(this, arguments);
            if (this.model == 'partner.communication.conditional.text') {
                if (this.$buttons) {
                    this.$buttons.find('.o_list_button_income').on('click', this.proxy('refresh_revision_text'));
                }
            }
        },

        refresh_revision_text: function () {
            console.log("refresh");
        }
    });

});
