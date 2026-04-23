import { Component, onMounted, useState } from "@odoo/owl";
import { LetterDAO } from "../models/letter_dao.esm";
import { TpBlurLoader } from "../components/tp_loader.esm";
import { TpLanguagesPickModal } from "../components/tp_languages_pick_modal.esm";

/**
 * Card showing a set of letters to translate for a given skill.
 * Props:
 *   title     {string}
 *   remaining {number}
 *   letters   {Array}
 *   status    {string|undefined} - 'highlight' | 'unverified' | 'waiting' | undefined
 *   navigate  {Function}
 */
class TpTranslationCard extends Component {
  static template = 'sbc_translation.TpTranslationCard';

  static props = {
    title: { type: String },
    remaining: { type: Number },
    letters: { type: Array },
    status: { type: String, optional: true },
    navigate: { type: Function },
  };
}

/**
 * Home page – shows the translator's dashboard with skills and available letters.
 * Props:
 *   translator {Object}  - current translator
 *   navigate   {Function}
 *   onRefreshTranslator {Function}
 */
export class TpHome extends Component {
  static template = 'sbc_translation.TpHome';

  static components = { TpLanguagesPickModal, TpTranslationCard, TpBlurLoader };

  static props = {
    translator: { type: Object, optional: true },
    navigate: { type: Function },
    onRefreshTranslator: { type: Function },
  };

  state = useState({
    loading: false,
    skillLetters: [],
    savedLetters: undefined,
    lettersAwaitingValidation: [],
    manageSkillsModal: false,
  });

  setup() {
    onMounted(() => this._refresh());
  }

  async _refresh() {
    this.state.loading = true;
    try {
      await Promise.all([
        this._fetchLetters(),
        this._fetchSaved(),
        this._fetchValidationLetters(),
      ]);
    } finally {
      this.state.loading = false;
    }
  }

  async _fetchSaved() {
    if (!this.props.translator) return;
    this.state.savedLetters = await LetterDAO.list({
      sortBy: ["priority desc", "date asc"],
      pageNumber: 0,
      pageSize: 5,
      search: [
        {
          column: "translatorId",
          term: this.props.translator.translatorId,
          operator: "=",
        },
        { column: "status", term: "in progress" },
        { column: "translationIssue", term: false, operator: "=" },
      ],
    });
  }

  async _fetchValidationLetters() {
    if (!this.props.translator) return;
    const results = await Promise.all(
      this.props.translator.skills.map(async (skill) => {
        const letters = await LetterDAO.list({
          search: [
            { column: "status", term: "to validate" },
            { column: "source", term: skill.source },
            { column: "target", term: skill.target },
          ],
        });
        return { skill, letters: letters.data };
      }),
    );
    this.state.lettersAwaitingValidation = results.filter(
      (r) => !r.skill.verified && r.letters.length > 0,
    );
  }

  async _fetchLetters() {
    if (!this.props.translator) return;
    const results = await Promise.all(
      this.props.translator.skills.map(async (skill) => {
        const letters = await LetterDAO.list({
          sortBy: ["priority desc", "date asc"],
          pageSize: 5,
          pageNumber: 0,
          search: [
            { column: "status", term: "to do" },
            { column: "source", term: skill.source },
            { column: "target", term: skill.target },
            { column: "translationIssue", term: false, operator: "=" },
          ],
        });
        return { skill, total: letters.total, letters: letters.data };
      }),
    );
    // Put unverified skills first
    this.state.skillLetters = results.sort((a, b) => {
      if (a.skill.verified && !b.skill.verified) return 1;
      if (!a.skill.verified && b.skill.verified) return -1;
      return 0;
    });
  }

  getCardStatus(item) {
    if (!item.skill.verified) {
      const waiting = this.state.lettersAwaitingValidation.find(
        (w) => w.skill === item.skill,
      );
      return waiting ? "waiting" : "unverified";
    }
    return undefined;
  }

  async onSkillsChange() {
    this.state.manageSkillsModal = false;
    this.state.loading = true;
    await this.props.onRefreshTranslator();
    await this._refresh();
  }

  closeSkillsModal() {
    this.state.manageSkillsModal = false;
  }
}

export default TpHome;
