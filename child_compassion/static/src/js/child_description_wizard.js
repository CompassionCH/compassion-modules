openerp.child_compassion = function (instance) {
    instance.web.child_compassion = instance.web.child_compassion || {};
    
    instance.web.views.add('auto_description_form', 'instance.web.child_compassion.AutoDescriptionFormView');
    instance.web.child_compassion.AutoDescriptionFormView = instance.web.FormView.extend({
        start: function () {
            this._super();
            this.on('field_changed:child_property_value_ids', this, this.values_changed);
            this.on('field_changed:project_property_value_ids', this, this.values_changed);
        },
        update_value: function(lang, value, value_en) {
            var value_en_id = '[id="'+value_en[index]+'"]';

            if (value[2].hasOwnProperty('value_'+lang)) {
                var value_lang = value[2]['value_'+lang];
                if (value_lang) {
                    this.$('.oe_desc_'+lang+' iframe').contents().find(value_en_id).text(value_lang);
                    this.$('.oe_desc_'+lang+' iframe').contents().find(value_en_id).css('color', 'blue');
                }
                else {
                    this.$('.oe_desc_'+lang+' iframe').contents().find(value_en_id).text(value_en[index]);
                    this.$('.oe_desc_'+lang+' iframe').contents().find(value_en_id).css('color', 'red');
                }
            }
        },
        // Detect the changes on descriptions (Work for project description and child description)
        values_changed: function() {
            var value_en = [];
            $.each(this.$el.find('td[data-field="value_en"]'), function(index, value) {
                    value_en[index] = value.innerHTML;
            });
            var values = []
            
            // To use this method for both project and child description
            // Child description case
            if (this.fields.hasOwnProperty('child_property_value_ids')) {
                var values = this.get_field_value('child_property_value_ids');
            }
            // Project description case
            if (this.fields.hasOwnProperty('project_property_value_ids')) {
                var values = this.get_field_value('project_property_value_ids');
            }
            
            for(index in values) {
                var value = values[index];
                
                // Check if the value contain a object at 2 
                // value[2] can contains value_fr, value_de, or/and value_it
                if (value[2]) {
                    this.update_value('fr', value, value_en);
                    this.update_value('de', value, value_en);
                    this.update_value('it', value, value_en);
                }       
            }
        },

    });
}

