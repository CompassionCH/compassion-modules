import { Component, useState } from "@odoo/owl";
import { SettingsDAO } from "../models/settings_dao.esm";
import { TpModal } from "./tp_modal.esm";
import { call } from "../rpc.esm";
import { showNotification } from "../notification.esm";

/**
 * Modal for reporting a problem with a letter.
 * Props:
 *   letterId  {number}
 *   active    {Boolean}
 *   onClose   {Function}
 */
export class TpSignalProblem extends Component {
  static template = "sbc_translation.TpSignalProblem";

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
    this.state.loading = true;
    SettingsDAO.letterIssues().then((res) => {
      this.state.types = res;
      this.state.type = res[0]?.id || null;
      this.state.loading = false;
    });
  }

  async submit() {
    if (!this.state.type) {
      showNotification("Please select a problem in the list", "warning");
      return;
    }
    this.state.loading = true;
    try {
      await call("correspondence", "raise_translation_issue", [
        [parseInt(this.props.letterId, 10)],
        this.state.type,
        this.state.message,
      ]);
      showNotification(
        "Issue successfully sent, it will be quickly reviewed",
        "success",
      );
      this.props.onClose();
      if (this.props.onRefresh) {
        this.props.onRefresh();
      }
    } catch {
      showNotification("Unable to submit issue", "danger");
    } finally {
      this.state.loading = false;
    }
  }
}

export default TpSignalProblem;
