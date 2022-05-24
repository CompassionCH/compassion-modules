##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
# pylint: disable=C8101
{
    "name": "Compassion SMS Sponsorships",
    "version": "12.0.1.0.0",
    "category": "Other",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "depends": [
        "crm_compassion",  # compassion-modules
        "cms_form_compassion",  # compassion-modules
        "base_phone",  # OCA/connector_telephony
        "stock",  # source/addons
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/access_rules.xml",
        "data/sms_crons.xml",
        "data/utm_medium.xml",
        "data/queue_job.xml",
        "views/event_compassion_view.xml",
        "views/hold_view.xml",
        "views/sms_child_request_view.xml",
        "views/notification_settings_view.xml",
        "templates/assets.xml",
        "templates/sms_registration_confirmation_template.xml",
    ],
    "installable": True,
    "auto_install": False,
}
