/** @odoo-module */

import {
  Component,
  xml,
  useState,
  onMounted,
  onWillUpdateProps,
} from "@odoo/owl";
import { showNotification } from "../notification";
import { LetterDAO } from "../models/letter_dao";
import { TpLoader } from "../components/tp_loader";
import { TpTranslatorButton } from "../components/tp_translator_button";

const LETTERS_PER_PAGE = 10;

/**
 * Priority badge.
 */
class TpLetterPriority extends Component {
  static template = xml`
        <span class="badge"
              t-att-class="{
                'bg-danger': props.priority >= 4,
                'bg-warning text-dark': props.priority === 3,
                'bg-primary': props.priority === 2,
                'bg-success': props.priority === 1,
                'bg-secondary': !props.priority,
              }"
              t-esc="priorityLabel" />
    `;
  static props = { priority: { type: Number, optional: true } };

  get priorityLabel() {
    const labels = { 0: "—", 1: "Low", 2: "Normal", 3: "High", 4: "Urgent" };
    return labels[this.props.priority] || "—";
  }
}

/**
 * Letters list page with pagination and column search.
 * Props:
 *   navigate    {Function} - navigate(page, params)
 *   isAdmin     {Boolean}
 */
export class TpLetters extends Component {
  static template = xml`
        <div class="container-fluid py-4">
            <div class="d-flex align-items-center mb-4 gap-3">
                <div>
                    <h6 class="text-muted fw-light mb-0">Compassion</h6>
                    <h2 class="fw-light mb-0">Letters</h2>
                </div>
                <button type="button" class="btn btn-sm btn-outline-secondary ms-auto"
                        t-on-click="clearFilters">
                    <i class="fa fa-times me-1" />Clear Filters
                </button>
            </div>

            <div class="card shadow-sm">
                <div class="card-body p-0">
                    <div class="position-relative">
                        <table class="table table-sm table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th t-on-click="() => this.toggleSort('priority')" class="cursor-pointer">
                                        Priority <i t-att-class="sortIcon('priority')" />
                                    </th>
                                    <th t-on-click="() => this.toggleSort('title')" class="cursor-pointer">
                                        Title <i t-att-class="sortIcon('title')" />
                                    </th>
                                    <th>Status</th>
                                    <th>Comments</th>
                                    <th>Source</th>
                                    <th>Target</th>
                                    <th t-if="props.isAdmin">Translator</th>
                                    <th t-on-click="() => this.toggleSort('date')" class="cursor-pointer">
                                        Date <i t-att-class="sortIcon('date')" />
                                    </th>
                                    <th>Actions</th>
                                </tr>
                                <!-- Search row -->
                                <tr class="table-secondary">
                                    <td />
                                    <td>
                                        <input type="text" class="form-control form-control-sm"
                                               placeholder="Search title…"
                                               t-att-value="getFilter('title')"
                                               t-on-input="(e) => this.setFilter('title', e.target.value)" />
                                    </td>
                                    <td>
                                        <input type="text" class="form-control form-control-sm"
                                               placeholder="Search status…"
                                               t-att-value="getFilter('status')"
                                               t-on-input="(e) => this.setFilter('status', e.target.value)" />
                                    </td>
                                    <td />
                                    <td>
                                        <input type="text" class="form-control form-control-sm"
                                               placeholder="Source lang…"
                                               t-att-value="getFilter('source')"
                                               t-on-input="(e) => this.setFilter('source', e.target.value)" />
                                    </td>
                                    <td>
                                        <input type="text" class="form-control form-control-sm"
                                               placeholder="Target lang…"
                                               t-att-value="getFilter('target')"
                                               t-on-input="(e) => this.setFilter('target', e.target.value)" />
                                    </td>
                                    <td t-if="props.isAdmin" />
                                    <td />
                                    <td />
                                </tr>
                            </thead>
                            <tbody>
                                <tr t-if="state.letters.length === 0 and !state.loading">
                                    <td colspan="9" class="text-center text-muted py-5">
                                        <i class="fa fa-search fa-2x mb-2 d-block" />
                                        No letters found
                                    </td>
                                </tr>
                                <tr t-foreach="state.letters" t-as="letter" t-key="letter.id"
                                    t-att-class="{ 'table-danger': letter.translationIssue }">
                                    <td><TpLetterPriority priority="letter.priority" /></td>
                                    <td class="fw-medium" t-esc="letter.title" />
                                    <td>
                                        <span class="badge"
                                              t-att-class="letter.translationIssue ? 'bg-danger' : 'bg-secondary'"
                                              t-esc="letter.status" />
                                    </td>
                                    <td>
                                        <span t-if="letter.unreadComments" class="badge bg-warning text-dark">
                                            <i class="fa fa-comment" /> Unread
                                        </span>
                                        <span t-else="" class="text-muted">—</span>
                                    </td>
                                    <td class="small" t-esc="letter.source" />
                                    <td class="small" t-esc="letter.target" />
                                    <td t-if="props.isAdmin">
                                        <TpTranslatorButton t-if="letter.translatorId"
                                                            translatorId="letter.translatorId" />
                                        <span t-else="" class="text-muted">—</span>
                                    </td>
                                    <td class="small" t-esc="letter.date ? letter.date.toLocaleDateString() : ''" />
                                    <td>
                                        <button type="button" class="btn btn-sm btn-primary"
                                                t-on-click="() => props.navigate('letter-edit', { letterId: letter.id })">
                                            <i class="fa fa-pencil me-1" />Translate
                                        </button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <!-- Loading overlay -->
                        <div t-if="state.loading"
                             class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
                             style="background: rgba(255,255,255,0.7); z-index: 10;">
                            <TpLoader />
                        </div>
                    </div>
                    <!-- Pagination -->
                    <div class="d-flex align-items-center justify-content-between p-3 border-top"
                         t-if="state.letters.length > 0 or state.page > 0">
                        <span class="small text-muted">
                            Page <t t-esc="state.page + 1" /> · <t t-esc="state.total" /> letters total
                        </span>
                        <nav>
                            <ul class="pagination pagination-sm mb-0">
                                <li class="page-item" t-att-class="{ disabled: state.page === 0 }">
                                    <button class="page-link" t-on-click="prevPage">‹</button>
                                </li>
                                <li class="page-item" t-att-class="{ disabled: (state.page + 1) * LETTERS_PER_PAGE >= state.total }">
                                    <button class="page-link" t-on-click="nextPage">›</button>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
    `;

