# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.tests import common
from openerp.tools.config import config

from ..model import gp_connector
import logging

logger = logging.getLogger(__name__)


class test_contracts(common.TransactionCase):
    """ Test Contracts Synchronization with GP """

    def setUp(self):
        super(test_contracts, self).setUp()
        self.gp_connect = gp_connectorGPConnect(self.cr, self.uid)

    def _create_contract_for_cino(self, vals):
        """ Creates a new contract for partner Emanuel Cino """
        cino_id = self.registry('res.partner').search(
            self.cr, self.uid, [('name', 'like', 'Cino Emanuel')])
        con_obj = self.registry('recurring.contract')
        cino_con_id = con_obj.search(self.cr, self.uid,
                                     [('partner_id', 'in', cino_id)])
        self.assertTrue(cino_con_id)
        origin_ids = self.registry('recurring.contract.origin').search(
            self.cr, self.uid, [('name', 'like', 'Other')])
        vals.update({
            'origin_id': origin_ids[0],
            'channel': 'D'
        })
        self.assertTrue(
            con_obj.copy(self.cr, self.uid, cino_con_id[0], default=vals))
        res_ids = con_obj.search(
            self.cr, self.uid,
            [('partner_id', 'in', cino_id), ('state', '=', 'draft')])
        self.assertTrue(res_ids)
        return res_ids[0]
        

    def test_config_set(self):
        """Test that the config is properly set on the server
        """
        host = config.get('mysql_host')
        user = config.get('mysql_user')
        pw = config.get('mysql_pw')
        db = config.get('mysql_db')
        self.assertTrue(host)
        self.assertTrue(user)
        self.assertTrue(pw)
        self.assertTrue(db)
        self.assertTrue(self.gp_connect.is_alive())

    def test_sponsor_child(self):
        """ Test synchronization with GP. when a child is sponsored. """
        # Find an available child
        child_obj = self.registry('compassion.child')
        child_ids = child_obj.search(self.cr, self.uid,
                                     [('state', 'in', ('N', 'R'))])
        self.assertTrue(child_ids)
        child_id = child_ids[0]
        old_child_state = child_obj.browse(self.cr, self.uid, child_id).state

        # Test that the state of the child is the same in GP and Odoo
        child_state_sql = "SELECT Situation FROM Enfants WHERE id_erp = %s"
        gp_state = self.gp_connect.selectOne(child_state_sql, child_id).get(
            "Situation")
        self.assertEqual(old_child_state, gp_state)

        # Create new contract
        con_id = self._create_contract_for_cino({
            'child_id': child_id
        })

        # Test that the child is marked as sponsored in GP and Odoo
        child = child_obj.browse(self.cr, self.uid, child_id)
        child_state = child.state
        self.assertEqual(child_state, 'P')
        gp_query = .format(
            child_id)
        gp_state = self.gp_connect.selectOne(child_state_sql, child_id).get(
            "Situation")
        self.assertEqual(gp_state, 'P')

        # Various checks on child object
        self.assertTrue(child.sponsor_id)
        self.assertTrue(child.has_been_sponsored)
        
        # TODO : Validate contract, make a payment, end sponsorship
        # test synchronization for all states
