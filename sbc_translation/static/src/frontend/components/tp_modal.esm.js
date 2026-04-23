import {
  Component,
  onMounted,
  onPatched,
  onWillUpdateProps,
  useState,
} from "@odoo/owl";
import { TpLoader } from "./tp_loader.esm";

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
  static template = "sbc_translation.TpModal";

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
