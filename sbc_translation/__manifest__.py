##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#                            in Jesus' name
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# pylint: disable=C8101
{
    "name": "SBC Translation Platform",
    "version": "18.0.1.0.0",
    "category": "Compassion",
    "summary": "SBC - Translation Platform",
    "sequence": 150,
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": ["sbc_compassion", "partner_contact_birthdate", "portal"],
    "assets": {
        "web.assets_frontend": [
            "sbc_translation/static/src/translation_platform.css",
            "sbc_translation/static/src/rpc.esm.js",
            "sbc_translation/static/src/notification.esm.js",
            "sbc_translation/static/src/models/letter_dao.esm.js",
            "sbc_translation/static/src/models/translator_dao.esm.js",
            "sbc_translation/static/src/models/settings_dao.esm.js",
            # Component XML templates (must be loaded before the JS classes)
            "sbc_translation/static/src/components/tp_loader.xml",
            "sbc_translation/static/src/components/tp_modal.xml",
            "sbc_translation/static/src/components/tp_signal_problem.xml",
            "sbc_translation/static/src/components/tp_child_modal.xml",
            "sbc_translation/static/src/components/tp_translator_button.xml",
            "sbc_translation/static/src/components/tp_content_editor.xml",
            "sbc_translation/static/src/components/tp_letter_viewer.xml",
            "sbc_translation/static/src/components/tp_languages_pick_modal.xml",
            # Component JS
            "sbc_translation/static/src/components/tp_loader.esm.js",
            "sbc_translation/static/src/components/tp_modal.esm.js",
            "sbc_translation/static/src/components/tp_signal_problem.esm.js",
            "sbc_translation/static/src/components/tp_child_modal.esm.js",
            "sbc_translation/static/src/components/tp_translator_button.esm.js",
            "sbc_translation/static/src/components/tp_content_editor.esm.js",
            "sbc_translation/static/src/components/tp_letter_viewer.esm.js",
            "sbc_translation/static/src/components/tp_languages_pick_modal.esm.js",
            # Page XML templates
            "sbc_translation/static/src/pages/tp_letters.xml",
            "sbc_translation/static/src/pages/tp_letter_edit.xml",
            "sbc_translation/static/src/pages/tp_home.xml",
            "sbc_translation/static/src/pages/tp_translators.xml",
            # Page JS
            "sbc_translation/static/src/pages/tp_letters.esm.js",
            "sbc_translation/static/src/pages/tp_letter_edit.esm.js",
            "sbc_translation/static/src/pages/tp_home.esm.js",
            "sbc_translation/static/src/pages/tp_translators.esm.js",
            # Root app XML template and JS entry point
            "sbc_translation/static/src/translation_platform.xml",
            "sbc_translation/static/src/translation_platform.esm.js",
        ],
    },
    "data": [
        "security/ir_groups.xml",
        "security/ir.model.access.csv",
        "security/access_rules.xml",
        "wizards/reply_to_comments_view.xml",
        "wizards/reply_to_issue_view.xml",
        "wizards/translation_letter_counting_view.xml",
        "data/mail_template.xml",
        "data/update_translation_priority_cron.xml",
        "data/queue_job.xml",
        "templates/portal_templates.xml",
        "views/translation_user_view.xml",
        "views/correspondence_view.xml",
        "views/translation_pool_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
