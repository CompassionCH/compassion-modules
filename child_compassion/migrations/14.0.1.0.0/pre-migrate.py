from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.rename_xmlids(
        cr,
        [
            (
                "partner_communication_switzerland.child_him_en",
                "child_compassion.child_him",
            ),
            ("child_switzerland.child_he_en", "child_compassion.child_he"),
            ("child_switzerland.child_his_en", "child_compassion.child_his"),
            (
                "partner_communication_switzerland.child_child_en",
                "child_compassion.child_child",
            ),
            (
                "partner_compassion.savvy_stewards",
                "partner_segmentation.savvy_stewards",
            ),
            (
                "partner_compassion.movement_mobilizers",
                "partner_segmentation.movement_mobilizers",
            ),
            (
                "partner_compassion.compassionate_caregiver",
                "partner_segmentation.compassionate_caregiver",
            ),
            (
                "partner_compassion.hands_on_helpers",
                "partner_segmentation.hands_on_helpers",
            ),
            (
                "partner_compassion.curious_novices",
                "partner_segmentation.curious_novices",
            ),
            (
                "partner_compassion.partner_segmentation_survey",
                "partner_segmentation.partner_segmentation_survey",
            ),
            (
                "partner_compassion.pss_question_1",
                "partner_segmentation.pss_question_1",
            ),
            (
                "partner_compassion.pss_question_2",
                "partner_segmentation.pss_question_2",
            ),
            (
                "partner_compassion.pss_question_3",
                "partner_segmentation.pss_question_3",
            ),
            (
                "partner_compassion.pss_question_4",
                "partner_segmentation.pss_question_4",
            ),
            (
                "partner_compassion.pss_question_5",
                "partner_segmentation.pss_question_5",
            ),
            (
                "partner_compassion.pss_question_6",
                "partner_segmentation.pss_question_6",
            ),
            (
                "partner_compassion.pss_question_7",
                "partner_segmentation.pss_question_7",
            ),
        ],
    )
    openupgrade.logged_query(
        cr,
        """
        update ir_model_data set module='partner_segmentation'
        where module='partner_compassion' and model like 'survey%';
       """,
    )
