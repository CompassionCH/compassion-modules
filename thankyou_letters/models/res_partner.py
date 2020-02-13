##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' namenoupdate="1"
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from datetime import datetime
from babel.dates import format_date

from odoo import api, models, fields, _


class ResPartner(models.Model):
    """ Add fields for retrieving values for communications.

        - Short address
            Mr. John Doe
            Street
            City
            Country
    """
    _name = 'res.partner'
    _inherit = 'res.partner'

    salutation = fields.Char(compute='_compute_salutation')
    short_salutation = fields.Char(compute='_compute_salutation')
    informal_salutation = fields.Char(compute='_compute_salutation')
    full_salutation = fields.Char(compute='_compute_salutation')
    gender = fields.Selection(related='title.gender', readonly=True)
    thankyou_preference = fields.Selection(
        '_get_delivery_preference', default='auto_digital', required=True)
    full_name = fields.Char(compute='_compute_full_name')
    short_address = fields.Char(compute='_compute_address')
    date_communication = fields.Char(compute='_compute_date_communication')

    @api.multi
    def _compute_salutation(self):
        for partner in self:
            if partner.title and partner.firstname and not partner.is_company:
                title = partner.title
                title_salutation = partner.env['ir.advanced.translation'].get(
                    'salutation', female=title.gender == 'F',
                    plural=title.plural
                ).title()
                title_name = title.name
                partner.salutation = title_salutation + ' ' + \
                    title_name + ' ' + partner.lastname
                partner.short_salutation =\
                    title_salutation + ' ' + partner.firstname
                partner.informal_salutation = title_salutation + ' ' + \
                    partner.firstname
                partner.full_salutation = title_salutation + ' ' + \
                    partner.firstname + ' ' + partner.lastname
            else:
                partner.salutation = _("Dear friends of ") + \
                    self.env.user.company_id.name
                partner.short_salutation = partner.salutation
                partner.informal_salutation = _("Dear friend of ") + \
                    self.env.user.company_id.name
                partner.full_salutation = partner.salutation

    @api.multi
    def _compute_full_name(self):
        for partner in self.filtered('firstname'):
            partner.full_name = partner.firstname + ' ' + partner.lastname

    @api.multi
    def _compute_address(self):
        # Replace line returns
        p = re.compile('\\n+')
        for partner in self:
            res = ''
            t_partner = partner.with_context(lang=partner.lang)
            if not partner.is_company and partner.title.shortcut:
                res = t_partner.title.shortcut + ' '
                if partner.firstname:
                    res += partner.firstname + ' '
                res += partner.lastname + '<br/>'
            res += t_partner.contact_address
            partner.short_address = p.sub('<br/>', res)

    @api.multi
    def _compute_date_communication(self):
        """City and date displayed in the top right of a letter"""
        today = datetime.today()
        city = self.env.user.partner_id.company_id.city
        for partner in self:
            date = format_date(today, format='long', locale=partner.lang)
            formatted_date = f"le {date}" if 'fr' in partner.lang else date
            partner.date_communication = f"{city}, {formatted_date}"


class ResUsers(models.Model):
    _inherit = 'res.users'

    signature_letter = fields.Html(compute='_compute_signature_letter')

    @api.multi
    def _compute_signature_letter(self):
        for user in self:
            employee = user.employee_ids.sudo()
            signature = ''
            if len(employee) == 1:
                signature = employee.name + '<br/>'
                if employee.department_id:
                    signature += employee.department_id.name + '<br/>'
            signature += user.sudo().company_id.name
            user.signature_letter = signature
