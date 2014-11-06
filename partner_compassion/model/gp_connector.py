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

from mysql_connector.model.mysql_connector import mysql_connector


class GPConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields.
    """

    # Used to map Postgres columns to MySQL columns. The update method will
    # automatically translate fields that are listed in this dictionary.
    # The commented mappings are treated specifically by a method that needs
    # to read several fields value in order to perform a correct mapping.
    colMapping = {
        'id': 'erp_id',
        'lang': 'langue_parrain',
        'street': 'rue',
        'street2': 'rue2',
        'street3': 'rue3',
        'city': 'commune',
        'zip': 'codepostal',
        'country_id': 'codepays',
        'title': 'titre',
        'function': 'metier',
        'email': 'e_mail',
        'website': 'web',
        'fax': 'numfax',
        'phone': 'teldom',
        'date': 'datecreation',
        'mobile': 'telmobile',
        # 'ref' : 'codega',
        'lastname': 'nom',
        'firstname': 'prenom',
        'church_id': 'eglise',
        'church_unlinked': 'eglise',
        'deathdate': 'datedeces',
        'nbmag': 'nbsel',
        'birthdate': 'anneenaissance',
        # 'category_id' : '',         --- not directly translated to a field,
        #                                 but to several rows in another table
        'tax_certificate': 'recu_annuel',
        'thankyou_letter': 'recu_immediat',
        'calendar': 'calendrier',
        'christmas_card': 'carte_noel',
        'birthday_reminder': 'rappel_anniversaire',
        # 'abroad': '',               --- treated with the categories
        # 'opt_out': '',              --- treated with the categories
    }

    # This gives the MySQL Sponsor Category ids corresponding to the Category
    # Names defined in OpenERP.
    # Please ensure that the mapping is up to date and correct (this saves a
    # lot of useless queries).
    catMapping = {
        'Donor': '1',
        'Sponsor': '2',
        'Ambassador': '3',
        'Church': '4',
        'Translator': '5',
        'Complete Mailing': '6',
        'Abroad': '7',
        'Correspondance Program': '8',
        'Correspondance by Compassion': '9',
        'Old Sponsor': '10'
    }

    # Gives the language in the format stored in the MySQL database.
    langMapping = {
        'fr_CH': 'fra',
        'fr_FR': 'fra',
        'de_DE': 'deu',
        'en_US': 'eng',
        'en_UK': 'eng',
        'it_IT': 'ita',
        'es_ES': 'esp'
    }

    # Gives the corresponding title ID in the MySQL database.
    titleMapping = {
        'Mister': '1',
        'Madam': '2',
        'Misters': '4',
        'Ladies': '5',
        'Mister and Madam': '7',
        'Family': '8',
        'Doctor': '9',
        'Pastor': '10',
        'Friends of Compassion': '11'
    }

    def createPartner(self, uid, vals, record, id, titleName=None,
                      churchRef=None, categories=None, countryCode=None):
        """ Export a new partner into the MySQL Address table. If the
        reference is a new number, it inserts a line in the MySQL Address
        Table and then call the update method to set properly all the fields.
        Otherwise, it updates the MySQL Address table so that the partner is
        linked to the corresponding reference.

        Args:
            vals (dict): the fields values of the new partner. The accepted
                         values are listed in the 'colMapping' dictionary.
            record (res.partner): the current res.partner object that is
                                  created.
            id (long) : the partner id that will be referenced in the
                        MySQL Address table.
            *titleName (string): full title name of the partner,
                                 must be given in english.
            *churchRef (string): reference number (CODEGA) of the partner's
                                 church.
            *categories (list): full names of the partner's categories.
            *countryCode (string): two letters country code of the partner's
                                   country.

        Returns:
            The result of the execution of the MySQL query.

        Raises:
            Some errors if the query contains errors due to invalid
            field names or values.
        """
        sql = "INSERT INTO Adresses (CODEGA, id_erp, DATECREATION, IDUSER) " \
              "VALUES (%s,%s, NOW(), (SELECT ID FROM login WHERE " \
              "ERP_ID = %s)) on duplicate key UPDATE id_erp=values(id_erp)"
        if self.query(sql, (vals['ref'], id, uid)):
            # Remove unset fields
            for name in vals.keys():
                if not vals[name] and not name == 'opt_out':
                    del(vals[name])
            return self.updatePartner(uid, vals, record, titleName, churchRef,
                                      categories, countryCode, False)

    def updatePartner(self, uid, vals, record, titleName=None, churchRef=None,
                      categories=None, countryCode=None, deleteAbsent=True):
        """ Synchronize the MySQL Address table with the partner in Odoo,
        by updating values provided in vals and in optional arguments.

            Args:
                vals (dict): the fields values of the new partner.
                             The accepted values are listed in the
                             'colMapping' dictionary.
                record (res.partner): the current res.partner object
                                      that is updated.
                *titleName (string): full title name of the partner,
                                     must be given in english.
                *churchRef (string): reference number (CODEGA) of the
                                     partner's church.
                *lang (string): the spoken language of the partner.
                *categories (list): of full names of the partner's categories.
                *countryCode (string): two letters country code of the
                                       partner's country.
                *deleteAbsent (boolean): if set to false, no category will be
                                         deleted even if it is absent in Odoo.

            Returns:
                The result of the execution of the MySQL query.

            Raises:
                Some errors if the query contains errors due to invalid
                field names or values.
        """

        sqlQuery = "UPDATE Adresses SET {0} WHERE CODEGA = '" + \
            record.ref + "' OR id_erp = " + str(record.id)
        # Holds the SQL string that will list the updates to perform.
        fieldsUpdate = ""

        # If it is a company, we change the name mapping
        if record.is_company:
            self.colMapping['lastname'] = 'raissociale'

        for name, value in vals.iteritems():
            # Holds the converted value to insert in the MySQL table.
            mVal = ""
            # Used to add an escape character to string values (')
            mString = ""

            # Convert the language
            if name == 'lang':
                mVal = self.langMapping[value]
                mString = "'"
            # Convert the country code (use the code instead of the id)
            elif name == 'country_id':
                mVal = countryCode
                mString = "'"
            # These are the fields that need no particular transformation
            elif name in ('city', 'zip', 'function', 'email', 'website',
                          'fax', 'phone', 'date', 'mobile', 'lastname',
                          'firstname', 'street', 'street2', 'street3',
                          'deathdate', 'birthdate', 'church_unlinked'):
                mVal = value
                mString = "'"
            # Non string fields that need no particular transformation
            elif name in ('nbmag', 'calendar', 'birthday_reminder',
                          'christmas_card'):
                mVal = str(value)
            # Convert the title (use the correct ids found in the MySQL
            # database)
            elif name == 'title' and titleName:
                mVal = self.titleMapping[titleName]
            # Convert the church (use the reference number instead of the id)
            elif name == 'church_id':
                mVal = churchRef
            # Convert the categories (insert the correct ids found
            # in the MySQL database)
            elif name == 'category_id':
                self._updateCategories(record.ref, categories, deleteAbsent)
            # Convert the 'abroad' Category
            elif name == 'abroad':
                self._updateBooleanCategory(record.ref, 'Abroad', value)
            # Convert the 'opt_out' (Mailing complet) Category
            elif name == 'opt_out':
                # Add the category if the value is False !
                self._updateBooleanCategory(
                    record.ref, 'Complete Mailing', not value)
            # Convert the receipts
            elif name in ('tax_certificate', 'thankyou_letter'):
                if value == 'no':
                    mVal = "0"
                elif value == 'paper':
                    mVal = "1"
                elif value == 'email':
                    mVal = "2"
                elif value == 'default':
                    mVal = "3"

            # Construct the statement with the converted value, if there is
            # any.
            if mVal:
                fieldsUpdate += self.colMapping[name] + "=" + \
                    mString + mVal.replace("'", "\\'") + mString + ", "
            # Happens if a string field is deleted.
            elif mString:
                # Avoid deleting name fields.
                if name not in ('lastname', 'name', 'firstname'):
                    fieldsUpdate += self.colMapping[name] + "='', "
            # Happens if a non string field is deleted.
            elif name in self.colMapping:
                fieldsUpdate += self.colMapping[name] + "=Null, "

        # Execute the final query, if there is any update to perform.
        if fieldsUpdate:
            fieldsUpdate += "IDUSER = (SELECT ID " \
                            "FROM login WHERE ERP_ID = {0})".format(uid)
            sqlQuery = sqlQuery.format(fieldsUpdate).encode("ISO-8859-1")
            return self.query(sqlQuery)

    def _checkExists(self, ref):
        """ Check that a given reference (CODEGA) exists in the MySQL
        Address Table. """
        res = self.selectOne(
            "SELECT COUNT(*) AS NB FROM Adresses WHERE CODEGA = %s", (ref))
        return (res["NB"] > 0) if res else False

    def _updateCategories(self, ref, categories, deleteAbsent=True):
        """ Given a partner reference and his category names, update the
        MySQL Categories_adresses Table. """
        oldCategoryIds = []
        # Convert the list of category names into a list of category ids used
        # in the MySQL table (-1 if not found).
        currentCatIds = map(lambda catName: int(self.catMapping[catName])
                            if catName in self.catMapping.keys()
                            else -1, categories)

        for row in self.selectAll("SELECT ID_CAT FROM Categories_adresses "
                                  "WHERE CODEGA = %s AND DATE_FIN IS NULL",
                                  ref):
            catId = row["ID_CAT"]
            oldCategoryIds.append(catId)
            # If the category is no more present, remove it (by setting an end
            # date), except for "Mailing Complet" and "Abroad" which are
            # treated separately (boolean categories).
            if deleteAbsent and catId not in currentCatIds and catId not in (
               int(self.catMapping["Complete Mailing"]),
               int(self.catMapping["Abroad"])):
                self.query(
                    "UPDATE Categories_adresses SET DATE_FIN = NOW() "
                    "WHERE CODEGA = %s AND ID_CAT = %s", (ref, catId))

        # Add current categories that are not already present in the MySQL
        # table.
        sqlInsert = "INSERT INTO Categories_adresses(CODEGA,ID_CAT," \
                    "Date_Ajout) VALUES (%s,{0},now())"
        sqlUpdate = "UPDATE Categories_adresses SET DATE_AJOUT = NOW(), " \
                    "DATE_FIN = NULL WHERE CODEGA = %s AND ID_CAT = {0}"
        for category in currentCatIds:
            if category > 0 and category not in oldCategoryIds:
                if self.selectOne("SELECT ID_CAT FROM Categories_adresses "
                                  "WHERE CODEGA = %s AND ID_CAT = %s",
                                  (ref, category)):
                    self.query(sqlUpdate.format(category), ref)
                else:
                    self.query(sqlInsert.format(category), ref)

    def _updateBooleanCategory(self, ref, categoryName, activeStatus):
        """ Given a partner reference and his boolean category status,
        update the MySQL Categories_adresses Table.
        Currently, this method is used for the 'Mailing Complet' (=opt_out)
        and 'A l'étranger/e-mail' (=abroad) Categories.
        """
        catId = self.catMapping[categoryName]
        if activeStatus:
            if self.selectOne("SELECT ID_CAT FROM Categories_adresses "
                              "WHERE CODEGA = %s AND ID_CAT = %s",
                              (ref, catId)):
                sql = "UPDATE Categories_adresses SET Date_Ajout = NOW(), " \
                      "DATE_FIN = NULL WHERE CODEGA = %s AND ID_CAT = %s"
            else:
                sql = "INSERT INTO Categories_adresses(CODEGA,ID_CAT," \
                      "Date_Ajout) VALUES (%s,%s,now())"
        else:
            sql = "UPDATE Categories_adresses SET DATE_FIN = NOW() " \
                  "WHERE CODEGA = %s AND ID_CAT = %s"
        return self.query(sql, (ref, catId))

    def nextRef(self):
        """ Gives the next valid value for the CODEGA sequence field """
        result = self.selectOne(
            "SELECT currval FROM sequences WHERE nom = 'CODEGA'")
        if result:
            self.query(
                "UPDATE sequences SET currval = currval+1 "
                "WHERE nom = 'CODEGA'")
            return result['currval'] + 1

    def linkContact(self, uid, company_ref, contact_id):
        """ Link a contact to a company and use one single line address for
        both in the MySQL Table.
        Args:
            company_ref (string) : the reference of the company partner
                                   in MySQL
            contact_id (long) : the id of the contact in OpenERP
        """
        return self.query("UPDATE Adresses SET id_erp = %s, IDUSER = "
                          "(SELECT ID FROM login WHERE ERP_ID = %s) "
                          "WHERE CODEGA = %s", (contact_id, uid, company_ref))

    def unlinkContact(self, uid, company, company_categories):
        """ Unlink a contact from a company and use two different addresses
        in the MySQL Table.
        Args:
            company (res.partner) : the company partner
            company_categories (list) : the category names of the company,
                                        in order to restore them and remove
                                        the categories of the contact.
        """
        sql = "UPDATE Adresses SET id_erp = {0}, PRENOM='', NOM='', " \
              "TITRE=NULL, TELMOBILE='', LANGUE_PARRAIN='{2}', IDUSER = (" \
              "SELECT ID FROM login WHERE ERP_ID = {3}) " \
              "WHERE CODEGA = '{1}'".format(company.id, company.ref,
                                            self.langMapping[company.lang],
                                            uid)
        self.query(sql)
        self._updateCategories(company.ref, company_categories)
        self._updateBooleanCategory(
            company.ref, 'Complete Mailing', not company.opt_out)
        self._updateBooleanCategory(company.ref, 'Abroad', company.abroad)

    def unlink(self, uid, id):
        """ Unlink a partner in MySQL. """
        return self.query("UPDATE Adresses SET id_erp=NULL, IDUSER = ("
                          "SELECT ID FROM login WHERE ERP_ID = {0}) "
                          "WHERE id_erp={1}".format(uid, id))

    def changeToCompany(self, uid, ref, name):
        """ Changes the selected partner in MySQL so that it becomes a
        company.
        Args:
            ref (string) : the reference of the partner in MySQL
        """
        return self.query("UPDATE Adresses SET PRENOM='', NOM='', TITRE=NULL,"
                          "RAISSOCIALE = '{2}', IDUSER = (SELECT ID "
                          "FROM login WHERE ERP_ID = {0}) "
                          "WHERE CODEGA='{1}'".format(uid, ref, name))

    def changeToPrivate(self, uid, ref):
        """ Changes the selected partner in MySQL so that it is no
        more a company.
        Args:
            ref (string) : the reference of the partner in MySQL
        """
        return self.query("UPDATE Adresses SET RAISSOCIALE='', IDUSER = ("
                          "SELECT ID FROM login WHERE ERP_ID = {0}) "
                          "WHERE CODEGA='{1}'".format(uid, ref))

    def getRefContact(self, id):
        """ Returns the reference of the partner in MySQL that has"
        id_erp pointing to the id given (returns -1 if not found). """
        res = self.selectOne(
            "SELECT CODEGA FROM Adresses WHERE id_erp = {0}".format(id))
        return res['CODEGA'] if res else -1
