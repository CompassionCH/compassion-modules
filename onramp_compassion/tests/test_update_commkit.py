# -*- coding: utf-8 -*-
#
#    Author: Yannick Vaucher
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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
        result = simplejson.loads(response.read()).get('result')
        self.assertTrue('ConfirmationId' in result)
        self.assertFalse('ErrorId' in result)
        self.assertEqual(result['Message'],
                         'Your message was successfully received.')
