odoo.define('account_reconcile_compassion.relational_fields', function (require) {
    "use strict";
    var FieldMany2One = require('web.relational_fields').FieldMany2One;

    FieldMany2One.include({
        start: function () {
            // We add coloration by force if we deal with sponsorship_id. We have to do
            // so because this is a QWeb form (we have no template to set options="" on)
            if (this.name === "sponsorship_id") {
                this.nodeOptions.colors = {'draft':'blue', 'waiting':'green', 'cancelled':'grey', 'terminated':'grey', 'mandate':'red'};
                this.nodeOptions.field_color = 'state';
            }
            return this._super.apply(this, arguments);
        }
    });
});

