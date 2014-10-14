# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Copyright EduSense BV, Therp BV, ACSONE SA/NV
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm


class payment_order_create(orm.TransientModel):
    _inherit = 'payment.order.create'

    def extend_payment_order_domain(
            self, cr, uid, payment_order, domain, context=None):
        super(payment_order_create, self).extend_payment_order_domain(
            cr, uid, payment_order, domain, context=context)
        # apply payment term filter
        if payment_order.mode.payment_term_ids:
            domain += [
                ('invoice.payment_term', 'in',
                 [term.id for term in payment_order.mode.payment_term_ids]
                 )
            ]
        return True
