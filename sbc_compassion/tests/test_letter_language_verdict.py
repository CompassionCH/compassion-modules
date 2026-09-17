##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.tests import TransactionCase

SHORT_CAPTION = "Salut, C'est Martial. Juste un bonjour!"
LONG_ENGLISH = (
    "Dear sponsor, thank you very much for your letter and for the gift you "
    "sent me. I am doing well at school. God bless you."
)
LONG_SWAHILI = (
    "Habari yako mlezi wangu, asante sana kwa barua yako na zawadi "
    "uliyonitumia. Mimi ni mzima wa afya. Mungu akubariki sana."
)


class TestLetterLanguageVerdict(TransactionCase):
    """Pins the verdict the B2S translation gate is built on (T3339 / T3371).

    Covers `_letter_language_verdict` only. `_sponsor_can_read_letter` needs a
    persisted letter, because `supporter_languages_ids` is related to
    `partner_id.spoken_lang_ids` and comes back NewId-wrapped on an in-memory
    record, and building one needs `BaseSponsorshipTest`, whose `setUpClass` is
    currently broken for all 13 test classes that use it.
    """

    def _letter(self, text, field="translated_text"):
        return self.env["correspondence"].new(
            {"page_ids": [(0, 0, {"paragraph_ids": [(0, 0, {field: text})]})]}
        )

    def test_short_text_gives_no_opinion(self):
        """Photo captions are too short to judge: the gate must fall back."""
        language, has_opinion = self._letter(SHORT_CAPTION)._letter_language_verdict()
        self.assertFalse(language)
        self.assertFalse(has_opinion)

    def test_long_text_is_detected(self):
        language, has_opinion = self._letter(LONG_ENGLISH)._letter_language_verdict()
        self.assertTrue(has_opinion)
        self.assertEqual(
            language, self.env.ref("advanced_translation.lang_compassion_english")
        )

    def test_long_untranslatable_text_still_gives_an_opinion(self):
        """A language we do not handle is an answer, not an absence of one.

        Without this the letter falls back to the field-office stamp and can
        reach the sponsor untranslated (T3339).
        """
        letter = self._letter(LONG_SWAHILI, field="original_text")
        language, has_opinion = letter._letter_language_verdict()
        self.assertFalse(language)
        self.assertTrue(has_opinion)
