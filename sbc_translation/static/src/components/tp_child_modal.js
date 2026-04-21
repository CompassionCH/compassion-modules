/** @odoo-module */

import { Component, xml } from "@odoo/owl";
import { TpModal } from "./tp_modal";

/**
 * Child protection policy modal.
 * Props:
 *   active  {Boolean}
 *   onClose {Function}
 */
export class TpChildModal extends Component {
  static template = xml`
        <TpModal active="props.active" onClose="props.onClose" title="'Child Protection'">
            <div class="p-3" style="max-width: 750px; max-height: 70vh; overflow-y: auto;">
                <h6 class="fw-semibold">Expected/acceptable behaviors:</h6>
                <ul class="small mb-4">
                    <li class="mb-2">I will demonstrate the proper respect and dignity of all children and will demonstrate Jesus's love and care for them, regardless of their gender, age, race, religion, social background, culture, special need or disability.</li>
                    <li class="mb-2">I will maintain appropriate and reasonable expectations for children based on their age and ability level.</li>
                    <li class="mb-2">I will engage in age-appropriate communication with beneficiaries.</li>
                    <li class="mb-2">I will submit to the appropriate background or police checks as permissible by law prior to face-to-face contact with beneficiaries.</li>
                    <li class="mb-2">I will engage in activities with beneficiaries only in open or visible places, and in the event that an activity needs to take place in an enclosed space, I will ensure that at least one other approved adult is present.</li>
                    <li class="mb-2">If I witness child abuse, know a child is in danger, observe any concerning behaviors from colleagues, partners or other representatives, or a child comes to me with a report of abuse, I will take it seriously and report it to the proper staff or relevant authorities.</li>
                    <li class="mb-2">I will keep all information about child protection investigations confidential, keeping in mind privacy and dignity concerns of all involved.</li>
                    <li class="mb-2">I will contribute to building an environment where children are respected and encouraged to discuss their concerns and rights.</li>
                    <li class="mb-2">I will follow Compassion's rules about communication with beneficiaries, including social media interaction.</li>
                </ul>
                <h6 class="fw-semibold">Unacceptable behaviors:</h6>
                <ul class="small mb-4">
                    <li class="mb-2">I will not solicit a romantic/dating relationship and will never engage in sexual/sexually suggestive behavior with any beneficiary, regardless of age.</li>
                    <li class="mb-2">I will never engage in sexual/sexually suggestive behavior with any child under age 18, regardless of the legal age of consent in-country.</li>
                    <li class="mb-2">I will never use language that is verbally/emotionally abusive, sexually suggestive, degrading, humiliating, shaming or is otherwise culturally inappropriate with a beneficiary.</li>
                    <li class="mb-2">I will not touch beneficiaries in an inappropriate or culturally insensitive way.</li>
                    <li class="mb-2">I will never use any kind of physical discipline or physical punishment as a method of correction for beneficiaries.</li>
                    <li class="mb-2">I will never travel alone with a beneficiary, without an approved representative or prior approval, except in a life-threatening emergency.</li>
                    <li class="mb-2">I will not hire any child in any harmful form of child labor and follow local laws regarding child employment.</li>
                    <li class="mb-2">I will not gather, disclose or support the disclosure of information about beneficiaries or their families without prior, express permission.</li>
                </ul>
                <div class="p-3 bg-light border-top d-flex flex-column align-items-center">
                    <p class="small fw-semibold mb-2">Child Protection Videos</p>
                    <div class="d-flex gap-2 flex-wrap justify-content-center">
                        <a href="https://drive.google.com/file/d/1p9_o89wYkbSt3F4Y71Gy3XXdbsJLp9oT/view?usp=sharing"
                           target="_blank" class="btn btn-sm btn-outline-secondary">
                            Watch child protection video
                        </a>
                    </div>
                </div>
            </div>
        </TpModal>
    `;

  static components = { TpModal };

  static props = {
    active: { type: Boolean },
    onClose: { type: Function },
  };
}

export default TpChildModal;
