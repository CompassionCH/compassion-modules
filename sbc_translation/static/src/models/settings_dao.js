/** @odoo-module */

import { searchRead, call } from "../rpc";

/**
 * Settings DAO - data access for translation competences and letter issues.
 * Uses direct JSON-RPC (portal/frontend compatible).
 */

export const SettingsDAO = {
  /**
   * Fetch all translation competences (language pairs).
   * @returns {Promise<Array<{id: number, source: string, target: string}>>}
   */
  async translationCompetences() {
    const raw = await searchRead(
      "translation.competence",
      [],
      ["source_language_id", "dest_language_id"],
    );
    return (raw || []).map((it) => ({
      id: it.id,
      source: it.source_language_id[1],
      target: it.dest_language_id[1],
    }));
  },

  /**
   * Fetch all unique languages (sources + targets combined).
   * @returns {Promise<string[]>}
   */
  async languages() {
    const competences = await SettingsDAO.translationCompetences();
    const langs = competences.flatMap((c) => [c.source, c.target]);
    return [...new Set(langs)];
  },

  /**
   * Fetch the list of possible letter issue types.
   * @returns {Promise<Array<{id: string, text: string}>>}
   */
  async letterIssues() {
    const raw = await call(
      "correspondence",
      "get_translation_issue_list",
      [],
    );
    return (raw || []).map(([id, text]) => ({ id, text }));
  },
};

export default SettingsDAO;
