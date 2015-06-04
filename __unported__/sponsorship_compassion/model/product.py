# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, fields, models

# Name of gifts products
GIFT_NAMES = ["Birthday Gift", "General Gift", "Family Gift", "Project Gift",
              "Graduation Gift"]

# Name of gift category
GIFT_CATEGORY = "Sponsor gifts"

# Name of sponsorship category
SPONSORSHIP_CATEGORY = "Sponsorship"

# Name of fund category
FUND_CATEGORY = "Fund"


class product(models.Model):
    _inherit = 'product.product'

    gmc_name = fields.Char(compute='_set_gmc_name')

    @api.multi
    def _set_gmc_name(self):
        gmc_names = {
            'Birthday Gift': 'BirthdayGift',
            'General Gift': 'GeneralChildGift',
            'Family Gift': 'FamilyGift',
            'Project Gift': 'ProjectGift',
            'Graduation Gift': 'FinalOrGraduationGift'
        }
        for product in self.with_context(lang='en_US'):
            if product.categ_name == GIFT_CATEGORY:
                product.gmc_names = gmc_names[product.name]
            else:
                product.gmc_names = "Undefined"
