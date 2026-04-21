/** @odoo-module */

import {
  Component,
  xml,
  useState,
  useRef,
  onMounted,
  onWillUnmount,
  onWillUpdateProps,
  onPatched,
} from "@odoo/owl";
import { TpLoader } from "./tp_loader";
import { TpSignalProblem } from "./tp_signal_problem";

/**
 * Header that shows child/sponsor data and letter metadata.
 * Props:
 *   letter  {Object}  - letter data object
 *   loading {Boolean} - show spinner when saving
 *   navigateBack {Function} - navigate back to letters list
 */
class TpLetterInfoHeader extends Component {
  static template = xml`
        <div t-if="props.letter" id="tp-letter-viewer-header">
            <div class="d-flex bg-white border-bottom p-3 flex-wrap gap-4">
                <!-- Child info -->
                <div>
                    <h6 class="fw-semibold mb-2">Child Data</h6>
                    <div class="small text-secondary mb-1">
                        <span class="fw-medium me-2">Preferred Name</span>
                        <span t-esc="props.letter.child.preferredName" />
                    </div>
                    <div class="small text-secondary mb-1">
                        <span class="fw-medium me-2">Sex</span>
                        <span t-esc="props.letter.child.sex === 'M' ? 'Man' : 'Woman'" />
                    </div>
                    <div class="small text-secondary">
                        <span class="fw-medium me-2">Age</span>
                        <span t-esc="(props.letter.child.age || '') + ' Years Old'" />
                    </div>
                </div>
                <!-- Sponsor info -->
                <div>
                    <h6 class="fw-semibold mb-2">Sponsor Data</h6>
                    <div class="small text-secondary mb-1">
                        <span class="fw-medium me-2">Preferred Name</span>
                        <span t-esc="props.letter.sponsor.preferredName" />
                    </div>
                    <div class="small text-secondary mb-1">
                        <span class="fw-medium me-2">Title</span>
                        <span t-esc="props.letter.sponsor.sex === 'M' ? 'Man' : (props.letter.sponsor.sex === 'F' ? 'Woman' : (props.letter.sponsor.sex || ''))" />
                    </div>
                    <div class="small text-secondary">
                        <span class="fw-medium me-2">Age</span>
                        <span t-esc="(props.letter.sponsor.age || '') + ' Years Old'" />
                    </div>
                </div>
                <!-- Letter info -->
                <div class="flex-grow-1">
                    <h6 class="fw-semibold mb-2">Letter Information</h6>
                    <div class="small text-secondary mb-1">
                        <span class="fw-medium me-2">Title</span>
                        <span t-esc="props.letter.title" />
                    </div>
                    <div class="small text-secondary mb-1">
                        <span class="fw-medium me-2">Identifier</span>
                        <span t-esc="props.letter.id" />
                    </div>
                    <div class="small text-secondary">
                        <span class="fw-medium me-2">Language</span>
                        <span t-esc="props.letter.source" />
                        <span class="fw-bold mx-1">→</span>
                        <span t-esc="props.letter.target" />
                    </div>
                </div>
            </div>
            <!-- Status bar + actions -->
            <div class="d-flex align-items-center justify-content-between bg-light border-bottom px-3 py-2">
                <div class="d-flex align-items-center gap-2">
                    <span class="badge"
                          t-att-class="props.letter.translationIssue ? 'bg-danger' : 'bg-secondary'"
                          t-esc="props.letter.status" />
                    <span class="small text-muted">
                        <t t-if="props.letter.lastUpdate">
                            Last updated <t t-esc="props.letter.lastUpdate.toLocaleString()" />
                        </t>
                        <t t-else="">Never modified</t>
                    </span>
                    <TpLoader t-if="props.loading" />
                </div>
                <!-- Action buttons slot -->
                <div class="d-flex gap-2">
                    <t t-slot="default" />
                </div>
            </div>
            <!-- Child protection reminder -->
            <div class="bg-light border-bottom px-3 py-2">
                <p class="small text-secondary mb-0">
                    Please always signal the problem if the name of the child mentioned in the letter
                    isn't the preferred name. Thank you.
                </p>
            </div>
        </div>
    `;

  static components = { TpLoader };

  static props = {
    letter: { type: Object, optional: true },
    loading: { type: Boolean, optional: true },
    slots: { optional: true },
  };
}

