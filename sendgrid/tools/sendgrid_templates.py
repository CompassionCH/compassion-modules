# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller
#
#    The licence is in the file __openerp__.py
#
##############################################################################


class Templates(object):
    """The transactional templates API lets you programmatically create and
    manage templates for your transactional email."""

    def __init__(self, client, **opts):
        """
        Constructs SendGrid Templates object.

        See https://sendgrid.com/docs/API_Reference/Web_API_v3/Transactional_Templates/templates.html
        """
        self._base_endpoint = "/v3/templates"
        self._endpoint = "/v3/templates"
        self._client = client

    @property
    def base_endpoint(self):
        return self._base_endpoint

    @property
    def endpoint(self):
        endpoint = self._endpoint
        return endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    @property
    def client(self):
        return self._client

    def get(self):
        return self.client.get(self)
