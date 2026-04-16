/** @odoo-module */

/**
 * Letter DAO - data access for the correspondence model.
 * All methods take `orm` (the Odoo ORM service) as first argument.
 */

export const LetterDAO = {
    /**
     * Fetch a single letter's full info.
     * @param {Object} orm - Odoo orm service
     * @param {number|string} id
     * @returns {Promise<Object>}
     */
    async find(orm, id) {
        const result = await orm.call("correspondence", "get_letter_info", [[parseInt(id, 10)]]);
        return LetterDAO._cleanLetter(result);
    },

    /**
     * List letters matching params.
     * @param {Object} orm
     * @param {Object} params - { search, sortBy, pageNumber, pageSize }
     * @returns {Promise<{data: Object[], total: number}>}
     */
    async list(orm, params = {}) {
        const domain = LetterDAO._buildDomain(params.search || []);
        // Always filter to letters in translation queue
        domain.push(["state", "=", "Global Partner translation queue"]);
        const offset = (params.pageNumber || 0) * (params.pageSize || 10);
        const limit = params.pageSize || 10;
        const order = LetterDAO._buildOrder(params.sortBy || []);

        const [ids, total] = await Promise.all([
            orm.search("correspondence", domain, { offset, limit, order }),
            orm.searchCount("correspondence", domain),
        ]);

        if (!ids || ids.length === 0) {
            return { data: [], total };
        }

        // list_letters is a record-level method; pass IDs as first arg
        const rawLetters = await orm.call("correspondence", "list_letters", [ids]);
        const data = (rawLetters || []).map((l) => LetterDAO._cleanLetter(l));
        return { data, total };
    },

    /**
     * List all IDs matching params (for select-all).
     * @param {Object} orm
     * @param {Object} params
     * @returns {Promise<number[]>}
     */
    async listIds(orm, params = {}) {
        const domain = LetterDAO._buildDomain(params.search || []);
        domain.push(["state", "=", "Global Partner translation queue"]);
        return orm.search("correspondence", domain);
    },

    /**
     * Save (update) a translation in progress.
     * @param {Object} orm
     * @param {Object} letter
     * @returns {Promise<boolean>}
     */
    async update(orm, letter) {
        return orm.call("correspondence", "save_translation", [
            [letter.id],
            letter.translatedElements,
            letter.translatorId || false,
        ]);
    },

    /**
     * Submit a completed translation.
     * @param {Object} orm
     * @param {Object} letter
     * @returns {Promise<boolean>}
     */
    async submit(orm, letter) {
        return orm.call("correspondence", "submit_translation", [
            [letter.id],
            letter.translatedElements,
            letter.translatorId || false,
        ]);
    },

    /**
     * Report an issue with a letter.
     * @param {Object} orm
     * @param {number} letterId
     * @param {string} issueType
     * @param {string} message
     * @returns {Promise<boolean>}
     */
    async reportIssue(orm, letterId, issueType, message) {
        return orm.call("correspondence", "raise_translation_issue", [
            [parseInt(letterId, 10)],
            issueType,
            message,
        ]);
    },

    /**
     * Reply to translator comments on a letter.
     * @param {Object} orm
     * @param {Object} letter
     * @param {string} html
     * @returns {Promise<boolean>}
     */
    async replyToComments(orm, letter, html) {
        return orm.call("correspondence", "reply_to_comments", [[letter.id], html]);
    },

    /**
     * Mark all comments as read.
     * @param {Object} orm
     * @param {Object} letter
     * @returns {Promise<boolean>}
     */
    async markCommentsAsRead(orm, letter) {
        return orm.call("correspondence", "mark_comments_read", [[letter.id]]);
    },

    /**
     * Put a letter back into the translation queue (resubmit).
     * @param {Object} orm
     * @param {Object} letter
     * @returns {Promise<boolean>}
     */
    async makeTranslatable(orm, letter) {
        return orm.call("correspondence", "action_resubmit_to_translation", [[letter.id]]);
    },

    /**
     * Remove a letter from the translation queue.
     * @param {Object} orm
     * @param {Object} letter
     * @returns {Promise<boolean>}
     */
    async deleteLetter(orm, letter) {
        return orm.call("correspondence", "action_remove_local_translate", [[letter.id]]);
    },

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    /**
     * Map the frontend search params to an Odoo domain.
     * @param {Array} search - [{column, term, operator}]
     * @returns {Array}
     */
    _buildDomain(search) {
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
        for (const item of search) {
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
     * @returns {string}
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
            lastUpdate: letter.lastUpdate && letter.lastUpdate !== "None"
                ? new Date(letter.lastUpdate)
                : undefined,
            translatorId: letter.translatorId !== "None" ? letter.translatorId : undefined,
            translatedElements: letter.translatedElements !== "None"
                ? letter.translatedElements
                : [],
            priority: parseInt(letter.priority, 10) || 0,
        };
    },
};

export default LetterDAO;
