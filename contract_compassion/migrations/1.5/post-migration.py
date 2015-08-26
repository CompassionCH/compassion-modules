# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


def update_contract_names(cr):
    """ Store contract names. """
    cr.execute(
        """
        UPDATE recurring_contract c
        SET name = CONCAT(
            (SELECT ref FROM res_partner WHERE id = c.partner_id),
            ' - ',
            COALESCE(
               (SELECT code FROM compassion_child WHERE id = c.child_id),
               (SELECT p.name_template FROM recurring_contract_line l
                JOIN product_product p ON l.product_id = p.id
                WHERE l.contract_id = c.id
                LIMIT 1)
            )
        )
        """
        )


def migrate(cr, version):
    if not version:
        return

    update_contract_names(cr)
