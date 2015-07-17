# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, fields, models, _

# fields that are synced if 'use_parent_address' is checked
ADDRESS_FIELDS = [
    'street', 'street2', 'street3', 'zip', 'city', 'state_id', 'country_id']


class ResPartner(models.Model):
    """ This class upgrade the partners to match Compassion needs.
    """

    _inherit = 'res.partner'

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################

    ref = fields.Char(default=lambda self: self.env[
        'ir.sequence'].get('partner.ref'))
    street3 = fields.Char("Street3", size=128)
    member_ids = fields.One2many(
        'res.partner', 'church_id', 'Members',
        domain=[('active', '=', True)])
    is_church = fields.Boolean(
        string="Is a Church", compute='_is_church', store=True)
    church_id = fields.Many2one(
        'res.partner', 'Church', domain=[('is_church', '=', True)])
    church_unlinked = fields.Char(
        "Church (N/A)",
        help=_("Use this field if the church of the partner"
               " can not correctly be determined and linked."))
    deathdate = fields.Date('Death date')
    birthdate = fields.Date('Birthdate')
    lang = fields.Selection(
        '_lang_get', string='Language', required=True,
        help="If the selected language is loaded in the system, all "
        "documents related to this contact will be printed in this "
        "language. If not, it will be English.")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.model
    def _lang_get(self):
        lang_obj = self.env['res.lang']
        ids = lang_obj.search([])
        res = ids.read(['code', 'name'])
        return [(r['code'], r['name']) for r in res]

    @api.multi
    def _is_church(self):
        """ Tell if the given Partners are Church Partners
            (by looking at their categories). """

        # Retrieve all the categories and check if one is Church
        for record in self:
            record.is_church = False
            for category in record.category_id:
                if category.name.upper() in ('CHURCH', 'EGLISE', 'KIRCHE'):
                    record.is_church = True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    @api.multi
    def _display_address(self, address, without_company=False):
        """ Build and return an address formatted accordingly to
        Compassion standards.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country
                  habits (or the default ones if not country is specified)
        :rtype: string
        """

        # get the information that will be injected into the display format
        # get the address format
        address_format = "%(street)s\n%(street2)s\n%(street3)s\n%(city)s " \
                         "%(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'state_code': address.state_id and address.state_id.code or '',
            'state_name': address.state_id and address.state_id.name or '',
            'country_code':
            address.country_id and address.country_id.code or '',
            'country_name':
            address.country_id and address.country_id.name or '',
            'company_name':
            address.parent_id and address.parent_id.name or '',
        }

        for field in ADDRESS_FIELDS:
            args[field] = getattr(address, field) or ''

        if without_company:
            args['company_name'] = ''
        elif address.parent_id:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args
