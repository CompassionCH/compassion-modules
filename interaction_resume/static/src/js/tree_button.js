odoo.define('interaction_resume.tree_button', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');

    var TreeButton = ListController.extend({
        buttons_template: 'button_near_create.buttons',

        events: _.extend({}, ListController.prototype.events, {
            'click .btn-refresh': '_onRefresh',
        }),

        _onRefresh: function () {
            var self = this;
            console.log(this);
            console.log('Refresh button clicked');
        }
    });

    var ExtendedListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: TreeButton,
        }),
    });

    viewRegistry.add('button_in_tree', ExtendedListView);
});