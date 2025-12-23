odoo.define("interaction_resume/static/src/js/message.js", function (require) {
  "use strict";

  const components = {
    Message: require("mail/static/src/components/message/message.js"),
  };
  const { patch } = require("web.utils");

  patch(components.Message, "interaction_resume/static/src/js/message.js", {
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onMessageToInteraction: function (ev) {
      ev.stopPropagation();
      this.message.messageToInteraction();
    },
  });

  const {
    registerInstancePatchModel,
  } = require("mail/static/src/model/model_core.js");

  registerInstancePatchModel(
    "mail.message",
    "interaction_resume/static/src/js/message.js",
    {
      /**
       * Open message edit dialog and reload component on close
       */
      async messageToInteraction() {
        await this.async(() =>
          this.env.services.rpc({
            model: "mail.message",
            method: "convert_as_other_interaction",
            args: [[this.id]], // 'this.id' is the ID of the current message record
          }),
        );
        this.env.bus.trigger("do-action", {
          action: {
            type: "ir.actions.client",
            tag: "reload",
          },
        });
      },
    },
  );
});
