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
from openerp.tools.translate import _
from openerp.tools.config import config

from datetime import date, datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

logger = logging.getLogger(__name__)


class compassion_child(orm.Model):
    """ A sponsored child """
    _name = 'compassion.child'
    _rec_name = 'code'
    _inherit = 'mail.thread'
    _description = "Child"

    def get_gp_exit_reasons(self, cr, uid, context=None):
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

    def _get_project(self, cr, uid, ids, field_name, args, context=None):
        res = dict()
        for child in self.browse(cr, uid, ids, context):
            project_ids = self.pool.get('compassion.project').search(
                cr, uid, [('code', '=', child.code[:5])], context=context)
            if project_ids:
                res[child.id] = project_ids[0]
        return res

    def _get_child_from_project(project_obj, cr, uid, ids, context=None):
        self = project_obj.pool.get('compassion.child')
        child_ids = list()
        for project in project_obj.browse(cr, uid, ids, context):
            child_ids += self.search(
                cr, uid, [('code', 'like', project.code)], context=context)
        return child_ids

    def _get_child_states(self, cr, uid, context=None):
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

    def _get_child_from_case_study(prop_obj, cr, uid, ids, context=None):
        child_ids = list()
        for case_study in prop_obj.browse(cr, uid, ids, context):
            child_ids.append(case_study.child_id.id)
        return child_ids

    def _has_desc(self, cr, uid, ids, field_names, args, context=None):
        res = dict()
        field_res = dict()
        for child in self.browse(cr, uid, ids, context):
            field_res['has_desc_fr'] = bool(child.desc_fr)
            field_res['has_desc_de'] = bool(child.desc_de)
            field_res['has_desc_it'] = bool(child.desc_it)
            field_res['has_desc_en'] = bool(child.desc_en)
            res[child.id] = field_res.copy()

        return res

    def _is_available(self, cr, uid, ids, field_name, args, context=None):
        """ Tells if child is available for sponsorship. """
        return {child.id: child.state in self._available_states()
                for child in self.browse(cr, uid, ids, context)}

    def _available_states(self):
        return ['N', 'D', 'I', 'Z', 'R']

    _columns = {
        ######################################################################
        #                      1. General Information                        #
        ######################################################################
        'name': fields.char(_("Name"), size=128),
        'firstname': fields.char(_("First name"), size=128),
        'project_id': fields.function(
            _get_project, type='many2one', obj='compassion.project',
            string=_('Project'), store={
                'compassion.project': (
                    _get_child_from_project,
                    ['code'],
                    10),   
                'compassion.child': (
                    lambda self, cr, uid, ids, context=None: ids,
                    ['code'],
                    10)}),
        'unique_id': fields.char(_("Unique ID"), size=128),
        'birthdate': fields.date(_("Birthday")),
        'code': fields.char(_("Child code"), size=9, required=True,
                            track_visibility='onchange'),
        'type': fields.selection(
            [('CDSP', 'CDSP'),
             ('LDP', 'LDP')], _('Type of sponsorship program'), required=True),
        'date': fields.date(_("Allocation date"),
                            help=_("The date at which Compass allocated "
                                   "this child to Switzerland")),
        'gender': fields.selection(
            [('F', _('Female')),
             ('M', _('Male'))], _('Gender')),
        'completion_date': fields.date(_("Completion date"),
                                       track_visibility="onchange"),
        # Dummy field which is overwritten in module sponsorship_compassion
        'unsponsored_since': fields.date('Unsponsored since'),
        # TODO : We store the descriptions in child database since we
        # imported the descriptions from GP in this field. When all children
        # will have a new case study fetched from Cornerstone,
        # we can remove the field from db by removing store=True.
        'desc_en': fields.related(
            'case_study_ids', 'desc_en', type='text',
            string=_('English description'), store={
                'compassion.child.property': (
                    _get_child_from_case_study,
                    ['desc_en', 'desc_fr', 'desc_de', 'desc_it'],
                    10)}),
        'desc_fr': fields.related(
            'case_study_ids', 'desc_fr', type='text',
            string=_('French description'), store={
                'compassion.child.property': (
                    _get_child_from_case_study,
                    ['desc_en', 'desc_fr', 'desc_de', 'desc_it'],
                    10)}),
        'desc_de': fields.related(
            'case_study_ids', 'desc_de', type='text',
            string=_('German description'), store={
                'compassion.child.property': (
                    _get_child_from_case_study,
                    ['desc_en', 'desc_fr', 'desc_de', 'desc_it'],
                    10)}),
        'desc_it': fields.related(
            'case_study_ids', 'desc_it', type='text',
            string=_('Italian description'), store={
                'compassion.child.property': (
                    _get_child_from_case_study,
                    ['desc_en', 'desc_fr', 'desc_de', 'desc_it'],
                    10)}),
        'has_desc_fr': fields.function(
            _has_desc, string='FR', type='boolean', multi='has_desc'),
        'has_desc_de': fields.function(
            _has_desc, string='DE', type='boolean', multi='has_desc'),
        'has_desc_it': fields.function(
            _has_desc, string='IT', type='boolean', multi='has_desc'),
        'has_desc_en': fields.function(
            _has_desc, string='EN', type='boolean', multi='has_desc'),
        'case_study_ids': fields.one2many(
            'compassion.child.property', 'child_id', string=_('Case studies'),
            readonly=True, track_visibility="onchange"),
        'pictures_ids': fields.one2many(
            'compassion.child.pictures', 'child_id',
            string=_('Child pictures'), track_visibility="onchange"),
        'portrait': fields.related(
            'pictures_ids', 'headshot', type='binary'),
        'fullshot': fields.related(
            'pictures_ids', 'fullshot', type='binary'),
        'state': fields.selection(
            _get_child_states, _("Status"), select=True, readonly=True,
            track_visibility="onchange", required=True),
        'has_been_sponsored': fields.boolean('Has been sponsored'),
        'sponsor_id': fields.many2one('res.partner', _('Sponsor'),
                                      readonly=True,
                                      track_visibility='onchange'),
        'sponsor_ref': fields.related('sponsor_id', 'ref', type='char',
                                      string=_('Sponsor reference')),
        'delegated_to': fields.many2one('res.partner', _("Delegated to")),
        'delegated_comment': fields.text(_("Delegated comment")),
        'date_delegation': fields.date(_("Delegated date")),
        'date_end_delegation': fields.date(_("Delegated until")),
        'date_info': fields.related('case_study_ids', 'info_date',
                                    type='date', string=_("Last info")),
        'is_available': fields.function(
            _is_available, string='Is available', type='boolean'),

        ######################################################################
        #                      2. Exit Details                               #
        ######################################################################
        'exit_date': fields.date(_("Exit date"), track_visibility="onchange",
                                 readonly=True),
        'last_attended_project': fields.date(_("Last time attended project")),
        'presented_gospel': fields.boolean(
            _("Has been presented with gospel")),
        'professes_faith': fields.boolean(
            _("Child made profession of faith")),
        'faith_description': fields.text(_("Description of faith")),
        'primary_school': fields.boolean(_("Has completed primary school")),
        'us_grade_completed': fields.char(_("US Grade level completed"),
                                          size=5),
        # study_area may become an automated translated field if needed
        'study_area': fields.char(_('Primary area of study in school')),
        'vocational_training': fields.boolean(
            _("Has received vocational training")),
        # Vocational skills may become an automated translated field if needed
        'vocational_skills': fields.char(_('Skills learned')),
        'disease_free': fields.boolean(_("Free from diseases")),
        'health_description': fields.text(_("Health description")),
        'social_description': fields.text(_("Social behavior description")),
        'exit_description': fields.text(_("Exit description")),
        'steps_prevent_description': fields.text(
            _("Steps taken to prevent exit")),
        # Future plans may become an automated translated field if needed
        'future_plans_description': fields.text(_("Child future plans")),
        'new_situation_description': fields.text(_("New situation")),
        'exit_reason': fields.char(_('Exit reason')),
        'last_letter_sent': fields.boolean(_("Last letter was sent")),
        'transfer_country_id': fields.many2one('res.country',
                                               _("Transfered to")),
        'gp_exit_reason': fields.selection(
            get_gp_exit_reasons, _("Exit Reason"),
            track_visibility="onchange"),
    }

    _defaults = {
        'type': 'CDSP',
        'state': 'N',
    }

    _sql_constraints = [
        ('unique_id',
         'unique(unique_id)',
         _('The child already exists in database.'))
    ]

    def _get_basic_informations(self, cr, uid, ids, context=None):
        """ Retrieves basic information from Get Child Information service.
        """
        if not isinstance(ids, list):
            ids = [ids]

        for child in self.browse(cr, uid, ids, context):
            url = self.get_url(child.code, 'information')
            r = self.https_get(url)
            json_data = dict()
            try:
                json_data = json.loads(r)
            except:
                raise orm.except_orm(
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
            self.write(cr, uid, [child.id], vals, context=context)
        return True

    def get_infos(self, cr, uid, ids, context=None):
        """
            Get the most recent case study, basic informations, updates
            portrait picture and creates the project if it doesn't exist
        """
        if not isinstance(ids, list):
            ids = [ids]
        proj_obj = self.pool.get('compassion.project')
        res = True
        for child in self.browse(cr, uid, ids, context):
            if child.type == 'LDP':
                res = res and self._create_empty_case_study(
                    cr, uid, child, context)
                if child.state == 'F':
                    self.get_exit_details(cr, uid, child.id, context)
            else:
                if child.state != 'F':
                    self._get_basic_informations(cr, uid, child.id, context)
                    res = res and self._get_case_study(cr, uid, child,
                                                       context)
                else:
                    self.get_exit_details(cr, uid, child.id, context)

            project_ids = proj_obj.search(
                cr, uid, [('code', '=', child.code[:5])],
                context=context)
            if not project_ids:
                proj_id = proj_obj.create(cr, uid, {
                    'code': child.code[:5],
                    'name': child.code[:5],
                })
                proj_obj.update_informations(cr, uid, proj_id)

            res = res and self._get_last_pictures(cr, uid, child.id, context)
        return res

    def generate_descriptions(self, cr, uid, child_id, context=None):
        if child_id and isinstance(child_id, list):
            child_id = child_id[0]
        child = self.browse(cr, uid, child_id, context)
        if not child:
            raise orm.except_orm('ObjectError', _('No valid child id given !'))
        if not child.case_study_ids:
            raise orm.except_orm('ValueError',
                                 _('Cannot generate a description '
                                   'for a child without a case study'))
        case_study = child.case_study_ids[0]
        context['child_id'] = child_id
        context['property_id'] = case_study.id
        return {
            'name': _('Description generation'),
            'type': 'ir.actions.act_window',
            'res_model': 'child.description.wizard',
            'view_mode': 'auto_description_form',
            'view_type': 'form',
            'context': context,
            'target': 'new',
        }

    def update_child_pictures(self, cr, uid, child_ids, context=None):
        res = True
        # Update child's pictures
        for child_id in child_ids:
            res = self._get_last_pictures(
                cr, uid, child_id, context) and res
        return res

    def _get_last_pictures(self, cr, uid, child_id, context=None):
        pictures_obj = self.pool.get('compassion.child.pictures')
        pic_id = pictures_obj.create(
            cr, uid, {'child_id': child_id}, context)
        if pic_id:
            # Add a note in child
            self.pool.get('mail.thread').message_post(
                cr, uid, child_id, "The picture has been updated.",
                "Picture update", 'comment',
                context={'thread_model': self._name})

        return pic_id

    def _create_empty_case_study(self, cr, uid, child, context=None):
        child_prop_obj = self.pool.get('compassion.child.property')

        if not (child_prop_obj.search(
                cr, uid,
                [('child_id', '=', child.id)],
                context=context)):
            vals = {
                'child_id': child.id,
                'info_date': date.today(),
                'last_modification_date': date.today(),
                'code': child.code,
                'unique_id': child.unique_id,
                'name': child.name,
                'firstname': child.firstname,
                'gender': child.gender,
                'birthdate': child.birthdate,
                'comments': 'Empty Case Study for LDP Student',
            }
            return child_prop_obj.create(cr, uid, vals, context)
        return True

    def update_delegate(self, cr, uid, context=None):
        obj_undelegate_wizard = self.pool.get('undelegate.child.wizard')

        child_ids = self.search(cr, uid, [
            ('state', 'not in', ['F', 'X', 'P'])], context=context)
        child_ids_to_delegate = []
        child_ids_to_undelegate = []

        for child in self.browse(cr, uid, child_ids, context=context):
            if child.date_delegation:
                if datetime.strptime(child.date_delegation, DF) \
                   <= datetime.today() and child.is_available:
                    child_ids_to_delegate.append(child.id)

                if child.date_end_delegation and \
                   datetime.strptime(child.date_end_delegation, DF) <= \
                   datetime.today():
                    child_ids_to_undelegate.append(child.id)

        self.write(cr, uid, child_ids_to_delegate, {'state': 'D'},
                   context=context)
        obj_undelegate_wizard.undelegate(cr, uid, 0, {'active_ids':
                                                      child_ids_to_undelegate})

        return True

    ##################################################
    #            Case study retrieving               #
    ##################################################
    def _get_case_study(self, cr, uid, child, context=None):
        ''' Get case study from compassion webservices and parse
            the json response.
            Returns id of generated case_study or None if failed
        '''
        if context is None:
            context = dict()
        url = self.get_url(child.code, 'casestudy')
        r = self.https_get(url)
        json_data = dict()
        try:
            json_data = json.loads(r)
        except:
            raise orm.except_orm('NetworkError',
                                 _('An error occured while fetching the last '
                                   'case study for child %s. ') % child.code)

        child_prop_obj = self.pool.get('compassion.child.property')
        info_date = json_data['childCaseStudyDate']
        study_ids = child_prop_obj.search(cr, uid, [
            ('child_id', '=', child.id),
            ('info_date', '=', info_date)], context=context)
        vals = {
            'child_id': child.id,
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

        value_obj = self.pool.get('compassion.translated.value')
        values = []

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
            values.extend(value_obj.get_value_ids(cr, uid, section_values,
                                                  prop_name, context))

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

                values.append(value_obj.get_value_ids(cr, uid, value,
                                                      property_name, context))
                context['default_is_tag'] = False
        # Other sections
        values.append(value_obj.get_value_ids(
            cr, uid, json_data['naturalParents']['maritalStatusOfParents'],
            'marital_status', context))
        vals['us_school_level'] = json_data['schooling']['usSchoolEquivalent']

        values.append(value_obj.get_value_ids(cr, uid, json_data['schooling']
                                              ['schoolPerformance'],
                                              'school_performance', context))
        values.append(value_obj.get_value_ids(cr, uid, json_data['schooling']
                                              ['childsBestSubject'],
                                              'school_best_subject', context))
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
        if study_ids:
            child_prop_obj.write(cr, uid, study_ids, vals, context)
        else:
            child_prop_obj.create(cr, uid, vals, context)
            # Remove old descriptions
            child.write({
                'desc_fr': False,
                'desc_de': False,
                'desc_it': False,
                'desc_en': False})

        # Add a note in child
        self.pool.get('mail.thread').message_post(
            cr, uid, child.id, "The case study has been updated.",
            "Case Study update", 'comment',
            context={'thread_model': self._name})
        return True

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

    def get_url(self, child_code, api_mess):
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        if not url or not api_key:
            raise orm.except_orm('ConfigError',
                                 _('Missing compass_url or compass_api_key '
                                   'in conf file'))
        if url.endswith('/'):
            url = url[:-1]
        url += ('/ci/v1/children/' + child_code + '/' + api_mess +
                '?api_key=' + api_key)
        return url

    ##################################################
    #        Workflow Activities Callbacks           #
    ##################################################
    def child_available(self, cr, uid, ids, context=None):
        """Called on creation of workflow. Determine the state of
        allocated child."""
        for child in self.browse(cr, uid, ids, context):
            state = 'N'
            if child.has_been_sponsored:
                if child.state == 'F':
                    # Child reinstatement
                    state = 'Z'
                else:
                    # Child is waiting a new sponsor
                    state = 'R'
            if child.sponsor_id:
                # Child is already sponsored
                state = 'P'
            child.write({'state': state})
        return True

    def child_sponsored(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'P',
            'has_been_sponsored': True}, context)
        return True

    def child_departed(self, cr, uid, ids, context=None):
        """ Is called when a child changes his status to 'F' or 'X'."""
        for child in self.browse(cr, uid, ids, context):
            if child.state == 'F':
                child.write({'sponsor_id': False})
                self.get_exit_details(cr, uid, child.id, context)
        return True

    def get_exit_details(self, cr, uid, child_id, context=None):
        child = self.browse(cr, uid, child_id, context)
        if not child:
            raise orm.except_orm('ObjectError', _('No valid child id given !'))
        url = self.get_url(child.code, 'exitdetails')
        r = self.https_get(url)
        try:
            json_data = json.loads(r)
        except:
            self.pool.get('mail.thread').message_post(
                cr, uid, child_id, "Invalid JSON Data received",
                "Error fetching exit details", 'comment',
                context={'thread_model': self._name})
            return False
        if json_data.get('error'):
            self.pool.get('mail.thread').message_post(
                cr, uid, child_id, json_data['error']['message'],
                "Error fetching exit details", 'comment',
                context={'thread_model': self._name})
            return False

        child.write({
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

    def _get_gender(self, cr, uid, gender, context=None):
        if gender == 'M':
            return 1
        else:
            return 2
