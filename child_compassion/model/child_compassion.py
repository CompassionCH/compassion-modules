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

import requests
import json
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.config import config


class compassion_child(orm.Model):
    """ A sponsored child """
    _name = 'compassion.child'
    _rec_name = 'code'
    _inherit = ['mail.thread']
    _description = "Child"

    def get_portrait(self, cr, uid, ids, name, args, context=None):
        attachment_obj = self.pool.get('ir.attachment')
        res = dict()
        for child_id in ids:
            child = self.browse(cr, uid, child_id, context)
            case_study_id = -1
            if child.case_study_ids:
                case_study_id = child.case_study_ids[-1].id
            attachment_ids = attachment_obj.search(
                cr, uid, [('res_model', '=', 'compassion.child.property'),
                          ('res_id', '=', case_study_id),
                          ('datas_fname', '=', 'Headshot.jpeg')],
                limit=1, context=context)
            if not attachment_ids:
                res[child_id] = None
                continue

            attachment = attachment_obj.browse(cr, uid, attachment_ids[0],
                                               context)
            res[child_id] = attachment.datas
        return res

    _columns = {
        ######################################################################
        #                      1. General Information
        ######################################################################
        'name': fields.char(_("Name"), size=128),
        'firstname': fields.char(_("Firstname"), size=128),
        'code': fields.char(_("Child code"), size=128, required=True),
        'unique_id': fields.integer(_("Unique ID")),
        'birthdate': fields.date(_("Birthdate")),
        'type': fields.selection(
            [('CDSP', 'CDSP'),
             ('LDP', 'LDP')], _('Type of sponsorship program'), required=True),
        'date': fields.date(_("Allocation date"),
                            help=_("The date at which Compass allocated "
                                   "this child to Switzerland")),
        'gender': fields.selection(
            [('F', _('Female')),
             ('M', _('Male'))], _('Gender')),
        'completion_date': fields.date(_("Completion date")),
        'desc_en': fields.text(_('English description')),
        'desc_fr': fields.text(_('French description')),
        'desc_de': fields.text(_('German description')),
        'desc_it': fields.text(_('Italian description')),
        'start_date': fields.date(_("Start date")),
        'case_study_ids': fields.one2many(
            'compassion.child.property', 'child_id', string=_('Case studies'),
            readonly=False),  # FIXME readonly
        'portrait': fields.function(get_portrait, type='binary',
                                    string=_('Portrait')),
        'state': fields.selection([
            ('N', _('Available')),
            ('D', _('Delegated')),
            ('I', _('On Internet')),
            ('P', _('Sponsored')),
            ('R', _('Waiting new sponsor')),
            ('F', _('Departed'))], _("Status"), select=True, readonly=True,
            track_visibility='onchange', required=True), 

        ######################################################################
        #                      2. Exit Details
        ######################################################################
        'exit_date': fields.date(_("Exit date")),
        'last_attended_project': fields.date(_("Last time attended project")),
        'presented_gospel': fields.boolean(_("Has been presented with gospel")),
        'professes_faith': fields.boolean(_("Child made profession of faith")),
        'faith_description': fields.text(_("Description of faith")),
        'primary_school': fields.boolean(_("Has completed primary school")),
        'us_grade_completed': fields.char(_("US Grade level completed"), size=5),
        'study_area': fields.many2many(
            'compassion.translated.value', 'child_exit_to_value',
            'property_id', 'value_id', _('Primary area of study in school'),
            domain=[('property_name', '=', 'study_area')]),
        'vocational_training': fields.boolean(_("Has received vocational training")),
        'vocational_skills': fields.many2many(
            'compassion.translated.value', 'child_exit_to_value',
            'property_id', 'value_id', _('Skills learned'),
            domain=[('property_name', '=', 'vocational_skills')]),
        'disease_free': fields.boolean(_("Free from diseases")),
        'health_description': fields.text(_("Health description")),
        'social_description': fields.text(_("Social behaviour description")),
        'exit_description': fields.text(_("Exit description")),
        'steps_prevent_description': fields.text(_("Steps taken to prevent exit")),
        # TODO : See if future plans can be an automated translated field
        'future_plans_description': fields.text(_("Child future plans")),
        'new_situation_description': fields.text(_("New situation")),
        'exit_reason': fields.many2many(
            'compassion.translated.value', 'child_exit_to_value',
            'property_id', 'value_id', _('Other exit reason'),
            domain=[('property_name', '=', 'exit_reason')]),
        'other_exit_reason': fields.many2many(
            'compassion.translated.value', 'child_exit_to_value',
            'property_id', 'value_id', _('Exit reason'),
            domain=[('property_name', '=', 'other_exit_reason')]),
        'last_letter_sent': fields.boolean(_("Last letter was sent")),
    }

    _defaults = {
        'type': 'CDSP',
        'state': 'N',
    }

    def _get_basic_informations(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]

        for child in self.browse(cr, uid, ids, context):
            case_study = child.case_study_ids[-1]
            if case_study:
                self.write(cr, uid, [child.id], {
                    'name': case_study.name,
                    'firstname': case_study.firstname,
                    'birthdate': case_study.birthdate,
                    'gender': case_study.gender,
                    'unique_id': case_study.unique_id,
                    }, context=context)
        return True

    def get_infos(self, cr, uid, ids, context=None):
        """
            Get the most recent case study, basic informations, updates
            portrait picture and creates the project if it doesn't exist
        """
        if not isinstance(ids, list):
            ids = [ids]
        res = {}
        proj_obj = self.pool.get('compassion.project')
        for child in self.browse(cr, uid, ids, context):
            res[child.id] = self._get_case_study(cr, uid, child, context)
            self._get_picture(cr, uid, child, 'Fullshot',
                              300, 1500, 1200, context=context)
            self._get_picture(cr, uid, child, context=context)
            self._get_basic_informations(cr, uid, child.id)
            project_ids = proj_obj.search(
                cr, uid, [('code', '=', child.code[:5])],
                context=context)
            if not project_ids:
                proj_id = proj_obj.create(cr, uid, {
                    'code': child.code[:5],
                    'name': child.code[:5],
                })
                proj_obj.update_informations(cr, uid, proj_id)
        return res

    def generate_descriptions(self, cr, uid, child_id, context=None):
        child = self.browse(cr, uid, child_id, context)
        if not child:
            raise orm.except_orm('ObjectError', _('No valid child id given !'))
        child = child[0]
        if not child.case_study_ids:
            raise orm.except_orm('ValueError',
                                 _('Cannot generate a description '
                                   'for a child without a case study'))
        case_study = child.case_study_ids[-1]
        context['child_id'] = child_id
        context['property_id'] = case_study.id
        return {
            'name': _('Description generation'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'child.description.wizard',
            'context': context,
            'target': 'new',
        }

    ##################################################
    #            Case study retrieving               #
    ##################################################
    def _get_case_study(self, cr, uid, child, context=None):
        ''' Get case study from compassion webservices and parse
            the json response.
            Returns id of generated case_study or None if failed
        '''
        url = self._get_url(child.code, 'casestudy')
        r = requests.get(url)
        if not r.status_code/100 == 2:
            raise orm.except_orm('NetworkError',
                                 _('An error occured while fetching the last '
                                   'case study for child %s.') % child.code)

        json_data = json.loads(r.text)
        vals = {
            'child_id': child.id,
            'info_date': json_data['childCaseStudyDate'],
            'name': json_data['childName'],
            'firstname': json_data['childPersonalName'],
            'gender': json_data['gender'],
            'birthdate': json_data['birthDate'],
            'unique_id': json_data['childID']
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

                # otherEmployment is a string,
                # as well as motherIllnes and some others
                if value:
                    value = (key.replace(prop_names[2],
                             '').replace(prop_names[3], ''))
                else:
                    continue

                values.append(value_obj.get_value_ids(cr, uid, value,
                              property_name, context))
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
        vals['nb_children_family'] = int(json_data['familySize']
                                         ['totalFamilyFemalesUnder18'])
        vals['nb_sisters'] = int(json_data['familySize']
                                 ['totalFamilyFemalesUnder18'])
        vals['nb_children_family'] += int(json_data['familySize']
                                          ['totalFamilyMalesUnder18'])-1
        vals['nb_brothers'] = int(json_data['familySize']
                                  ['totalFamilyMalesUnder18'])
        if child.gender == 'M':
            vals['nb_brothers'] -= 1
        else:
            vals['nb_sisters'] -= 1
        vals['hobbies_ids'] = [(6, 0, values)]
        child_prop_obj = self.pool.get('compassion.child.property')
        prop_id = child_prop_obj.create(cr, uid, vals, context)
        return prop_id

    def _get_picture(self, cr, uid, child, type='Headshot', dpi=72, width=400,
                     height=400, format='jpeg', context=None):
        ''' Gets a picture from Compassion webservice '''
        url = self._get_url(child.code, 'image')
        url += '&Height=%s&Width=%s&DPI=%s&ImageFormat=%s&ImageType=%s' \
            % (height, width, dpi, format, type)
        r = requests.get(url)
        if not r.status_code/100 == 2:
            raise orm.except_orm('NetworkError',
                                 _('An error occured while fetching the last '
                                   'picture for child %s.') % child.code)
        data = json.loads(r.text)['image']['imageData']
        attachment_obj = self.pool.get('ir.attachment')
        if not context:
            context = {}
        context['store_fname'] = type + '.' + format
        attachment_obj.create(cr, uid,
                              {'datas_fname': type + '.' + format,
                               'res_model': 'compassion.child.property',
                               'res_id': child.case_study_ids[-1].id,
                               'datas': data,
                               'name': type + '.' + format}, context)
        return False

    def _get_url(self, child_code, api_mess):
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        if not url or not api_key:
            raise orm.except_orm('ConfigError',
                                 _('Missing compass_url or compass_api_key '
                                   'in conf file'))
        if url.endswith('/'):
            url = url[:-1]
        url += ('/ci/v1/children/' + child_code + '/' + api_mess + '?api_key='
                + api_key)
        return url
