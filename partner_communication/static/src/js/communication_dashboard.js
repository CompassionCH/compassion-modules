odoo.define('partner_communication.dashboard', function (require) {
    'use strict';

    var core = require('web.core');
    var Model = require('web.Model');
    var KanbanView = require('web_kanban.KanbanView');

    var QWeb = core.qweb;

    var _model = new Model('partner.communication.config');

    var _lt = core._lt;

    // Code copied from sales_team/static/src/js/sales_team_dashboard.js
    var CommunicationDashboardView = KanbanView.extend({
        display_name: _lt('Dashboard'),
        icon: 'fa-dashboard',
        searchview_hidden: true,
        events: {
            'click .o_dashboard_action': 'on_dashboard_action_clicked'
        },

        /**
         * Renders the widget
         * @returns {*}
         */
        render: function() {
            var super_render = this._super;
            var self = this;

            return _model.call('get_communication_rubbon_datas')
                .then(function(result){
                    var sales_dashboard = QWeb.render(
                        'partner_communication.CommunicationDashboard', {
                            widget: self,
                            values: result
                        });
                    super_render.call(self);
                    $(sales_dashboard).prependTo(self.$el);
                });
        },

        /**
         * Action is called
         * @param ev
         */
        on_dashboard_action_clicked: function(ev){
            ev.preventDefault();

            var $action = $(ev.currentTarget);
            var action_name = $action.attr('name');
            $action.data('extra');
            var additional_context = {};

            this.do_action(action_name, {
                additional_context: additional_context
            });
        }
    });

    core.view_registry.add('partner_communication_dashboard',
        CommunicationDashboardView);

    return CommunicationDashboardView;

});
