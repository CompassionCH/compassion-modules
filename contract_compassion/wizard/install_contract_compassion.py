# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.osv import orm


class install_contract_compassion(orm.TransientModel):
    _name = "install.contract.compassion"

    def install(self, cr, uid, ids=None, context=None):

        # Modify old ir_model_data to change module name
        product_ids = self.pool.get('product.product').search(
            cr, uid,
            [('categ_name', 'in', ['Sponsorship', 'Sponsor gifts'])],
            context)
        sql_request = ("UPDATE ir_model_data "
                       "SET module='contract_compassion' "
                       "WHERE module='sponsorship_compassion' AND "
                       "model = 'product.product' ")
        if product_ids:
            sql_request += "AND res_id NOT IN ({0}) ".format(
                (','.join(str(id) for id in product_ids))
            )
        cr.execute(sql_request)

        cr.execute(
            """
        UPDATE ir_model_data
        SET module='contract_compassion'
        WHERE module='sponsorship_compassion' AND
        model IN ('workflow.activity','workflow.transition')
        """
        )
        cr.execute(
            """
        UPDATE ir_model_data
        SET module= 'contract_compassion'
        WHERE module = 'sponsorship_compassion' AND
        name IN ('view_recurring_contract_form_compassion',
        'view_contract_group_form_compassion') AND
        model = 'ir.ui.view'
        """
        )

        # Set the contract type
        cr.execute(
            '''
        UPDATE recurring_contract
        SET type = 'S'
        WHERE child_id IS NOT NULL
        AND type IN ('ChildSponsorship') OR type IS NULL
        '''
        )
        cr.execute(
            '''
        UPDATE recurring_contract
        SET type = 'O'
        WHERE child_id IS NULL
        AND type IN ('ChildSponsorship') OR type IS NULL
        ''')
