# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging
from openerp import http, fields
from openerp.exceptions import MissingError
from openerp.addons.website_crm.controllers.main import contactus

logger = logging.getLogger(__name__)


class EventForm(http.Controller):
    @http.route(['/events', '/events/<int:event_id>'], type='http',
                auth='public', website=True)
    def index(self, **kwargs):
        request = http.request.httprequest
        path = request.path.split('/')
        try:
            event_id = int(path[-1])
            event = http.request.env['crm.event.compassion'].sudo().browse(
                event_id)
            if event:
                return http.request.render(
                    'website_crm_compassion.event_contactus_form', {
                        'name': event.name,
                        'event_id': event_id,
                    }
                )
        except (ValueError, MissingError):
            logger.warning("No valid event found")

        # Fallback case with no event
        return http.request.render(
            'website.contactus', {
                'kwargs': kwargs.items()
            }
        )

    @http.route('/events/contactus', type='http', auth='public', website=True)
    def contactus(self, **kwargs):
        kwargs['contact_name'] = kwargs['contact_firstname'] + ' ' + kwargs[
            'contact_name']
        del kwargs['contact_firstname']

        description = 'Submitted at ' + fields.Datetime.now() + '\n\n'
        birthdate = kwargs.get('contact_birthdate')
        if birthdate:
            description += '* Birthdate : ' + birthdate + '\n'
        del kwargs['contact_birthdate']
        if kwargs.get('magazine'):
            description += '* I want the magazine\n'
            del kwargs['magazine']
        if kwargs.get('volunteer'):
            description += '* I want to volunteer!\n'
            del kwargs['volunteer']
        if kwargs.get('church_presentation'):
            description += '* I want a church presentation!\n'
            del kwargs['church_presentation']
        if kwargs.get('contest'):
            description += '* I participate to the Poverty Bible Contest!\n'
            del kwargs['contest']
        kwargs['description'] = description
        crm_controller = contactus()
        crm_controller.contactus(**kwargs)
        return http.request.render(
            'website_crm_compassion.contactus_thanks', {
                'event_id': kwargs['event_id']
            }
        )
