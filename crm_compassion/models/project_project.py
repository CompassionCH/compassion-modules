##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields, exceptions, _


class Project(models.Model):
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
        """ Set the analytic tag. """
        if self.project_type == 'marketing':
            tag_id = self.env.ref(
                'crm_compassion.tag_campaign')
            self.tag_ids += tag_id

    @api.model
    def create(self, vals):
        type = vals.get('project_type')
        if type in ('stand', 'concert', 'presentation', 'meeting',
                    'sport') and not self.env.context.get('from_event'):
            raise exceptions.UserError(
                _("Please create an event. It will automatically create "
                  "an associated Project for the event."))
        project = super().create(vals)
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
        super().write(vals)
        if 'project_type' in vals and not self.env.context.get('from_event'):
            raise exceptions.UserError(
                _("You cannot change the type of the project."))
        return True
