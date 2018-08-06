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
from odoo.addons.cms_form.controllers.main import FormControllerMixin

from odoo.http import request, route, Controller


def get_child_request(request_id, lang):
    matching_lang = request.env['res.lang'].sudo().search([
        ('code', 'like', lang)
    ], limit=1)
    final_lang = matching_lang.code or 'en_US'
    return request.env['sms.child.request'].sudo() \
        .with_context(lang=final_lang).search([('id', '=', int(request_id))])


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
        body = request.jsonrequest
        lang = body.get('lang', 'en')
        sms_child_request = get_child_request(child_request_id, lang)
        if not sms_child_request:
            return [{'invalid_sms_child_request': True}]
        if sms_child_request.sponsorship_confirmed:
            return [{'sponsorship_confirmed': True}]
        if sms_child_request.child_id:
            child = sms_child_request.child_id
            result = child.get_sms_sponsor_child_data()
            partner = sms_child_request.partner_id
            if sms_child_request.partner_id:
                result['partner'] = partner.read(['firstname', 'lastname',
                                                  'email'])
            return result

        # No child for this request, we try to fetch one
        if not sms_child_request.is_trying_to_fetch_child:
            sms_child_request.is_trying_to_fetch_child = True
            sms_child_request.with_delay().reserve_child()
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
        sms_child_request = get_child_request(child_request_id,
                                              body.get('lang', 'en_US'))
        if sms_child_request:
            sms_child_request.ensure_one()
            body['phone'] = sms_child_request.sender
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
        sms_child_request = get_child_request(child_request_id,
                                              body.get('lang', 'en_US'))
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
    @route('/sms_sponsorship/step2/<model("recurring.contract"):sponsorship>/',
           auth='public', website=True)
    def step2_confirm_sponsorship(self, sponsorship=None, **kwargs):
        """ SMS step2 controller. Returns the sponsorship registration form."""
        return self.make_response(
            'recurring.contract',
            model_id=sponsorship and sponsorship.id,
            **kwargs
        )

    @route('/sms_sponsorship/step2/<model("recurring.contract"):sponsorship>/'
           'confirm', type='http', auth='public',
           methods=['GET'], website=True)
    def sms_registration_confirmation(self, sponsorship=None):
        values = {
            'sponsorship': sponsorship.sudo()
        }
        return request.render(
            'sms_sponsorship.sms_registration_confirmation', values)
