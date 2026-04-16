/** @odoo-module */

import { Component, xml, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { TpModal } from "./tp_modal";

/**
 * Tips modal showing translation best practices.
 * Props:
 *   active  {Boolean}
 *   onClose {Function}
 */
class TpTipsModal extends Component {
    static template = xml`
        <TpModal active="props.active" onClose="props.onClose" title="'Tips for a Successful Translation'">
            <div class="p-3 small" style="max-width: 500px;">
                <ul class="mb-0">
                    <li class="mb-2">Keep the same tone and emotional register as the source text.</li>
                    <li class="mb-2">Do not paraphrase – translate as closely as possible.</li>
                    <li class="mb-2">Preserve paragraph breaks from the source.</li>
                    <li class="mb-2">If the source text is unclear, add a comment explaining the issue.</li>
                    <li class="mb-2">Names of people and places should be kept as they appear.</li>
                    <li class="mb-2">If you're unsure about a phrase, use the comment field to flag it.</li>
                </ul>
            </div>
        </TpModal>
    `;
    static components = { TpModal };
    static props = {
        active: { type: Boolean },
        onClose: { type: Function },
    };
}

/**
 * Content editor for translating individual paragraphs.
 * Props:
 *   letter {Object} - letter data with translatedElements array
 */
export class TpContentEditor extends Component {
    static template = xml`
        <div id="tp-content-editor">
            <div t-foreach="props.letter.translatedElements"
                 t-as="element"
                 t-key="element.id"
                 class="mb-3 border rounded transition-all">
                <!-- Page break marker -->
                <div t-if="element.type === 'pageBreak'"
                     class="text-center text-muted small py-2 bg-light border-top border-bottom">
                    — Page Break —
                </div>
                <!-- Paragraph editor -->
                <div t-if="element.type === 'paragraph'" class="row g-0 bg-white shadow-sm">
                    <div class="col-8 p-3 border-end">
                        <h6 class="fw-medium text-secondary mb-2">Translated Content</h6>
                        <textarea class="form-control form-control-sm" rows="5" t-model="element.content" />
                    </div>
                    <div class="col-4 p-3 bg-light">
                        <h6 class="fw-medium text-secondary mb-2">Comment on the translation</h6>
                        <textarea class="form-control form-control-sm" rows="5" t-model="element.comments" />
                    </div>
                </div>
                <!-- Action buttons (view source / tips) -->
                <div t-if="element.type === 'paragraph'"
                     class="d-flex gap-1 px-3 py-1 border-top bg-light">
                    <button type="button" class="btn btn-sm btn-outline-secondary"
                            title="View source text"
                            t-on-click="() => openSource(element.id)">
                        <i class="fa fa-eye" /> Source
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary"
                            title="Translation tips"
                            t-on-click="openTips">
                        <i class="fa fa-info-circle" /> Tips
                    </button>
                </div>
            </div>

            <!-- Modals -->
            <TpTipsModal active="state.showTips" onClose="() => state.showTips = false" />
            <TpModal active="state.sourceElem !== undefined"
                     title="'Source Text'"
                     onClose="() => state.sourceElem = undefined">
                <div class="p-3" style="min-width: 350px;">
                    <p t-if="state.sourceElem and state.sourceElem.trim() !== ''"
                       class="small" t-esc="state.sourceElem" />
                    <p t-else="" class="small text-muted fst-italic">No source text available</p>
                </div>
            </TpModal>
        </div>
    `;

    static components = { TpModal, TpTipsModal };

    static props = {
        letter: { type: Object },
    };

    state = useState({
        sourceElem: undefined,
        showTips: false,
    });

    openSource(elemId) {
        const elem = this.props.letter.translatedElements.find((e) => e.id === elemId);
        if (elem && elem.type === "paragraph") {
            this.state.sourceElem = elem.source || "";
        }
    }

    openTips() {
        this.state.showTips = true;
    }
}

export default TpContentEditor;
