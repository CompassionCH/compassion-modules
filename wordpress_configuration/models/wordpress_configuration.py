from odoo import api, fields, models
from odoo.tools import config

import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WordpressConfiguration(models.Model):
    _name = "wordpress.configuration"
    _description = "Wordpress parameters (host, user, password) for a company"
    _order = "host"

    company_id = fields.Many2one('res.company', 'Company', required=False)

    host = fields.Char(required=True)
    user = fields.Char(required=True)
    password = fields.Char(required=True) # , invisible=true ?

    @api.model
    def create(self, values):
        self._remove_previous_config(values)
        return super(WordpressConfiguration, self).create(values)

    @api.multi
    def write(self, values):
        self._remove_previous_config(values)
        return super(WordpressConfiguration, self).write(values)


    @api.model
    def _remove_previous_config(self, values):
        """
            ensure a one-to-one relationship (companies have at most one config)
        """
        company = values.get("company_id")
        configs = self.search([('company_id', '=', company)])
        for cfg in configs:
            cfg.company_id = False

    @api.model
    def default_configuration(self):
        """
        Tries to read wordpress configs from odoo's config file.
        If the configs exists, applies them for the current user's company
        """
        host = config.get('wordpress_host')
        user = config.get('wordpress_user')
        pwd = config.get('wordpress_pwd')
        if not (host and user and pwd):
            return

        _logger.info("Wordpress.configuration: using configs found in odoo.conf")

        self.create({
            'host': host,
            'user': user,
            'password': pwd,
            'company_id': self.env.user.company_id.id
        })
