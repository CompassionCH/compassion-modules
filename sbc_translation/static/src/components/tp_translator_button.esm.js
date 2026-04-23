import { Component, useState } from "@odoo/owl";
import { TpModal } from "./tp_modal.esm";
import { TranslatorDAO } from "../models/translator_dao.esm";

/**
 * Inline button showing a translator's name; opens a detail modal on click.
 * Props:
 *   translatorId {number}
 */
export class TpTranslatorButton extends Component {
  static template = 'sbc_translation.TpTranslatorButton';

  static components = { TpModal };

  static props = {
    translatorId: { type: Number },
  };

  state = useState({
    translator: null,
    loading: false,
    showModal: false,
  });

  async loadAndOpen() {
    if (!this.state.translator) {
      this.state.loading = true;
      try {
        this.state.translator = await TranslatorDAO.find(
          this.props.translatorId,
        );
      } finally {
        this.state.loading = false;
      }
    }
    this.state.showModal = true;
  }
}

export default TpTranslatorButton;
