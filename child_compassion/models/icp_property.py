# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import api, models, fields, _


class ICPProperty(models.TransientModel):
    """ An ICP property is a class linked to projects to describe
    the project hobbies/activities/etc... in several languages. """
    _name = 'icp.property'
    _inherit = 'connect.multipicklist'
    res_model = 'compassion.project'
    value = fields.Char(translate=True)


class ProjectInvolvement(models.Model):
    _inherit = 'icp.property'
    _name = 'icp.involvement'
    _description = 'ICP Involvement'
    res_field = 'involvement_ids'


class ChurchMinistry(models.Model):
    _name = 'icp.church.ministry'
    _inherit = 'icp.property'
    _description = 'ICP Church ministry'
    res_field = 'ministry_ids'


class ICPProgram(models.Model):
    _name = 'icp.program'
    _inherit = 'icp.property'
    _description = 'ICP Program'
    res_field = 'implemented_program_ids'


class ICPChurchFacility(models.Model):
    _name = 'icp.church.facility'
    _inherit = 'icp.property'
    _description = 'ICP Church facility'
    res_field = 'facility_ids'


class ICPMobileDevice(models.Model):
    _name = 'icp.mobile.device'
    _inherit = 'icp.property'
    _description = 'ICP mobile device'
    res_field = 'mobile_device_ids'


class ICPChurchUtility(models.Model):
    _name = 'icp.church.utility'
    _inherit = 'icp.property'
    _description = 'ICP Church utility'
    res_field = 'utility_ids'


class ICPSpiritualActivity(models.Model):
    _name = 'icp.spiritual.activity'
    _inherit = 'icp.property'
    _description = 'ICP spiritual activity'


class ICPCognitiveActivity(models.Model):
    _name = 'icp.cognitive.activity'
    _inherit = 'icp.property'
    _description = 'ICP cognitive activity'


class ICPPhysicalActivity(models.Model):
    _name = 'icp.physical.activity'
    _inherit = 'icp.property'
    _description = 'ICP physical activity'


class ICPSociologicalActivity(models.Model):
    _name = 'icp.sociological.activity'
    _inherit = 'icp.property'
    _description = 'ICP sociological activity'


class ICPCommunityOccupation(models.Model):
    _name = 'icp.community.occupation'
    _inherit = 'icp.property'
    _description = 'ICP Community occupation'
    res_field = 'primary_adults_occupation_ids'


class ICPSchoolCost(models.Model):
    _name = 'icp.school.cost'
    _inherit = 'icp.property'
    _description = 'ICP School costs'
    res_field = 'school_cost_paid_ids'


class ConnectMonth(models.Model):
    _name = 'connect.month'
    _inherit = 'connect.multipicklist'
    _description = 'Connect month'

    name = fields.Char(translate=True)

    @api.model
    def get_months_selection(self):
        return [
            ('Jan', _('January')),
            ('Feb', _('February')),
            ('Mar', _('March')),
            ('Apr', _('April')),
            ('May', _('May')),
            ('Jun', _('June')),
            ('Jul', _('July')),
            ('Aug', _('August')),
            ('Sep', _('September')),
            ('Oct', _('October')),
            ('Nov', _('November')),
            ('Dec', _('December')),
        ]


class ICPDiet(models.Model):
    _name = 'icp.diet'
    _inherit = 'icp.property'
    _description = 'ICP Diet'
    res_field = 'primary_diet_ids'
