# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import simplejson

from base_test_onramp import TestOnramp


class TestUpdateCommkit(TestOnramp):
    """ All Commkit messages tests. """

    def test_valid_post(self):
        response = self._send_post({
            'Beneficiary': {
                'Age': 13,
            }
        })
        self.assertTrue(response.code, 201)
        result = simplejson.loads(response.read())
        self.assertTrue('ConfirmationId' in result)
        self.assertFalse('ErrorId' in result)
        self.assertEqual(result['Message'],
                         'Your message was successfully received.')

    def test_bad_scenarios(self):
        self._test_no_token()
        self._test_bad_token()
        self._test_body_no_json()
