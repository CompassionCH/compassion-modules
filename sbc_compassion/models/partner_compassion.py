# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models, _


class ResPartner(models.Model):
    """ Add correspondence preferences to Partners
    """

    _inherit = 'res.partner'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    spoken_lang_ids = fields.Many2many(
        'res.lang.compassion', string='Spoken languages', required=True)
    mandatory_review = fields.Boolean(
        help='Indicates that we should review the letters of this sponsor '
             'before sending them to GMC.')
    delivery_preference = fields.Selection([
        ('digital', _('By e-mail')),
        ('physical', _('By postal service'))], default='digital',
        required=True, help='Delivery preference for Child letters')
    send_original = fields.Boolean(
        help='Indicates that we request the original letters for this sponsor'
        )
