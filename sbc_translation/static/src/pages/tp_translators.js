/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";
import { showNotification } from "../notification";
import { TranslatorDAO } from "../models/translator_dao";
import { TpTranslatorButton } from "../components/tp_translator_button";
import { TpLoader } from "../components/tp_loader";
import { TpModal } from "../components/tp_modal";
import { TpLanguagesPickModal } from "../components/tp_languages_pick_modal";

const PER_PAGE = 10;

/**
 * Admin page: list all translators with skill management.
 * Props:
 *   navigate {Function}
 */
export class TpTranslators extends Component {
  static template = xml`
        <div class="container-fluid py-4">
            <div class="mb-4">
                <h6 class="text-muted fw-light mb-0">Compassion</h6>
                <h2 class="fw-light mb-0">Translators</h2>
            </div>

            <div class="card shadow-sm">
                <div class="card-body p-0">
                    <div class="position-relative">
                        <table class="table table-sm table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th t-on-click="() => this.toggleSort('name')" class="cursor-pointer">
                                        Name <i t-att-class="sortIcon('name')" />
                                    </th>
                                    <th t-on-click="() => this.toggleSort('email')" class="cursor-pointer">
                                        Email <i t-att-class="sortIcon('email')" />
                                    </th>
                                    <th>Role</th>
                                    <th t-on-click="() => this.toggleSort('total')" class="cursor-pointer">
                                        Letters <i t-att-class="sortIcon('total')" />
                                    </th>
                                    <th>Skills</th>
                                    <th>Actions</th>
                                </tr>
                                <tr class="table-secondary">
                                    <td>
                                        <input type="text" class="form-control form-control-sm"
                                               placeholder="Search name…"
                                               t-att-value="getFilter('name')"
                                               t-on-input="(e) => this.setFilter('name', e.target.value)" />
                                    </td>
                                    <td>
                                        <input type="text" class="form-control form-control-sm"
                                               placeholder="Search email…"
                                               t-att-value="getFilter('email')"
                                               t-on-input="(e) => this.setFilter('email', e.target.value)" />
                                    </td>
                                    <td colspan="4" />
                                </tr>
                            </thead>
                            <tbody>
                                <tr t-if="state.translators.length === 0 and !state.loading">
                                    <td colspan="6" class="text-center text-muted py-5">
                                        <i class="fa fa-users fa-2x mb-2 d-block" />
                                        No translators found
                                    </td>
                                </tr>
                                <tr t-foreach="state.translators" t-as="translator" t-key="translator.translatorId">
                                    <td class="fw-medium" t-esc="translator.name or '—'" />
                                    <td class="small text-muted" t-esc="translator.email or '—'" />
                                    <td>
                                        <span class="badge"
                                              t-att-class="translator.role === 'admin' ? 'bg-danger' : 'bg-secondary'"
                                              t-esc="translator.role" />
                                    </td>
                                    <td t-esc="translator.total or 0" />
                                    <td class="small">
                                        <span t-foreach="translator.skills" t-as="skill" t-key="skill_index"
                                              class="badge bg-light text-dark border me-1">
                                            <t t-esc="skill.source" /> → <t t-esc="skill.target" />
                                            <span t-if="!skill.verified" class="ms-1 text-warning">⚠</span>
                                        </span>
                                    </td>
                                    <td>
                                        <button type="button" class="btn btn-sm btn-outline-secondary"
                                                t-on-click="() => this.openSkillsModal(translator)">
                                            <i class="fa fa-cog me-1" />Skills
                                        </button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <div t-if="state.loading"
                             class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
                             style="background: rgba(255,255,255,0.7); z-index: 10;">
                            <TpLoader />
                        </div>
                    </div>
                    <div class="d-flex align-items-center justify-content-between p-3 border-top"
                         t-if="state.translators.length > 0 or state.page > 0">
                        <span class="small text-muted">
                            Page <t t-esc="state.page + 1" /> · <t t-esc="state.total" /> translators
                        </span>
                        <nav>
                            <ul class="pagination pagination-sm mb-0">
                                <li class="page-item" t-att-class="{ disabled: state.page === 0 }">
                                    <button class="page-link" t-on-click="prevPage">‹</button>
                                </li>
                                <li class="page-item" t-att-class="{ disabled: (state.page + 1) * PER_PAGE >= state.total }">
                                    <button class="page-link" t-on-click="nextPage">›</button>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </div>
            </div>

            <!-- Skills management modal -->
            <TpLanguagesPickModal
                t-if="state.editingTranslator"
                active="!!state.editingTranslator"
                onClose="closeSkillsModal"
                translatorId="state.editingTranslator ? state.editingTranslator.translatorId : 0"
                onChange="onSkillsChanged" />
        </div>
    `;

  static components = { TpLoader, TpLanguagesPickModal };

  static props = {
    navigate: { type: Function },
  };

  PER_PAGE = PER_PAGE;

  state = useState({
    translators: [],
    total: 0,
    page: 0,
    loading: false,
    filters: {},
    sortBy: [],
    editingTranslator: null,
    searchTimeout: null,
  });

  setup() {
    onMounted(() => this._loadTranslators());
  }

  async _loadTranslators() {
    this.state.loading = true;
    try {
      const search = Object.entries(this.state.filters)
        .filter(([, term]) => term.trim())
        .map(([col, term]) => ({ column: col, term }));

      const result = await TranslatorDAO.list({
        search,
        sortBy: this.state.sortBy,
        pageNumber: this.state.page,
        pageSize: PER_PAGE,
      });
      this.state.translators = result.data;
      this.state.total = result.total;
    } catch (e) {
      showNotification("Unable to load translators", "danger");
    } finally {
      this.state.loading = false;
    }
  }

  getFilter(col) {
    return this.state.filters[col] || "";
  }

  setFilter(col, value) {
    if (this.state.searchTimeout) clearTimeout(this.state.searchTimeout);
    this.state.filters[col] = value;
    this.state.searchTimeout = setTimeout(() => {
      this.state.page = 0;
      this._loadTranslators();
    }, 400);
  }

  sortIcon(col) {
    const clause = this.state.sortBy.find((s) => s.startsWith(col));
    if (!clause) return "fa fa-sort text-muted";
    return clause.endsWith("desc") ? "fa fa-sort-down" : "fa fa-sort-up";
  }

  toggleSort(col) {
    const index = this.state.sortBy.findIndex((s) => s.startsWith(col));
    if (index >= 0) {
      const dir = this.state.sortBy[index].endsWith("asc") ? "desc" : "asc";
      this.state.sortBy[index] = `${col} ${dir}`;
    } else {
      this.state.sortBy = [`${col} asc`];
    }
    this._loadTranslators();
  }

  prevPage() {
    if (this.state.page > 0) {
      this.state.page--;
      this._loadTranslators();
    }
  }

  nextPage() {
    if ((this.state.page + 1) * PER_PAGE < this.state.total) {
      this.state.page++;
      this._loadTranslators();
    }
  }

  openSkillsModal(translator) {
    this.state.editingTranslator = translator;
  }

  closeSkillsModal() {
    this.state.editingTranslator = null;
  }

  onSkillsChanged() {
    this.closeSkillsModal();
    this._loadTranslators();
  }
}

export default TpTranslators;
