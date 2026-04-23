import { Component, useState } from "@odoo/owl";
import { TpModal } from "./tp_modal.esm";

/**
 * Tips modal showing translation best practices.
 * Props:
 *   active  {Boolean}
 *   onClose {Function}
 */
class TpTipsModal extends Component {
  static template = 'sbc_translation.TpTipsModal';
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
  static template = 'sbc_translation.TpContentEditor';

  static components = { TpModal, TpTipsModal };

  static props = {
    letter: { type: Object },
  };

  state = useState({
    sourceElem: undefined,
    showTips: false,
  });

  openSource(elemId) {
    const elem = this.props.letter.translatedElements.find(
      (e) => e.id === elemId,
    );
    if (elem && elem.type === "paragraph") {
      this.state.sourceElem = elem.source || "";
    }
  }

  openTips() {
    this.state.showTips = true;
  }
}

export default TpContentEditor;
