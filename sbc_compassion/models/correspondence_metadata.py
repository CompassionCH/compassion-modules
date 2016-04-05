# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, _


class CorrespondenceMetadata(models.Model):
    """ This class defines all metadata of a correspondence"""

    _name = 'correspondence.metadata'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    physical_attachments = fields.Selection(selection=[
        ('sent_by_mail', _('Sent by mail')),
        ('not_sent', _('Not sent'))])
    attachments_description = fields.Text()
    template_id = fields.Many2one(
        'correspondence.template', 'Template')
    mandatory_review = fields.Boolean()
