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
from openerp.osv import fields, orm
from openerp.tools.translate import _

# fields that are synced if 'use_parent_address' is checked
ADDRESS_FIELDS = [
    'street', 'street2', 'street3', 'zip', 'city', 'state_id', 'country_id']


class ResPartner(orm.Model):
    """ This class upgrade the partners to match Compassion needs.
    """

    _inherit = 'res.partner'

    def _lang_get(self, cr, uid, context=None):
        lang_obj = self.pool.get('res.lang')
        ids = lang_obj.search(cr, uid, [], context=context)
        res = lang_obj.read(cr, uid, ids, ['code', 'name'], context)
        return [(r['code'], r['name']) for r in res]

    def _is_church(self, cr, uid, ids, field_name, arg, context=None):
        """ Tell if the given Partners are Church Partners
            (by looking at their categories). """
        # Set the default return value to False
        res = dict.fromkeys(ids, False)

        # Retrieve all the categories and check if one is Church
        for record in self.browse(cr, uid, ids, context):
            for category in record.category_id:
                if category.name.upper() in ('CHURCH', 'EGLISE', 'KIRCHE'):
                    res[record.id] = True

        return res

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################
    _columns = {
        'street3': fields.char("Street3", size=128),
        'member_ids': fields.one2many(
            'res.partner', 'church_id', 'Members',
            domain=[('active', '=', True)]),
        'is_church': fields.function(
            _is_church, type='boolean', method=True, string="Is a Church",
            store={'res.partner': (
                lambda self, cr, uid, ids, context=None: ids,
                ['category_id'],
                10)}
            ),
        'church_id': fields.many2one(
            'res.partner', 'Church', domain=[('is_church', '=', True)]),
        'church_unlinked': fields.char(
            _("Church (N/A)"),
            help=_("Use this field if the church of the partner"
                   " can not correctly be determined and linked.")),
        'deathdate': fields.date(_('Death date')),
        'birthdate': fields.date(_('Birthdate')),
        'lang': fields.selection(
            _lang_get,
            'Language',
            required=True,
            help="If the selected language is loaded in the system, all "
            "documents related to this contact will be printed in this "
            "language. If not, it will be English."),
    }

    _defaults = {
        'ref': lambda self, cr, uid, context=None: self.pool.get(
            'ir.sequence').get(cr, uid, 'partner.ref'),
    }

    def _display_address(self, cr, uid, address, without_company=False,
                         context=None):
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
