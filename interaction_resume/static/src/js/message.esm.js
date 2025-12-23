/** @odoo-module */

import { Message } from "@mail/core/common/message";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(Message.prototype, {
  setup() {
    super.setup();
    this.orm = useService("orm");
    this.actionService = useService("action");
  },

  async messageToInteraction() {
    await this.orm.call("mail.message", "convert_as_other_interaction", [
      [this.message.id],
    ]);

    // Trigger a reload or action if needed
    this.actionService.doAction({
      type: "ir.actions.client",
      tag: "reload",
    });
  },
});
