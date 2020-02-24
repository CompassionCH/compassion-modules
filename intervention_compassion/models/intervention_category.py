##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, _


class InterventionCategory(models.Model):
    _name = 'compassion.intervention.category'
    _description = 'Intervention Category'

    name = fields.Char(required=True, translate=False)
    type = fields.Selection('get_types', required=True)
    subcategory_ids = fields.Many2many(
        'compassion.inter.subcat',
        'compassion_intervention_cat_subcat_rel',
        'category_id', 'subcategory_id',
        'Subcategories', readonly=False
    )

    _sql_constraints = [
        ('unique_name_type', 'unique(name, type)',
         'Category name and type must be unique!')
    ]

    def get_types(self):
        return [
            ("Ongoing CIV", _("Ongoing CIV")),
            ("Ongoing CIV FY Details", _("Ongoing CIV FY Details")),
            ("Individual CIV", _("Individual CIV")),
            ("Survival", _("Survival (CSP)")),
            ("Survival FY Details", _("Survival FY Details")),
            ("Sponsorship Launch", _("Sponsorship Launch")),
        ]
