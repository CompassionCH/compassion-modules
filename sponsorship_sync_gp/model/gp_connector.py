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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from mysql_connector.model.mysql_connector import mysql_connector
from sponsorship_compassion.model.product import GIFT_TYPES
from datetime import datetime, date
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
        'Web Payment': 'WEB',
    }

    # Mapping for child transfers to exit_reason_code in GP
    transfer_mapping = {
        'AU': '15',
        'CA': '16',
        'DE': '17',
        'ES': '38',
        'FR': '18',
        'GB': '20',
        'IT': '19',
        'KR': '37',
        'NL': '35',
        'NZ': '40',
        'US': '21',
    }

    channel_mapping = {
        'postal': 'C',
        'direct': 'D',
        'email': 'E',
        'internet': 'I',
        'phone': 'T',
        'payment': 'V'
    }

    origin_mapping = {
        'partner': 'A',
        'event': 'E',
        'marketing': 'E',
        'sub': 'R',
        'transfer': 'T',
        'already_sponsor': 'P',
        'other': 'D'
    }

    def create_or_update_contract(self, uid, contract):
        """ Read new contract information and convert it to GP Poles
            structure. """
        typevers = self._find_typevers(
            contract.group_id.payment_term_id.name, 'OP')
        origin = self._find_origin(contract)
        iduser = self.selectOne('SELECT ID FROM login WHERE ERP_ID = %s;',
                                uid)
        iduser = iduser.get('ID', 'EC')
        typeprojet = 'P' if contract.child_id else 'T'
        codespe = self._find_codespe(contract)
        if len(codespe) > 1:
            raise orm.except_orm(
                _("Not compatible with GP"),
                _("GP cannot handle multiple funds in one contract. Please "
                  "make a different contract for each supported fund."))

        vals = {
            'codega': contract.correspondant_id.ref,
            'base': contract.total_amount,
            'typevers': typevers,
            'iduser': iduser,
            'freqpaye': self.freq_mapping[contract.group_id.advance_billing],
            'ref': contract.group_id.bvr_reference or
            contract.group_id.compute_partner_bvr_ref(),
            'num_pol_ga': contract.num_pol_ga,
            'codega_fin': contract.partner_id.ref,
            'id_erp': contract.id,
        }

        if contract.state == 'draft':
            # Fields updated only in draft state
            vals.update({
                'typep': 'C',
                'codespe': codespe[0],
                'origine': origin,
                'datecreation': contract.start_date,
                'datedebut': contract.next_invoice_date,
                'typeprojet': typeprojet,
            })

        insert_string = "INSERT INTO Poles (%s) VALUES(%s) "\
                        "ON DUPLICATE KEY UPDATE %s;"
        col_string = ",".join(vals.keys())
        values_string = ",".join([
            "'" + value + "'" if isinstance(value, basestring) else str(value)
            for value in vals.values()])
        update_string = ",".join([key + "=VALUES(" + key + ")"
                                  for key in vals.keys()])
        sql_query = insert_string % (col_string, values_string, update_string)
        logger.info(sql_query)

        return self.query(sql_query)

    def _find_typevers(self, payment_term_name, default):
        for term in self.terms_mapping.keys():
            if payment_term_name and term in payment_term_name:
                return self.terms_mapping[term]

        # If nothing, found return the requested default value
        return default

    def _find_origin(self, contract):
        channel = self.channel_mapping[contract.channel]
        origin = self.origin_mapping[contract.origin_id.type]
        return channel + origin

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
            if gp_fund_ids:
                rows = self.selectAll(find_fund_query % ",".join(gp_fund_ids))
            elif not contract.state == 'draft':
                # If no fund is selected, it means a sponsorship should be set
                raise orm.except_orm(
                    _("Missing child"),
                    _("You forgot to specify the child for this sponsorship.")
                )
            else:
                return [""]
            return [row.get('CODESPE') for row in rows]

    def validate_contract(self, contract):
        """ Compute for which month the sponsor will pay, based on
        next_invoice_date.
        """
        # Check that the codespe is correct
        self._find_codespe(contract)
        next_invoice_date = datetime.strptime(contract.next_invoice_date,
                                              DF).date()
        # Month corresponds to number of months already paid
        month = next_invoice_date.month
        today = date.today()
        if next_invoice_date.day <= 15:
            month -= 1
        if month == 0 and today.month == 12:
            month = 12
        date_start = next_invoice_date.replace(day=1)
        return self.query(
            "UPDATE Poles SET mois=%s, datedebut=%s WHERE id_erp=%s",
            [month, date_start, contract.id])

    def activate_contract(self, contract):
        sql_query = "UPDATE Poles SET typep=%s, bascule=curdate(), "\
                    "datepremier=%s WHERE id_erp={}".format(contract.id)
        typep = '+' if contract.total_amount > 42 else 'S'
        return self.query(sql_query, [typep, contract.activation_date])

    def finish_contract(self, contract):
        state = 'F' if contract.state == 'terminated' else 'A'
        end_reason = contract.end_reason
        res = True
        # If reason is '1' (child departure), the case is handled in
        # set_child_sponsor_state method, when the child is marked as departed
        if end_reason != '1':
            res = self.query(
                "UPDATE Poles SET typep=%s, datefin=curdate(), "
                "id_motif_fin=%s WHERE id_erp = %s",
                [state, end_reason, contract.id])
            if contract.child_id:
                res = res and self.query("UPDATE Enfants SET id_motif_fin=%s "
                                         "WHERE code=%s",
                                         [end_reason, contract.child_id.code])
        return res

    def register_payment(self, contract_id, payment_date=None, amount=1):
        """ When a new payment is done (invoice paid), update the Sponsorship
        in GP. """
        sql_date = ", datedernier='{}'".format(payment_date) \
            if payment_date else ""
        sql_query = "UPDATE Poles SET MOIS=MOIS+{:d}{} " \
                    "WHERE id_erp={:d}".format(amount, sql_date, contract_id)
        logger.info(sql_query)
        return self.query(sql_query)

    def undo_payment(self, contract_id, amount=1):
        """ Set the MOIS value backwards. """
        return self.query("UPDATE Poles SET MOIS=MOIS-{:d} WHERE id_erp={:d}"
                          .format(amount, contract_id))

    def insert_affectat(self, uid, invoice_line, payment_date):
        """ When a new payment is done (invoice paid), update the Sponsorship
        in GP, and add a line for this payment. """
        contract = invoice_line.contract_id
        product = invoice_line.product_id

        # Determine the nature of the payment (sponsorship, fund)
        if product.name in GIFT_TYPES + ['Sponsorship', 'LDP Sponsorship']:
            if not contract:
                raise orm.except_orm(
                    _('Missing sponsorship'),
                    _('Invoice line for sponsor %s is missing a sponsorship')
                    % invoice_line.partner_id.name)
            codespe = contract.child_id.code
            if 'LDP' in product.name:
                codespe = 'LDP'
            typeprojet = "P"
            id_pole = self.selectOne(
                "Select id_pole FROM Poles WHERE id_erp=%s",
                contract.id).get("id_pole")
        else:   # Fund donation
            gp_fund_id = product.gp_fund_id
            codespe = self.selectOne(
                "SELECT Codespe FROM Libspe WHERE ID_CODE_SPE = %s",
                gp_fund_id).get("Codespe", "")
            typeprojet = "T"
            id_pole = 0

        # Determine if payment was a gift for a supported child
        cadeau = 0
        typecadeau = 0
        libcadeau = ""
        if product.name in GIFT_TYPES:
            cadeau = 1
            typecadeau = GIFT_TYPES.index(product.name) + 1
            libcadeau = invoice_line.name

        payment_term = self._find_typevers(
            invoice_line.invoice_id.payment_term.name, 'BVR')
        iduser = self.selectOne(
            'SELECT ID FROM login WHERE ERP_ID = %s;', uid).get('ID', 'EC')

        vals = {
            'CODEGA': invoice_line.partner_id.ref,
            'NUMVERS': invoice_line.invoice_id.id,
            'CODESPE': codespe,
            'MONTANT': invoice_line.price_subtotal,
            'DATE': invoice_line.invoice_id.date_invoice,
            'TYPEVERS': payment_term,
            'JNLVERS': product.property_account_income.code,
            'CADEAU': cadeau,
            'TITULAIRE': invoice_line.partner_id.name,
            'IDUSER': iduser,
            'PARTICULIER': 1,
            'TYPEPROJET': typeprojet,
            'LIBCADEAU': libcadeau,
            'TYPECADEAU': typecadeau,
            'REF': invoice_line.invoice_id.bvr_reference,
            'DATEFISCALE': payment_date,
            'DATE_SAISIE': date.today().strftime('%Y-%m-%d'),
            'ID_POLE': id_pole,
            'MOIS': 1 if cadeau == 0 else 0,
            'ID_ERP': invoice_line.id,
        }
        if not id_pole:
            del vals['ID_POLE']
        insert_affectat = "INSERT INTO Affectat(%s) VALUES (%s) " \
            "ON DUPLICATE KEY UPDATE %s"
        update_string = ",".join([key + "=VALUES(" + key + ")"
                                  for key in vals.keys()])
        sql_query = insert_affectat % (
            ",".join(vals.keys()),
            ",".join(["%s" for i in range(0, len(vals))]),
            update_string)

        return self.query(sql_query, vals.values())

    def remove_affectat(self, invoice_id, invoice_date):
        max_date = self.selectOne("SELECT MAX(Date) AS Date FROM Affectat "
                                  "WHERE Numvers=%s",
                                  invoice_id).get("Date", invoice_date)
        return self.query(
            "DELETE FROM Affectat WHERE Numvers=%s AND DATE>=%s",
            [invoice_id, max_date])

    def set_child_sponsor_state(self, child):
        update_string = "UPDATE Enfants SET %s WHERE code='%s'"
        update_fields = "situation='{}'".format(child.state)
        if child.sponsor_id:
            update_fields += ", codega='{}'".format(child.sponsor_id.ref)

        if child.state == 'F':
            # If the child is sponsored, mark the sponsorship as terminated in
            # GP and set the child exit reason in tables Poles and Enfant
            end_reason = child.gp_exit_reason or \
                self.transfer_mapping[child.transfer_country_id.code]
            update_fields += ", id_motif_fin={}".format(end_reason)
            # We don't put a child transfer in ending reason of a sponsorship
            if not child.transfer_country_id:
                pole_sql = "UPDATE Poles SET TYPEP = IF(TYPEP = 'C', " \
                           "'A', 'F'), id_motif_fin={}, datefin=curdate() " \
                           "WHERE codespe='{}' AND TYPEP NOT IN " \
                           "('F','A')".format(end_reason, child.code)
                logger.info(pole_sql)
                self.query(pole_sql)

        if child.state == 'P':
            # Remove delegation and end_reason, if any was set
            update_fields += ", datedelegue=NULL, codedelegue=''" \
                             ", id_motif_fin=NULL"

        sql_query = update_string % (update_fields, child.code)
        logger.info(sql_query)
        return self.query(sql_query)

    def delete_contracts(self, ids):
        return self.query(
            "DELETE FROM Poles WHERE id_erp IN (%s)", ",".join(
                str(id) for id in ids))
