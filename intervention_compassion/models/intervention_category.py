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

import logging
import csv
import os
from openerp import api, models, fields, _

logger = logging.getLogger(__name__)

IMPORT_DIR = os.path.join(os.path.dirname(__file__)) + '/../data/'


class InterventionCategory(models.Model):
    _name = 'compassion.intervention.category'
    _description = 'Intervention Category'

    name = fields.Char(required=True, translate=False)
    type = fields.Selection('get_types', required=True)
    subcategory_ids = fields.Many2many(
        'compassion.intervention.subcategory',
        'compassion_intervention_cat_subcat_rel',
        'category_id', 'subcategory_id',
        'Subcategories'
    )

    _sql_constraints = [
        ('unique_name_type', 'unique(name, type)',
         'Category name and type must be unique!')
    ]

    def get_types(self):
        return [
            ("Ongoing CIV FY Details", _("Ongoing CIV")),
            ("Ongoing CIV", _("Ongoing CIV")),
            ("Individual CIV", _("Individual CIV")),
            ("Survival FY Details", _("Survival (CSP)")),
            ("Survival", _("Survival (CSP)")),
            ("Sponsorship Launch", _("Sponsorship Launch")),
        ]


class InterventionSubCategory(models.Model):
    _name = 'compassion.intervention.subcategory'
    _description = 'Intervention Subcategory'

    name = fields.Char(required=True, translate=False)
    category_ids = fields.Many2many(
        'compassion.intervention.category',
        'compassion_intervention_cat_subcat_rel',
        'subcategory_id', 'category_id', 'Categories',
    )

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Category name must be unique!')
    ]

    @api.model
    def install_cat_rel(self):
        logger.info("Intervention Installation : Loading Category Relations")
        with open(IMPORT_DIR + 'compassion.intervention.cat.subcat.rel.csv',
                  'rb') as csvfile:
            csvreader = csv.reader(csvfile)
            # Skip header
            csvreader.next()
            for row in csvreader:
                cat_id = self.env.ref('intervention_compassion.' + row[1]).id
                subcat_id = self.env.ref(
                    'intervention_compassion.' + row[2]).id
                self.env.cr.execute("""
                    INSERT INTO compassion_intervention_cat_subcat_rel
                    ("category_id", "subcategory_id")
                    VALUES ({}, {})""".format(cat_id, subcat_id))
