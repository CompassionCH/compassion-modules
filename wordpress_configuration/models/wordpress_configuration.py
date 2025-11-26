import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class WordpressConfiguration(models.Model):
    _name = "wordpress.configuration"
    _description = "Wordpress parameters (host, user, password) for a company"
    _order = "host"

    company_id = fields.Many2one(
        "res.company", "Company", required=False, readonly=False
    )

    host = fields.Char(required=True)
    sponsorship_url = fields.Char(translate=True)
    survival_sponsorship_url = fields.Char(translate=True)
    fund_gift_url = fields.Char(translate=True)
    child_gift_url = fields.Char(translate=True)
    user = fields.Char(required=True)
    password = fields.Char(required=True)

    @api.model_create_multi
    def create(self, vals_list):
        self._check_values(vals_list)
        self._remove_previous_config(vals_list)
        return super().create(vals_list)

    def write(self, values):
        self._check_values(values)
        self._remove_previous_config(values)
        return super().write(values)

    def copy(self, values=None):
        res = super().copy(values)
        res.company_id = False
        return res

    @api.model
    def get_config(self, company_id=None, raise_error=True):
        """
        Returns the config for the given or current company
        """
        wp_config = self.search(
            [("company_id", "in", [company_id or self.env.company.id, False])], limit=1
        )
        if not wp_config and raise_error:
            raise UserError(_("Missing Wordpress configuration for current company"))
        return wp_config

    @api.model
    def get_host(self, company_id=None):
        """
        Returns the wordpress host for the current company
        """
        return self.get_config(company_id).host

    @api.model
    def create_default_configuration(self):
        """
        Tries to read wordpress configs from odoo's config file.
        If the configs exists, applies them for the current user's company
        """
        host = config.get("wordpress_host")
        user = config.get("wordpress_user")
        pwd = config.get("wordpress_pwd")
        if not (host and user and pwd):
            return

        self.create(
            {
                "host": host,
                "user": user,
                "password": pwd,
                "company_id": self.env.user.company.id,
            }
        )

    @api.model
    def _remove_previous_config(self, vals_list):
        """
        ensure a one-to-one relationship (companies have at most one config)
        """
        for vals in vals_list:
            if "company_id" in vals and vals["company_id"] is not False:
                configs = self.search([("company_id", "=", vals["company_id"])]) - self
                for cfg in configs:
                    cfg.company_id = False

    @api.model
    def _check_values(self, vals_list):
        """
        The dependent modules do not expect the http part
        """
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        for vals in vals_list:
            if "host" in vals and vals.get("host").lower().startswith("http"):
                raise ValidationError(
                    _("Hostname should not contain the protocol part ('http://').")
                )
