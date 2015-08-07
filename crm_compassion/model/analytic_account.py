# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields


class account_analytic_account(models.Model):
    """ Add a type of analytic account related to events. """
    _inherit = 'account.analytic.account'

    event_type = fields.Selection('_get_event_types', 'Event type')
    type = fields.Selection(
        '_get_analytic_types', 'Type of Account', required=True,
        help=("If you select the View Type, it means you won\'t allow to "
              "create journal entries using that account.\n"
              "The type 'Analytic account' stands for usual accounts "
              "that you only want to use in accounting.\n"
              "If you select Contract or Project, it offers you the "
              "possibility to manage the validity and the invoicing "
              "options for this account.\n"
              "The special type 'Template of Contract' allows you to "
              "define a template with default data that you can reuse "
              "easily.\n"
              "The type 'Event' is used for Compassion Events."))

    def _get_event_types(self):
        return self.env['crm.event.compassion'].get_event_types()

    def _get_analytic_types(self):
        return [
            ('view', 'Analytic View'),
            ('normal', 'Analytic Account'),
            ('contract', 'Contract or Project'),
            ('template', 'Template of Contract'),
            ('event', 'Analytic Account for Event')]
