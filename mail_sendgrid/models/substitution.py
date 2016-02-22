# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging

from openerp import models, fields
from openerp.tools import ustr
from openerp.addons.email_template.email_template import mako_template_env

_logger = logging.getLogger(__name__)


class Substitution(models.Model):
    """ Substitution values for a SendGrid email message """
    _name = 'sendgrid.substitution'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    key = fields.Char()
    lang = fields.Char()
    email_template_id = fields.Many2one(
        'email.template', ondelete='cascade')
    email_id = fields.Many2one(
        'mail.mail', ondelete='cascade')
    value = fields.Char()

    def get_substitutions(self, object):
        """Render the values and returns a dictionary with the keys and values
           Replace mako expressions ``${expr}``
           with the result of evaluating these expressions with
           an evaluation context containing:

                * ``user``: browse_record of the current user
                * ``object``: browse_record of the document record this mail is
                              related to

           :param object: browse record this mail is related to.
        """
        result = dict()
        variables = {
            'user': self.user,
            'ctx': self.context,  # context kw would clash with mako internals
            'object': object
        }
        for substitution in self:
            result[substitution.key] = substitution.value
            try:
                template = mako_template_env.from_string(ustr(
                    substitution.value))
                result[substitution.key] = template.render(variables)
            except Exception:
                _logger.exception("Failed to render substitution %r",
                                  substitution.value)

        return result
