import { Component, useState } from "@odoo/owl";
import { TpLoader } from "./tp_loader.esm";
import { TpSignalProblem } from "./tp_signal_problem.esm";

/**
 * Header that shows child/sponsor data and letter metadata.
 * Props:
 *   letter  {Object}  - letter data object
 *   loading {Boolean} - show spinner when saving
 *   navigateBack {Function} - navigate back to letters list
 */
class TpLetterInfoHeader extends Component {
  static template = 'sbc_translation.TpLetterInfoHeader';

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
  static template = 'sbc_translation.TpLetterViewer';

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
