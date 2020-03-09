##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, tools

testing = tools.config.get("test_enable")


if not testing:
    # prevent these forms to be registered when running tests

    class Form(models.AbstractModel):
        _inherit = "cms.form"

        def form_make_field_wrapper_klass(self, fname, field, **kw):
            """ Allow to hide fields. """
            res = super().form_make_field_wrapper_klass(fname, field, **kw)
            if "field-hidden" in field["widget"]._w_css_klass:
                res += " field-hidden"
            return res
