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

    openupgrade.rename_models(cr, [
        ('icp.property', 'fcp.property'),
        ('icp.involvement', 'fcp.involvement'),
        ('icp.church.ministry', 'fcp.church.ministry'),
        ('icp.program', 'fcp.program'),
        ('icp.church.facility', 'fcp.church.facility'),
        ('icp.mobile.device', 'fcp.mobile.device'),
        ('icp.church.utility', 'fcp.church.utility'),
        ('icp.spiritual.activity', 'fcp.spiritual.activity'),
        ('icp.cognitive.activity', 'fcp.cognitive.activity'),
        ('icp.physical.activity', 'fcp.physical.activity'),
        ('icp.sociological.activity', 'fcp.sociological.activity'),
        ('icp.community.occupation', 'fcp.community.occupation'),
        ('icp.school.cost', 'fcp.school.cost'),
        ('icp.diet', 'fcp.diet'),
        ('icp.lifecycle.reason', 'fcp.lifecycle.reason'),
        ('icp.suspension.extension.reason', 'fcp.suspension.extension.reason'),
        ('icp.disaster.impact', 'fcp.disaster.impact'),
    ])

    openupgrade.rename_tables(cr, [
        ('icp_property', 'fcp_property'),
        ('icp_involvement', 'fcp_involvement'),
        ('icp_church_ministry', 'fcp_church_ministry'),
        ('icp_program', 'fcp_program'),
        ('icp_church_facility', 'fcp_church_facility'),
        ('icp_mobile_device', 'fcp_mobile_device'),
        ('icp_church_utility', 'fcp_church_utility'),
        ('icp_spiritual_activity', 'fcp_spiritual_activity'),
        ('icp_cognitive_activity', 'fcp_cognitive_activity'),
        ('icp_physical_activity', 'fcp_physical_activity'),
        ('icp_sociological_activity', 'fcp_sociological_activity'),
        ('icp_community_occupation', 'fcp_community_occupation'),
        ('icp_school_cost', 'fcp_school_cost'),
        ('icp_diet', 'fcp_diet'),
        ('icp_lifecycle_reason', 'fcp_lifecycle_reason'),
        ('icp_suspension_extension_reason', 'fcp_suspension_extension_reason'),
        ('icp_disaster_impact', 'fcp_disaster_impact'),
        ('icp_spiritual_baby_act', 'fcp_spiritual_baby_act'),
        ('icp_spiritual_kid_act', 'fcp_spiritual_kid_act'),
        ('icp_spiritual_ado_act', 'fcp_spiritual_ado_act'),
        ('icp_cognitive_baby_act', 'fcp_cognitive_baby_act'),
        ('icp_cognitive_kid_act', 'fcp_cognitive_kid_act'),
        ('icp_cognitive_ado_act', 'fcp_cognitive_ado_act'),
        ('icp_physical_baby_act', 'fcp_physical_baby_act'),
        ('icp_physical_kid_act', 'fcp_physical_kid_act'),
        ('icp_physical_ado_act', 'fcp_physical_ado_act'),
        ('icp_socio_baby_act', 'fcp_socio_baby_act'),
        ('icp_socio_kid_act', 'fcp_socio_kid_act'),
        ('icp_socio_ado_act', 'fcp_socio_ado_act'),
        ('compassion_project_ile_icp_lifecycle_reason_rel',
         'compassion_project_ile_fcp_lifecycle_reason_rel'),
        ('compassion_project_ile_icp_involvement_rel',
         'compassion_project_ile_fcp_involvement_rel'),
    ])

    openupgrade.rename_columns(cr, {
        'fcp_spiritual_baby_act': [('icp_spiritual_activity_id',
                                    'fcp_spiritual_activity_id')],
        'fcp_spiritual_kid_act': [('icp_spiritual_activity_id',
                                   'fcp_spiritual_activity_id')],
        'fcp_spiritual_ado_act': [('icp_spiritual_activity_id',
                                   'fcp_spiritual_activity_id')],
        'fcp_cognitive_baby_act': [('icp_cognitive_activity_id',
                                    'fcp_cognitive_activity_id')],
        'fcp_cognitive_kid_act': [('icp_cognitive_activity_id',
                                   'fcp_cognitive_activity_id')],
        'fcp_cognitive_ado_act': [('icp_cognitive_activity_id',
                                   'fcp_cognitive_activity_id')],
        'fcp_physical_baby_act': [('icp_physical_activity_id',
                                   'fcp_physical_activity_id')],
        'fcp_physical_kid_act': [('icp_physical_activity_id',
                                  'fcp_physical_activity_id')],
        'fcp_physical_ado_act': [('icp_physical_activity_id',
                                  'fcp_physical_activity_id')],
        'fcp_socio_baby_act': [('icp_sociological_activity_id',
                                'fcp_sociological_activity_id')],
        'fcp_socio_kid_act': [('icp_sociological_activity_id',
                               'fcp_sociological_activity_id')],
        'fcp_socio_ado_act': [('icp_sociological_activity_id',
                               'fcp_sociological_activity_id')],
        'compassion_project_ile_fcp_lifecycle_reason_rel': [
            ('icp_lifecycle_reason_id', 'fcp_lifecycle_reason_id')],
        'compassion_project_ile_transition_reason_rel': [
            ('icp_lifecycle_reason_id', 'fcp_lifecycle_reason_id')],
        'compassion_project_ile_fcp_involvement_rel': [
            ('icp_involvement_id', 'fcp_involvement_id')],
    })
