/* Copied from base_phone module -> Only change the returned action */

odoo.define('partner_communication.phone_widget', function (require) {
    'use strict';

    var core = require('web.core');
    var base_phone = require('base_phone.phone_widget');
    var web_client = require('web.web_client');
    var _t = core._t;

    var PhoneCommunication = base_phone.FieldPhone.extend({
        render_value: function() {
            if (this.get('effective_readonly') && this.clickable) {
                var self = this;
                var phone_num = this.get('value');
                if(phone_num) {
                    phone_num = phone_num.replace(/\s/g, '').replace(/-/g, '');
                }
                var click2dial_text = '';
                if (phone_num && !this.options.dial_button_invisible) {
                    click2dial_text = _t('Dial');
                }
                this.$el.filter('#click2dial').text(click2dial_text).attr(
                    'href', '#').on('click', function() {
                    self.do_notify(
                        _t('Click2dial started'),
                        _t('Unhook your ringing phone'),
                        false);
                    var arg = {
                        'phone_number': phone_num,
                        'click2dial_model': self.view.dataset.model,
                        'click2dial_id': self.view.datarecord.id};
                    self.rpc('/base_phone/click2dial', arg).done(function(r) {
                        // console.log('Click2dial r=%s', JSON.stringify(r));
                        if (r === false) {
                            self.do_warn('Click2dial failed');
                        } else if (typeof r === 'object') {
                            self.do_notify(
                                _t('Click2dial successfull'),
                                _t('Number dialed:') + ' ' + r.dialed_number,
                                false);
                            if (r.action_model) {
                                var context = {
                                    'click2dial_model': 'res.partner',
                                    'click2dial_id':
                                        self.view.datarecord.partner_id[0],
                                    'phone_number': phone_num,
                                    'communication_id': self.view.datarecord.id,
                                    'timestamp': new Date().getTime(),
                                    'call_name':
                                        self.view.datarecord.config_id[1]
                                };
                                var action = {
                                    name: _t('Log your call'),
                                    type: 'ir.actions.act_window',
                                    res_model:
                                        'partner.communication.call.wizard',
                                    view_mode: 'form',
                                    views: [[false, 'form']],
                                    target: 'new',
                                    context: context
                                };
                                web_client.action_manager.do_action(action);
                            }
                        }
                    });
                });
            }
        }
    });

    if(!core.form_widget_registry.get('phone_communication')) {
        core.form_widget_registry.add('phone_communication',
            PhoneCommunication);
    }
});
