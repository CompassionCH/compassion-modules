import { call, search, searchCount } from "../rpc.esm";

/**
 * Letter DAO - data access for the correspondence model.
 * Uses direct JSON-RPC (portal/frontend compatible).
 */

export const LetterDAO = {
  /**
   * Fetch a single letter's full info.
   * @param {number|string} id
   * @returns {Promise<Object>}
   */
  async find(id) {
    const result = await call("correspondence", "get_letter_info", [
      [parseInt(id, 10)],
    ]);
    return LetterDAO._cleanLetter(result);
  },

  /**
   * List letters matching params.
   * @param {Object} params - { search, sortBy, pageNumber, pageSize }
   * @returns {Promise<{data: Object[], total: number}>}
   */
  async list(params = {}) {
    const domain = LetterDAO._buildDomain(params.search || []);
    // Always filter to letters in translation queue
    domain.push(["state", "=", "Global Partner translation queue"]);
    const offset = (params.pageNumber || 0) * (params.pageSize || 10);
    const limit = params.pageSize || 10;
    const order = LetterDAO._buildOrder(params.sortBy || []);

    const [ids, total] = await Promise.all([
      search("correspondence", domain, { offset, limit, order }),
      searchCount("correspondence", domain),
    ]);

    if (!ids || ids.length === 0) {
      return { data: [], total };
    }

    // List_letters is a record-level method; pass IDs as first arg
    const rawLetters = await call("correspondence", "list_letters", [ids]);
    const data = (rawLetters || []).map((l) => LetterDAO._cleanLetter(l));
    return { data, total };
  },

  /**
   * List all IDs matching params (for select-all).
   * @param {Object} params
   * @returns {Promise<number[]>}
   */
  async listIds(params = {}) {
    const domain = LetterDAO._buildDomain(params.search || []);
    domain.push(["state", "=", "Global Partner translation queue"]);
    return search("correspondence", domain);
  },

  /**
   * Save (update) a translation in progress.
   * @param {Object} letter
   * @returns {Promise<boolean>}
   */
  async update(letter) {
    return call("correspondence", "save_translation", [
      [letter.id],
      letter.translatedElements,
      letter.translatorId || false,
    ]);
  },

  /**
   * Submit a completed translation.
   * @param {Object} letter
   * @returns {Promise<boolean>}
   */
  async submit(letter) {
    return call("correspondence", "submit_translation", [
      [letter.id],
      letter.translatedElements,
      letter.translatorId || false,
    ]);
  },

  /**
   * Report an issue with a letter.
   * @param {Number} letterId
   * @param {String} issueType
   * @param {String} message
   * @returns {Promise<boolean>}
   */
  async reportIssue(letterId, issueType, message) {
    return call("correspondence", "raise_translation_issue", [
      [parseInt(letterId, 10)],
      issueType,
      message,
    ]);
  },

  /**
   * Reply to translator comments on a letter.
   * @param {Object} letter
   * @param {String} html
   * @returns {Promise<boolean>}
   */
  async replyToComments(letter, html) {
    return call("correspondence", "reply_to_comments", [[letter.id], html]);
  },

  /**
   * Mark all comments as read.
   * @param {Object} letter
   * @returns {Promise<boolean>}
   */
  async markCommentsAsRead(letter) {
    return call("correspondence", "mark_comments_read", [[letter.id]]);
  },

  /**
   * Put a letter back into the translation queue (resubmit).
   * @param {Object} letter
   * @returns {Promise<boolean>}
   */
  async makeTranslatable(letter) {
    return call("correspondence", "action_resubmit_to_translation", [
      [letter.id],
    ]);
  },

  /**
   * Remove a letter from the translation queue.
   * @param {Object} letter
   * @returns {Promise<boolean>}
   */
  async deleteLetter(letter) {
    return call("correspondence", "action_remove_local_translate", [
      [letter.id],
    ]);
  },

  // -------------------------------------------------------------------------
  // Private helpers
  // -------------------------------------------------------------------------

  /**
   * Map the frontend search params to an Odoo domain.
   * @param {Array} search_vals - [{column, term, operator}]
   * @returns {Array}
   */
  _buildDomain(search_vals) {
    const fieldMap = {
      status: "translation_status",
      title: "name",
      priority: "translation_priority",
      unreadComments: "unread_comments",
      date: "scanned_date",
      source: "src_translation_lang_id.name",
      target: "translation_language_id.name",
      translatorId: "new_translator_id",
      translationIssue: "translation_issue",
    };
    const domain = [];
    for (const item of search_vals) {
      const field = fieldMap[item.column] || item.column;
      const op = item.operator || "ilike";
      let term = item.term;
      // Handle booleans and false
      if (term === false || term === "false") term = false;
      else if (term === true || term === "true") term = true;
      domain.push([field, op, term]);
    }
    return domain;
  },

  /**
   * Map the frontend sortBy array to an Odoo order string.
   * @param {string[]} sortBy
   * @returns {String}
   */
  _buildOrder(sortBy) {
    const fieldMap = {
      status: "translation_status",
      title: "name",
      priority: "translation_priority",
      date: "scanned_date",
      unreadComments: "unread_comments",
    };
    return sortBy
      .map((clause) => {
        const [field, dir = "asc"] = clause.split(" ");
        return `${fieldMap[field] || field} ${dir}`;
      })
      .join(", ");
  },

  /**
   * Clean/normalise a raw letter object coming from the server.
   * @param {Object} letter
   * @returns {Object}
   */
  _cleanLetter(letter) {
    if (!letter) return undefined;
    return {
      ...letter,
      status: letter.status || "to do",
      date: letter.date ? new Date(letter.date) : new Date(),
      lastUpdate:
        letter.lastUpdate && letter.lastUpdate !== "None"
          ? new Date(letter.lastUpdate)
          : undefined,
      translatorId:
        letter.translatorId === "None" ? undefined : letter.translatorId,
      translatedElements:
        letter.translatedElements === "None" ? [] : letter.translatedElements,
      priority: parseInt(letter.priority, 10) || 0,
    };
  },
};

export default LetterDAO;
