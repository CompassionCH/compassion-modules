# -*- coding: utf-8 -*-

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
    password = fields.Char(required=True, groups="base.group_system")  # only admins can access this field

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
    def get(self):
        """
        Returns the config for the current company
        """
        company = self.env.user.company
        config = self.search([('company_id', '=', company.id)])
        assert len(config) == 1, "Missing Wordpress configuration for current company"

        return config

    @api.model
    def get_host(self):
        """
        Returns the wordpress host for the current company
        """
        return self.get().host

    @api.model
    def create_default_configuration(self):
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

    @api.model
    def _remove_previous_config(self, values):
        """
        ensure a one-to-one relationship (companies have at most one config)
        """
        if "company_id" in values and values["company_id"] is not False:
            configs = self.search([('company_id', '=', values["company_id"])]) - self
            for cfg in configs:
                cfg.company_id = False

    @api.model
    def _check_values(self, values):
        """
        The dependent modules do not expect the http part
        """
        if "host" in values and values.get("host").lower().startswith("http"):
            raise ValidationError(_("Hostname should not contain the protocol part 'http://'."))
