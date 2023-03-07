from odoo import models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = 'res.partner'

    def write(self, vals):
        res = True
        for partner in self:
            res = super().write(vals) & res
            partner._updt_invoices_rp(vals)
        return res

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
            data_invs = invoices._build_invoice_data(payment_term_id=self.property_payment_term_id.id)
            if data_invs:
                invoices.update_open_invoices(data_invs)
