import re

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import SQL, Query

regex_order = re.compile(r"^similarity\((.*),.*\)(\s+(desc|asc))?$", re.I)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_fuzzy_search_value(self, domain):
        """Extract fuzzy search value from domain if present."""
        for arg in domain:
            if isinstance(arg, list | tuple) and len(arg) == 3:
                if arg[1] == "%":
                    return arg[0], arg[2]
        return False, False

    def _build_similarity_order(self, field_name, search_value):
        """Build similarity order SQL for fuzzy search."""
        if search_value and field_name:
            # Validate field_name to prevent SQL injection
            if field_name not in self._fields:
                return None
            return self.env.cr.mogrify(
                f"similarity(res_partner.{field_name}, %s) DESC", [search_value]
            ).decode("utf-8")
        return None

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=80):
        """Extends to use trigram search."""
        if args is None:
            args = []
        if name:
            # First find by reference
            res = self.search([("ref", "like", name)] + args, limit=limit)
            if not res:
                res = self.search(
                    [("name", "%", name)] + args,
                    limit=limit,
                )
            # Search by e-mail
            if not res:
                res = self.search([("email", "%", name)] + args, limit=limit)
        else:
            res = self.search(args, limit=limit)
        return [(record.id, record.display_name) for record in res]

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        """Order search results based on similarity if name search is used."""
        field_name, search_value = self._get_fuzzy_search_value(domain)
        fuzzy_order = self._build_similarity_order(field_name, search_value)
        return super().search(
            domain, offset=offset, limit=limit, order=fuzzy_order or order
        )

    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        """Order search results based on similarity if name search is used."""
        field_name, search_value = self._get_fuzzy_search_value(domain)
        fuzzy_order = self._build_similarity_order(field_name, search_value)
        return super().search_fetch(
            domain, field_names, offset=offset, limit=limit, order=fuzzy_order or order
        )

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
