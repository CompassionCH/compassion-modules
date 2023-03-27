from odoo import models, api
from odoo.exceptions import UserError
from odoo.models import regex_order


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = 'res.partner'

    def write(self, vals):
        res = True
        for partner in self:
            res = super().write(vals) & res
            partner._updt_invoices_rp(vals)
        return res

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

    def _check_duplicates_domain(self, vals=None, skip_props_check=False):
        """
        Generates a search domain to find duplicates for this partner based on various filters
        :param dict vals: a dictionnary containing values used by the filters, inferred from self if not provided
        :param bool skip_props_checks: whether you want to skip verifying that each variable's filter are set, thus running them all anyway
        """
        if not vals:
            vals = {
                "email": self.email,
                "firstname": self.firstname,
                "lastname": self.lastname,
                "zip": self.zip,
                "street": self.street,
            }

        # define set of checks for duplicates and required fields
        checks = [
            # Email check
            (vals.get('email'), [
                '&',
                ('email', '=', vals.get('email')),
                ('email', '!=', False)
            ]),
            # zip and name check
            (vals.get('firstname') and vals.get('lastname') and vals.get('zip'), [
                "&",
                "&",
                ("firstname", "ilike", vals.get('firstname')),
                ("lastname", "ilike", vals.get('lastname')),
                ("zip", "=", vals.get('zip')),
            ]),
            # name and address check
            (vals.get('lastname') and vals.get('street') and vals.get('zip'), [
                "&",
                "&",
                ("lastname", "ilike", vals.get('lastname')),
                ("zip", "=", vals.get('zip')),
                ("street", "ilike", vals.get('street'))
            ])
        ]

        # This step builds a domain query based on the checks that
        # passed, prepending the list with a "|" operator for all item
        # once its size is > 1
        search_filters = []
        for check in checks:
            if skip_props_check or check[0]:
                if len(search_filters) > 0:
                    search_filters.insert(0, "|")
                search_filters.extend(check[1])
        return search_filters

    def _updt_invoices_rp(self, vals):
        """
        It updates the invoices of a partner when the partner is updated.
        Should be called after the write has been done

        :param vals: the values that are being updated on the partner
        """
        self.ensure_one()
        if any(key in vals for key in ["property_payment_term_id"]):
            invoices = self.env['account.move'].search([
                ("partner_id", "=", self.id),
                ("payment_state", "=", "not_paid"),
                ("state", "!=", "cancel")
            ])
            data_invs = invoices._build_invoices_data(payment_term_id=self.property_payment_term_id.id)
            if data_invs:
                invoices.update_open_invoices(data_invs)
