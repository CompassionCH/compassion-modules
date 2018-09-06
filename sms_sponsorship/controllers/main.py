# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samuel Fringeli <samuel.fringeli@me.com>
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import werkzeug.utils
from odoo import _
from odoo.addons.cms_form.controllers.main import FormControllerMixin
from odoo.exceptions import ValidationError
from odoo.http import request, route, Controller


def get_child_request(request_id):
    sms_request = request.env['sms.child.request'].sudo() \
        .search([('id', '=', int(request_id))])
    return sms_request.with_context(lang=sms_request.lang_code)


class SmsSponsorshipWebsite(Controller, FormControllerMixin):

    # STEP 1
    ########
    @route('/sms_sponsorship/step1/<int:child_request_id>', auth='public',
           website=True)
    def step1_redirect_react(self, child_request_id=None):
        """ URL for SMS step 1, redirects to REACT app showing the mobile
        form.
        """
        url = '/sms_sponsorship/static/react/index.html?child_request_id=' + \
            str(child_request_id)
        return werkzeug.utils.redirect(url, 301)

    @route('/sms_sponsorship/step1/<int:child_request_id>/get_child_data',
           type='json', auth='public', methods=['POST'], csrf=False)
    def get_child_data(self, child_request_id):
        """
        API Called by REACT app in order to get relevant data for displaying
        the mobile sponsorship form (step 1).
        :param child_request_id: id of sms_child_request
        :return: JSON data
        """
        sms_child_request = get_child_request(child_request_id)
        if not sms_child_request or sms_child_request.state == 'expired':
            return {'invalid_sms_child_request': True}
        if sms_child_request.sponsorship_confirmed:
            return {'sponsorship_confirmed': True}

        # No child for this request, we try to fetch one
        child = sms_child_request.child_id
        if not child and not sms_child_request.is_trying_to_fetch_child:
            sms_child_request.is_trying_to_fetch_child = True
            if not sms_child_request.reserve_child():
                sms_child_request.is_trying_to_fetch_child = True
                sms_child_request.take_child_from_childpool()
        if child:
            result = child.get_sms_sponsor_child_data()
            partner = sms_child_request.partner_id
            if sms_child_request.partner_id:
                result['partner'] = partner.read(['firstname', 'lastname',
                                                  'email'])
                result['lang'] = partner.lang[:2]
            else:
                result['lang'] = sms_child_request.lang_code[:2]
            return result
        return {'has_a_child': False, 'invalid_sms_child_request': False}

    @route('/sms_sponsorship/step1/<int:child_request_id>/confirm',
           type='json', auth='public', methods=['POST'], csrf=False)
    def sms_sponsor_confirm(self, child_request_id):
        """
        Route called by REACT app when step 1 form is submitted.
        :param child_request_id: id of sms_child_request
        :return: JSON result
        """
        env = request.env
        body = request.jsonrequest
        sms_child_request = get_child_request(child_request_id)
        if sms_child_request:
            sms_child_request.ensure_one()
            body['mobile'] = sms_child_request.sender
            partner = sms_child_request.partner_id \
                if sms_child_request.partner_id else False
            env['recurring.contract'].sudo().with_delay()\
                .create_sms_sponsorship(body, partner, sms_child_request)
            sms_child_request.write({'sponsorship_confirmed': True})
            return {'result': 'success'}

    @route('/sms_sponsorship/step1/<int:child_request_id>/change_child',
           type='json', auth='public', methods=['POST'], csrf=False)
    def sms_change_child(self, child_request_id):
        """
        Route called by REACT app for selecting another child.
        :param child_request_id: id of sms_child_request
        :return: None, REACT page will be refreshed after this call.
        """
        body = request.jsonrequest
        sms_child_request = get_child_request(child_request_id)
        tw = dict()  # to write
        if body['gender'] != '':
            tw['gender'] = body['gender']
        else:
            tw['gender'] = False
        if body['age'] != '':
            tw['min_age'], tw['max_age'] = map(int, body['age'].split('-'))
        else:
            tw['min_age'], tw['max_age'] = False, False
        if body['country']:
            # doesn't work
            field_office = request.env['compassion.field.office'].sudo()\
                .search([('country_code', '=', body['country'])], limit=1)
            if field_office:
                tw['field_office_id'] = field_office.id
            else:
                tw['field_office_id'] = False
        else:
            tw['field_office_id'] = False
        if tw:
            sms_child_request.write(tw)

        sms_child_request.change_child()

    # STEP 2
    ########
    @route('/sms_sponsorship/step2/<int:sponsorship_id>/',
           auth='public', website=True)
    def step2_confirm_sponsorship(self, sponsorship_id=None, **kwargs):
        """ SMS step2 controller. Returns the sponsorship registration form."""
        sponsorship = request.env['recurring.contract'].sudo().browse(
            sponsorship_id)
        if sponsorship.sms_request_id.state == 'step2':
            # Sponsorship is already confirmed
            return self.sms_registration_confirmation(sponsorship.id, **kwargs)
        return self.make_response(
            'recurring.contract',
            model_id=sponsorship and sponsorship.id,
            **kwargs
        )

    @route('/sms_sponsorship/step2/<int:sponsorship_id>/'
           'confirm', type='http', auth='public',
           methods=['GET'], website=True)
    def sms_registration_confirmation(self, sponsorship_id=None, **post):
        """
        This is either called after form submission, or when the user
        is redirected back from the payment website. We use ogone as provider
        but this could be replaced in a method override.
        NB: at this stage, the sponsorship is no more draft so we use id
            to avoid access rights issues.
        :param sponsorship_id: the sponsorship
        :return: The view to render
        """
        sponsorship = request.env['recurring.contract'].sudo().browse(
            sponsorship_id)
        values = {
            'sponsorship': sponsorship
        }
        try:
            tx = request.env['payment.transaction'].sudo().\
                _ogone_form_get_tx_from_data(post)
        except ValidationError:
            tx = None

        if tx and tx.state != 'done' or post.get('error'):
            request.website.add_status_message(
                _("The payment was not successful, but your sponsorship has "
                  "still been activated! You will be able to pay later using "
                  "your selected payment method."),
                type_='danger')
        return request.render(
            'sms_sponsorship.sms_registration_confirmation', values)
