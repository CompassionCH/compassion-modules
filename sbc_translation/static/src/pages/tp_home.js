/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { LetterDAO } from "../models/letter_dao";
import { TpLanguagesPickModal } from "../components/tp_languages_pick_modal";
import { TpBlurLoader } from "../components/tp_loader";

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
    static template = xml`
        <div class="card tp-translation-card" style="min-width: 260px; max-width: 300px;"
             t-att-class="{
               'border-primary': props.status === 'highlight',
               'border-warning': props.status === 'unverified',
               'border-info': props.status === 'waiting',
             }">
            <div class="card-header d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="mb-0 fw-light" t-esc="props.title" />
                    <small t-if="!props.status or props.status === 'highlight'" class="text-muted">
                        <t t-esc="props.remaining" /> Letters
                    </small>
                    <small t-elif="props.status === 'waiting'" class="text-muted">Awaiting approval</small>
                    <small t-else="" class="text-muted">Waiting for your verification letter</small>
                </div>
            </div>
            <div class="card-body">
                <div t-if="props.letters.length === 0">
                    <p class="text-muted text-center small">No letters to translate here</p>
                </div>
                <div t-elif="!props.status or props.status === 'highlight'">
                    <button type="button" class="btn btn-sm btn-primary w-100 mb-2"
                            t-on-click="() => props.navigate('letter-edit', { letterId: props.letters[0].id })">
                        <i class="fa fa-star me-1" />Take the first
                    </button>
                    <div t-foreach="props.letters" t-as="letter" t-key="letter.id">
                        <button type="button"
                                class="btn btn-link btn-sm p-0 d-block mb-1 text-start"
                                t-att-class="{ 'text-danger': letter.translationIssue }"
                                t-on-click="() => props.navigate('letter-edit', { letterId: letter.id })">
                            <span class="fw-semibold" t-esc="letter.child.ref" />
                            <span class="ms-1 text-muted" t-esc="'(' + letter.date.toLocaleDateString() + ')'" />
                        </button>
                    </div>
                </div>
                <div t-elif="props.status === 'waiting'" class="text-center text-muted small">
                    <p>Your verification letter is awaiting approval. Once approved you will be able to start translating.</p>
                </div>
                <div t-else="">
                    <button type="button" class="btn btn-sm btn-primary w-100 mb-2"
                            t-if="props.letters.length > 0"
                            t-on-click="() => props.navigate('letter-edit', { letterId: props.letters[0].id })">
                        <i class="fa fa-star me-1" />Translate Verification Letter
                    </button>
                    <p class="text-center text-muted small">
                        This skill must be validated. Translate the given letter for it to be reviewed.
                    </p>
                </div>
            </div>
        </div>
    `;

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
    static template = xml`
        <div class="container py-4 position-relative">
            <TpBlurLoader active="state.loading" />

            <TpLanguagesPickModal
                active="state.manageSkillsModal"
                onClose="() => closeSkillsModal()"
                translatorId="props.translator ? props.translator.translatorId : undefined"
                onChange="() => onSkillsChange()" />

            <div class="text-center pt-4 pb-3">
                <p class="text-muted fw-light fs-5">Compassion</p>
                <h1 class="fw-light display-5">Translation Platform</h1>
            </div>

            <!-- Has skills: show letter cards -->
            <div t-if="state.skillLetters.length > 0">
                <p class="text-center text-secondary mb-2">
                    Welcome <strong t-esc="props.translator ? props.translator.name : ''" />.
                    Here are the texts waiting to be translated.
                </p>
                <div t-if="props.translator and props.translator.total > 1" class="text-center mb-3">
                    <p class="text-secondary">
                        You have translated a total of
                        <span class="text-primary fw-semibold mx-1" t-esc="props.translator.total" />
                        letters – thank you so much!
                    </p>
                </div>
                <div class="d-flex justify-content-center mb-4">
                    <button type="button" class="btn btn-sm btn-outline-secondary"
                            t-on-click="() => state.manageSkillsModal = true">
                        <i class="fa fa-cog me-1" />Manage your translation skills
                    </button>
                </div>
                <div class="d-flex flex-wrap gap-4 justify-content-center">
                    <TpTranslationCard
                        t-if="state.savedLetters and state.savedLetters.total > 0"
                        title="'Saved Letters'"
                        remaining="state.savedLetters.total"
                        letters="state.savedLetters.data"
                        status="'highlight'"
                        navigate="props.navigate" />
                    <TpTranslationCard t-foreach="state.skillLetters"
                        t-as="item" t-key="item_index"
                        title="item.skill.source + ' → ' + item.skill.target"
                        remaining="item.total"
                        letters="item.letters"
                        status="getCardStatus(item)"
                        navigate="props.navigate" />
                </div>
                <div class="text-center py-5 text-muted fw-light fs-5">Thank you.</div>
            </div>

            <!-- No skills yet -->
            <div t-else="" class="text-center my-5">
                <p class="text-secondary mb-4">
                    Welcome <strong t-esc="props.translator ? props.translator.name : ''" />.
                    It seems you don't have any translation skill yet.
                    Start by picking the languages you are confident in.
                </p>
                <button type="button" class="btn btn-primary"
                        t-on-click="() => state.manageSkillsModal = true">
                    <i class="fa fa-plus me-1" />Pick Languages
                </button>
            </div>
        </div>
    `;

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
        this.orm = useService("orm");
        this.notification = useService("notification");
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
        this.state.savedLetters = await LetterDAO.list(this.orm, {
            sortBy: ["priority desc", "date asc"],
            pageNumber: 0,
            pageSize: 5,
            search: [
                { column: "translatorId", term: this.props.translator.translatorId, operator: "=" },
                { column: "status", term: "in progress" },
                { column: "translationIssue", term: false, operator: "=" },
            ],
        });
    }

    async _fetchValidationLetters() {
        if (!this.props.translator) return;
        const results = await Promise.all(
            this.props.translator.skills.map(async (skill) => {
                const letters = await LetterDAO.list(this.orm, {
                    search: [
                        { column: "status", term: "to validate" },
                        { column: "source", term: skill.source },
                        { column: "target", term: skill.target },
                    ],
                });
                return { skill, letters: letters.data };
            })
        );
        this.state.lettersAwaitingValidation = results.filter(
            (r) => !r.skill.verified && r.letters.length > 0
        );
    }

    async _fetchLetters() {
        if (!this.props.translator) return;
        const results = await Promise.all(
            this.props.translator.skills.map(async (skill) => {
                const letters = await LetterDAO.list(this.orm, {
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
            })
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
            const waiting = this.state.lettersAwaitingValidation.find((w) => w.skill === item.skill);
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
