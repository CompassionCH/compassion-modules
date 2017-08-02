# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging
import json

from odoo import api, models, fields, _

logger = logging.getLogger(__name__)


class CommunicationDashboard(models.Model):

    _inherit = 'partner.communication.config'
    _description = 'Communication Dashboard'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    @api.multi
    def _kanban_dashboard(self):
        for config in self:
            config.kanban_dashboard = json.dumps(config.get_communication_dashboard_datas())

    @api.multi
    def _kanban_dashboard_graph(self):
        for config in self:
            config.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())

    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')
    kanban_dashboard = fields.Text(compute='_kanban_dashboard')

    @api.multi
    def get_communication_dashboard_datas(self):
        number_in_progress = self.env['partner.communication.job'].search_count([['state', '=', 'pending'], ['config_id.name', '=', self.display_name]])
        number_email = self.env['partner.communication.job'].search_count([['send_mode', '=', 'digital'], ['config_id.name', '=', self.display_name]])
        number_paper = self.env['partner.communication.job'].search_count([['send_mode', '=', 'physical'], ['config_id.name', '=', self.display_name]])
        number_calls = self.env['partner.communication.job'].search_count([['need_call', '=', True], ['user_id', '=', self.env.uid], ['config_id.name', '=', self.display_name]])
        return {
            'number_email': number_email,
            'number_paper': number_paper,
            'number_in_progress' : number_in_progress,
            'number_calls' : number_calls
        }

    @api.multi
    def open_action(self, context={}):
        [action] = self.env.ref('partner_communication.action_communication_tree').read()
        communication_type = context.get('communication_type')
        name = self.display_name + ' - '
        if(communication_type == 'in_progress'):
            name += 'Communications en cours'
            action['domain'] = [('state', '=', 'pending'), ('config_id.name', '=', self.display_name)]
        if(communication_type == 'paper'):
            name += 'Communications papiers'
            action['domain'] = [('send_mode', '=', 'physical'), ('config_id.name', '=', self.display_name)]
        if(communication_type == 'email'):
            name += 'Communications par e-mails'
            action['domain'] = [('send_mode', '=', 'digital'), ('config_id.name', '=', self.display_name)]
        if(communication_type == 'calls'):
            name += 'Appel a faire'
            action['domain'] = [('need_call', '=', True), ('user_id', '=', self.env.uid), ('config_id.name', '=', self.display_name)]
        action['name'] = action['display_name'] = name
        return action

    @api.model
    def get_communication_rubbon_datas(self):
        number_communication = self.env['partner.communication.job'].search_count([])
        return {
            'number_communication': number_communication,
        }