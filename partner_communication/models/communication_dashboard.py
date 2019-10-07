
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import json

from odoo import api, models, fields, _

logger = logging.getLogger(__name__)


class CommunicationDashboard(models.Model):

    _inherit = 'partner.communication.config'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    @api.multi
    def _compute_kanban_dashboard(self):
        for config in self:
            config.kanban_dashboard = json.dumps(
                config.get_communication_dashboard_datas())

    @api.multi
    def _compute_kanban_dashboard_graph(self):
        for config in self:
            config.kanban_dashboard_graph = json.dumps(
                self.get_bar_graph_datas())

    kanban_dashboard_graph = fields.Text(
        compute='_compute_kanban_dashboard_graph')
    kanban_dashboard = fields.Text(compute='_compute_kanban_dashboard')

    @api.multi
    def get_communication_dashboard_datas(self):
        job_obj = self.env['partner.communication.job']
        number_in_progress = job_obj.search_count([
            ['state', '=', 'pending'],
            ['config_id.name', '=', self.display_name]
        ])
        number_email = job_obj.search_count([
            ['send_mode', '=', 'digital'],
            ['config_id.name', '=', self.display_name]
        ])
        number_paper = job_obj.search_count([
            ['send_mode', '=', 'physical'],
            ['config_id.name', '=', self.display_name]
        ])
        number_calls = job_obj.search_count([
            ['need_call', '=', True],
            ['user_id', '=', self.env.uid],
            ['config_id.name', '=', self.display_name]
        ])
        return {
            'number_email': number_email,
            'number_paper': number_paper,
            'number_in_progress': number_in_progress,
            'number_calls': number_calls
        }

    @api.multi
    def open_action(self):
        [action] = self.env.ref(
            'partner_communication.action_communication_tree').read()
        communication_type = self.env.context.get('communication_type')
        name = self.display_name + ' - '
        if communication_type == 'in_progress':
            name += _('Pending communications')
            action['domain'] = [('state', '=', 'pending'),
                                ('config_id.name', '=', self.display_name)]
        if communication_type == 'paper':
            name += _('Print jobs')
            action['domain'] = [
                ('send_mode', '=', 'physical'),
                ('state', '=', 'pending'),
                ('config_id.name', '=', self.display_name)
            ]
        if communication_type == 'email':
            name += _('E-mail jobs')
            action['domain'] = [
                ('state', '=', 'pending'),
                ('send_mode', '=', 'digital'),
                ('config_id.name', '=', self.display_name)
            ]
        if communication_type == 'calls':
            name += _('Pending calls')
            action['domain'] = [
                ('need_call', '=', True),
                ('user_id', '=', self.env.uid),
                ('config_id.name', '=', self.display_name)
            ]
        action['name'] = action['display_name'] = name
        return action

    @api.model
    def get_communication_rubbon_datas(self):
        nb_communication = self.env[
            'partner.communication.job'].search_count([])
        return {
            'number_communication': nb_communication,
        }
