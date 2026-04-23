import { Component, onMounted, useState } from "@odoo/owl";
import { TpLanguagesPickModal } from "../components/tp_languages_pick_modal.esm";
import { TpLoader } from "../components/tp_loader.esm";
import { TranslatorDAO } from "../models/translator_dao.esm";
import { showNotification } from "../notification.esm";

const PER_PAGE = 10;

/**
 * Admin page: list all translators with skill management.
 * Props:
 *   navigate {Function}
 */
export class TpTranslators extends Component {
  static template = "sbc_translation.TpTranslators";

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
    } catch {
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
