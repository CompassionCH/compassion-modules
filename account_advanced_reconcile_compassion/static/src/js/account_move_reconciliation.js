/* This is Javascript extension of module account
   in order to add custom reconcile buttons in the 
   Manual Reconcile view */
openerp.account_advanced_reconcile_compassion = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    

    // Extend the class written in module account
    instance.web.account.ReconciliationListView.include({
        init: function() {
            this._super.apply(this, arguments);
            var self = this;
            // Enable or disable buttons based on number of lines selected
            this.on('record_selected', this, function() {
                if (self.get_selected_ids().length === 0) {
                    self.$(".oe_account_recon_reconcile").attr("disabled", "");
                } else {
                    self.$(".oe_account_recon_reconcile").removeAttr("disabled");
                }
                if (self.get_selected_ids().length < 2) {
                    self.$(".oe_account_recon_reconcile_fund").attr("disabled", "");
                    self.$(".oe_account_recon_reconcile_split").attr("disabled", "");
                } else {
                    self.$(".oe_account_recon_reconcile_fund").removeAttr("disabled");
                    self.$(".oe_account_recon_reconcile_split").removeAttr("disabled");
                }
            });
        },
        
        load_list: function() {
            var self = this;
            var tmp = this._super.apply(this, arguments);
            if (this.partners) {
                // Add the buttons of reconciliation
                this.$(".oe_account_recon_reconcile").after(QWeb.render("AccountReconciliationCompassion", {widget: this}));
                this.$(".oe_account_recon_next").after(QWeb.render("AccountReconciliationOpenPartner", {widget: this}));
                
                // Add listeners to button clicks and open the corresponding wizard
                this.$(".oe_account_recon_reconcile_fund").click(function() {
                    self.reconcile_fund();
                });
                this.$(".oe_account_recon_reconcile_split").click(function() {
                    self.reconcile_split();
                });
                this.$(".oe_account_recon_open_partner").click(function() {
                    self.open_partner();
                });
            }
            
            return tmp;
        },
        reconcile_fund: function() {
            this.reconcile_custom_wizard("action_reconcile_fund_wizard")
        },
        reconcile_split: function() {
            this.reconcile_custom_wizard("action_reconcile_split_payment_wizard")
        },
        reconcile_custom_wizard: function(action_wizard){
            var self = this;
            var ids = this.get_selected_ids();
            if (ids.length < 2) {
                instance.web.dialog($("<div />").text(_t("You must choose at least two records.")), {
                    title: _t("Warning"),
                    modal: true
                });
                return false;
            }

            new instance.web.Model("ir.model.data").call("get_object_reference", ["account_advanced_reconcile_compassion", action_wizard]).then(function(result) {
                var additional_context = _.extend({
                    active_id: ids[0],
                    active_ids: ids,
                    active_model: self.model
                });
                return self.rpc("/web/action/load", {
                    action_id: result[1],
                    context: additional_context
                }).done(function (result) {
                    result.context = instance.web.pyeval.eval('contexts', [result.context, additional_context]);
                    result.flags = result.flags || {};
                    result.flags.new_window = true;
                    return self.do_action(result, {
                        on_close: function () {
                            // Refresh the Manual Reconcile View after wizard is closed
                            self.do_search(self.last_domain, self.last_context, self.last_group_by);
                        }
                    });
                });
            });
        },
        open_partner: function() {
            this.do_action({
                views: [[false, 'form']],
                view_type: 'form',
                view_mode: 'form',
                res_model: 'res.partner',
                type: 'ir.actions.act_window',
                target: 'current',
                res_id: this.partners[this.current_partner][0],
            });
        }
    });
    
};
