# author Quentin Gigon <gigon.quentin@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):

    openupgrade.rename_xmlids(
        env.cr,
        [('recurring_contract.recurring_invoicer_cron',
          'sponsorship_compassion.recurring_invoicer_cron'),
         ('recurring_contract.menu_recurring_contract_form',
          'sponsorship_compassion.menu_recurring_contract_form'),
         ('recurring_contract.menu_invoice_automatic_generation',
          'sponsorship_compassion.menu_invoice_automatic_generation'),
         ('recurring_contract.menu_recurring_invoicer_form',
          'sponsorship_compassion.menu_recurring_invoicer_form'),
         ('recurring_contract.menu_contracts_section',
          'sponsorship_compassion.menu_contracts_section')
         ])

    openupgrade.rename_columns(env.cr, {
        'crm_lead_res_partner_industry_rel': [
            ('res_partner_sector_id', 'res_partner_industry_id'),
        ],
    })
