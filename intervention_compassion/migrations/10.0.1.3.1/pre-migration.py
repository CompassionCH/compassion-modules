# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    openupgrade.rename_tables(cr, [
        ('icp_interventions', 'fcp_interventions'),
        ('icp_global_interventions', 'fcp_global_interventions'),
        ('compassion_intervention_search_icp',
         'compassion_intervention_search_fcp'),
    ])
    openupgrade.rename_columns(cr, {
        'fcp_interventions': [('icp_id', 'fcp_id')],
        'compassion_intervention_search_fcp': [('icp_id', 'fcp_id')],
        'fcp_global_interventions': [('icp_id', 'fcp_id')],
        'intervention_spiritual_activities': [
            ('icp_spiritual_activity_id', 'fcp_spiritual_activity_id')],
        'intervention_cognitive_activities': [
            ('icp_cognitive_activity_id', 'fcp_cognitive_activity_id')],
        'intervention_physical_activities': [
            ('icp_physical_activity_id', 'fcp_physical_activity_id')],
        'intervention_socio_activities': [
            ('icp_sociological_activity_id', 'fcp_sociological_activity_id')],
    })
