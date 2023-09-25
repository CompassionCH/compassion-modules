##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import csv
import logging
import os

from odoo import api, fields, models

logger = logging.getLogger(__name__)

IMPORT_DIR = os.path.join(os.path.dirname(__file__)) + "/../data/"


class InterventionSubCategory(models.Model):
    _name = "compassion.intervention.subcategory"
    _description = "Intervention Subcategory"

    name = fields.Char(required=True, translate=False)
    category_ids = fields.Many2many(
        "compassion.intervention.category",
        "compassion_intervention_cat_subcat_rel",
        "subcategory_id",
        "category_id",
        "Categories",
        readonly=False,
    )

    _sql_constraints = [
        ("unique_name", "unique(name)", "Category name must be unique!")
    ]

    @api.model
    def install_cat_rel(self):
        logger.info("Intervention Installation : Loading Category Relations")
        with open(
            IMPORT_DIR + "compassion.intervention.cat.subcat.rel.csv", "r"
        ) as csvfile:
            csvreader = csv.reader(csvfile)
            # Skip header
            next(csvreader, None)
            for row in csvreader:
                cat_id = self.env.ref("intervention_compassion." + row[1]).id
                subcategory = self.env.ref("intervention_compassion." + row[2])
                if cat_id not in subcategory.category_ids.ids:
                    self.env.cr.execute(
                        f"""
                        INSERT INTO compassion_intervention_cat_subcat_rel
                        ("category_id", "subcategory_id")
                        VALUES ({cat_id}, {subcategory.id})
                        """
                    )
