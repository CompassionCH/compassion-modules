/** @odoo-module */

/**
 * Settings DAO - data access for translation competences and letter issues.
 * All methods take `orm` (the Odoo ORM service) as first argument.
 */

export const SettingsDAO = {
    /**
     * Fetch all translation competences (language pairs).
     * @param {Object} orm
     * @returns {Promise<Array<{id: number, source: string, target: string}>>}
     */
    async translationCompetences(orm) {
        const raw = await orm.searchRead(
            "translation.competence",
            [],
            ["source_language_id", "dest_language_id"]
        );
        return (raw || []).map((it) => ({
            id: it.id,
            source: it.source_language_id[1],
            target: it.dest_language_id[1],
        }));
    },

    /**
     * Fetch all unique languages (sources + targets combined).
     * @param {Object} orm
     * @returns {Promise<string[]>}
     */
    async languages(orm) {
        const competences = await SettingsDAO.translationCompetences(orm);
        const langs = competences.flatMap((c) => [c.source, c.target]);
        return [...new Set(langs)];
    },

    /**
     * Fetch the list of possible letter issue types.
     * @param {Object} orm
     * @returns {Promise<Array<{id: string, text: string}>>}
     */
    async letterIssues(orm) {
        const raw = await orm.call("correspondence", "get_translation_issue_list", []);
        return (raw || []).map(([id, text]) => ({ id, text }));
    },
};

export default SettingsDAO;
