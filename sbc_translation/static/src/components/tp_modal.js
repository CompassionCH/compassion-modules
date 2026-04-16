/** @odoo-module */

import { Component, xml, useState, onMounted, onWillUpdateProps, onPatched } from "@odoo/owl";
import { TpLoader } from "./tp_loader";

// Duration of the Bootstrap modal fade-in/out CSS transition (ms).
// The unmount delay must match the animation so the backdrop disappears correctly.
const MODAL_TRANSITION_DURATION_MS = 200;

/**
 * A Bootstrap modal component.
 * Props:
 *   active  {Boolean}  - whether the modal is open
 *   title   {String}   - modal title
 *   subtitle {String}  - optional subtitle
 *   onClose {Function} - called when the close button is clicked
 *   loading {Boolean}  - shows a loading overlay inside the modal
 *   showCloseButton {Boolean} - whether to show footer close button (default true)
 *   closeButtonText {String}  - label for the footer close button
 */
export class TpModal extends Component {
    static template = xml`
        <div t-if="state.mounted"
             class="modal tp-modal"
             t-att-class="{ 'show d-block': state.display, 'd-none': !state.display }"
             tabindex="-1"
             t-on-click.self="props.onClose or (() => null)">
            <div class="modal-dialog modal-dialog-centered modal-lg" t-att-class="props.dialogClass || ''">
                <div class="modal-content position-relative">
                    <!-- Loading overlay -->
                    <div t-if="props.loading"
                         class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
                         style="background: rgba(255,255,255,0.8); z-index: 10; backdrop-filter: blur(2px);">
                        <TpLoader />
                    </div>
                    <!-- Header -->
                    <div class="modal-header" t-if="props.title or props.onClose">
                        <div>
                            <h5 class="modal-title" t-if="props.title" t-esc="props.title" />
                            <p class="text-muted small mb-0" t-if="props.subtitle" t-esc="props.subtitle" />
                        </div>
                        <button t-if="props.onClose" type="button" class="btn-close" t-on-click="props.onClose" />
                    </div>
                    <!-- Body -->
                    <div class="modal-body p-0">
                        <t t-slot="default" />
                    </div>
                    <!-- Footer -->
                    <t t-slot="footer">
                        <div class="modal-footer" t-if="!props.empty">
                            <button t-if="props.onClose and props.showCloseButton !== false"
                                    type="button"
                                    class="btn btn-outline-secondary btn-sm"
                                    t-on-click="props.onClose"
                                    t-esc="props.closeButtonText or 'Close'" />
                            <t t-slot="footer-buttons" />
                        </div>
                    </t>
                </div>
            </div>
        </div>
        <!-- Backdrop -->
        <div t-if="state.display" class="modal-backdrop show" />
    `;

    static components = { TpLoader };

    static props = {
        active: { type: Boolean, optional: true },
        title: { type: String, optional: true },
        subtitle: { type: String, optional: true },
        onClose: { type: Function, optional: true },
        loading: { type: Boolean, optional: true },
        showCloseButton: { type: Boolean, optional: true },
        closeButtonText: { type: String, optional: true },
        empty: { type: Boolean, optional: true },
        dialogClass: { type: String, optional: true },
        "*": {},
    };

    state = useState({
        mounted: false,
        display: false,
    });

    setup() {
        onMounted(() => this._handleMount(this.props));
        onWillUpdateProps((next) => this._handleMount(next));
        onPatched(() => this._postRendered());
    }

    _handleMount(props) {
        if (props.active && !this.state.mounted) {
            this.state.mounted = true;
        } else if (this.state.mounted && !props.active) {
            this.state.display = false;
            setTimeout(() => {
                this.state.mounted = false;
            }, MODAL_TRANSITION_DURATION_MS);
        }
    }

    _postRendered() {
        if (this.props.active && this.state.mounted && !this.state.display) {
            this.state.display = true;
        }
    }
}

export default TpModal;
