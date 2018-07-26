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

from odoo.addons.cms_form.controllers.main import FormControllerMixin
from odoo.addons.website_portal.controllers.main import website_account
from odoo.http import route
from odoo.http import request
from odoo import http
import werkzeug.utils


def get_child_request(request_id):
    return request.env['sms.child.request'].sudo() \
        .search([('id', '=', int(request_id))])


class SmsSponsorshipWebsite(website_account, FormControllerMixin):
    @route('/sms-sponsorship/step2/<model("recurring.contract"):sponsorship>/',
           auth='public', website=True)
    def sms_partner_register(self, sponsorship=None, **kwargs):
        model = 'recurring.contract'
        return self.make_response(model,
                                  model_id=sponsorship and sponsorship.id,
                                  **kwargs)


class SmsSponsorshipController(http.Controller):
    @route('/sms_sponsorship_api', type='json',
           auth='public', methods=['POST'], csrf=False)
    def sms_sponsorship_api_handler(self, **kwargs):
        request_id = request.jsonrequest['child_request_id']
        sms_child_request = get_child_request(request_id)
        if not sms_child_request:
            return [{'invalid_sms_child_request': True}]
        if sms_child_request.sponsorship_confirmed:
            return [{'sponsorship_confirmed': True}]
        if sms_child_request.child_id:
            child = sms_child_request.child_id
            result = child.read(['name', 'birthdate', 'display_name',
                                 'desc_en', 'field_office_id', 'gender',
                                 'image_url', 'age'])
            result[0]['has_a_child'] = True
            result[0]['invalid_sms_child_request'] = False
            result[0]['countries'] = sms_child_request.field_office_id\
                .search([]).filtered('available_on_childpool')\
                .mapped(lambda x: {
                    'value': x.country_code,
                    'text': x.name
                })
            partner = sms_child_request.partner_id
            if sms_child_request.partner_id:
                result[0]['partner'] = partner.read(['firstname', 'lastname',
                                                     'email'])
            return result
        return [{'has_a_child': False, 'invalid_sms_child_request': False}]

    @route('/sponsor-now/<int:child_request_id>', auth='public',
           website=True)
    def sms_redirect(self, child_request_id=None):
        url = '/sms_sponsorship/static/index.html?child_request_id=' +\
              str(child_request_id)
        # redirects to webapp
        return werkzeug.utils.redirect(url, 301)

    @route('/sms_sponsor_confirm', type='json', auth='public',
           methods=['POST'], csrf=False)
    def sms_sponsor_confirm(self):
        env = request.env
        body = request.jsonrequest
        request_id = body['child_request_id']
        sms_child_request = get_child_request(request_id)
        if sms_child_request:
            sms_child_request.ensure_one()
            body['phone'] = sms_child_request.sender
            partner = sms_child_request.partner_id \
                if sms_child_request.partner_id else False
            env['recurring.contract'].with_delay().create_sms_sponsorship(
                vals=body,
                partner=partner,
                sms_child_request=sms_child_request
            )
            sms_child_request.write({'sponsorship_confirmed': True})
            return {'result': 'success'}

    @route('/sms_change_child', type='json', auth='public',
           methods=['POST'], csrf=False)
    def sms_change_child(self):
        body = request.jsonrequest
        request_id = body['child_request_id']
        sms_request = get_child_request(request_id)
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
            field_office = request.env['compassion.field.office']\
                .search([('country_code', '=', body['country'])], limit=1)
            if field_office:
                tw['field_office_id'] = field_office.id
            else:
                tw['field_office_id'] = False
        else:
            tw['field_office_id'] = False
        if tw:
            sms_request.write(tw)

        sms_request.change_child()
