/* eslint-disable */
odoo.define("account_reconcile_compassion.reconciliation", function (require) {
  "use strict";

  var core = require("web.core");
  var basic_fields = require("web.basic_fields");
  var relational_fields = require("web.relational_fields");
  var reconciliation_renderer = require("account.ReconciliationRenderer");
  var reconciliation_model = require("account.ReconciliationModel");
  var statement_action = require("account.ReconciliationClientAction");
  var rpc = require("web.rpc");
  var qweb = core.qweb;
  var _t = core._t;

  statement_action.StatementAction.include({
    // Event which allows to modify fields programmatically The
    // update_proposition event handled by _onAction uses the target of the
    // event to get the handle, which won't be available if the event is
    // triggered programmatically. Therefore the handle is passed in data
    custom_events: _.extend(
      {},
      statement_action.StatementAction.prototype.custom_events,
      {
        update_proposition_programmatically:
          "_onUpdatePropositionProgrammatically",
      }
    ),

    _onUpdatePropositionProgrammatically: function (event) {
      var self = this;
      var handle = event.data.data.handle;
      var line = this.model.getLine(handle);
      this.model.updateProposition(handle, event.data.data).then(function () {
        self._getWidget(handle).update(line);
      });
    },

    // BUG FIX in module reconciliation_widget when some lines are not visible.
    // Code copied from there.
    _openFirstLine: function (previous_handle) {
      var self = this;
      previous_handle = previous_handle || "rline0";
      var handle = _.compact(
        _.map(this.model.lines, function (line, handle) {
          // This is the FIX: !line.visible ||
          return !line.visible ||
            line.reconciled ||
            parseInt(handle.substr(5)) < parseInt(previous_handle.substr(5))
            ? null
            : handle;
        })
      )[0];
      if (handle) {
        var line = this.model.getLine(handle);
        this.model
          .changeMode(handle, "default")
          .then(function () {
            self._getWidget(handle).update(line);
          })
          .guardedCatch(function () {
            self._getWidget(handle).update(line);
          })
          .then(function () {
            self._getWidget(handle).$el.focus();
          });
      }
      return handle;
    },
  });

  reconciliation_renderer.StatementRenderer.include({
    events: _.extend(
      {},
      reconciliation_renderer.StatementRenderer.prototype.events,
      {
        "click div:first h1.statement_name": "statementNameClickHandler",
      }
    ),

    // Change behaviour when clicking on name of bank statement
    statementNameClickHandler: function () {
      this.do_action({
        views: [[false, "form"]],
        view_type: "form",
        view_mode: "form",
        res_model: "account.bank.statement",
        type: "ir.actions.act_window",
        target: "current",
        res_id: this.model.bank_statement_id.id,
      });
    },
  });

  reconciliation_renderer.LineRenderer.include({
    // Overload of the default function in 'account.ReconciliationRenderer'
    // which adds the product_id field. It doesn't seem possible to call the
    // superclass function and then add the field as basic_model.js doesn't
    // have a method to add fields to an existing record, only makeRecord.
    _renderCreate: function (state) {
      var self = this;
      return this.model
        .makeRecord(
          "account.bank.statement.line",
          [
            {
              relation: "account.account",
              type: "many2one",
              name: "account_id",
              domain: [
                ["company_id", "=", state.st_line.company_id],
                ["deprecated", "=", false],
              ],
            },
            {
              relation: "account.journal",
              type: "many2one",
              name: "journal_id",
              domain: [["company_id", "=", state.st_line.company_id]],
            },
            {
              relation: "account.tax",
              type: "many2many",
              name: "tax_ids",
              domain: [["company_id", "=", state.st_line.company_id]],
            },
            {
              relation: "account.analytic.account",
              type: "many2one",
              name: "analytic_account_id",
            },
            {
              relation: "account.analytic.tag",
              type: "many2many",
              name: "analytic_tag_ids",
            },
            {
              type: "boolean",
              name: "force_tax_included",
            },
            {
              type: "char",
              name: "label",
            },
            {
              type: "char",
              name: "ref",
            },
            {
              type: "float",
              name: "amount",
            },
            {
              type: "char", // TODO is it a bug or a feature when type date exists ?
              name: "date",
            },
            {
              type: "boolean",
              name: "to_check",
            },
            // CHANGE: Product, sponsorship, user_id and comment
            // added from original function
            {
              relation: "product.product",
              type: "many2one",
              name: "product_id",
            },
            {
              relation: "recurring.contract",
              type: "many2one",
              name: "sponsorship_id",
              domain: [
                "|",
                "|",
                ["partner_id", "=", state.st_line.partner_id],
                ["partner_id.parent_id", "=", state.st_line.partner_id],
                ["correspondent_id", "=", state.st_line.partner_id],
                ["state", "!=", "draft"],
              ],
            },
            {
              type: "char",
              name: "comment",
            },
            {
              type: "boolean",
              name: "avoid_thankyou_letter",
            },
          ],
          {
            account_id: {
              string: _t("Account"),
            },
            label: {
              string: _t("Label"),
            },
            amount: {
              string: _t("Account"),
            },
            // CHANGE: Product, sponsorship, user_id and comment
            // added from original function
            product_id: {
              string: _t("Product"),
            },
            sponsorship_id: {
              string: _t("Sponsorship"),
            },
            comment: {
              string: _t("Gift instructions"),
            },
            avoid_thankyou_letter: {
              string: _t("Disable thank you letter"),
            },
          }
        )
        .then(function (recordID) {
          self.handleCreateRecord = recordID;
          var record = self.model.get(self.handleCreateRecord);

          self.fields.account_id = new relational_fields.FieldMany2One(
            self,
            "account_id",
            record,
            {
              mode: "edit",
              attrs: {
                can_create: false,
              },
            }
          );

          self.fields.journal_id = new relational_fields.FieldMany2One(
            self,
            "journal_id",
            record,
            {
              mode: "edit",
            }
          );

          self.fields.tax_ids = new relational_fields.FieldMany2ManyTags(
            self,
            "tax_ids",
            record,
            {
              mode: "edit",
              additionalContext: {
                append_type_to_tax_name: true,
              },
            }
          );

          self.fields.analytic_account_id = new relational_fields.FieldMany2One(
            self,
            "analytic_account_id",
            record,
            {
              mode: "edit",
            }
          );

          self.fields.analytic_tag_ids = new relational_fields.FieldMany2ManyTags(
            self,
            "analytic_tag_ids",
            record,
            {
              mode: "edit",
            }
          );

          self.fields.force_tax_included = new basic_fields.FieldBoolean(
            self,
            "force_tax_included",
            record,
            {
              mode: "edit",
            }
          );

          self.fields.label = new basic_fields.FieldChar(
            self,
            "label",
            record,
            {
              mode: "edit",
            }
          );

          self.fields.amount = new basic_fields.FieldFloat(
            self,
            "amount",
            record,
            {
              mode: "edit",
            }
          );

          self.fields.date = new basic_fields.FieldDate(self, "date", record, {
            mode: "edit",
          });

          self.fields.to_check = new basic_fields.FieldBoolean(
            self,
            "to_check",
            record,
            {
              mode: "edit",
            }
          );

          // CHANGE: Product, sponsorship, user_id and comment
          // added from original function
          self.fields.product_id = new relational_fields.FieldMany2One(
            self,
            "product_id",
            record,
            {
              mode: "edit",
            }
          );

          self.fields.sponsorship_id = new relational_fields.FieldMany2One(
            self,
            "sponsorship_id",
            record,
            {
              mode: "edit",
            }
          );

          self.fields.comment = new basic_fields.FieldChar(
            self,
            "comment",
            record,
            {
              mode: "edit",
            }
          );

          self.fields.avoid_thankyou_letter = new basic_fields.FieldBoolean(
            self,
            "avoid_thankyou_letter",
            record,
            {
              mode: "edit",
            }
          );

          var $create = $(
            qweb.render("reconciliation.line.create", {
              state: state,
            })
          );

          function addRequiredStyle(widget) {
            widget.$el.addClass("o_required_modifier");
          }

          self.fields.account_id
            .appendTo($create.find(".create_account_id .o_td_field"))
            .then(addRequiredStyle.bind(self, self.fields.account_id));
          self.fields.journal_id.appendTo(
            $create.find(".create_journal_id .o_td_field")
          );
          self.fields.tax_ids.appendTo(
            $create.find(".create_tax_id .o_td_field")
          );
          self.fields.analytic_account_id.appendTo(
            $create.find(".create_analytic_account_id .o_td_field")
          );
          self.fields.analytic_tag_ids.appendTo(
            $create.find(".create_analytic_tag_ids .o_td_field")
          );
          self.fields.force_tax_included.appendTo(
            $create.find(".create_force_tax_included .o_td_field")
          );
          self.fields.label
            .appendTo($create.find(".create_label .o_td_field"))
            .then(addRequiredStyle.bind(self, self.fields.label));
          self.fields.amount
            .appendTo($create.find(".create_amount .o_td_field"))
            .then(addRequiredStyle.bind(self, self.fields.amount));
          self.fields.date.appendTo($create.find(".create_date .o_td_field"));
          self.fields.to_check.appendTo(
            $create.find(".create_to_check .o_td_field")
          );
          // CHANGE: Product, sponsorship, user_id and comment
          // added from original function
          self.fields.product_id.appendTo(
            $create.find(".create_product_id .o_td_field")
          );
          self.fields.sponsorship_id.appendTo(
            $create.find(".create_sponsorship_id .o_td_field")
          );
          self.fields.comment.appendTo(
            $create.find(".create_comment .o_td_field")
          );
          self.fields.avoid_thankyou_letter.appendTo(
            $create.find(".create_avoid_thankyou_letter .o_td_field")
          );
          self.$(".create").append($create);
        });
    },

    update: function (state) {
      this._super(state);
      var new_partner_id = state.st_line.partner_id;
      var sponsorship_field = this.fields.sponsorship_id;
      if (sponsorship_field !== undefined) {
        sponsorship_field.field["domain"] = [
          "|",
          ["correspondent_id", "=", new_partner_id],
          ["partner_id", "=", new_partner_id],
          ["state", "!=", "draft"],
        ];
      }
    },
  });

  reconciliation_model.StatementModel.include({
    quickCreateFields: [
      "product_id",
      "sponsorship_id",
      "comment",
      "account_id",
      "amount",
      "analytic_account_id",
      "label",
      "tax_id",
      "force_tax_included",
      "analytic_tag_ids",
      "avoid_thankyou_letter",
    ],

    createProposition: function (handle) {
      var self = this;
      var line = this.getLine(handle);
      var payment_ref = line.st_line.payment_ref;

      var gift_ref_key = payment_ref[21];
      var gift_default_code = {
        1: "gift_birthday",
        2: "gift_gen",
        3: "gift_family",
        4: "gift_project",
        5: "gift_graduation",
      };

      var gift_ref_default_code = false;

      if (gift_ref_key in gift_default_code) {
        gift_ref_default_code = gift_default_code[gift_ref_key];
      }

      // Try to prefill fields from the customer payment
      if (gift_ref_default_code) {
        // Search gift product
        rpc
          .query({
            model: "product.product",
            method: "search",
            args: [[["default_code", "ilike", gift_ref_default_code]]],
          })
          .then(function (product_ids) {
            if (product_ids !== "undefined" && product_ids.length > 0) {
              // This emits a custom event handled by
              // _onUpdatePropositionProgrammatically()
              // It is done this way because only StatementAction
              // has access to the mode for updating the data and
              // the renderer for refreshing the interface
              self.trigger_up("update_proposition_programmatically", {
                data: {
                  product_id: {
                    id: product_ids[0],
                  },
                  handle: handle,
                },
              });
            }
          });

        var gift_commitment_number_ref_key = payment_ref.substring(19, 21);
        var gift_commitment_number = parseInt(gift_commitment_number_ref_key).toString()

              // Search sponsorship
              rpc.query({
                  model: "recurring.contract",
                  method: "search",
                  args: [
                      [
                          ["commitment_number",
                              "=",
                              gift_commitment_number
                          ],
                          "|",
                          ["correspondent_id",
                              "=", line
                              .partner_id
                          ],
                          ["partner_id", "=",
                              line.partner_id],
              ],
            ],
          })
          .then(function (sponsorship_ids) {
            if (
              typeof sponsorship_ids !== "undefined" &&
              sponsorship_ids.length > 0
            ) {
              self.trigger_up("update_proposition_programmatically", {
                data: {
                  sponsorship_id: {
                    id: sponsorship_ids[0],
                  },
                  handle: handle,
                },
              });
            }
          });
      }

      return this._super(handle);
    },

    updateProposition: function (handle, values) {
      // Update other fields when product_id is changed
      var self = this;
      if ("product_id" in values) {
        var parent = this._super;
        return this._rpc({
          model: "account.reconcile.model",
          method: "product_changed",
          args: [values.product_id.id, self.statement.statement_id],
        }).then(function (changes) {
          if (changes) {
            if (changes.account_id) values.account_id = changes.account_id;
            if (changes.tax_id) values.tax_id = changes.tax_id;
            if (changes.analytic_account_id)
              values.analytic_account_id = changes.analytic_account_id;
            if (changes.analytic_tag_ids) {
              // Replace analytic tags as the parent method doesn't support several tags added
              var line = self.getLine(handle);
              var prop = _.last(
                _.filter(line.reconciliation_proposition, "__focus")
              );
              prop.analytic_tag_ids = changes.analytic_tag_ids;
            }
          }
          return parent.call(self, handle, values);
        });
      } else {
        return this._super(handle, values);
      }
    },

    // Copy from the original function, I did not find a better way to do this
    quickCreateProposition: function (handle, reconcileModelId) {
        var line = this.getLine(handle);
        var reconcileModel = _.find(this.reconcileModels, function (r) {
            return r.id === reconcileModelId;
        });
        var fields = [
            "product_id", // product_id added from the original fields list
            "account_id",
            "amount",
            "amount_type",
            "analytic_account_id",
            "journal_id",
            "label",
            "force_tax_included",
            "tax_ids",
            "analytic_tag_ids",
            "to_check",
            "amount_string",
            "decimal_separator",
        ];
        this._blurProposition(handle);
        let focus = null;
        const defs = [];
        for (const reconcileModelLineIndex in reconcileModel.line_ids) {
            const reconcileModelLine = reconcileModel.line_ids[reconcileModelLineIndex];
            if (reconcileModelLineIndex === "0") {
                focus = this._formatQuickCreate(
                    line,
                    _.pick(reconcileModelLine, fields),
                    reconcileModel
                );
                focus.reconcileModelId = reconcileModelId;
                line.reconciliation_proposition.push(focus);
            } else {
                defs.push(
                    this._computeLine(line).then(() => {
                        const second_focus = this._formatQuickCreate(
                            line,
                            _.pick(reconcileModelLine, fields),
                            reconcileModel
                        );
                        second_focus.reconcileModelId = reconcileModelId;
                        line.reconciliation_proposition.push(second_focus);
                        this._computeReconcileModels(handle, reconcileModelId);
                    })
                );
            }
        }
        return Promise.all(defs).then(() => {
            line.createForm = _.pick(focus, this.quickCreateFields);
            return this._computeLine(line);
        });
    },

    // Add product_id to the QuickCreate prop
    _formatQuickCreate: function (line, values) {
      values = values || {};
      var prop = this._super(line, values);
      prop.product_id = this._formatNameGet(values.product_id);
      return prop;
    },

    // Add additional fields to send information server side
    _formatToProcessReconciliation: function (line, prop) {
      var result = this._super(line, prop);
      result.product_id = prop.product_id ? prop.product_id.id : null;
      result.sponsorship_id = prop.sponsorship_id
        ? prop.sponsorship_id.id
        : null;
      result.comment = prop.comment;
      result.avoid_thankyou_letter = prop.avoid_thankyou_letter
        ? prop.avoid_thankyou_letter
        : false;
      result.analytic_account_id = prop.analytic_account_id
        ? prop.analytic_account_id.id
        : null;
      return result;
    },
  });

  return {
    StatementAction: statement_action,
    renderer: reconciliation_renderer,
    model: reconciliation_model,
  };
});
