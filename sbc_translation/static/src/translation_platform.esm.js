import { Component, mount, onMounted, useState, whenReady } from "@odoo/owl";
import { TpChildModal } from "./components/tp_child_modal.esm";
import { TpHome } from "./pages/tp_home.esm";
import { TpLetterEdit } from "./pages/tp_letter_edit.esm";
import { TpLetters } from "./pages/tp_letters.esm";
import { TpModal } from "./components/tp_modal.esm";
import { TpTranslators } from "./pages/tp_translators.esm";
import { TranslatorDAO } from "./models/translator_dao.esm";
import { showNotification } from "./notification.esm";

/**
 * Help modal.
 */
class TpHelpModal extends Component {
  static template = 'sbc_translation.TpHelpModal';
  static components = { TpModal };
  static props = { active: { type: Boolean }, onClose: { type: Function } };
}

/**
 * Root client action component: Translation Platform.
 *
 * Manages top-level navigation (state-based: home / letters / letter-edit / translators)
 * and loads the current translator's info.
 */
export class TranslationPlatform extends Component {
  static props = {};

  static template = 'sbc_translation.TranslationPlatform';

  static components = {
    TpHome,
    TpLetters,
    TpLetterEdit,
    TpTranslators,
    TpChildModal,
    TpHelpModal,
  };

  state = useState({
    page: "home",
    letterId: null,
    loading: false,
    translator: null,
    childModal: false,
    helpModal: false,
  });

  setup() {
    this.state.loading = true;
    onMounted(() => this._loadTranslator());
  }

  async _loadTranslator() {
    try {
      this.state.translator = await TranslatorDAO.current();
    } catch {
      showNotification("Unable to load your translator profile", "danger");
    } finally {
      this.state.loading = false;
    }
  }

  refreshTranslator = async () => {
    this.state.translator = await TranslatorDAO.current();
  };

  /**
   * State-based navigation.
   * @param {String} page - 'home' | 'letters' | 'letter-edit' | 'translators'
   * @param {Object} [params] - e.g. { letterId: 42 }
   */
  navigate = (page, params = {}) => {
    this.state.page = page;
    if (params.letterId !== undefined) {
      this.state.letterId = params.letterId;
    }
  };
}

// Mount the app on the portal page container
whenReady(async () => {
  const target = document.getElementById("tp-app-root");
  if (!target) return;
  await mount(TranslationPlatform, target, { env: {} });
});
