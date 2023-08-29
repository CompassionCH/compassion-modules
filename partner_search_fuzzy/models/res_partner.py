import re
from odoo import models, api
from odoo.exceptions import UserError


regex_order = re.compile('^similarity\((.*),.*\)(\s+(desc|asc))?$', re.I)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=80):
        """Extends to use trigram search."""
        if args is None:
            args = []
        if name:
            # First find by reference
            res = self.search([("ref", "like", name)], limit=limit)
            if not res:
                res = self.search(
                    ["|", ("name", "%", name), ("name", "ilike", name)],
                    order="similarity(name, '%s') DESC" % name,
                    limit=limit,
                )
            # Search by e-mail
            if not res:
                res = self.search([("email", "ilike", name)], limit=limit)
        else:
            res = self.search(args, limit=limit)
        return res.name_get()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """ Order search results based on similarity if name search is used."""
        fuzzy_search = False
        for arg in args:
            if arg[0] == "name" and arg[1] == "%":
                fuzzy_search = arg[2]
                break
        if fuzzy_search:
            order = self.env.cr.mogrify(
                "similarity(res_partner.name, %s) DESC", [fuzzy_search]
            )
        if order and isinstance(order, bytes):
            order = order.decode("utf-8")
        return super().search(args,
                              offset=offset, limit=limit, order=order, count=count)

    @api.model
    def _generate_order_by_inner(self, alias, order_spec, query,
                                 reverse_direction=False, seen=None):
        # Small trick to allow similarity ordering while bypassing odoo checks
        is_similarity_ordering = regex_order.match(order_spec) if order_spec else False
        if is_similarity_ordering:
            order_by_elements = [order_spec]
        else:
            order_by_elements = super()._generate_order_by_inner(
                alias, order_spec, query, reverse_direction, seen)
        return order_by_elements

    def _check_qorder(self, word):
        """ Allow similarity order """
        try:
            super()._check_qorder(word)
        except UserError:
            if not regex_order.match(word):
                raise
        return True
