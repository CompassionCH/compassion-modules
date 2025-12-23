odoo.define("interaction_resume.tree_button", function (require) {
  "use strict";

  var ListController = require("web.ListController");
  var ListView = require("web.ListView");
  var viewRegistry = require("web.view_registry");
  var rpc = require("web.rpc");

  var TreeButton = ListController.extend({
    buttons_template: "button_near_create.buttons",

    events: _.extend({}, ListController.prototype.events, {
      "click .btn-refresh": "_onRefresh",
      "click .btn-fetch-more": "_onFetchMore",
      "click .btn-log-interaction": "_onLogInteraction",
    }),

    _onRefresh: function () {
      var self = this;
      var res_ids = this.model.get(this.handle).res_ids;
      if (!res_ids.length) {
        console.log("No records to refresh");
        return;
      }

      rpc
        .query({
          model: "interaction.resume",
          method: "refresh",
          args: [res_ids[0]],
        })
        .then(function () {
          self.reload();
        })
        .catch(function () {
          console.log("Error refreshing record");
        });
    },

    _onFetchMore: function () {
      var self = this;
      var res_ids = this.model.get(this.handle).res_ids;
      if (!res_ids.length) {
        console.log("No records to fetch more");
        return;
      }

      rpc
        .query({
          model: "interaction.resume",
          method: "fetch_more",
          args: [res_ids[0]],
        })
        .then(function () {
          self.reload();
        })
        .catch(function () {
          console.log("Error fetching more records");
        });
    },

    _onLogInteraction: function () {
      var self = this;
      var context = this.model.get(this.handle).data[0].context;

      if (!context) {
        console.log("No context to log interaction");
        return;
      }

      this.do_action(
        {
          type: "ir.actions.act_window",
          res_model: "partner.log.other.interaction.wizard",
          views: [[false, "form"]],
          target: "new",
          context: context,
        },
        {
          on_close: function () {
            self.reload();
          },
        }
      )
        .then(function (result) {
          console.log("Action executed:", result);
        })
        .catch(function (error) {
          console.error("Error executing action:", error);
        });
    },
  });

  var ExtendedListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
      Controller: TreeButton,
    }),
  });
  viewRegistry.add("button_in_tree", ExtendedListView);
});
