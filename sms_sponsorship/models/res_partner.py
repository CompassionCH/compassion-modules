##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, _
from odoo.addons.queue_job.job import job, related_action


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def sms_send_step1_confirmation(self, child_request):
        # Override this method to change the message sent to the partner.
        child = child_request.child_id
        self.message_post(
            body=_(
                "You chose to invest in the life of %s. There are two "
                "more steps before %s will be informed that you sponsor %s,"
                " but you don't have to hurry! We have reserved the child "
                "so that you can take your time to complete the registration."
                "<br/><br/>"
                "1. You can <a href='%s'>click here</a> to complete your "
                "information and your payment option in the coming days. <br/>"
                "2. Your sponsorship will be activated when we receive your "
                "first payment. <br/><br/>Best regards"
            ) % (child.preferred_name, child.get('he'), child.get('him'),
                 child_request.full_url),
            subject=_("Thank you for your sponsorship!"),
            partner_ids=self.ids,
            type='comment',
            subtype='mail.mt_comment',
            content_subtype='html'
        )
        return True

    @api.multi
    def sms_send_step2_confirmation(self, child_request):
        # Override this method to change the message sent to the partner.
        self.message_post(
            body=_(
                "Thank you for your commitment towards %s. Now that all "
                "information is completed, we will activate your sponsorship "
                "as soon as we receive your first payment. <br/><br/>"
                "You will receive more documentation by post in the coming "
                "days. In the mean time, feel free to reach us if you have "
                "any question. <br/><br/>"
            ) % child_request.child_id.preferred_name,
            subject=_("Thank you for your sponsorship!"),
            partner_ids=self.ids,
            type='comment',
            subtype='mail.mt_comment',
            content_subtype='html'
        )
        return True

    @job(default_channel="root.res_partner")
    @related_action(action='related_action_update_partner')
    def update_partner(self, partner_vals):
        return self.write(partner_vals)
