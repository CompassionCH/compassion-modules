# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <michaelsandoz87@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging
import pdb
from datetime import datetime
from datetime import timedelta

from openerp import http
from openerp.http import request

from werkzeug.wrappers import Response
from werkzeug.datastructures import Headers

_logger = logging.getLogger(__name__)


class RestController(http.Controller):

    @http.route('/web_children_hold', type='http', auth='public', methods=[
        'GET'])
    def handler_web_children_hold(self):

        headers = request.httprequest.headers
        self._validate_headers(headers)

        # load children via a research on childpool
        child_research = request.env['compassion.childpool.search'].sudo()
        research = child_research.create({'take': 5})
        research.rich_mix()

        #####################################################
        # C'est ici que ça bug
        #####################################################
        # create a hold for all children found
        child_hold = request.env['child.hold.wizard'].sudo()
        expiration_date = datetime.now() + timedelta(minutes=15)

        holds = child_hold.create({
            'type': 'Reservation Hold',
            'hold_expiration_date': expiration_date.strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            'primary_owner': 'Roma Reber',
            'secondary_owner': 'Carole Rochat',
            'no_money_yield_rate': '1.1',
            'yield_rate': '1.1',
            'channel': 'Site',
        })
        holds.send()

        #####################################################
        # A corriger ICI AUSSI
        #####################################################
        data = ""
        # return principal children info
        for child in child_research.global_child_ids:
            data += child.name + child.birthdate + '<br>'

        # data = "Salut c'est un test ! {}".format(research.take)
        headers = Headers()
        pdb.set_trace()
        response = Response(data, content_type='text/html', headers=headers)

        return response

    def _validate_headers(self, headers):
        pass
