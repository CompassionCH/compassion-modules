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
            if (value.newValue) {
                $('.oe_desc_'+lang+' iframe').contents().find(value_en_id).text(value.newValue);
                $('.oe_desc_'+lang+' iframe').contents().find(value_en_id).css('color', 'blue');
            }
            else {
                $('.oe_desc_'+lang+' iframe').contents().find(value_en_id).text(value_en);
                $('.oe_desc_'+lang+' iframe').contents().find(value_en_id).css('color', 'red');
            }
        },
        values_changed: function(field, value) {
            var value_en = this.$().parent().find('[data-fieldname="value_en"]').children().text();
            this.update_value(field.name, value, value_en);
        },
    });
    instance.web.form.widgets.add('autoDescription', 'instance.child_compassion.autoDescription');
}

