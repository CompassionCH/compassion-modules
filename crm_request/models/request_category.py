#    Copyright (C) 2019 Compassion CH
#    @author: Stephane Eicher <seicher@compassion.ch>


from odoo import models, fields, api, _


class RequestCategory(models.Model):
    _inherit = "crm.claim.category"

    template_id = fields.Many2one(
        "mail.template",
        "Template",
        domain="[('model_id', '=', 'crm.claim')]",
        readonly=False,
    )
    keywords = fields.Char(
        string="Keywords",
        help='List of keywords (separated by a comma ",") who could be '
             "contained in the demand subject",
    )

    description = fields.Char(string="Description")

    @api.constrains("keywords")
    def _check_existing_key(self):
        # Avoid having two identical keys
        records = self.search([("keywords", "!=", False)])
        for record in self:
            records = records - record
            keywords = records.get_keys()
            if records:
                for keyword in record.get_keys():
                    if any([keyword in k for k in keywords]):
                        raise models.ValidationError(
                            _(
                                "One keyword must be unique over all types and "
                                "not be included in another keyword"
                            )
                        )

    @api.multi
    def get_keys(self):
        keywords_list = []
        for record in self:
            keywords_list.extend(record.keywords.split(","))
        return keywords_list
