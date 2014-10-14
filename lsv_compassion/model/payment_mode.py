# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Copyright EduSense BV, Therp BV
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields


class payment_mode(orm.Model):
    _inherit = "payment.mode"

    _columns = {
        'payment_term_ids': fields.many2many(
            'account.payment.term', 'account_payment_order_terms_rel', 
            'mode_id', 'term_id', 'Payment terms',
            help=('Limit selected invoices to invoices with these payment '
                  'terms')
            ),
        }
