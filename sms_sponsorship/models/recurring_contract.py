# coding: utf-8
from odoo import api, models, fields
from odoo.addons.queue_job.job import job


class RecurringContract(models.Model):
    _inherit = 'recurring.contract'

    group_id = fields.Many2one(required=False)

    @api.model
    @job
    def create_sms_sponsorship(self, vals, partner, sms_child_request):
        """
        Creates sponsorship from REACT webapp data.
        :param vals: form values
        :param partner: res.partner record
        :param sms_child_request: sms.child.request record
        :return: True
        """
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
            sms_child_request.new_partner = True
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
            'medium_id': self.env.ref('sms_sponsorship.utm_medium_sms').id,
            'origin_id': sms_child_request.event_id.origin_id.id,
        })
        sponsorship.on_change_origin()
        sponsorship.with_delay().put_child_on_no_money_hold()
        partner.set_privacy_statement(origin='new_sponsorship')
        sms_child_request.complete_step1(sponsorship.id)
        return True
