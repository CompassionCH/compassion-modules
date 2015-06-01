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


class Account_Banking_Mandate(orm.Model):
    """ This class upgrade the partners.bank to match Compassion needs.
    """
    _inherit = 'account.banking.mandate'

    def create(self, cr, uid, data, context):
        """Override function to notify creation in a message on partner feed
        """
        obj_bank = self.pool['res.partner.bank']
        account = obj_bank.browse(cr, uid, data['partner_bank_id'],
                                  context=context)

        account.partner_id.pool.get('mail.thread') \
            .message_post(cr, uid, account.partner_id.id,
                          "For account: " +
                          account.acc_number,
                          "New mandate created",
                          'comment',
                          context={'thread_model':
                                   account.partner_id._name})

        result = super(Account_Banking_Mandate, self).create(cr, uid, data,
                                                             context=context)
        return result

    def validate(self, cr, uid, ids, context=None):
        """Override function to notify validation in a message on partner feed
        """

        obj_mandate = self.pool['account.banking.mandate']

        for mandate in obj_mandate.browse(cr, uid, ids, context=context):
            self.message_post(
                cr, uid, mandate.partner_id.id, "For account: " +
                mandate.partner_bank_id.acc_number, "Mandate validated",
                'comment', context={'thread_model': mandate.partner_id._name})

        super(Account_Banking_Mandate, self).validate(cr, uid, ids, context)
        return True

    def cancel(self, cr, uid, ids, context=None):
        """
        Override function to notify cancellation in a message on partner feed
        """

        obj_mandate = self.pool['account.banking.mandate']

        for mandate in obj_mandate.browse(cr, uid, ids, context=context):
            mandate.partner_id.pool.get('mail.thread') \
                .message_post(cr, uid, mandate.partner_id.id,
                              "For account: " +
                              mandate.partner_bank_id.acc_number,
                              "Mandate cancelled",
                              'comment', context={'thread_model':
                                                  mandate.partner_id._name})

        super(Account_Banking_Mandate, self).cancel(cr, uid, ids, context)
        return True

    def back2draft(self, cr, uid, ids, context=None):
        """
        Override function to notify cancellation in a message on partner feed
        """

        obj_mandate = self.pool['account.banking.mandate']

        for mandate in obj_mandate.browse(cr, uid, ids, context=context):
            mandate.partner_id.pool.get('mail.thread') \
                .message_post(cr, uid, mandate.partner_id.id,
                              "For account: " +
                              mandate.partner_bank_id.acc_number,
                              "Mandate back to draft",
                              'comment', context={'thread_model':
                                                  mandate.partner_id._name})

        super(Account_Banking_Mandate, self).back2draft(cr, uid, ids, context)
        return True

    def unlink(self, cr, uid, ids, context):
        """Override function to notify removal in a message on partner feed
        """
        obj_mandate = self.pool['account.banking.mandate']

        for mandate in obj_mandate.browse(cr, uid, ids, context=context):
            mandate.partner_id.pool.get('mail.thread') \
                .message_post(cr, uid, mandate.partner_id.id,
                              "For account: " +
                              mandate.partner_bank_id.acc_number,
                              "Mandate deleted",
                              'comment', context={'thread_model':
                                                  mandate.partner_id._name})

        result = super(Account_Banking_Mandate, self).unlink(cr, uid, ids,
                                                             context=context)
        return result