/**
 * Full split-pane letter viewer.
 * Left pane: PDF (letter image) or source text.
 * Right pane: translation editor (slot).
 *
 * Props:
 *   letter      {Object}  - letter data object
 *   letterId    {number}  - always present, even if letter not found
 *   loading     {Boolean}
 *   smallLoading {Boolean} - spinner in header (save in progress)
 *   navigateBack {Function}
 *   slots:
 *     action-buttons - buttons in the header action area
 *     content        - right-pane content (ContentEditor, etc.)
 *     unsafe         - rendered outside the split layout (modals, etc.)
 *     right-pane     - additional overlay for the right pane
 */
export class TpLetterViewer extends Component {
  static template = xml`
        <div class="tp-letter-viewer position-relative" style="height: calc(100vh - 50px);">
            <t t-slot="unsafe" />
            <TpSignalProblem active="state.signalProblemModal"
                             letterId="props.letterId"
                             onClose="() => state.signalProblemModal = false" />

            <!-- Letter found -->
            <div t-if="props.letter" class="d-flex h-100">
                <!-- Left pane: PDF / source text -->
                <div class="position-relative bg-secondary-subtle border-end" style="width: 40%; min-width: 220px; flex-shrink: 0;">
                    <div class="h-100 overflow-hidden d-flex flex-column">
                        <!-- View toggle -->
                        <div class="d-flex gap-1 p-2 bg-white border-bottom">
                            <button type="button" class="btn btn-sm"
                                    t-att-class="state.mode === 'letter' ? 'btn-primary' : 'btn-outline-secondary'"
                                    t-on-click="() => state.mode = 'letter'">Letter</button>
                            <button type="button" class="btn btn-sm"
                                    t-att-class="state.mode === 'source' ? 'btn-primary' : 'btn-outline-secondary'"
                                    t-on-click="() => state.mode = 'source'">Source</button>
                        </div>
                        <!-- PDF iframe -->
                        <div t-if="state.mode === 'letter'" class="flex-grow-1">
                            <iframe t-att-src="props.letter.pdfUrl" class="w-100 h-100" style="border: none;" />
                        </div>
                        <!-- Source text -->
                        <div t-elif="state.mode === 'source'" class="flex-grow-1 overflow-auto p-3 bg-dark text-light">
                            <h5 class="fw-semibold">Source Text to translate</h5>
                            <p class="small text-secondary mb-3">
                                If the letter is unavailable, please signal a problem.
                            </p>
                            <div t-foreach="props.letter.translatedElements" t-as="elem" t-key="elem.id">
                                <div t-if="elem.type === 'paragraph'"
                                     class="bg-secondary p-3 mb-2 rounded small text-white">
                                    <p class="mb-0" t-esc="elem.source" />
                                </div>
                                <div t-if="elem.type === 'pageBreak'"
                                     class="text-center text-secondary-emphasis small py-2 mb-2 border rounded">
                                    — Page Break —
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right pane: translation editor -->
                <div class="flex-grow-1 d-flex flex-column position-relative overflow-hidden">
                    <t t-slot="right-pane" />
                    <!-- Header with letter info + action buttons -->
                    <TpLetterInfoHeader letter="props.letter" loading="props.smallLoading">
                        <t t-slot="action-buttons" />
                    </TpLetterInfoHeader>
                    <!-- Content area -->
                    <div class="flex-grow-1 overflow-auto bg-light p-3" id="tp-letter-viewer-content">
                        <t t-slot="content" letter="props.letter" />
                    </div>
                </div>
            </div>

            <!-- Letter not found -->
            <div t-elif="!props.loading"
                 class="d-flex flex-column align-items-center justify-content-center h-100">
                <i class="fa fa-exclamation-triangle fa-4x text-secondary mb-3" />
                <p class="text-secondary fw-semibold mb-3">This letter could not be found</p>
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-sm btn-outline-danger"
                            t-on-click="() => state.signalProblemModal = true">
                        Signal a Problem
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary"
                            t-on-click="props.navigateBack">
                        Back to Translations
                    </button>
                </div>
            </div>

            <!-- Loading overlay -->
            <div t-if="props.loading"
                 class="position-absolute top-0 start-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center bg-light"
                 style="z-index: 30;">
                <div class="spinner-border text-primary mb-2" />
                <p class="text-muted">Loading letter...</p>
            </div>
        </div>
    `;

  static components = { TpLetterInfoHeader, TpSignalProblem, TpLoader };

  static props = {
    letter: { type: Object, optional: true },
    letterId: {},
    loading: { type: Boolean, optional: true },
    smallLoading: { type: Boolean, optional: true },
    navigateBack: { type: Function, optional: true },
    slots: { optional: true },
  };

  state = useState({
    mode: "letter",
    signalProblemModal: false,
  });
}

export default TpLetterViewer;
