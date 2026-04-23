import { Component, xml } from "@odoo/owl";

/**
 * Generic loading spinner.
 */
export class TpLoader extends Component {
  static template = xml`
        <div class="d-flex justify-content-center">
            <span class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </span>
        </div>
    `;
  static props = { "*": {} };
}

/**
 * Full-screen blur overlay with a spinner (shown while loading).
 */
export class TpBlurLoader extends Component {
  static template = xml`
        <div t-if="props.active"
             class="position-absolute top-0 start-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center"
             style="background: rgba(255,255,255,0.7); backdrop-filter: blur(4px); z-index: 40;">
            <div class="p-4 bg-white rounded shadow">
                <TpLoader />
            </div>
            <p t-if="props.text" class="mt-3 text-muted fs-5" t-esc="props.text" />
        </div>
    `;
  static components = { TpLoader };
  static props = {
    active: { type: Boolean, optional: true },
    text: { type: String, optional: true },
  };
}
