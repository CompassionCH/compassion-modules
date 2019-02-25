# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from .onramp_base_test import TestOnramp


class TestOnRampController(TestOnramp):

    def setUp(self):
        super(TestOnRampController, self).setUp()

    def test_no_token(self):
        """ Check we have an access denied if token is not provided
        """
        self.opener.addheaders = [pair for pair in self.opener.addheaders
                                  if pair[0] != 'Authorization']
        response = self._send_post({'nothing': 'nothing'})
        self.assertEqual(response.code, 401)
        self.assertEqual(response.msg, 'UNAUTHORIZED')

    def test_bad_token(self):
        """ Check we have an access denied if token is not valid
        """
        self.opener.addheaders.append(('Authorization', 'Bearer notrealtoken'))
        response = self._send_post({'nothing': 'nothing'})
        self.assertEqual(response.code, 403)
        self.assertEqual(response.msg, 'FORBIDDEN')
