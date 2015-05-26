# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Steve Ferry
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.osv import orm


class ResPartnerBank(orm.Model):
    """ This class upgrade the partners.bank to match Compassion needs.
    """

    _inherit = 'res.partner.bank'

    def create(self, cr, uid, data, context):
        """Override function to notify creation in a message
        """
        obj_partner = self.pool['res.partner']
        part = obj_partner.browse(cr, uid, data['partner_id'], context=context)
        part.pool.get('mail.thread').message_post(cr, uid, part.id,
                                                  "<b>Account number: </b>" +
                                                  data['acc_number'],
                                                  "New account created",
                                                  'comment',
                                                  context={'thread_model':
                                                           part._name})
        result = super(ResPartnerBank, self).create(cr, uid, data,
                                                    context=context)
        self.post_write(cr, uid, [result], context=context)
        return result

    def unlink(self, cr, uid, ids, context):
        """Override function to notify delte in a message
        """

        obj_bank = self.pool['res.partner.bank']
        account = None

        for account in obj_bank.browse(cr, uid, ids, context=context):
            account.partner_id.pool.get('mail.thread'). \
                message_post(cr, uid, account.partner_id.id,
                             "<b>Account number: </b>" +
                             account.acc_number,
                             "Account deleted",
                             'comment',
                             context={'thread_model':
                                      account.partner_id._name})
        result = super(ResPartnerBank, self).unlink(cr, uid, ids,
                                                    context=context)
        return result
