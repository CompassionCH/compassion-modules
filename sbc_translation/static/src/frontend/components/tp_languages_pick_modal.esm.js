import { Component, useState } from "@odoo/owl";
import { SettingsDAO } from "../models/settings_dao.esm";
import { TpModal } from "./tp_modal.esm";
import { TranslatorDAO } from "../models/translator_dao.esm";
import { showNotification } from "../notification.esm";

/**
 * Component that renders a translator's current skills and allows deletion.
 * Props:
 *   skills       {Array}    - list of skill objects {source, target, verified}
 *   translatorId {number}
 *   onChange     {Function} - called after a skill is removed
 */
export class TpTranslationSkills extends Component {
  static template = "sbc_translation.TpTranslationSkills";

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
    } catch {
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
  static template = "sbc_translation.TpLanguagesPickModal";

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
    } catch {
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
    } catch {
      showNotification("Unable to register translation skills", "danger");
    } finally {
      this.state.loading = false;
    }
  }
}

export default TpLanguagesPickModal;
