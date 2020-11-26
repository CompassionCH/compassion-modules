from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def rule_is_enumerable(self, rule):
        """ Create a route parameter named no_sitemap. Set it
            to true to exclude this route from the sitemap
            generation.
            :type rule: werkzeug.routing.Rule
            :rtype: bool
        """
        if rule.endpoint.routing.get('no_sitemap'):
            return False
        return super(Website, self).rule_is_enumerable(rule)