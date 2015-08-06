# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Cyril Sester
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
import requests
import urllib3
import certifi
import json

from openerp import models, fields, api, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.config import config
from datetime import date, datetime

logger = logging.getLogger(__name__)


class compassion_child(models.Model):

    """ A sponsored child """
    _name = 'compassion.child'
    _rec_name = 'code'
    _inherit = 'mail.thread'
    _description = "Child"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # General Information
    #####################
    unique_id = fields.Char(size=128)
    name = fields.Char(size=128)
    firstname = fields.Char(size=128)
    code = fields.Char(
        'Child code', size=9, required=True, track_visibility='onchange')
    project_id = fields.Many2one(
        'compassion.project', 'Project', store=True, compute='_set_project')
    type = fields.Selection(
        [('CDSP', 'CDSP'), ('LDP', 'LDP')], required=True, default='CDSP')
    gender = fields.Selection([('F', 'Female'), ('M', 'Male')])
    birthdate = fields.Date()
    date = fields.Date('Allocation date')
    completion_date = fields.Date(track_visibility='onchange')
    unsponsored_since = fields.Date()
    state = fields.Selection(
        '_get_child_states', readonly=True, required=True,
        track_visibility='onchange', default='N')
    is_available = fields.Boolean(compute='_set_available')
    sponsor_id = fields.Many2one(
        'res.partner', 'Sponsor', readonly=True, track_visibility='onchange')
    sponsor_ref = fields.Char(
        'Sponsor reference', related='sponsor_id.ref')
    has_been_sponsored = fields.Boolean()

    # Delegation
    ############
    delegated_to = fields.Many2one('res.partner', 'Delegated to')
    delegated_comment = fields.Text('Delegated comment')
    date_delegation = fields.Date()
    date_end_delegation = fields.Date('Delegated until')

    # Case Studies
    ##############
    case_study_ids = fields.One2many(
        'compassion.child.property', 'child_id', 'Case studies',
        readonly=True, track_visibility='onchange')
    date_info = fields.Date(
        string='Last info', related='case_study_ids.info_date')
    pictures_ids = fields.One2many(
        'compassion.child.pictures', 'child_id', 'Child pictures',
        track_visibility='onchange')
    portrait = fields.Binary(related='pictures_ids.headshot')
    fullshot = fields.Binary(related='pictures_ids.fullshot')

    # Descriptions
    ##############
    #   TODO : We store the descriptions in child database since we
    #   imported the descriptions from GP in this field. When all children
    #   will have a new case study fetched from Cornerstone,
    #   we can remove the field from db by removing store=True.
    desc_en = fields.Text(
        'English description', related='case_study_ids.desc_en', store=True)
    desc_fr = fields.Text(
        'French description', related='case_study_ids.desc_fr', store=True)
    desc_de = fields.Text(
        'German description', related='case_study_ids.desc_de', store=True)
    desc_it = fields.Text(
        'Italian description', related='case_study_ids.desc_it', store=True)
    has_desc_en = fields.Boolean('EN', compute='_set_has_desc')
    has_desc_fr = fields.Boolean('FR', compute='_set_has_desc')
    has_desc_de = fields.Boolean('DE', compute='_set_has_desc')
    has_desc_it = fields.Boolean('IT', compute='_set_has_desc')

    # Exit Details
    ##############
    #   study_area, vocational_skills, and future_plans_description
    #   may become automated translated fields if needed
    exit_reason = fields.Char()
    gp_exit_reason = fields.Selection(
        'get_gp_exit_reasons', 'Exit reason', track_visibility='onchange')
    exit_date = fields.Date(readonly=True, track_visibility='onchange')
    last_attended_project = fields.Date('Last time attended project')
    presented_gospel = fields.Boolean('Has been presented with gospel')
    professes_faith = fields.Boolean('Child made profession of faith')
    faith_description = fields.Text('Description of faith')
    primary_school = fields.Boolean('Has completed primary school')
    us_grade_completed = fields.Char('US Grade level completed', size=5)
    study_area = fields.Char('Primary area of study in school')
    vocational_training = fields.Char('Has received vocational training')
    vocational_skills = fields.Char('Skills learned')
    disease_free = fields.Boolean('Free from diseases')
    health_description = fields.Text()
    social_description = fields.Text('Social behaviour description')
    exit_description = fields.Text()
    steps_prevent_description = fields.Text('Steps taken to prevent exit')
    future_plans_description = fields.Text('Child future plans')
    new_situation_description = fields.Text('New situation')
    last_letter_sent = fields.Boolean('Last letter was sent')
    transfer_country_id = fields.Many2one('res.country', 'Transferred to')

    _sql_constraints = [
        ('unique_id',
         'unique(unique_id)',
         _('The child already exists in database.'))
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def get_gp_exit_reasons(self):
        # Returns all ending reasons coming from GP
        return [
            ('1', _("Left the project")),
            ('13', _("Death of a child")),
            ('14', _("Now lives where a Compassion project is not available")),
            ('22', _("Unjustified absence for two consecutive years")),
            ('23', _("End of scholarship")),
            ('24', _("Cancellation from Compassion")),
            ('26', _("Project closed")),
            ('29', _("Financial situation improved")),
            ('30', _("Parents took out the child from the project")),
            ('31', _("Sponsored by another organization")),
            ('32', _("Ran away")),
            ('33', _("Has found a job")),
            ('34', _("Got married")),
            ('36', _("Disrespect of rules")),
            ('39', _("Fulfilled completion plan")),
            ('41', _("Reached maximum age")),
        ]

    @api.one
    @api.depends('code', 'project_id.code')
    def _set_project(self):
        if self.code:
            projects = self.env['compassion.project'].search(
                [('code', '=', self.code[:5])])
            if projects:
                self.project_id = projects[0].id

    def _get_child_states(self):
        return [
            ('N', _('Available')),
            ('D', _('Delegated')),
            ('I', _('On Internet')),
            ('Z', _('Reinstated')),
            ('P', _('Sponsored')),
            ('R', _('Waiting new sponsor')),
            ('F', _('Departed')),
            ('X', _('Deallocated'))
        ]

    def _set_has_desc(self):
        for child in self:
            child.write({
                'has_desc_fr': bool(child.desc_fr),
                'has_desc_de': bool(child.desc_de),
                'has_desc_it': bool(child.desc_it),
                'has_desc_en': bool(child.desc_en),
            })

    def _set_available(self):
        for child in self:
            child.is_available = child.state in self._available_states()

    def _available_states(self):
        return ['N', 'D', 'I', 'Z', 'R']

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def update_delegate(self):
        """Called by CRON to update delegated children.
        :param Recordset self: empty Recordset
        """
        children = self.search([('state', 'not in', ['F', 'X', 'P'])])
        children_to_delegate = self.copy()
        children_to_undelegate = list()

        for child in children:
            if child.date_delegation:
                if datetime.strptime(child.date_delegation, DF) \
                   <= datetime.today() and child.is_available:
                    children_to_delegate.add(child)

                if child.date_end_delegation and \
                   datetime.strptime(child.date_end_delegation, DF) <= \
                   datetime.today():
                    children_to_undelegate.append(child.id)

        children_to_delegate.write({'state': 'D'})

        self.env['undelegate.child.wizard'].with_context(
            active_ids=children_to_undelegate).undelegate()

        return True

    @api.model
    def https_get(self, url):
        """" Try to fetch URL with secure connection. """
        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',  # Force certificate check.
            ca_certs=certifi.where(),   # Path to the Certifi bundle.
        )
        r = None
        try:
            r = http.request('GET', url).data
        except urllib3.exceptions.SSLError:
            logger.error("Could not connect with SSL CERT.")
            r = requests.get(url).text
        return r

    @api.model
    def get_url(self, child_code, api_mess):
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        if not url or not api_key:
            raise exceptions.Warning(
                'ConfigError',
                _('Missing compass_url or compass_api_key in conf file'))
        if url.endswith('/'):
            url = url[:-1]
        url += ('/ci/v1/children/' + child_code + '/' + api_mess +
                '?api_key=' + api_key)
        return url

    def get_exit_details(self):
        self.ensure_one()
        url = self.get_url(self.code, 'exitdetails')
        r = self.https_get(url)
        try:
            json_data = json.loads(r)
        except:
            self.message_post("Invalid JSON Data received",
                              "Error fetching exit details", 'comment')
            return False
        if json_data.get('error'):
            self.message_post(json_data['error']['message'],
                              "Error fetching exit details", 'comment')
            return False

        self.write({
            'exit_date': json_data['exitDate'],
            'last_attended_project': json_data['dateLastAttendedProject'],
            'presented_gospel': json_data['presentedWithGospel'],
            'professes_faith': json_data['professesFaithInJesusChrist'],
            'faith_description': json_data['faithDescription'],
            'primary_school': json_data['completedPrimarySchool'],
            'us_grade_completed': json_data['usGradeEquivalentCompleted'],
            'study_area': json_data['areaOfStudy'],
            'vocational_training': json_data['receivedVocationalTraining'],
            'vocational_skills': json_data['vocationalSkillsLearned'],
            'disease_free': json_data['freeOfPovertyRelatedDisease'],
            'health_description': json_data['healthDescription'],
            'social_description': json_data['socialBehaviorDescription'],
            'exit_description': json_data['exitDescription'],
            'steps_prevent_description': json_data['stepsToPrevent'
                                                   'ExitDescription'],
            'future_plans_description': json_data['futurePlansDescription'],
            'new_situation_description': json_data['childNewSituation'
                                                   'Description'],
            'exit_reason': json_data['exitReason'],
            'last_letter_sent': json_data['lastChildLetterSent'],
        })

        return True

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def get_infos(self):
        """Get the most recent case study, basic informations, updates
           portrait picture and creates the project if it doesn't exist.
        """
        for child in self:
            res = True
            if child.type == 'LDP':
                res = res and child._create_empty_case_study()
                if child.state == 'F':
                    child.get_exit_details()
            else:
                if child.state != 'F':
                    child._get_basic_informations()
                    res = res and child._get_case_study()
                else:
                    child.get_exit_details()

            proj_obj = self.env['compassion.project']
            if not proj_obj.search_count([('code', '=', child.code[:5])]):
                project = proj_obj.create({
                    'code': child.code[:5],
                    'name': child.code[:5],
                })
                project.update_informations()

            res = res and child._get_last_pictures()
        return res

    @api.multi
    def update_child_pictures(self):
        res = True
        # Update child's pictures
        for child in self:
            res = child._get_last_pictures() and res
        return res

    @api.multi
    def generate_descriptions(self):
        self.ensure_one()
        if not self.case_study_ids:
            raise exceptions.Warning('ValueError',
                                     _('Cannot generate a description '
                                       'for a child without a case study'))
        case_study = self.case_study_ids[0]
        context = self.with_context(
            child_id=self.id, property_id=case_study.id).env.context
        return {
            'name': _('Description generation'),
            'type': 'ir.actions.act_window',
            'res_model': 'child.description.wizard',
            'view_mode': 'auto_description_form',
            'view_type': 'form',
            'context': context,
            'target': 'new',
        }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.one
    def child_available(self):
        """Called on creation of workflow. Determine the state of
        allocated child.
        """
        state = 'N'
        if self.has_been_sponsored:
            if self.state == 'F':
                # Child reinstatement
                state = 'Z'
            else:
                # Child is waiting a new sponsor
                state = 'R'
        if self.sponsor_id:
            # Child is already sponsored
            state = 'P'
        self.state = state
        return True

    @api.multi
    def child_sponsored(self):
        self.write({
            'state': 'P',
            'has_been_sponsored': True})
        return True

    @api.one
    def child_departed(self):
        """ Is called when a child changes his status to 'F' or 'X'."""
        if self.state == 'F':
            self.sponsor_id = False
            self.get_exit_details()
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_basic_informations(self):
        """ Retrieves basic information from Get Child Information service.
        """
        for child in self:
            url = self.get_url(child.code, 'information')
            r = self.https_get(url)
            json_data = dict()
            try:
                json_data = json.loads(r)
            except:
                raise exceptions.Warning(
                    'NetworkError',
                    _('An error occured while fetching general information '
                      'for child %s. ') % child.code)
            vals = {
                'name': json_data['childName'],
                'firstname': json_data['childPersonalName'],
                'birthdate': json_data['birthDate'] or False,
                'gender': json_data['gender'],
                'unique_id': json_data['childID'],
                'completion_date': json_data['cdspCompletionDate'] or False,
            }
            child.write(vals)
        return True

    def _get_last_pictures(self):
        self.ensure_one()
        pictures_obj = self.env['compassion.child.pictures']
        pictures = pictures_obj.create({'child_id': self.id})
        if pictures:
            # Add a note in child
            self.message_post(
                "The picture has been updated.",
                "Picture update", 'comment')

        return pictures

    def _create_empty_case_study(self):
        self.ensure_one()
        child_prop_obj = self.env['compassion.child.property']

        if not child_prop_obj.search_count([('child_id', '=', self.id)]):
            vals = {
                'child_id': self.id,
                'info_date': date.today(),
                'last_modification_date': date.today(),
                'code': self.code,
                'unique_id': self.unique_id,
                'name': self.name,
                'firstname': self.firstname,
                'gender': self.gender,
                'birthdate': self.birthdate,
                'comments': 'Empty Case Study for LDP Student',
            }
            return child_prop_obj.create(vals)
        return True

    ##################################################
    #            Case study retrieving               #
    ##################################################
    def _get_case_study(self):
        """Get case study from compassion webservices and parse
           the json response.
           Returns id of generated case_study or None if failed
        """
        self.ensure_one()
        context = dict()
        context.update(self.env.context)
        url = self.get_url(self.code, 'casestudy')
        r = self.https_get(url)
        json_data = dict()
        try:
            json_data = json.loads(r)
        except:
            raise exceptions.Warning(
                'NetworkError',
                _('An error occured while fetching the last '
                  'case study for child %s. ') % self.code)

        child_prop_obj = self.env['compassion.child.property']
        info_date = json_data['childCaseStudyDate']
        case_studies = child_prop_obj.search([
            ('child_id', '=', self.id),
            ('info_date', '=', info_date)])
        vals = {
            'child_id': self.id,
            'info_date': info_date,
            'last_modification_date': json_data[
                'childCaseStudyLastModifiedDate'],
            'name': json_data['childName'],
            'firstname': json_data['childPersonalName'],
            'gender': json_data['gender'],
            'birthdate': json_data['birthDate'],
            'unique_id': json_data['childID'],
            'code': json_data['childKey'],
            'comments': json_data['basicChildInternalComment'],
        }

        value_obj = self.env['compassion.translated.value']
        values = list()

        """ cs_sections_mapping holds the mapping of sections in case study
            to property.
            cs_sections_mapping is a dict of lists of the following form:
            {'property_name': ['CaseStudySectionName',
                               'OtherSectionAttribute']}
            For more information see documentation of compass at
            the following link (2 lines):
            http://developer.compassion.com/docs/read/private_cornerstone_test/
            REST_Get_Child_Case_Study
        """
        cs_sections_mapping = {
            'christian_activities': ['christianActivities',
                                     'otherChristianActivities'],
            'family_duties': ['familyDuties',
                              'otherFamilyDuties'],
            'hobbies': ['hobbiesAndSports', 'otherHobbies'],
            'health_conditions': ['healthConditions',
                                  'otherHealthConditions'],
            'guardians': ['guardians', False],
        }

        for prop_name, cs_section in cs_sections_mapping.iteritems():
            section_values = json_data[cs_section[0]]
            if cs_section[1]:
                other_values = json_data[cs_section[1]]
                if isinstance(other_values, list):
                    section_values += json_data[cs_section[1]]
                elif not other_values == 'None':
                    section_values.append(other_values)
            values.extend(value_obj.get_value_ids(section_values, prop_name))

        """ Natural Parents and Employment Section.
            nps_sections_mapping is of the form:
            {'CaseStudySectionName':['property_name_male',
             'property_name_female', 'CaseStudyKey_male',
             'CaseStudyKey_female']}
        """
        npe_sections_mapping = {
            'naturalParents': ['father', 'mother', 'father', 'mother'],
            'employment': ['male_guardian', 'female_guardian',
                           'fatherOrMaleGuardian', 'motherOrFemaleGuardian'],
        }
        for section, prop_names in npe_sections_mapping.iteritems():
            for key, value in json_data[section].iteritems():
                property_name = ''
                if key.startswith('father'):
                    property_name = prop_names[0]
                elif key.startswith('mother'):
                    property_name = prop_names[1]
                else:
                    continue
                if value:
                    if isinstance(value, bool):
                        context['default_is_tag'] = True
                        value = (key.replace(prop_names[2], '').replace(
                            prop_names[3], ''))

                values.append(value_obj.with_context(context).get_value_ids(
                    value, property_name))
                context['default_is_tag'] = False
        # Other sections
        values.append(value_obj.get_value_ids(
            json_data['naturalParents']['maritalStatusOfParents'],
            'marital_status'))
        vals['us_school_level'] = json_data['schooling']['usSchoolEquivalent']

        values.append(value_obj.get_value_ids(
            json_data['schooling']['schoolPerformance'],
            'school_performance'))
        values.append(value_obj.get_value_ids(
            json_data['schooling']['childsBestSubject'],
            'school_best_subject'))
        vals['attending_school_flag'] = bool(json_data['schooling']
                                             ['childAttendingSchool'])
        # Brothers and sisters
        vals['nb_sisters'] = int(json_data['familySize']
                                 ['totalFamilyFemalesUnder18'])
        vals['nb_brothers'] = int(json_data['familySize']
                                  ['totalFamilyMalesUnder18'])
        if json_data['gender'] == 'M':
            vals['nb_brothers'] -= 1
        else:
            vals['nb_sisters'] -= 1
        vals['sibling_project_1'] = json_data[
            'familySize']['firstBrotherOrSister']
        vals['sibling_project_2'] = json_data[
            'familySize']['secondBrotherOrSister']

        # Attach many2many values (and remove duplicates)
        vals['hobbies_ids'] = [(6, 0, list(set([v for v in values if v])))]

        # Write values to existing case_study or create a new one
        if case_studies:
            case_studies.write(vals)
        else:
            child_prop_obj.create(vals)
            # Remove old descriptions
            self.write({
                'desc_fr': False,
                'desc_de': False,
                'desc_it': False,
                'desc_en': False})

        # Add a note in child
        self.message_post("The case study has been updated.",
                          "Case Study update", 'comment')
        return True

    # TODO : Move in module child_sync_typo3
    def _get_gender(self, gender):
        return 1 if gender == 'M' else 2
