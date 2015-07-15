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
import logging

logger = logging.getLogger(__name__)


class test_webservice(common.TransactionCase):
    """ Test Project Webservices """

    def setUp(self):
        super(test_webservice, self).setUp()
        self.project_id = self._create_project("TZ112", "Project 1")
        self.child_id = self._create_child("TZ1120316", "Child 1")

    def _create_project(self, project_code, project_name):
        project_obj = self.env['compassion.project']
        project_id = project_obj.create({
            'code': project_code,
            'name': project_name,
        }).id
        return project_id

    def _create_child(self, child_code, child_name):
        child_obj = self.env['compassion.child']
        child_id = child_obj.create({
            'code': child_code,
            'name': child_name,
        }).id
        return child_id

    def test_config_set(self):
        """Test that the config is properly set on the server
        """
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        self.assertTrue(url)
        self.assertTrue(api_key)

    def test_project_tz112(self):
        """ Test the webservice on Project TZ112. """
        # Test the basics
        self.assertTrue(self.project_id)
        project_obj = self.env['compassion.project']
        project = project_obj.browse(self.project_id)
        self.assertTrue(project)
        self.assertEqual(project.id, self.project_id)
        logger.info("project id : " + str(project.id))

        # Retrieve the informations from the webservice
        project.update_informations()

        # Test the data
        self.assertEqual(project.name, "Tanzania Assembly of God (TAG) "
                         "Karatu Student Center")
        self.assertEqual(project.type, "CDSP")
        self.assertEqual(project.start_date, "2002-04-16")
        self.assertEqual(project.local_church_name,
                         "Tanzania Assembly of God Karatu")
        self.assertEqual(project.closest_city, "Arusha")
        self.assertEqual(project.terrain_description_ids[0].value_en, "hilly")
        self.assertEqual(project.country_id.name, 'Tanzania')
        self.assertTrue(project.country_id.description_en)

    def test_child_tz1120316(self):
        """ Test the webservice on child TZ1120316"""
        # Test the basics
        self.assertTrue(self.child_id)
        child_obj = self.env['compassion.child']
        child = child_obj.browse(self.child_id)
        self.assertTrue(child)
        self.assertEqual(child.name, "Child 1")
        logger.info("child name: " + str(child.name))
        self.assertEqual(child.id, self.child_id)
        logger.info("child id: " + str(child.id))

        # Retrieve the informations from the webservice
        child.get_infos()

        # Test the data
        self.assertEqual(child.code, "TZ1120316")
        self.assertEqual(child.name, "Happiness Joseph")
        self.assertEqual(child.firstname, "Happiness")
        self.assertEqual(child.gender, "F")
        self.assertEqual(child.birthdate, "2005-04-17")
        self.assertTrue(child.case_study_ids)
        self.assertTrue(child.portrait)
