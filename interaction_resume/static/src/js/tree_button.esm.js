/** @odoo-module */

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class InteractionResumeListController extends ListController {
  setup() {
    super.setup();
    this.orm = useService("orm");
    this.actionService = useService("action");
  }

  async onRefresh() {
    const resIds = this.model.root.records.map((rec) => rec.resId);
    if (!resIds.length) return;

    await this.orm.call("interaction.resume", "action_refresh", [resIds[0]]);
    await this.model.root.load();
  }

  async onFetchMore() {
    const resIds = this.model.root.records.map((rec) => rec.resId);
    if (!resIds.length) return;

    await this.orm.call("interaction.resume", "fetch_more", [resIds[0]]);
    await this.model.root.load();
  }

  async onLogInteraction() {
    const context = this.props.context || {};

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        res_model: "partner.log.other.interaction.wizard",
        views: [[false, "form"]],
        target: "new",
        context: context,
      },
      {
        onClose: () => {
          this.model.root.load();
        },
      },
    );
  }
}

export const interactionResumeListView = {
  ...listView,
  Controller: InteractionResumeListController,
  buttonTemplate: "interaction_resume.ListView.Buttons",
};

registry.category("views").add("button_in_tree", interactionResumeListView);
