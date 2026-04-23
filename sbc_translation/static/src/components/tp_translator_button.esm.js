import { Component, useState, xml } from "@odoo/owl";
import { TpModal } from "./tp_modal.esm";
import { TranslatorDAO } from "../models/translator_dao.esm";

/**
 * Inline button showing a translator's name; opens a detail modal on click.
 * Props:
 *   translatorId {number}
 */
export class TpTranslatorButton extends Component {
  static template = xml`
        <span>
            <button type="button"
                    class="btn btn-sm btn-link p-0"
                    t-on-click="loadAndOpen">
                <t t-if="state.translator">
                    <t t-esc="state.translator.name or ('Translator #' + props.translatorId)" />
                </t>
                <t t-else="">
                    <span class="spinner-border spinner-border-sm" t-if="state.loading" />
                    <span t-else="" t-esc="'#' + props.translatorId" />
                </t>
            </button>
            <TpModal active="state.showModal"
                     onClose="() => state.showModal = false"
                     title="'Translator Details'">
                <div class="p-3 small" t-if="state.translator">
                    <div class="mb-2">
                        <span class="fw-medium me-2">Name</span>
                        <span t-esc="state.translator.name" />
                    </div>
                    <div class="mb-2">
                        <span class="fw-medium me-2">Email</span>
                        <span t-esc="state.translator.email or '—'" />
                    </div>
                    <div class="mb-2">
                        <span class="fw-medium me-2">Letters translated</span>
                        <span t-esc="state.translator.total" />
                    </div>
                    <div>
                        <span class="fw-medium me-2">Role</span>
                        <span t-esc="state.translator.role" />
                    </div>
                </div>
            </TpModal>
        </span>
    `;

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
