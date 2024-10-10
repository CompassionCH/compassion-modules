from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(
        env,
        [("correspondence", "correspondence", "letter_image", "sponsor_letter_scan")],
    )
    # Avoids computation of existing pages. The image will be fetched as needed.
    openupgrade.add_fields(
        env,
        [
            (
                "cloudinary_original_page_url",
                "correspondence.page",
                "correspondence_page",
                "char",
                False,
                "sbc_compassion",
                False,
            ),
            (
                "cloudinary_final_page_url",
                "correspondence.page",
                "correspondence_page",
                "char",
                False,
                "sbc_compassion",
                False,
            ),
            (
                "width",
                "correspondence.text.box",
                "correspondence_text_box",
                "float",
                False,
                "sbc_compassion",
                False,
            ),
            (
                "height",
                "correspondence.text.box",
                "correspondence_text_box",
                "float",
                False,
                "sbc_compassion",
                False,
            ),
        ],
    )
    # Update correspondence template boxes coordinates (from millimeters to percents)
    env.cr.execute(
        """
            UPDATE correspondence_text_box
            SET text_line_height = 24,
                width = (x_max - x_min) / 210 * 100,
                height = (y_max - y_min) / 297 * 100,
                x_min = x_min / 210 * 100,
                y_min = y_min / 297 * 100
        """
    )
