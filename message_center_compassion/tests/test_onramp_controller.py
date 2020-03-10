##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from mock import patch

from .onramp_base_test import TestOnramp

mock_oauth = (
    "odoo.addons.message_center_compassion.models.ir_http.IrHTTP._oauth_validation"
)


class TestOnRampController(TestOnramp):
    def setUp(self):
        super().setUp()

    def test_no_token(self):
        """ Check we have an access denied if token is not provided
        """
        del self.opener.headers["Authorization"]
        response = self._send_post({"nothing": "nothing"})
        self.assertEqual(response.status_code, 401)
        error = response.json()
        self.assertEqual(error["ErrorMethod"], "ValidateToken")

    def test_bad_token(self):
        """ Check we have an access denied if token is not valid
        """
        self.opener.headers["Authorization"] = "Bearer notrealtoken"
        response = self._send_post({"nothing": "nothing"})
        self.assertEqual(response.status_code, 401)

    @patch(mock_oauth)
    def test_wrong_client_id(self, oauth_patch):
        """ Check that if we get a token with unrecognized client_id,
        access is denied. """
        oauth_patch.return_value = "wrong_user"
        response = self._send_post({"nothing": "nothing"})
        self.assertEqual(response.status_code, 401)

    @patch(mock_oauth)
    def test_good_client_id(self, oauth_patch):
        """ Check that if we connect with admin as client_id,
        access is granted. """
        oauth_patch.return_value = "admin"
        response = self._send_post({"nothing": "nothing"})
        json_result = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json_result["Message"], "Unknown message type - not processed."
        )
