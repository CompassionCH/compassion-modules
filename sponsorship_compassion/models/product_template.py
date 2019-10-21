from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    inter_company_reference = fields.Char('Inter-Company Reference')


    @api.multi
    def name_get(self):
        """
        We have multiple product template with the same name, one for each company.
        Cross-company users (e.g. admins) may want to differentiates the homonyms so we append the company name

        returns => [(template_id, "template_name [company]")]
        """
        names = super(ProductTemplate, self).name_get()
        if self.env.user.companies_count < 2:
            return names

        names = dict(names)
        return [(tpl.id, "[%s] %s" % (tpl.company_id.name, names[tpl.id])) for tpl in self]