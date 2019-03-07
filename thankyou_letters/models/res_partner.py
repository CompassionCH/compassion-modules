# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import locale
import re
import threading

from contextlib import contextmanager
from datetime import datetime

from odoo import api, models, fields, _

LOCALE_LOCK = threading.Lock()


@contextmanager
def setlocale(name):
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, (name, 'UTF-8'))
        except:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)


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
    gender = fields.Selection(related='title.gender', readonly=True)
    thankyou_preference = fields.Selection(
        '_get_delivery_preference', default='auto_digital', required=True)
    full_name = fields.Char(compute='_compute_full_name')
    short_address = fields.Char(compute='_compute_address')
    date_communication = fields.Char(compute='_compute_date_communication')

    @api.multi
    def _compute_salutation(self):
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
                p.short_salutation = title_salutation + ' ' + partner.firstname
                p.informal_salutation = title_salutation + p.firstname
            else:
                p.salutation = _("Dear friends of ") + \
                    self.env.user.company_id.name
                p.short_salutation = p.salutation

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
        lang_map = {
            'fr_CH': u'le %d %B %Y',
            'fr': u'le %d %B %Y',
            'de_DE': u'%d. %B %Y',
            'de_CH': u'%d. %B %Y',
            'en_US': u'%d %B %Y',
            'it_IT': u'%d %B %Y',
        }
        today = datetime.today()
        city = self.env.user.partner_id.company_id.city
        for partner in self:
            lang = partner.lang
            with setlocale(lang):
                date = today.strftime(
                    lang_map.get(lang, lang_map['en_US'])).decode('utf-8')
                partner.date_communication = city + u", " + date


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


class ResUsers(models.Model):
    _inherit = 'res.users'

    signature_letter = fields.Html(compute='_compute_signature_letter')

    @api.multi
    def _compute_signature_letter(self):
        for user in self:
            employee = user.employee_ids
            signature = ''
            if len(employee) == 1:
                signature = employee.name + '<br/>'
                if employee.department_id:
                    signature += employee.department_id.name + '<br/>'
            signature += user.company_id.name
            user.signature_letter = signature
