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


class l10n_ch_import(common.TransactionCase):
    """ Test Project Webservices """

    def setUp(self):
        super(l10n_ch_import, self).setUp()
        self.project_id = self._create_project("TZ112", "Project 1")

    def _create_project(self, project_code, project_name):
        project_obj = self.registry('compassion.project')
        project_id = project_obj.create(self.cr, self.uid, {
            'name': project_name,
            'code': project_code,
        })
        return project_id

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
        project_obj = self.registry('compassion.project')
        project = project_obj.browse(self.cr, self.uid, self.project_id)
        self.assertTrue(project)
        self.assertEqual(project.name, "Project 1")
        self.assertEqual(project.id, self.project_id)
        logger.info("project id : " + str(project.id))

        # Retrieve the informations from the webservice
        project_obj.update_informations(self.cr, self.uid, project.id)
        project = project_obj.browse(self.cr, self.uid, self.project_id)

        # Test the data
        self.assertEqual(project.name, "Tanzania Assembly of God (TAG) "
                         "Karatu Student Center")
        self.assertEqual(project.type, "CDSP")
        self.assertEqual(project.start_date, "2002-04-16")
        self.assertEqual(project.local_church_name,
                         "Tanzania Assembly of God Karatu")
        self.assertEqual(project.closest_city_ids, "Arusha")
        self.assertEqual(project.terrain_description_ids[0].value_en, "hilly")
