import re

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import SQL, Query

regex_order = re.compile(r"^similarity\((.*),.*\)(\s+(desc|asc))?$", re.I)


class ResPartner(models.Model):
    _inherit = "res.partner"

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
                    ["|", ("name", "%", name), ("name", "ilike", name)] + args,
                    limit=limit,
                )
            # Search by e-mail
            if not res:
                res = self.search([("email", "ilike", name)] + args, limit=limit)
        else:
            res = self.search(args, limit=limit)
        return [(record.id, record.display_name) for record in res]

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        """Order search results based on similarity if name search is used."""
        fuzzy_search = False
        for arg in domain:
            if isinstance(arg, list | tuple) and len(arg) == 3:
                if arg[0] == "name" and arg[1] == "%":
                    fuzzy_search = arg[2]
                    break
        if fuzzy_search:
            order = self.env.cr.mogrify(
                "similarity(res_partner.name, %s) DESC", [fuzzy_search]
            ).decode("utf-8")
        return super().search(domain, offset=offset, limit=limit, order=order)

    def _check_qorder(self, word):
        """Allow similarity order"""
        try:
            super()._check_qorder(word)
        except UserError:
            if not regex_order.match(word):
                raise
        return True

    def _order_to_sql(
        self,
        order: str,
        query: Query,
        alias: (str | None) = None,
        reverse: bool = False,
    ) -> SQL:
        if order and regex_order.match(order):
            return SQL(order)
        return super()._order_to_sql(order, query, alias, reverse)
