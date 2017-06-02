# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import re
from openerp import api, models, fields, _


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

    salutation = fields.Char(compute='_get_salutation')
    gender = fields.Selection(related='title.gender')
    thankyou_preference = fields.Selection(
        '_get_delivery_preference', default='auto_digital', required=True)
    full_name = fields.Char(compute='_compute_full_name')
    short_address = fields.Char(compute='_compute_address')

    @api.multi
    def _get_salutation(self):
        for p in self:
            partner = p.with_context(lang=p.lang)
            if partner.title and partner.firstname and not partner.is_company:
                title = partner.title
                title_salutation = partner.env['ir.advanced.translation'].get(
                    'salutation', female=title.gender == 'F',
                    plural=title.plural
                ).title()
                title_name = title.name
                p.salutation = title_salutation + ' ' + \
                    title_name + ' ' + partner.lastname
            else:
                p.salutation = _("Dear friends of ") + \
                    self.env.user.company_id.name

    @api.multi
    def _compute_full_name(self):
        for partner in self.filtered('firstname'):
            partner.full_name = partner.firstname + ' ' + partner.lastname

    @api.multi
    def _compute_address(self):
        # Replace line returns
        p = re.compile('\\n+')
        for partner in self:
            t_partner = partner.with_context(lang=partner.lang)
            if not partner.is_company and partner.title.shortcut:
                res = t_partner.title.shortcut + ' '
                if partner.firstname:
                    res += partner.firstname + ' '
                res += partner.lastname + '<br/>'
            else:
                res = partner.name + '<br/>'
            res += t_partner.contact_address
            partner.short_address = p.sub('<br/>', res)


class ResPartnerTitle(models.Model):
    """
    Adds salutation and gender fields.
    """
    _inherit = 'res.partner.title'
    gender = fields.Selection([
        ('M', 'Male'),
        ('F', 'Female'),
    ])
    plural = fields.Boolean()
