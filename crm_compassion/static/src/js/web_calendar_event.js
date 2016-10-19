openerp.crm_compassion = function (instance) {
    /**
     * This is the extension of the file:
     * bin/addons/web_calendar/static/src/js/web_calendar.js
     *
     * The aim is to override the function "quick_add" in order to have
     * more than a single field 'name' in the quick create popup.
     */

    instance.web.crm_compassion = instance.web.crm_compassion || {};
    instance.web_calendar.QuickCreate = instance.web_calendar.QuickCreate.extend({
        // template: 'CalendarView.quick_create',

        /**
         * Gathers data from the quick create dialog a launch quick_create(data) method
         * In the case were the function is not called from context
         * crm.event.compassion, then we use the original function
         */
        quick_add: function() {
            //var model = this.getParent().model;
            // .model -> "crm.event.compassion"
            // .name  -> "Events Calendar"

            //if (model !== "crm.event.compassion"){
            //    return this._super();
            //}

            // create a dictionary (called associative array in javascript)
            // with the values stored in input
            var vals = []
            for (var i = 0; i < this.$input.length; i++){
                var field = this.$input[i].name;
                var value = this.$input[i].value;

                // All fields are mandatory, so we refuse to create the
                // record if one information is missing
                if (value === ""){
                    window.alert("You have to fill all the fields.")
                    return false
                }
                vals[field] = value;
            }
            return this.quick_create(vals).always(function() { return true; });
        },

    });

};
