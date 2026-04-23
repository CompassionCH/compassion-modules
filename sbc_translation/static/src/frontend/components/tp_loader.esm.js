import { Component } from "@odoo/owl";

/**
 * Generic loading spinner.
 */
export class TpLoader extends Component {
  static template = "sbc_translation.TpLoader";
  static props = { "*": {} };
}

/**
 * Full-screen blur overlay with a spinner (shown while loading).
 */
export class TpBlurLoader extends Component {
  static template = "sbc_translation.TpBlurLoader";
  static components = { TpLoader };
  static props = {
    active: { type: Boolean, optional: true },
    text: { type: String, optional: true },
  };
}
