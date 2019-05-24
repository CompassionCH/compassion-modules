# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import os
import logging

from odoo import api, models, fields, _

try:
    from pyquery import PyQuery
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("Please install python pyquery")


NOMINATIVE = 0
ACCUSATIVE = 1
DATIVE = 2

SINGULAR = 0
PLURAL = 1

DIR = os.path.join(os.path.dirname(__file__)) + '/../static/src/html/'

__template_file = open(DIR + 'project_description_template.html')
HTML_TEMPLATE = __template_file.read()
__template_file.close()


class ProjectDescription(models.TransientModel):
    _name = 'compassion.project.description'
    _description = 'Project Description Generator'

    project_id = fields.Many2one(
        'compassion.project', required=True, ondelete='cascade')

    @api.model
    def create(self, vals):
        """ This will automatically generate all descriptions and save them
        in the related child.
        """
        generator = super(ProjectDescription, self).create(vals)
        for lang, field in self._supported_languages().iteritems():
            desc = generator.with_context(lang=lang)._generate_translation()
            generator.project_id.write({field: desc})

        return generator

    @api.model
    def _supported_languages(self):
        """
        Inherit to add more languages to have translations of
        descriptions.
        {lang: description_field}
        """
        return {'en_US': 'description_en'}

    def _generate_translation(self):
        """ Generate project description. """
        desc = PyQuery(HTML_TEMPLATE)

        # 1. Basic Information
        ######################
        project = self.project_id

        # Put country if not the same as Field Office
        if project.country_id and project.country_id != \
                project.field_office_id.country_id:
            desc('.project_country')[0].text = _(
                "The project is located in %s, close to the border."
            ) % project.country_id.name
        else:
            desc('#project_country').remove()

        desc('.project_name')[0].text = _("Project name")
        desc('.project_name')[1].text = project.name
        desc('.project_closest_city')[0].text = _("Closest city")
        self._show_field(
            desc('.project_closest_city')[1], desc('#project_closest_city'),
            project.closest_city
        )
        desc('.project_cdsp_number')[0].text = _("Number of children")
        self._show_field(
            desc('.project_cdsp_number')[1], desc('#project_cdsp_number'),
            project.nb_cdsp_kids
        )
        if project.electrical_power == 'Not Available':
            desc('.project_electricity').html(
                _("The project has no electricity."))
        else:
            desc('#project_electricity').remove()

        # 2. Community
        ##############
        desc('#community_label').html(_("Local community"))
        desc('.community_population')[0].text = _("Population")
        self._show_field(
            desc('.community_population')[1], desc('#community_population'),
            '{:,}'.format(project.community_population).replace(',', "'")
        )
        desc('.community_language')[0].text = _("Language")
        self._show_field(
            desc('.community_language')[1], desc('#community_language'),
            project.primary_language_id.name
        )
        if project.primary_adults_occupation_ids:
            desc('.community_job')[0].text = _("Typical job")
            self._show_field(
                desc('.community_job')[1], desc('#community_job'),
                project.primary_adults_occupation_ids[0].value
            )
        else:
            desc('#community_job').remove()
        desc('.community_food')[0].text = _("Typical food")
        if project.primary_diet_ids:
            desc('.community_food')[1].text = project.primary_diet_ids[0].value
        else:
            desc('#community_food').remove()
        desc('.community_school_begins')[0].text = _("School begins in")
        self._show_field(
            desc('.community_school_begins')[1],
            desc('#community_school_begins'),
            project.translate('school_year_begins')
        )

        # 3. Activities
        ###############
        spiritual = project.get_activities('spiritual_activity', 3)
        physical = project.get_activities('physical_activity', 3)
        cognitive = project.get_activities('cognitive_activity', 3)
        socio = project.get_activities('socio_activity', 3)
        if spiritual or physical or cognitive or socio:
            desc('#activities_label').html(
                _("Project activities for children"))
        else:
            desc('#activities').remove()

        if spiritual:
            desc('.spiritual_activities').html(_("Spiritual activities"))
            desc('#spiritual_activities_list').html(''.join(
                ['<li>' + activity + '</li>' for activity in spiritual]))
        else:
            desc('#spiritual_activities').remove()
        if physical:
            desc('.physical_activities').html(_("Physical activities"))
            desc('#physical_activities_list').html(''.join(
                ['<li>' + activity + '</li>' for activity in physical]))
        else:
            desc('#physical_activities').remove()
        if cognitive:
            desc('.cognitive_activities').html(_("Cognitive activities"))
            desc('#cognitive_activities_list').html(''.join(
                ['<li>' + activity + '</li>' for activity in cognitive]))
        else:
            desc('#cognitive_activities').remove()
        if socio:
            desc('.socio_activities').html(_("Socio-emotional activities"))
            desc('#socio_activities_list').html(''.join(
                ['<li>' + activity + '</li>' for activity in socio]))
        else:
            desc('#socio_activities').remove()
        if project.activities_for_parents:
            desc('.parent_activities').html(
                _("In addition, the project offers special activities for the "
                  "parents such as education courses."))
        else:
            desc('#parent_activities').remove()

        return desc.html()

    def _show_field(self, field, container, value):
        """ Used to display a field in the description, or hide it
        if the value is not set.
        """
        if value:
            if not isinstance(value, basestring):
                value = str(value)
            field.text = value
        else:
            container.remove()
