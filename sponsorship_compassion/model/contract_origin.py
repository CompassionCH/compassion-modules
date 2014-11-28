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


class contract_origin(orm.Model):

    """ Origin of a contract """
    _name = 'recurring.contract.origin'

    def _get_origin_types(self, cr, uid, context=None):
        return [
            ('partner', _("Contact with sponsor/ambassador")),
            ('event', _("Event")),
            ('marketing', _("Marketing campaign")),
            ('sub', _("SUB sponsorship")),
            ('transfer', _("Transfer")),
            ('already_sponsor', _("Is already sponsor")),
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
            name = origin.partner_id.name
        elif origin.type in ('event', 'marketing'):
            name = origin.analytic_id.name
        elif origin.type == 'sub':
            if origin.contract_id:
                name = 'SUB Sponsorship - {0} ({1})'.format(
                    origin.contract_id.child_id.code,
                    origin.contract_id.end_date)
            else:
                name = 'SUB Sponsorship'
        elif origin.type == 'transfer':
            if origin.country_id:
                name = 'Transfer from ' + origin.country_id.name
            else:
                name = 'Transfer from partner country'
        elif origin.type == 'already_sponsor':
            name = 'Was already a sponsor'
        elif origin.type == 'other':
            name = origin.other_name or 'Other...'
        return name

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
            " * SUB sponsorship : new sponsorship to replace a finished one."
            " * Transfer : sponsorship transferred from another country."
            " * Is already sponsor : the sponsor wanted a new sponsorship."
            " * Other : select only if none other type matches."
        ), required=True),
        'partner_id': fields.many2one('res.partner', _("Partner")),
        'analytic_id': fields.many2one('account.analytic.account',
                                       _("Analytic Account")),
        'contract_ids': fields.one2many(
            'recurring.contract', 'origin_id', _("Contracts originated"),
            readonly=True),
        'contract_id': fields.many2one('recurring.contract',
                                       _("Previous sponsorship")),
        'country_id': fields.many2one('res.country', _("Country")),
        'other_name': fields.char(_("Give details"), size=128),
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
        except Error:
            # Find the origin
            found_id = self.search(cr, uid, [
                ('type', '=', vals.get('type')),
                ('partner_id', '=', vals.get('type')),
                ('analytic_id', '=', vals.get('type')),
                ('contract_id', '=', vals.get('type')),
                ('country_id', '=', vals.get('type')),
                ('other_name', '=', vals.get('type')),
            ], context=context)
            if found_id:
                id = found_id[0]
            else:
                raise
        return id
