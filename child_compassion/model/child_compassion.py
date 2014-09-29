# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Cyril Sester. Copyright Compassion Suisse
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import requests
import json
import base64
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.config import config


class compassion_child(orm.Model):
    """ A sponsored child """
    _name = 'compassion.child'
    _rec_name = 'code'

    def get_portrait(self, cr, uid, ids, name, args, context=None):
        attachment_obj = self.pool.get('ir.attachment')
        ret = {}
        for child_id in ids:
            child = self.browse(cr, uid, child_id, context)
            case_study_id = -1
            if child.case_study_ids:
                case_study_id = child.case_study_ids[-1].id
            attachment_ids = attachment_obj.search(
                cr, uid, [('res_model', '=', 'compassion.child.property'),
                          ('res_id', '=', case_study_id), ('datas_fname', '=', 'Headshot.jpeg')],
                limit=1, context=context)
            if not attachment_ids:
                ret[child_id] = None
                continue
            
            attachment = attachment_obj.browse(cr, uid, attachment_ids[0], context)
            ret[child_id] = attachment.datas

        return ret

    _columns = {
        'name': fields.char(_("Name"),size=128),
        'firstname': fields.char(_("Firstname"), size=128),
        'code': fields.char(_("Child code"),size=128,required=True),
        'unique_id': fields.char(_("Unique ID"),size=128),
        'birthdate': fields.date(_("Birthdate")),
        'type': fields.selection(
            [('CDSP', 'CDSP'),
             ('LDP', 'LDP')], _('Type of sponsorship program'), required=True),
        'date': fields.date(_("Allocation date"),
                            help=_("The date at which Compass allocated this child to Switzerland")),
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
            readonly=False), #FIXME readonly
        'portrait': fields.function(get_portrait, type='binary', string=_('Portrait')),
    }
    
    _defaults = {
        'type' : 'CDSP'
    }

    def get_basic_informations(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]

        for child in self.browse(cr, uid, ids, context):
            case_study = child.case_study_ids[-1]
            if case_study:
                self.write(cr, uid, [child.id], {'name': case_study.name,
                                                 'firstname': case_study.firstname,
                                                 'birthdate': case_study.birthdate,
                                                 'gender': case_study.gender
                                               }, context=context)
        return True

    def get_last_case_study(self, cr, uid, ids, context=None):
        ''' Get the most recent case study and updates portrait picture '''
        if not isinstance(ids, list):
            ids = [ids]

        ret = {}
        for child in self.browse(cr, uid, ids, context):
            ret[child.id] = self._get_case_study(cr, uid, child, context)
            self._get_picture(cr, uid, child, 'Fullshot', 300, 1500, 1200, context=context)
            self._get_picture(cr, uid, child, context=context)
        return ret

    def generate_descriptions(self, cr, uid, child_id, context=None):
        child = self.browse(cr, uid, child_id, context)
        if not child:
            raise orm.except_orm('ObjectError', _('No valid child id given !'))
        child = child[0]
        if not child.case_study_ids:
            raise orm.except_orm('ValueError', _('Cannot generate a description for a child '
                                                 'without a case study'))
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
        ''' Get case study from compassion webservices and parse the json response.
            Returns id of generated case_study or None if failed
        '''
        url = self._get_url(child.code, 'casestudy')
        r = requests.get(url)
        if not r.status_code/100 == 2:
            raise orm.except_orm('NetworkError',
                                 _('An error occured while fetching the last '
                                   'case study for child %s.') % child.code)
        
        case_study = json.loads(r.text)
        vals = {
            'child_id': child.id,
            'info_date': case_study['ChildCaseStudyDate'],
            'name': case_study['ChildName'],
            'firstname': case_study['ChildPersonalName'],
            'gender': case_study['Gender'],
            'birthdate': case_study['BirthDate'],
        }
        values = []
        
        """ cs_sections_mapping holds the mapping of sections in case study to property. 
            cs_sections_mapping is a dict of lists of the following form:
            {'property_name': ['CaseStudySectionName','CaseStudySectionAttribute','OtherSectionAttribute']}
            For more information see documentation of compass at the following link:
            http://developer.compassion.com/docs/read/private_cornerstone_test/REST_Get_Child_Case_Study
        """
        cs_sections_mapping = {
            'christian_activities': ['ChristianActivities','ChristianActivity','OtherChristianActivities'],
            'family_duties': ['FamilyDuties','FamilyDuty','OtherFamilyDuties'],
            'hobbies': ['HobbiesAndSports','Hobby','OtherHobbies'],
            'health_conditions': ['HealthConditions','HealthCondition','OtherHealthConditions'],
            'guardians': ['Guardians','Guardian',False],
        }
        for prop_name, cs_attributes in cs_sections_mapping.iteritems():
            section = case_study[cs_attributes[0]]
            section_attr = cs_attributes[1]
            other_attrs = case_study[cs_attributes[2]] if cs_attributes[2] else 'None'
            if type(section) is dict and section.get(section_attr):
                values.extend(self._get_values(cr, uid, section[section_attr], prop_name, context))
            if other_attrs != 'None':
                values.append(self._get_values(cr, uid, other_attrs, prop_name, context))
        
        """ Natural Parents and Employment Section.
            nps_sections_mapping is of the form:
            {'CaseStudySectionName':['property_name_male','property_name_female','CaseStudyKey_male','CaseStudyKey_female']}
        """
        npe_sections_mapping = {
            'NaturalParents': ['father','mother','Father','Mother'],
            'Employment': ['male_guardian','female_guardian','FatherOrMaleGuardian','MotherOrFemaleGuardian'],
        }
        for section, prop_names in npe_sections_mapping.iteritems():
            for key, value in case_study[section].iteritems():
                property_name = ''
                if key.startswith('Father'):
                    property_name = prop_names[0]
                elif key.startswith('Mother'):
                    property_name = prop_names[1]
                else:
                    continue

                if value == 'false' or value == '':
                    continue
                elif value == 'true':
                    value = key.replace(prop_names[2], '').replace(prop_names[3], '')
                values.append(self._get_value_id(cr, uid, value, property_name, context))
                
        # Other sections
        values.append(self._get_value_id(cr, uid, case_study['NaturalParents']['MaritalStatusOfParents'], 
                                         'marital_status', context))
        vals['us_school_level'] = case_study['Schooling']['USSchoolEquivalent']
        values.append(self._get_value_id(cr, uid, case_study['Schooling']['SchoolPerformance'], 
                                         'school_performance', context))
        values.append(self._get_value_id(cr, uid, case_study['Schooling']['ChildsBestSubject'], 
                                         'school_best_subject', context))
        vals['attending_school_flag'] = bool(case_study['Schooling']['ChildAttendingSchool'])
        vals['nb_children_family'] = int(case_study['FamilySize']['TotalFamilyFemalesUnder18'])
        vals['nb_sisters'] = int(case_study['FamilySize']['TotalFamilyFemalesUnder18'])
        vals['nb_children_family'] += int(case_study['FamilySize']['TotalFamilyMalesUnder18'])-1
        vals['nb_brothers'] = int(case_study['FamilySize']['TotalFamilyMalesUnder18'])
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
        data = json.loads(r.text)['Image']['ImageData']
        
        attachment_obj = self.pool.get('ir.attachment')
        if not context:
            context = {}
        context['store_fname'] = type + '.' + format
        attachment_obj.create(cr, uid, {'datas_fname': type + '.' + format,
                                            'res_model': 'compassion.child.property',
                                            'res_id': child.case_study_ids[-1].id,
                                            'datas': data,
                                            'name': type + '.' + format}, context)
        return False

    def _get_values(self, cr, uid, _list, property_name, context):
        value_ids = []
        if isinstance(_list, list):
            for elem in _list:
                value_ids.append(self._get_value_id(cr, uid, elem,
                                                    property_name, context))
        elif isinstance(_list, basestring):
            value_ids.append(self._get_value_id(cr, uid, _list, property_name,
                                                context))
        return value_ids

    def _get_value_id(self, cr, uid, value, property_name, context=None):
        prop_val_obj = self.pool.get('compassion.child.property.value')
        value = value.lower()
        val_ids = prop_val_obj.search(cr, uid, [('value_en', '=like', value),
                                                ('property_name', '=', property_name)],
                                      context=context)
        if val_ids:
            return val_ids[0]
        prop_id = prop_val_obj.create(cr, uid, {'property_name': property_name,
                                                'value_en': value})
        return prop_id
        
    def _get_url(self, child_code, api_mess):
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        if not url or not api_key:
            raise orm.except_orm('ConfigError',
                                 _('Missing compass_url or compass_api_key '
                                   'in conf file'))
        if url.endswith('/'):
            url = url[:-1]     
        url += '/ci/v1/child/' + child_code + '/' + api_mess + '?api_key=' + api_key
        return url
