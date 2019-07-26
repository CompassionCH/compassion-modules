##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <michaelsandoz87@gmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import http
from odoo.http import request

from werkzeug.wrappers import Response
from werkzeug.datastructures import Headers

_logger = logging.getLogger(__name__)


class RestController(http.Controller):
    """
    Test Controller that could be called by a directly connected website
    for requesting children from the global childpool.
    """

    @http.route('/web_children_hold', type='http', auth='public', methods=[
        'GET'])
    def handler_web_children_hold(self):

        headers = request.httprequest.headers
        self._validate_headers(headers)

        # load children via a research on childpool
        child_research = request.env['compassion.childpool.search'].sudo()
        research = child_research.create({'take': 5})
        research.rich_mix()

        # create a hold for all children found
        research.with_delay().hold_children_job()

        data = ""
        # return principal children info
        for child in research.global_child_ids:
            if child.image_url:
                data += '<img src="' + child.image_url + '"/> <br>'
            data += child.name + ' ' + child.birthdate + '<br>'

        headers = Headers()
        response = Response(data, content_type='text/html', headers=headers)

        return response

    def _validate_headers(self, headers):
        pass
