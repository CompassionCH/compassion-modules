##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import api, models, fields, _


class FCPProperty(models.AbstractModel):
    """ An FCP property is a class linked to projects to describe
    the project hobbies/activities/etc... in several languages. """

    _name = "fcp.property"
    _inherit = ["connect.multipicklist", "compassion.mapped.model"]
    _description = "FCP Property"

    res_model = "compassion.project"
    value = fields.Char(translate=True)


class ProjectInvolvement(models.Model):
    _inherit = "fcp.property"
    _name = "fcp.involvement"
    _description = "FCP Involvement"
    res_field = "involvement_ids"


class ChurchMinistry(models.Model):
    _name = "fcp.church.ministry"
    _inherit = "fcp.property"
    _description = "FCP Church ministry"
    res_field = "ministry_ids"


class FCPProgram(models.Model):
    _name = "fcp.program"
    _inherit = "fcp.property"
    _description = "FCP Program"
    res_field = "implemented_program_ids"


class FCPChurchFacility(models.Model):
    _name = "fcp.church.facility"
    _inherit = "fcp.property"
    _description = "FCP Church facility"
    res_field = "facility_ids"


class FCPMobileDevice(models.Model):
    _name = "fcp.mobile.device"
    _inherit = "fcp.property"
    _description = "FCP mobile device"
    res_field = "mobile_device_ids"


class FCPChurchUtility(models.Model):
    _name = "fcp.church.utility"
    _inherit = "fcp.property"
    _description = "FCP Church utility"
    res_field = "utility_ids"


class FCPSpiritualActivity(models.Model):
    _name = "fcp.spiritual.activity"
    _inherit = "fcp.property"
    _description = "FCP spiritual activity"
    _order = "name"


class FCPCognitiveActivity(models.Model):
    _name = "fcp.cognitive.activity"
    _inherit = "fcp.property"
    _description = "FCP cognitive activity"
    _order = "name"


class FCPPhysicalActivity(models.Model):
    _name = "fcp.physical.activity"
    _inherit = "fcp.property"
    _description = "FCP physical activity"
    _order = "name"


class FCPSociologicalActivity(models.Model):
    _name = "fcp.sociological.activity"
    _inherit = "fcp.property"
    _description = "FCP sociological activity"
    _order = "name"


class FCPCommunityOccupation(models.Model):
    _name = "fcp.community.occupation"
    _inherit = "fcp.property"
    _description = "FCP Community occupation"
    res_field = "primary_adults_occupation_ids"


class FCPSchoolCost(models.Model):
    _name = "fcp.school.cost"
    _inherit = "fcp.property"
    _description = "FCP School costs"
    res_field = "school_cost_paid_ids"


class ConnectMonth(models.Model):
    _name = "connect.month"
    _inherit = "connect.multipicklist"
    _description = "Connect month"

    name = fields.Char(translate=True)

    @api.model
    def get_months_selection(self):
        return [
            ("Jan", _("January")),
            ("Feb", _("February")),
            ("Mar", _("March")),
            ("Apr", _("April")),
            ("May", _("May")),
            ("Jun", _("June")),
            ("Jul", _("July")),
            ("Aug", _("August")),
            ("Sep", _("September")),
            ("Oct", _("October")),
            ("Nov", _("November")),
            ("Dec", _("December")),
            ("January", _("January")),
            ("February", _("February")),
            ("March", _("March")),
            ("April", _("April")),
            ("May", _("May")),
            ("June", _("June")),
            ("July", _("July")),
            ("August", _("August")),
            ("September", _("September")),
            ("October", _("October")),
            ("November", _("November")),
            ("December", _("December")),
        ]


class FCPDiet(models.Model):
    _name = "fcp.diet"
    _inherit = "fcp.property"
    _description = "FCP Diet"
    res_field = "primary_diet_ids"


class FCPLifecycleReason(models.Model):
    _name = "fcp.lifecycle.reason"
    _inherit = "fcp.property"
    _description = "FCP Lifecycle Reason"
    res_model = "compassion.project.ile"
    res_field = "suspension_reason_ids"


class FCPSuspensionExtensionReason(models.Model):
    _name = "fcp.suspension.extension.reason"
    _inherit = "fcp.property"
    _description = "FCP Suspension Reason"
    res_model = "compassion.project.ile"
    res_field = "extension_1_reason_ids"
