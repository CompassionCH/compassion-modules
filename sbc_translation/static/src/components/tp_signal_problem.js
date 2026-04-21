/** @odoo-module */

import { Component, xml, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { TpModal } from "./tp_modal";
import { SettingsDAO } from "../models/settings_dao";

/**
 * Modal for reporting a problem with a letter.
 * Props:
 *   letterId  {number}
 *   active    {Boolean}
 *   onClose   {Function}
 */
export class TpSignalProblem extends Component {
  static template = xml`
        <TpModal active="props.active" onClose="props.onClose"
                 title="'Signal a Problem'"
                 subtitle="'Notify Compassion of a problem with this letter'"
                 loading="state.loading">
            <div class="p-3">
                <select class="form-select form-select-sm mb-2" t-model="state.type">
                    <option t-foreach="state.types" t-as="type" t-key="type.id"
                            t-att-value="type.id" t-esc="type.text" />
                </select>
                <textarea class="form-control form-control-sm" rows="4"
                          t-model="state.message"
                          placeholder="Your Message" />
            </div>
            <t t-set-slot="footer-buttons">
                <button type="button" class="btn btn-primary btn-sm" t-on-click="submit">
                    Send Message
                </button>
            </t>
        </TpModal>
    `;

  static components = { TpModal };

  static props = {
    letterId: {},
    active: { type: Boolean },
    onClose: { type: Function },
    onRefresh: { type: Function, optional: true },
  };

  state = useState({
    loading: false,
    message: "",
    type: null,
    types: [],
  });

  setup() {
    this.orm = useService("orm");
    this.notification = useService("notification");
    this.state.loading = true;
    SettingsDAO.letterIssues(this.orm).then((res) => {
      this.state.types = res;
      this.state.type = res[0]?.id || null;
      this.state.loading = false;
    });
  }

  async submit() {
    if (!this.state.type) {
      this.notification.add(_t("Please select a problem in the list"), {
        type: "warning",
      });
      return;
    }
    this.state.loading = true;
    try {
      await this.orm.call("correspondence", "raise_translation_issue", [
        [parseInt(this.props.letterId, 10)],
        this.state.type,
        this.state.message,
      ]);
      this.notification.add(
        _t("Issue successfully sent, it will be quickly reviewed"),
        {
          type: "success",
        },
      );
      this.props.onClose();
      if (this.props.onRefresh) {
        this.props.onRefresh();
      }
    } catch (e) {
      this.notification.add(_t("Unable to submit issue"), { type: "danger" });
    } finally {
      this.state.loading = false;
    }
  }
}

export default TpSignalProblem;
