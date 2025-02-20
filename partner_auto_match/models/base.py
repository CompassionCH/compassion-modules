from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _job_prepare_context_before_enqueue_keys(self):
        """Keys to keep in context of stored jobs
        Empty by default for backward compatibility.
        """
        whitelist = super()._job_prepare_context_before_enqueue_keys()
        return tuple(
            set(
                whitelist
                + (
                    "tz",
                    "lang",
                    "allowed_company_ids",
                    "force_company",
                    "active_test",
                    "skip_check_zip",
                    "no_upsert",
                )
            )
        )
