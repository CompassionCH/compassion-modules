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
        """ Installation script to update < 1.5 compassion database. """
        self._move_xml_objects(cr, uid, context)
        self._upgrade_contracts(cr, uid, context)
        return True

    def _move_xml_objects(self, cr, uid, context=None):
        """ Modify old ir_model_data to change module name of xml objects
        moved from sponsorship_compassion to contract_compassion.
        """
        update_sql = "UPDATE ir_model_data SET module='contract_compassion' "\
            "WHERE module='sponsorship_compassion' AND ({0})"

        # Move fund category
        sql_filters = "(name='product_category_fund' AND " \
            "model='product.category')"

        # Move product templates
        sql_filters += " OR (model='product.template'"
        temp_ids = self.pool.get('product.template').search(
            cr, uid,
            [('categ_id.name', 'in', ['Sponsorship', 'Sponsor gifts'])],
            context)
        if temp_ids:
            sql_filters += " AND res_id NOT IN ({0})".format(
                (','.join(str(id) for id in temp_ids)))
        sql_filters += ")"

        # Move non sponsorship products
        product_ids = self.pool.get('product.product').search(
            cr, uid,
            [('categ_name', 'in', ['Sponsorship', 'Sponsor gifts'])],
            context)
        sql_filters += " OR (model = 'product.product'"
        if product_ids:
            sql_filters += " AND res_id NOT IN ({0})".format(
                (','.join(str(id) for id in product_ids))
            )
        sql_filters += ")"

        # Move workflow activities and transitions
        sql_filters += " OR model IN ('workflow.activity', " \
            "'workflow.transition')"

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

        # Move views
        sql_filters += " OR (name IN (" \
            "'view_recurring_contract_form_compassion'," \
            "'view_recurring_contract_tree_compassion'," \
            "'view_recurring_contract_compassion_filter'," \
            "'view_contract_origin_tree'," \
            "'view_contract_origin_form'," \
            "'view_contract_origin_filter'," \
            "'view_contract_group_form_compassion') " \
            "AND model='ir.ui.view')"

        # Perform the moves
        cr.execute(update_sql.format(sql_filters))

    def _upgrade_contracts(self, cr, uid, context=None):
        """ Update old contracts """
        # Set the contract type for existing contracts
        cr.execute(
            """
        UPDATE recurring_contract
        SET type = 'S'
        WHERE child_id IS NOT NULL
        AND type IN ('ChildSponsorship') OR type IS NULL
        """
        )
        cr.execute(
            """
        UPDATE recurring_contract
        SET type = 'O'
        WHERE child_id IS NULL
        AND type IN ('ChildSponsorship') OR type IS NULL
        """)

        # Update change_method of contract_groups
        cr.execute(
            """
        UPDATE recurring_contract_group
        SET change_method = 'clean_invoices'
        """)
