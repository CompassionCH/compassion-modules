# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from mysql_connector.model.mysql_connector import mysql_connector
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GPConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields. """

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

    def upsert_child(self, uid, child):
        """Push or update child in GP after converting all relevant
        information in the destination structure."""
        name = child.name
        if child.firstname and name.endswith(child.firstname):
            name = name[:-len(child.firstname)]
        vals = {
            'CODE': child.code,
            'NOM': name,
            'PRENOM': child.firstname,
            'SEXE': child.gender,
            'DATENAISSANCE': child.birthdate,
            'SITUATION': child.state,
            'ID': self._get_gp_uid(uid),
            'COMPLETION_DATE': child.completion_date,
            'DATEDELEGUE': child.date_delegation,
            'CODEDELEGUE': child.delegated_to.ref,
            'REMARQUEDELEGUE': child.delegated_comment or '',
            'id_erp': child.id
        }
        if child.gp_exit_reason:
            vals['ID_MOTIF_FIN'] = int(child.gp_exit_reason)
        res = self.upsert("Enfants", vals)
        if child.case_study_ids:
            # Upsert last Case Study
            id_fichier = self.upsert_case_study(
                uid, child.case_study_ids[-1])
            if id_fichier:
                vals = {
                    'ID_DERNIER_FICHIER': id_fichier,
                    'CODE': child.code,
                    'id_erp': child.id}
                self.upsert("Enfants", vals)
        return res

    def upsert_case_study(self, uid, case_study):
        """Push or update Case Study in GP."""
        if case_study.child_id.pictures_ids:
            date_photo = case_study.child_id.pictures_ids[-1].date
        else:
            date_photo = '0000-00-00'
        vals = {
            'DATE_PHOTO': date_photo,
            'COMMENTAIRE_FR': case_study.child_id.desc_fr or '',
            'COMMENTAIRE_DE': case_study.child_id.desc_de or '',
            'COMMENTAIRE_ITA': case_study.child_id.desc_it or '',
            'COMMENTAIRE_EN': case_study.child_id.desc_en or '',
            'IDUSER': self._get_gp_uid(uid),
            'CODE': case_study.code,
            'DATE_INFO': case_study.info_date,
            'DATE_IMPORTATION': datetime.today().strftime(DF),
        }
        if self.upsert("Fichiersenfants", vals):
            return self.selectOne(
                "SELECT MAX(Id_Fichier_Enfant) AS id FROM Fichiersenfants "
                "WHERE Code = %s", case_study.code).get('id')
        return False

    def set_child_sponsor_state(self, child):
        update_string = "UPDATE Enfants SET %s WHERE code='%s'"
        update_fields = "situation='{}'".format(child.state)
        if child.sponsor_id:
            update_fields += ", codega='{}'".format(child.sponsor_id.ref)

        if child.state == 'F':
            # If the child is sponsored, mark the sponsorship as terminated in
            # GP and set the child exit reason in tables Poles and Enfant
            end_reason = child.gp_exit_reason or \
                self.transfer_mapping[child.transfer_country_id.code] \
                if child.transfer_country_id else 'NULL'
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

    def upsert_project(self, uid, project):
        """Update a given Compassion project in GP."""
        vals = {
            'CODE_PROJET': project.code,
            'DESCRIPTION_FR': project.description_fr or '',
            'DESCRIPTION_DE': project.description_de or '',
            'DESCRIPTION_EN': project.description_en or '',
            'DESCRIPTION_IT': project.description_it or '',
            'NOM': project.name,
            'IDUSER': self._get_gp_uid(uid),
            'DATE_MAJ': project.last_update_date,
            'SITUATION': self._get_project_state(project),
            'PAYS': project.code[:2],
            'LIEU_EN': project.community_name + ', ' +
            project.country_id.name if project.community_name 
            and project.country_id.name else '',
            'date_situation': project.status_date,
            'ProgramImplementorTypeCode': project.type,
            'StartDate': project.start_date,
            'LastReviewDate': project.last_update_date,
            'OrganizationName': project.local_church_name,
            'WesternDenomination': project.western_denomination,
            'CountryDenomination': project.country_denomination,
            'CommunityName': project.community_name
        }
        return self.upsert("Projet", vals)

    def _get_project_state(self, project):
        """ Returns the state of a project in GP format. """
        gp_state = 'Actif'
        if project.status == 'A':
            active_status_mapping = {
                'suspended': 'Suspension',
                'fund-suspended': 'Suspension avec retenue'}
            gp_state = active_status_mapping.get(project.suspension, 'Actif')
        elif project.status == 'P':
            gp_state = 'Phase out'
        elif project.status == 'T':
            gp_state = 'Terminé'
        return gp_state
