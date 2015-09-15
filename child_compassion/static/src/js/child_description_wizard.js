openerp.child_compassion = function (instance, local) {
    
    /* 
     * new autoDescription
     * how: add widget="autoDescription" to the char field  
     */
    local.autoDescription = instance.web.form.FieldChar.extend({
        init: function(field_manager, node) {
            this._super.apply(this, arguments);
        },
        start: function() {
            this._super();
            this.on("change:value", this, this.values_changed)
        },
        update_value: function(value_lang, value, value_en) {
            lang = value_lang.replace('value_', '');
            var value_en_id = '[id="'+value_en+'"]';
            var desc_field_keyword = $('.oe_desc_'+lang+' iframe').contents().find(value_en_id);
            if (value.newValue) {
                desc_field_keyword.text(value.newValue);
                desc_field_keyword.css('color', 'blue');
            }
            else {
                desc_field_keyword.text(value_en);
                desc_field_keyword.css('color', 'red');
            }
            return desc_field_keyword.parent().html()
        },
        values_changed: function(field, value) {
            var value_en = this.$().parent().find('[data-fieldname="value_en"]').children().text();
            new_desc = this.update_value(field.name, value, value_en);
            // Store the change.
            var lang = field.name.replace('value_', '');
            var desc_field = this.getParent().getParent().getParent().getParent().getParent().fields['desc_' + lang];
            desc_field.set_value(new_desc);

        },
    });
    instance.web.form.widgets.add('autoDescription', 'instance.child_compassion.autoDescription');
}

