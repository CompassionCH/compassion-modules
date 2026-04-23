import { Component, onMounted, useEffect, useState } from "@odoo/owl";
import { LetterDAO } from "../models/letter_dao.esm";
import { TpBlurLoader } from "../components/tp_loader.esm";
import { TpContentEditor } from "../components/tp_content_editor.esm";
import { TpLetterViewer } from "../components/tp_letter_viewer.esm";
import { TpModal } from "../components/tp_modal.esm";
import { TpSignalProblem } from "../components/tp_signal_problem.esm";
import { showNotification } from "../notification.esm";

// 30 seconds
const AUTOSAVE_DELAY_MS = 30000;

/**
 * Submitted confirmation modal.
 */
class TpLetterSubmittedModal extends Component {
  static template = "sbc_translation.TpLetterSubmittedModal";
  static components = { TpModal };
  static props = {
    active: { type: Boolean },
    onClose: { type: Function },
    onHome: { type: Function },
  };
}

/**
 * Letter editing page – the core translation interface.
 * Props:
 *   letterId    {number|string}
 *   navigate    {Function}
 *   translator  {Object}
 */
export class TpLetterEdit extends Component {
  static template = "sbc_translation.TpLetterEdit";

  static components = {
    TpLetterViewer,
    TpSignalProblem,
    TpLetterSubmittedModal,
    TpContentEditor,
    TpBlurLoader,
  };

  static props = {
    letterId: {},
    navigate: { type: Function },
    translator: { type: Object, optional: true },
  };

  state = useState({
    loading: false,
    internalLoading: false,
    saveLoading: false,
    letter: undefined,
    signalProblemModal: false,
    letterSubmitted: false,
    saveTimeout: undefined,
  });

  setup() {
    this.state.loading = true;
    onMounted(() => this._refreshLetter());

    // Keyboard shortcuts: Ctrl+S saves
    useEffect(() => {
      const listener = (event) => {
        if (event.ctrlKey && event.key === "s") {
          event.preventDefault();
          if (this.state.saveTimeout) {
            clearTimeout(this.state.saveTimeout);
            this.state.saveTimeout = undefined;
          }
          this.save(true);
        }
      };
      document.addEventListener("keydown", listener);

      // Auto-save triggered by typing in textarea/input inside the editor
      const inputListener = (event) => {
        const target = event.target;
        if (
          target &&
          (target.tagName === "TEXTAREA" || target.tagName === "INPUT")
        ) {
          this._queueSave();
        }
      };
      document.addEventListener("input", inputListener);

      return () => {
        document.removeEventListener("keydown", listener);
        document.removeEventListener("input", inputListener);
      };
    });
  }

  async _refreshLetter() {
    try {
      const letter = await LetterDAO.find(this.props.letterId);
      if (letter) {
        this.state.letter = letter;
      } else {
        showNotification(
          "Unable to find letter with identifier " + this.props.letterId,
          "danger",
        );
      }
    } catch {
      showNotification("Error loading letter", "danger");
    } finally {
      this.state.loading = false;
    }
  }

  _queueSave() {
    if (this.state.saveTimeout) clearTimeout(this.state.saveTimeout);
    this.state.saveTimeout = setTimeout(
      () => this.save(true),
      AUTOSAVE_DELAY_MS,
    );
  }

  async save(background = false) {
    if (!this.state.letter?.translatedElements || this.state.saveLoading)
      return;

    if (!background) this.state.internalLoading = true;
    this.state.saveLoading = true;

    // If not yet attributed, assign current translator
    const newAttribution = !this.state.letter.translatorId;
    if (newAttribution && this.props.translator) {
      this.state.letter.translatorId = this.props.translator.translatorId;
    }

    try {
      await LetterDAO.update(this.state.letter);
      if (!background) {
        showNotification("Letter saved", "success");
      }
      // Refresh lastUpdate from server
      const updated = await LetterDAO.find(this.props.letterId);
      if (updated) this.state.letter.lastUpdate = updated.lastUpdate;
    } catch {
      showNotification("Unable to save letter", "danger");
    } finally {
      if (!background) this.state.internalLoading = false;
      this.state.saveLoading = false;
    }
  }

  async submit() {
    if (!this.state.letter?.translatedElements) return;
    if (this.state.saveTimeout) clearTimeout(this.state.saveTimeout);
    this.state.internalLoading = true;
    try {
      await LetterDAO.submit(this.state.letter);
      this.state.letterSubmitted = true;
    } catch {
      showNotification(
        "Unable to save and submit letter, please save it first and retry.",
        "danger",
      );
    } finally {
      this.state.internalLoading = false;
    }
  }
}

export default TpLetterEdit;
