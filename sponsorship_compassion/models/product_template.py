# -*- coding: utf-8 -*-

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def name_get(self):
        """
        We have multiple product template with the same name, one for each
        company.
        Cross-company users (e.g. admins) may want to differentiates the
        homonyms so we prepend the company name.

        returns => [(template_id, "[company] template_name")]
        """
        names = super(ProductTemplate, self).name_get()
        if self.env.user.companies_count < 2:
            return names

        names = dict(names)

        # for each template_product, reformat the name with the company name
        return [(t.id, "[%s] %s" % (t.company_id.name, names[t.id])) for t in
                self]
