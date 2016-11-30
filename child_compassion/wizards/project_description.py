# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import os

from pyquery import PyQuery
from openerp import api, models, fields, _

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

    project_id = fields.Many2one('compassion.project', required=True)
    desc_fr = fields.Html()
    desc_de = fields.Html()
    desc_it = fields.Html()
    desc_en = fields.Html()

    @api.model
    def create(self, vals):
        """ This will automatically generate all descriptions and save them
        in the related child.
        """
        generator = super(ProjectDescription, self).create(vals)
        generator.desc_fr = generator.with_context(
            lang='fr_CH')._generate_translation()
        generator.desc_de = generator.with_context(
            lang='de_DE')._generate_translation()
        generator.desc_it = generator.with_context(
            lang='it_IT')._generate_translation()
        generator.desc_en = generator.with_context(
            lang='en_US')._generate_translation()
        generator.project_id.write({
            'description_fr': generator.desc_fr,
            'description_de': generator.desc_de,
            'description_it': generator.desc_it,
            'description_en': generator.desc_en,
        })

        return generator

    def _generate_translation(self):
        """ Generate child description. """
        desc = PyQuery(HTML_TEMPLATE)

        # 1. Basic Information
        ######################
        project = self.project_id
        desc('.project_name')[0].text = _("Project name")
        desc('.project_name')[1].text = project.name
        desc('.project_closest_city')[0].text = _("Closest city")
        desc('.project_closest_city')[1].text = project.closest_city
        desc('.project_cdsp_number')[0].text = _("Number of children")
        desc('.project_cdsp_number')[1].text = str(project.nb_cdsp_kids)
        if project.electrical_power == 'Not Available':
            desc('.project_electricity').html(
                _("The project has no electricity."))
        else:
            desc('#project_electricity').remove()

        # 2. Community
        ##############
        desc('#community_label').html(_("Local community"))
        desc('.community_population')[0].text = _("Population")
        desc('.community_population')[1].text = str(
            project.community_population)
        desc('.community_language')[0].text = _("Language")
        desc('.community_language')[1].text = project.primary_language_id.name
        desc('.community_job')[0].text = _("Typical job")
        desc('.community_job')[1].text = \
            project.primary_adults_occupation_ids[0].value
        desc('.community_income')[0].text = _("Family    monthly income")
        desc('.community_income')[1].text = 'CHF {:10.0f}.-'.format(
            project.chf_income)
        desc('.community_food')[0].text = _("Typical food")
        desc('.community_food')[1].text = project.primary_diet_ids[0].value
        desc('.community_school_begins')[0].text = _("School begins in")
        desc('.community_school_begins')[1].text = project.translate(
            'school_year_begins')

        # 3. Activities
        ###############
        desc('#activities_label').html(_("Project activities for children"))

        desc('.spiritual_activities').html(_("Spiritual activities"))
        desc('#spiritual_activities_list').html(''.join(
            ['<li>' + activity + '</li>' for activity in
             project.get_activities('spiritual_activity', 3)]))

        desc('.physical_activities').html(_("Physical activities"))
        desc('#physical_activities_list').html(''.join(
            ['<li>' + activity + '</li>' for activity in
             project.get_activities('physical_activity', 3)]))

        desc('.cognitive_activities').html(_("Cognitive activities"))
        desc('#cognitive_activities_list').html(''.join(
            ['<li>' + activity + '</li>' for activity in
             project.get_activities('cognitive_activity', 3)]))

        desc('.socio_activities').html(_("Socio-emotional activities"))
        desc('#socio_activities_list').html(''.join(
            ['<li>' + activity + '</li>' for activity in
             project.get_activities('socio_activity', 3)]))

        if project.activities_for_parents:
            desc('.parent_activities').html(
                _("In addition, the project offers special activities for the "
                  "parents such as education courses."))
        else:
            desc('#parent_activities').remove()

        return desc.html()
