/** @odoo-module */

import { Component, xml, useState } from "@odoo/owl";
import { showNotification } from "../notification";
import { TpModal } from "./tp_modal";
import { SettingsDAO } from "../models/settings_dao";
import { TranslatorDAO } from "../models/translator_dao";

/**
 * Component that renders a translator's current skills and allows deletion.
 * Props:
 *   skills       {Array}    - list of skill objects {source, target, verified}
 *   translatorId {number}
 *   onChange     {Function} - called after a skill is removed
 */
export class TpTranslationSkills extends Component {
  static template = xml`
        <div>
            <div t-foreach="props.skills" t-as="skill" t-key="skill_index"
                 class="d-flex align-items-center justify-content-between mb-2 p-2 border rounded">
                <span class="small">
                    <t t-esc="skill.source" /> → <t t-esc="skill.target" />
                    <span t-if="!skill.verified" class="badge bg-warning text-dark ms-2">Unverified</span>
                    <span t-if="skill.verified" class="badge bg-success ms-2">Verified</span>
                </span>
                <button type="button" class="btn btn-sm btn-outline-danger"
                        t-on-click="() => this.removeSkill(skill)">
                    <i class="fa fa-trash" />
                </button>
            </div>
            <p t-if="props.skills.length === 0" class="text-muted small text-center">
                No translation skills defined yet.
            </p>
        </div>
    `;

  static props = {
    skills: { type: Array },
    translatorId: { type: Number },
    onChange: { type: Function },
  };

  async removeSkill(skill) {
    try {
      await TranslatorDAO.deleteSkill(this.props.translatorId, {
        source: skill.source,
        target: skill.target,
        verified: skill.verified,
      });
      showNotification("Skill removed", "success");
      this.props.onChange();
    } catch (e) {
      showNotification("Unable to remove skill", "danger");
    }
  }
}

/**
 * Modal for picking/registering new translation skills.
 * Props:
 *   active       {Boolean}
 *   onClose      {Function}
 *   onChange     {Function} - called after skills are changed
 *   translatorId {number}
 */
export class TpLanguagesPickModal extends Component {
  static template = xml`
        <TpModal active="props.active" onClose="props.onClose"
                 title="'Languages'" subtitle="'Your translation skills'"
                 loading="state.loading" closeButtonText="'Cancel'">
            <div t-if="state.translator" class="p-3">
                <div class="row">
                    <div class="col-md-6" t-if="state.translator.skills.length > 0">
                        <h6 class="fw-medium mb-3">Your current translation skills</h6>
                        <TpTranslationSkills
                            skills="state.translator.skills"
                            translatorId="state.translator.translatorId"
                            onChange="() => this.props.onChange()" />
                    </div>
                    <div t-att-class="state.translator.skills.length > 0 ? 'col-md-6 bg-light p-3 rounded' : 'col-12'">
                        <h6 class="fw-medium mb-2">Register a new translation skill</h6>
                        <p class="small text-muted mb-3">
                            Translating from a language to another and back are two different skills.
                        </p>
                        <div t-foreach="state.potentialSkills" t-as="skill" t-key="skill_index"
                             class="input-group mb-2">
                            <select class="form-select form-select-sm" t-model="skill.competenceId">
                                <option t-foreach="state.competences" t-as="comp" t-key="comp.id"
                                        t-att-value="comp.id"
                                        t-att-disabled="translatorHasSkill(comp)"
                                        t-esc="comp.source + ' → ' + comp.target" />
                            </select>
                            <button type="button" class="btn btn-sm btn-outline-danger"
                                    t-on-click="() => state.potentialSkills.splice(skill_index, 1)">
                                <i class="fa fa-trash" />
                            </button>
                        </div>
                        <div class="text-center mt-2">
                            <button type="button" class="btn btn-sm btn-outline-secondary"
                                    t-if="state.allowedCompetences.length > 0"
                                    t-on-click="addSkill">
                                Add Skill
                            </button>
                            <p t-else="" class="small text-muted fw-semibold">
                                You already have all available translation skills!
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            <div t-else="" class="p-5 text-center text-muted">
                <span class="spinner-border spinner-border-sm" />
            </div>
            <t t-set-slot="footer-buttons">
                <button type="button" class="btn btn-primary btn-sm"
                        t-att-disabled="state.potentialSkills.length === 0"
                        t-on-click="registerSkills">
                    Register
                    <span t-esc="state.potentialSkills.length" />
                    new Skill<span t-esc="state.potentialSkills.length === 1 ? '' : 's'" />
                </button>
            </t>
        </TpModal>
    `;

  static components = { TpModal, TpTranslationSkills };

  static props = {
    active: { type: Boolean },
    onClose: { type: Function },
    onChange: { type: Function },
    translatorId: { type: Number, optional: true },
  };

  state = useState({
    loading: false,
    competences: [],
    potentialSkills: [],
    allowedCompetences: [],
    translator: null,
  });

  setup() {
    this._loadData();
  }

  async _loadData() {
    this.state.loading = true;
    try {
      const [competences, translator] = await Promise.all([
        SettingsDAO.translationCompetences(),
        TranslatorDAO.find(this.props.translatorId),
      ]);
      this.state.competences = competences;
      this.state.translator = translator;
      this.state.allowedCompetences = competences.filter(
        (c) => !this.translatorHasSkill(c),
      );
    } catch (e) {
      showNotification("Unable to load translator information", "danger");
      this.props.onClose();
    } finally {
      this.state.loading = false;
    }
  }

  translatorHasSkill(competence) {
    return (this.state.translator?.skills || []).some(
      (s) => s.source === competence.source && s.target === competence.target,
    );
  }

  addSkill() {
    if (this.state.allowedCompetences.length > 0) {
      this.state.potentialSkills.push({
        competenceId: this.state.allowedCompetences[0].id,
      });
    }
  }

  async registerSkills() {
    this.state.loading = true;
    try {
      await TranslatorDAO.registerSkills(
        this.props.translatorId,
        this.state.potentialSkills.map((s) => parseInt(s.competenceId, 10)),
      );
      showNotification("Your new skills have been registered", "success");
      this.state.potentialSkills = [];
      this.props.onChange();
    } catch (e) {
      showNotification("Unable to register translation skills", "danger");
    } finally {
      this.state.loading = false;
    }
  }
}

export default TpLanguagesPickModal;
