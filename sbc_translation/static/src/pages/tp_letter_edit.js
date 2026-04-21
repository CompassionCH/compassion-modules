/** @odoo-module */

import { Component, xml, useState, onMounted, useEffect } from "@odoo/owl";
import { showNotification } from "../notification";
import { LetterDAO } from "../models/letter_dao";
import { TpLetterViewer } from "../components/tp_letter_viewer";
import { TpContentEditor } from "../components/tp_content_editor";
import { TpSignalProblem } from "../components/tp_signal_problem";
import { TpModal } from "../components/tp_modal";
import { TpBlurLoader } from "../components/tp_loader";

const AUTOSAVE_DELAY_MS = 30000; // 30 seconds

/**
 * Submitted confirmation modal.
 */
class TpLetterSubmittedModal extends Component {
  static template = xml`
        <TpModal active="props.active" title="'Translation Submitted'" onClose="props.onClose">
            <div class="p-4 text-center">
                <i class="fa fa-check-circle fa-4x text-success mb-3 d-block" />
                <p class="fw-medium">Your translation has been submitted successfully!</p>
                <p class="small text-muted">Thank you for your contribution. You will be redirected to the home page.</p>
            </div>
            <t t-set-slot="footer-buttons">
                <button type="button" class="btn btn-primary btn-sm" t-on-click="props.onHome">
                    <i class="fa fa-home me-1" />Back to Home
                </button>
            </t>
        </TpModal>
    `;
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
  static template = xml`
        <TpLetterViewer
            letter="state.letter"
            letterId="props.letterId"
            loading="state.loading"
            smallLoading="state.saveLoading"
            navigateBack="() => props.navigate('letters')">

            <!-- Action buttons in header -->
            <t t-set-slot="action-buttons">
                <button type="button" class="btn btn-sm btn-outline-danger"
                        t-if="state.letter and !state.letter.translationIssue"
                        t-on-click="() => state.signalProblemModal = true">
                    <i class="fa fa-exclamation-triangle me-1" />Signal Problem
                </button>
                <button type="button" class="btn btn-sm btn-outline-success"
                        t-on-click="() => this.save()">
                    <i class="fa fa-floppy-o me-1" />Save
                </button>
                <button type="button" class="btn btn-sm btn-primary"
                        t-if="state.letter and !state.letter.translationIssue"
                        t-on-click="submit">
                    <i class="fa fa-paper-plane me-1" />Submit
                </button>
            </t>

            <!-- Signal problem + submitted modals (rendered outside the split layout) -->
            <t t-set-slot="unsafe">
                <TpSignalProblem active="state.signalProblemModal"
                                 letterId="props.letterId"
                                 onClose="() => state.signalProblemModal = false"
                                 onRefresh="() => this._refreshLetter()" />
                <TpLetterSubmittedModal active="state.letterSubmitted"
                                        onClose="() => state.letterSubmitted = false"
                                        onHome="() => props.navigate('home')" />
            </t>

            <!-- Loading overlay in the right pane when saving -->
            <t t-set-slot="right-pane">
                <TpBlurLoader active="state.internalLoading" />
            </t>

            <!-- Content editor in the right pane -->
            <t t-set-slot="content" t-slot-scope="scope">
                <TpContentEditor t-if="scope.letter" letter="scope.letter" />
            </t>
        </TpLetterViewer>
    `;

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
      if (!letter) {
        showNotification(
          "Unable to find letter with identifier " + this.props.letterId,
          "danger",
        );
      } else {
        this.state.letter = letter;
      }
    } catch (e) {
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
    } catch (e) {
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
    } catch (e) {
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
