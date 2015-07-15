# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
from psycopg2 import IntegrityError


class contract_origin(orm.Model):
    """ Origin of a contract """
    _name = 'recurring.contract.origin'

    def _get_origin_types(self, cr, uid, context=None):
        return [
            ('partner', _("Contact with sponsor/ambassador")),
            ('event', _("Event")),
            ('marketing', _("Marketing campaign")),
            ('sub', _("SUB Sponsorship")),
            ('transfer', _("Transfer")),
            ('other', _("Other")),
        ]

    def _define_name(self, cr, uid, ids, field_name, args, context=None):
        """ Returns a good name for related fields. """
        if not isinstance(ids, list):
            ids = [ids]
        return {origin.id: self._name_get(origin)
                for origin in self.browse(cr, uid, ids, context)}

    def _name_get(self, origin):
        name = ""
        if origin.type == 'partner':
            if origin.partner_id.parent_id:
                name = origin.partner_id.parent_id.name + ", "
            name += origin.partner_id.name
        elif origin.type in ('event', 'marketing'):
            name = origin.analytic_id.name
        elif origin.type == 'transfer':
            if origin.country_id:
                name = 'Transfer from ' + origin.country_id.name
            else:
                name = 'Transfer from partner country'
        elif origin.type == 'other':
            name = origin.other_name or 'Other'
        elif origin.type == 'sub':
            name = 'SUB Sponsorship'

        return name

    def _get_won_sponsorships(self, cr, uid, ids, field, arg, context=None):
        res = dict()
        if not isinstance(ids, list):
            ids = [ids]
        for origin in self.browse(cr, uid, ids, context):
            contract_ids = [contract.id for contract in origin.contract_ids
                            if contract.state in ('active', 'terminated')]
            res[origin.id] = len(contract_ids)
        return res

    def _get_origin_from_contract(contract_obj, cr, uid, ids, context=None):
        res = []
        for contract in contract_obj.browse(cr, uid, ids, context):
            if contract.state == 'active' and contract.origin_id:
                res.append(contract.origin_id.id)
        return res

    _columns = {
        'name': fields.function(_define_name, type="char", string=_("Name"),
                                store=True),
        'type': fields.selection(_get_origin_types, _("Type"), help=_(
            "Origin of contract : "
            " * Contact with sponsor/ambassador : an other sponsor told the "
            "person about Compassion."
            " * Event : sponsorship was made during an event"
            " * Marketing campaign : sponsorship was made after specific "
            "campaign (magazine, ad, etc..)"
            " * Transfer : sponsorship transferred from another country."
            " * Other : select only if none other type matches."
        ), required=True),
        'partner_id': fields.many2one('res.partner', _("Partner")),
        'analytic_id': fields.many2one('account.analytic.account',
                                       _("Analytic Account")),
        'contract_ids': fields.one2many(
            'recurring.contract', 'origin_id', _("Sponsorships originated"),
            readonly=True),
        'country_id': fields.many2one('res.country', _("Country")),
        'other_name': fields.char(_("Give details"), size=128),
        'won_sponsorships': fields.function(
            _get_won_sponsorships, type="integer",
            string=_("Won sponsorships"), store={
                'recurring.contract': (
                    _get_origin_from_contract,
                    ['state', 'origin_id'],
                    10)}),
    }

    _sql_constraints = [(
        'name_uniq', 'UNIQUE(name)',
        _("You cannot have two origins with same name."
          "The origin does probably already exist.")
    )]

    def create(self, cr, uid, vals, context=None):
        """Try to find existing origin instead of raising an error."""
        try:
            id = super(contract_origin, self).create(cr, uid, vals, context)
        except IntegrityError:
            # Find the origin
            cr.commit()     # Release the lock
            found_id = self.search(cr, uid, [
                ('type', '=', vals.get('type')),
                ('partner_id', '=', vals.get('partner_id')),
                ('analytic_id', '=', vals.get('analytic_id')),
                ('country_id', '=', vals.get('country_id')),
                ('other_name', '=', vals.get('other_name')),
            ], context=context)
            if found_id:
                id = found_id[0]
            else:
                raise
        return id
