import { Component } from "@odoo/owl";
import { TpModal } from "./tp_modal.esm";

/**
 * Child protection policy modal.
 * Props:
 *   active  {Boolean}
 *   onClose {Function}
 */
export class TpChildModal extends Component {
  static template = "sbc_translation.TpChildModal";

  static components = { TpModal };

  static props = {
    active: { type: Boolean },
    onClose: { type: Function },
  };
}

export default TpChildModal;
