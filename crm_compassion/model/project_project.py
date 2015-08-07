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

from openerp import api, models, fields, exceptions, _


class project_project(models.Model):
    _inherit = "project.project"

    project_type = fields.Selection([
        ('stand', _("Stand")),
        ('concert', _("Concert")),
        ('presentation', _("Presentation")),
        ('meeting', _("Meeting")),
        ('sport', _("Sport event")),
        ('marketing', _("Marketing campaign"))], 'Type')

    @api.onchange('project_type')
    def on_change_type(self):
        """ Set the parent analytic account. """
        if self.project_type == 'marketing':
            parent_id = self.env.ref(
                'sponsorship_compassion.account_analytic_account_campaign').id
            self.parent_id = parent_id

    @api.model
    def create(self, vals):
        type = vals.get('project_type')
        if type in ('stand', 'concert', 'presentation', 'meeting',
                    'sport') and not self.env.context.get('from_event'):
            raise exceptions.Warning(
                _("Type not allowed for creation"),
                _("Please create an event. It will automatically create "
                  "an associated Project for the event."))
        project = super(project_project, self).create(vals)
        project.analytic_account_id.write({
            'use_timesheets': True,
            'manager_id': project.user_id.id})
        if type == 'marketing':
            # Create an origin for contracts
            self.env['recurring.contract.origin'].create({
                'type': 'marketing',
                'partner_id': project.partner_id.id,
                'analytic_id': project.analytic_account_id.id})
        return project

    @api.multi
    def write(self, vals):
        """ Push the changes to linked events and to analytic account. """
        super(project_project, self).write(vals)
        if 'project_type' in vals and not self.env.context.get('from_event'):
            raise exceptions.Warning(
                _("Type cannot be changed"),
                _("You cannot change the type of the project."))
        return True
