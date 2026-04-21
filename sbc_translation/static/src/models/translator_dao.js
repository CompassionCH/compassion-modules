/** @odoo-module */

import { search, searchCount, call } from "../rpc";

/**
 * Translator DAO - data access for the translation.user model.
 * Uses direct JSON-RPC (portal/frontend compatible).
 */

export const TranslatorDAO = {
  /**
   * Get a single translator's full info.
   * @param {number} id
   * @returns {Promise<Object>}
   */
  async find(id) {
    const data = await call("translation.user", "get_user_info", [
      [parseInt(id, 10)],
    ]);
    return TranslatorDAO._cleanTranslator(data);
  },

  /**
   * Get the current authenticated user's translator info.
   * @returns {Promise<Object>}
   */
  async current() {
    const data = await call("translation.user", "get_my_info", []);
    if (!data) {
      throw new Error("Unable to find current authenticated translator");
    }
    return TranslatorDAO._cleanTranslator(data);
  },

  /**
   * List translators with optional filters and pagination.
   * @param {Object} params
   * @returns {Promise<{data: Object[], total: number}>}
   */
  async list(params = {}) {
    const domain = TranslatorDAO._buildDomain(params.search || []);
    const offset = (params.pageNumber || 0) * (params.pageSize || 10);
    const limit = params.pageSize || 10;
    const order = TranslatorDAO._buildOrder(params.sortBy || []);

    const [ids, total] = await Promise.all([
      search("translation.user", domain, { offset, limit, order }),
      searchCount("translation.user", domain),
    ]);

    if (!ids || ids.length === 0) {
      return { data: [], total };
    }

    const rawTranslators = await call("translation.user", "list_users", [ids]);
    const data = (rawTranslators || [])
      .map((t) => TranslatorDAO._cleanTranslator(t))
      .filter((t) => t !== undefined);
    return { data, total };
  },

  /**
   * List all matching translator IDs.
   * @param {Object} params
   * @returns {Promise<number[]>}
   */
  async listIds(params = {}) {
    const domain = TranslatorDAO._buildDomain(params.search || []);
    return search("translation.user", domain);
  },

  /**
   * Register new translation skills for a translator.
   * @param {number} translatorId
   * @param {number[]} competenceIds
   * @returns {Promise<boolean>}
   */
  async registerSkills(translatorId, competenceIds) {
    for (const skillId of competenceIds) {
      await call("translation.user", "add_skill", [[translatorId], skillId]);
    }
    return true;
  },

  /**
   * Remove a translation skill from a translator.
   * @param {number} translatorId
   * @param {Object} skill - { source, target, verified }
   * @returns {Promise<boolean>}
   */
  async deleteSkill(translatorId, skill) {
    await call("translation.user", "unlink_skill", [[translatorId], skill]);
    return true;
  },

  // -------------------------------------------------------------------------
  // Private helpers
  // -------------------------------------------------------------------------

  _buildDomain(search) {
    const fieldMap = {
      total: "nb_translated_letters",
      year: "nb_translated_letters_this_year",
      lastYear: "nb_translated_letters_last_year",
      name: "partner_id.name",
      email: "user_id.email",
    };
    const domain = [];
    for (const item of search) {
      const field = fieldMap[item.column] || item.column;
      domain.push([field, item.operator || "ilike", item.term]);
    }
    return domain;
  },

  _buildOrder(sortBy) {
    const fieldMap = {
      total: "nb_translated_letters",
      year: "nb_translated_letters_this_year",
      lastYear: "nb_translated_letters_last_year",
      name: "partner_id.name",
      email: "user_id.email",
    };
    return sortBy
      .map((clause) => {
        const [field, dir = "asc"] = clause.split(" ");
        return `${fieldMap[field] || field} ${dir}`;
      })
      .join(", ");
  },

  _cleanTranslator(data) {
    if (!data) return undefined;
    return {
      ...data,
      email: data.email !== "None" ? data.email : undefined,
      name: data.name !== "None" ? data.name : undefined,
      age: data.age !== "None" ? data.age : undefined,
      language: data.language !== "None" ? data.language : undefined,
      total: data.total !== "None" ? data.total : 0,
      year: data.year !== "None" ? data.year : 0,
      lastYear: data.lastYear !== "None" ? data.lastYear : 0,
      skills: data.skills !== "None" ? data.skills || [] : [],
    };
  },
};

export default TranslatorDAO;
