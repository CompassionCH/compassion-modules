from odoo import api, models


class RecurringContract(models.Model):
    _inherit = 'recurring.contract'

    @api.model
    def _get_sponsorship_standard_lines(self):
        """ Select Sponsorship and General Fund by default """
        res = []
        product_obj = self.env['product.product'].with_context(lang='en_US')
        sponsorship_id = product_obj.search(
            [('name', '=', 'Sponsorship')])[0].id
        gen_id = product_obj.search(
            [('name', '=', 'General Fund')])[0].id
        sponsorship_vals = {
            'product_id': sponsorship_id,
            'quantity': 1,
            'amount': 42,
            'subtotal': 42
        }
        gen_vals = {
            'product_id': gen_id,
            'quantity': 1,
            'amount': 8,
            'subtotal': 8
        }
        res.append([0, 6, sponsorship_vals])
        res.append([0, 6, gen_vals])
        return res

    @api.model
    def create_sms_sponsorship(self, vals, partner, sms_child_request):
        if not partner:
            # Search for existing partner
            partner = self.env['res.partner'].search([
                ('firstname', 'ilike', vals['firstname']),
                ('lastname', 'ilike', vals['lastname']),
                ('email', '=', vals['email'])
            ])
            sms_child_request.partner_id = partner
        else:
            if not (partner.firstname == vals['firstname'] and
                    partner.lastname == vals['lastname'] and
                    partner.email == vals['email']):
                    partner = False

        if not partner:
            partner = self.env['res.partner'].create({
                'firstname': vals['firstname'],
                'lastname': vals['lastname'],
                'phone': vals['phone'],
                'email': vals['email'],
            })
            sms_child_request.partner_id = partner

        # Create sponsorship
        lines = self._get_sponsorship_standard_lines()
        if not vals['sponsorship_plus']:
            lines = lines[:-1]
        sponsorship = self.create({
            'partner_id': partner.id,
            'correspondent_id': partner.id,
            'child_id': sms_child_request.child_id.id,
            'type': 'S',
            'contract_line_ids': lines,
            'medium_id': self.env.ref('sms_sponsorship.utm_medium_sms').id
        })

        # Convert to No Money Hold
        sponsorship.with_delay().update_child_hold()

        partner.set_privacy_statement(origin='new_sponsorship')

        return True
