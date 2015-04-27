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

from openerp.osv import orm, fields


class product(orm.Model):
    _inherit = 'product.product'

    def _get_gmc_name(self, cr, uid, ids, field_name, arg, context=None):
        res = dict()
        gmc_names = {
            'Birthday Gift': 'BirthdayGift',
            'General Gift': 'GeneralChildGift',
            'Family Gift': 'FamilyGift',
            'Project Gift': 'ProjectGift',
            'Graduation Gift': 'FinalOrGraduationGift'
        }
        for product in self.browse(cr, uid, ids, {'lang': 'en_US'}):
            if product.product_tmpl_id.categ_id.name == 'Sponsor gifts':
                res[product.id] = gmc_names[product.name]
            else:
                res[product.id] = "Undefined"
        return res

    _columns = {
        'gp_fund_id': fields.integer("GP Fund id", size=4),
        'gmc_name': fields.function(_get_gmc_name, type='char'),
    }
