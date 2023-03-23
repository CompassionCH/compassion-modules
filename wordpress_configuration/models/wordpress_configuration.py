import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
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
    user = fields.Char(required=True)
    password = fields.Char(required=True)

    @api.model
    def create(self, values):
        self._check_values(values)
        self._remove_previous_config(values)
        return super(WordpressConfiguration, self).create(values)

    @api.multi
    def write(self, values):
        self._check_values(values)
        self._remove_previous_config(values)
        return super(WordpressConfiguration, self).write(values)

    @api.multi
    def copy(self, values=None):
        res = super(WordpressConfiguration, self).copy(values)
        res.company_id = False
        return res

    @api.model
    def get_config(self, company_id=None, raise_error=True):
        """
        Returns the config for the given or current company
        """
        wp_config = self.search(
            [("company_id", "=", company_id or self.env.user.company_id.id)], limit=1
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
                "company_id": self.env.user.company_id.id,
            }
        )

    @api.model
    def _remove_previous_config(self, values):
        """
        ensure a one-to-one relationship (companies have at most one config)
        """
        if "company_id" in values and values["company_id"] is not False:
            configs = self.search([("company_id", "=", values["company_id"])]) - self
            for cfg in configs:
                cfg.company_id = False

    @api.model
    def _check_values(self, values):
        """
        The dependent modules do not expect the http part
        """
        if "host" in values and values.get("host").lower().startswith("http"):
            raise ValidationError(
                _("Hostname should not contain the protocol part ('http://').")
            )
