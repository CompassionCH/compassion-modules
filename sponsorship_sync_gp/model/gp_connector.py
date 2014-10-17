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

from openerp.osv import orm
from openerp.tools.translate import _
from mysql_connector.model.mysql_connector import mysql_connector
from datetime import date
import logging

logger = logging.getLogger(__name__)


class GPConnect(mysql_connector):

    """ Contains all the utility methods needed to talk with the MySQL server
        used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields. """
    # Mapping for determining frequency of payment in GP
    freq_mapping = {
        'monthly': 1,
        'bimonthly': 2,
        'quarterly': 3,
        'fourmonthly': 4,
        'biannual': 6,
        'annual': 12
    }

    # Mapping for determining type of payment in GP
    terms_mapping = {
        'BVR': 'BVR',
        'LSV': 'LSV',
        'Postfinance': 'DD',
        'Permanent Order': 'OP',
        'Bank Transfer': 'VIR',
    }

    def create_contract(self, uid, contract):
        """ Read new contract information and convert it to GP Poles
            structure. """
        typevers = self._find_typevers(contract.group_id.payment_term_id.name)
        origin = self._find_origin()
        iduser = self.selectOne('SELECT ID FROM login WHERE ERP_ID = %s;', uid)
        iduser = iduser.get('ID') if iduser else 'EC'
        typeprojet = 'P' if contract.child_id else 'T'
        codespe = self._find_codespe(contract)
        if len(codespe) > 1:
            raise orm.except_orm(
                _("Not compatible with GP"),
                _("GP cannot handle multiple funds in one contract. Please "
                  "make a different contract for each supported fund."))

        fields_create = {
            'codega': contract.correspondant_id.ref,
            'codespe': codespe[0],
            'typep': 'C',
            'base': contract.total_amount,
            'typevers': typevers,
            'origine': origin,
            'iduser': iduser,
            'freqpaye': self.freq_mapping[contract.group_id.advance_billing],
            'datecreation': date.today().strftime('%Y-%m-%d'),
            'datedebut': contract.start_date,
            'ref': contract.group_id.bvr_reference,
            'typeprojet': typeprojet,
            'num_pol_ga': contract.num_pol_ga,
            'codega_fin': contract.partner_id.ref,
            'id_erp': contract.id,
        }

        # TODO : Parrainage Plus ???
        insert_string = "INSERT INTO Poles (%s) VALUES(%s);"
        col_string = ",".join(fields_create.keys())
        values_string = ",".join([
            "'" + value + "'" if isinstance(value, basestring) else str(value)
            for value in fields_create.values()])
        sql_query = insert_string % (col_string, values_string)
        logger.info(sql_query)

        return self.query(sql_query)

    def _find_typevers(self, payment_term_name):
        for term in self.terms_mapping.keys():
            if term in payment_term_name:
                return self.terms_mapping[term]

        # If nothing, found return 'OP' by default
        return 'OP'

    def _find_origin(self):
        # TODO : Implement this !
        return 'DD'

    def _find_codespe(self, contract):
        """ Finds the given CODESPE from GP given the nature of the contract.

        - Sponsorship :   returns a list of one item containing the child_code
                          of the sponsored kid.
        - Fund donation : returns a list of the corresponding CODESPE for
                          each contract_line.
        """
        if contract.child_id:
            return [contract.child_code]
        else:
            find_fund_query = 'SELECT CODESPE FROM Libspe '\
                              'WHERE ID_CODE_SPE IN (%s)'
            gp_fund_ids = [str(line.product_id.gp_fund_id)
                           for line in contract.contract_line_ids
                           if line.product_id.gp_fund_id]
            rows = self.selectAll(find_fund_query % ",".join(gp_fund_ids))
            return [row.get('CODESPE') for row in rows]

    def cancel_contract(self, contract_id):
        return self.query(
            "UPDATE Poles SET typep='A', datefin=curdate() WHERE id_erp = %s",
            contract_id)

    def activate_contract(self, contract):
        sql_query = "UPDATE Poles SET typep=%s, bascule=curdate(), "\
                    "datepremier=%s WHERE id_erp={}".format(contract.id)
        typep = '+' if contract.total_amount > 42 else 'S'
        return self.query(sql_query, [typep, contract.first_payment_date])

    def finish_contract(self, contract_id):
        return self.query(
            "UPDATE Poles SET typep='F', datefin=curdate() WHERE id_erp = %s",
            contract_id)

    def register_payment(self, contract_id, payment_date):
        sql_query = "UPDATE Poles SET datedernier=%s WHERE id_erp=%s"
        return self.query(sql_query, [payment_date, contract_id])
