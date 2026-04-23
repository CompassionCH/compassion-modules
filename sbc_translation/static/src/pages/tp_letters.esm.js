import { Component, onMounted, useState } from "@odoo/owl";
import { LetterDAO } from "../models/letter_dao.esm";
import { TpLoader } from "../components/tp_loader.esm";
import { TpTranslatorButton } from "../components/tp_translator_button.esm";
import { showNotification } from "../notification.esm";

const LETTERS_PER_PAGE = 10;

/**
 * Priority badge.
 */
class TpLetterPriority extends Component {
  static template = 'sbc_translation.TpLetterPriority';
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
  static template = 'sbc_translation.TpLetters';

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
    } catch {
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
