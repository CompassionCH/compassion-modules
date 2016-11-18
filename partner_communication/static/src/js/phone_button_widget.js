/* Copied from base_phone module -> Only change the returned action */

openerp.partner_communication = function (instance) {

    var _t = instance.web._t;

    instance.partner_communication.PhoneCommunication = instance.base_phone.FieldPhone.extend({

        render_value: function () {
            if (!this.get('effective_readonly')) {
                this._super();
            } else {
                var self = this;
                var phone_num = this.get('value');
                //console.log('BASE_PHONE phone_num = %s', phone_num);
                var href = '#';
                var href_text = '';
                if (phone_num) {
                    href = 'tel:' + phone_num;
                    href_text = formatInternational('', phone_num) || '';
                }
                if (href_text) {
                    this.$el.find('a.oe_form_uri').attr('href', href).text(href_text);
                    this.$el.find('span.oe_form_char_content').text('');
                } else {
                    this.$el.find('a.oe_form_uri').attr('href', '').text('');
                    this.$el.find('span.oe_form_char_content').text(phone_num || '');
                }
                var click2dial_text = '';
                if (href_text && !this.options.dial_button_invisible) {
                    click2dial_text = _t('Dial');
                }
                this.$el.find('#click2dial').off('click');
                this.$el.find('#click2dial')
                    .text(click2dial_text)
                    .on('click', function (ev) {
                        self.do_notify(
                            _t('Click2dial started'),
                            _t('Unhook your ringing phone'));
                        var arg = {
                            'phone_number': phone_num,
                            'click2dial_model': self.view.dataset.model,
                            'click2dial_id': self.view.datarecord.id,
                        };
                        self.rpc('/base_phone/click2dial', arg).done(function (r) {
                            //console.log('Click2dial r=%s', JSON.stringify(r));
                            if (r === false) {
                                self.do_warn("Click2dial failed");
                            } else if (typeof r === 'object') {
                                self.do_notify(
                                    _t('Click2dial successfull'),
                                    _t('Number dialed:') + ' ' + r.dialed_number);
                                var context = {
                                    'click2dial_id': self.view.datarecord.partner_id[0],
                                    'phone_number': phone_num,
                                    'call_name': self.view.datarecord.config_id[1],
                                    'timestamp': new Date().getTime(),
                                    'communication_id': self.view.datarecord.id,
                                };
                                var action = {
                                    name: _t("Log your call"),
                                    type: 'ir.actions.act_window',
                                    res_model: 'partner.communication.call.wizard',
                                    view_mode: 'form',
                                    views: [[false, 'form']],
                                    target: 'new',
                                    context: context,
                                };
                                instance.client.action_manager.do_action(action);
                            }
                        });
                    });
            }
        }
    });

    instance.web.form.widgets.add('phone_communication', 'instance.partner_communication.PhoneCommunication');
};