  static components = { TpLetterPriority, TpTranslatorButton, TpLoader };

  static props = {
    navigate: { type: Function },
    isAdmin: { type: Boolean, optional: true },
    translator: { type: Object, optional: true },
  };

  LETTERS_PER_PAGE = LETTERS_PER_PAGE;

  state = useState({
    letters: [],
    total: 0,
    page: 0,
    loading: false,
    filters: {},
    sortBy: [],
    searchTimeout: null,
  });

  setup() {
    onMounted(() => this._loadLetters());
  }

  async _loadLetters() {
    this.state.loading = true;
    try {
      const search = Object.entries(this.state.filters)
        .filter(([, term]) => term.trim())
        .map(([col, term]) => ({ column: col, term }));

      const result = await LetterDAO.list({
        search,
        sortBy: this.state.sortBy,
        pageNumber: this.state.page,
        pageSize: LETTERS_PER_PAGE,
      });
      this.state.letters = result.data;
      this.state.total = result.total;
    } catch (e) {
      showNotification("Unable to load letters", "danger");
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
      this._loadLetters();
    }, 400);
  }

  clearFilters() {
    this.state.filters = {};
    this.state.sortBy = [];
    this.state.page = 0;
    this._loadLetters();
  }

  sortIcon(col) {
    const clause = this.state.sortBy.find((s) => s.startsWith(col));
    if (!clause) return "fa fa-sort text-muted";
    return clause.endsWith("desc") ? "fa fa-sort-down" : "fa fa-sort-up";
  }

  toggleSort(col) {
    const index = this.state.sortBy.findIndex((s) => s.startsWith(col));
    if (index >= 0) {
      const current = this.state.sortBy[index];
      const dir = current.endsWith("asc") ? "desc" : "asc";
      this.state.sortBy[index] = `${col} ${dir}`;
    } else {
      this.state.sortBy = [`${col} asc`];
    }
    this._loadLetters();
  }

  prevPage() {
    if (this.state.page > 0) {
      this.state.page--;
      this._loadLetters();
    }
  }

  nextPage() {
    if ((this.state.page + 1) * LETTERS_PER_PAGE < this.state.total) {
      this.state.page++;
      this._loadLetters();
    }
  }
}

export default TpLetters;
