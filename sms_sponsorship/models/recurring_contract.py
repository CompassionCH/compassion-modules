from odoo import _, api, models


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
    def create_sms_sponsorship(self, vals, utm_source, utm_medium, utm_campaign, partner, sms_child_request):
        if not partner:
            # Search for existing partner
            partner = self.env['res.partner'].search([
                ('firstname', 'ilike', vals['firstname']),
                ('lastname', 'ilike', vals['lastname']),
                ('email', '=', vals['email'])
            ])
            sms_child_request.partner_id = partner

        if not partner:
            partner = self.env['res.partner'].create({
                'firstname': vals['firstname'],
                'lastname': vals['lastname'],
                'phone': vals['phone'],
                'email': vals['email'],
            })
            sms_child_request.partner_id = partner

        # Check origin
        internet_id = self.env.ref('utm.utm_medium_website').id
        utms = self.env['utm.mixin'].get_utms(
            utm_source, utm_medium, utm_campaign)

        # Create sponsorship
        child = sms_child_request.child_id
        lines = self._get_sponsorship_standard_lines()
        if not vals['sponsorship_plus']:
            lines = lines[:-1]
        sponsorship = self.create({
            'partner_id': partner.id,
            'correspondent_id': partner.id,
            'child_id': sms_child_request.child_id.id,
            'type': 'S',
            'contract_line_ids': lines,
            'source_id': utms['source'],
            'medium_id': utms.get('medium', internet_id),
            'campaign_id': utms['campaign'],
        })

        # Notify staff
        staff_param = 'sponsorship_' + 'fr' + '_id'
        staff = self.env['staff.notification.settings'].get_param(staff_param)
        notify_text = "A new sponsorship was made from a SMS. Please " \
                      "verify all information and validate the sponsorship " \
                      "on Odoo: <br/><br/><ul>"

        infos = vals.copy()
        for element in ['child', 'utm_source', 'utm_medium', 'utm_campaign']:
            infos[element] = eval(element)

        for k, v in infos.items():
            notify_text += "<li>" + k + ": " + unicode(v) + '</li>'

        sponsorship.message_post(
            body=notify_text,
            subject=_('New sponsorship from SMS'),
            partner_ids=[staff],
            type='comment',
            subtype='mail.mt_comment',
            content_subtype='html'
        )

        # Mark child as sponsored even if not yet linked to sponsor
        child.state = 'P'
        # Convert to No Money Hold
        sponsorship.with_delay().update_child_hold()

        partner.set_privacy_statement(origin='new_sponsorship')

        return True
