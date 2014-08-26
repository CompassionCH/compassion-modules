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

import logging
logger = logging.getLogger(__name__)
from openerp.osv import orm, fields
from openerp.tools.translate import _


class child_description_wizard(orm.TransientModel):
    _name = 'child.description.wizard'
    
    def get_value_ids(self, cr, uid, ids, field_name, arg, context=None):
        property_id = context.get('case_study_id', False)
        logger.info("%s" % context)
        if not property_id:
            return {ids[0]: []}

        value_obj = self.pool.get('compassion.child.property.value')
        value_ids = value_obj.search(cr, uid, vals = [('property_id', '=', property_id)])
        logger.info("%s" % value_ids)
        return {ids[0]: value_ids}
    
    _columns = {
        'keep_desc_fr': fields.boolean(_('Keep french description')),
        'desc_fr': fields.text(_('French description')),
        'keep_desc_de': fields.boolean(_('Keep german description')),
        'desc_de': fields.text(_('German description')),
        'keep_desc_it': fields.boolean(_('Keep italian description')),
        'desc_it': fields.text(_('Italian description')),
        'keep_desc_en': fields.boolean(_('Keep english description')),
        'desc_en': fields.text(_('English description')),
        'child_property_value_ids': fields.function(get_value_ids, type='char',
                                                    relation='compassion.child.property.value'),
        'state': fields.selection(
            [('values', _('Values completion')),
             ('descriptions', _('Descriptions correction'))],
            _('State'), required=True, readonly=True),
    }

    _defaults = {
        'state': 'values',
        'keep_desc_fr': False,
        'keep_desc_de': False,
        'keep_desc_it': False,
        'keep_desc_en': False,
    }
    
    def generate_descriptions(self, cr, uid, ids, context=None):
        child_obj = self.pool.get('compassion.child')
        child = child_obj.browse(cr, uid, context.get('child_id'), context)
        if not child:
            raise orm.except_orm('ObjectError', _('No valid child id given !'))
        child = child[0]
        case_study = child.case_study_ids[-1]
        self.write(cr, uid, ids, {
            'state': 'descriptions',
            'desc_fr': self.gen_fr_translation(cr, uid, child, case_study, context)
            }, context)
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': ids[0],
            'context': context,
            'target': 'new',
            }

    def validate_descriptions(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids, context)[0]
        vals = {}
        if wizard.keep_desc_fr:
            vals['desc_fr'] = wizard.desc_fr
        if wizard.keep_desc_de:
            vals['desc_de'] = wizard.desc_de
        if wizard.keep_desc_it:
            vals['desc_it'] = wizard.desc_it
        if wizard.keep_desc_en:
            vals['desc_en'] = wizard.desc_en

        if not vals:
            raise orm.except_orm('ValueError',
                                 _('No description selected. Please select one or click cancel '
                                   'to abort current task.'))
        child_obj = self.pool.get('compassion.child')
        child_obj.write(cr, uid, context['child_id'], vals, context)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _gen_list_string(self, list, separator, last_separator):
        string = separator.join(list[:-1])
        if len(list) > 1:
            string += last_separator
        string += list[-1]
        return string

    ##################################################
    #              French description                #
    #                  generation                    #
    ##################################################
    def gen_fr_translation(self, cr, uid, child, case_study, context=None):
        desc_fr = self._get_guardians_info_fr(cr, uid, child, case_study, context)
        desc_fr += self._get_school_info_fr(cr, uid, child, case_study, context)
        desc_fr += self._gen_christ_act_fr(cr, uid, child, case_study, context)
        desc_fr += self._gen_family_act_info_fr(cr, uid, child, case_study, context)
        desc_fr += self._gen_hobbies_info_fr(cr, uid, child, case_study, context)
        return desc_fr
        
    def _gen_christ_act_fr(self, cr, uid, child, case_study, context=None):
        ''' Generate the christian activities description part.
            Words as 'à', 'aux', ... are included in value_fr field.
        '''
        if not case_study.christian_activities_ids:
            return ''
        activities = [activity.value_fr if activity.value_fr else activity.value_en 
                      for activity in case_study.christian_activities_ids]
        activities_str = self._gen_list_string(activities, ', ', ' et ')
        string = u"A l'Église, %s participe %s. " % (child.firstname, activities_str)
        return string

    def _gen_family_act_info_fr(self, cr, uid, child, case_study, context=None):
        ''' Generate the family duties description part. There are 2 kind of
            activities: 
             - Standards : introduced by 'aide à faire' and having the determinant in value_fr
             - Specials : having the action verb included in value_fr
        '''
        if not case_study.family_duties_ids:
            return ''
        specials = ['carries water', 'animal care', 'running errands', 'buying/selling in market'
                     'gathers firewood', 'teaching others']
        activities = [activity.value_fr if activity.value_fr else activity.value_en
                      for activity in case_study.family_duties_ids
                      if activity.value_en not in specials]
        if len(activities):
            activities[0] = u'aide à faire %s' % activities[0]
        activities.extend([activity.value_fr if activity.value_fr else activity.value_en
                           for activity in case_study.family_duties_ids
                           if activity.value_en in specials])
        activities_str = self._gen_list_string(activities, ', ', ' et ')
        string = u"A la maison, %s %s. " % (child.firstname, activities_str)
        return string

    def _gen_hobbies_info_fr(self, cr, uid, child, case_study, context=None):
        ''' Generate the hobbies description part. There are 2 kind of hobbies :
             - games, which are introduced by 'jouer' and having the determinant included in value_fr
             - verbs, which are simply printed without any decoration.
        '''
        if not case_study.hobbies_ids:
            return ''
        verbs = ['art/drawing', 'bicycling', 'jump rope', 'listening to music'
                 'musical instrument', 'reading', 'running', 'singing', 'story telling',
                 'swimming', 'walking']
        activities = [activity.value_fr if activity.value_fr else activity.value_en
                      for activity in case_study.hobbies_ids
                      if activity.value_en not in verbs]
        if len(activities):
            activities[0] = u'jouer %s' % activities[0]
        activities.extend([activity.value_fr if activity.value_fr else activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in verbs])
        activities_str = self._gen_list_string(activities, ', ', ' et ')
        string = u"%s aime beaucoup %s. " % ('Il' if child.gender == 'M' else 'Elle', activities_str)
        return string

    def _get_school_info_fr(self, cr, uid, child, case_study, context=None):
        ''' Generate the school description part. Description includes :
             - If child is attending school
             - Reason why not attending school if relevant and existing
             - US school level if relevant
             - School performance if relevant and existing
             - School favourite subject if relevant and existing
        '''
        ordinals = [u'première', u'deuxième', u'troisième', u'quatrième', u'cinquième',
                    u'sixième', u'septième', u'huitième', u'neuvième', u'dixième', u'onzième',
                    u'douzième', u'treizième', u'quatorzième', u'quinzième']
        string = u'Il' if child.gender == 'M' else u'Elle'
        if case_study.attending_school_flag:
            if case_study.us_school_level and int(case_study.us_school_level) < 16:
                string += u' est en %s année (US)' % ordinals[int(case_study.us_school_level)-1]
            else:
                string += u' va à l\'école'
            if case_study.school_performance:
                string += u' et %s a des résultats %s. ' % (child.firstname, 
                          case_study.school_performance[0].value_fr
                          if case_study.school_performance[0].value_fr
                            else case_study.school_performance[0].value_en)
            elif case_study.school_best_subject:
                string += ' et aime bien %s. ' % (case_study.school_best_subject[0].value_fr
                          if case_study.school_best_subject[0].value_fr
                            else case_study.school_best_subject[0].value_en)
            else:
                string += '.'
        else:
            string += ' ne va pas à l\'école' #TODO reason
            

        return string

    def _get_guardians_info_fr(self, cr, uid, child, case_study, context=None):
        ''' Generate the guardian description part. Guardians jobs are also included here.
        '''
        if not case_study.guardians_ids:
            return ''
        male_values = ['father', 'uncle', 'brother', 'grandfather', 'stepfather', 'godfather']
        plur_values = ['friends', 'other relatives']
        live_with = []
        male_guardian = ''
        female_guardian = ''
        for guardian in case_study.guardians_ids:
            value = guardian.value_fr if guardian.value_fr else guardian.value_en
            if guardian.value_en in male_values:
                live_with.append(u'son %s' % value)
                male_guardian = value if not male_guardian else male_guardian
            elif guardian.value_en in plur_values:
                live_with.append(u'des %s' % value)
            else:
                live_with.append(u'sa %s' % value)
                female_guardian = value if not female_guardian else female_guardian
                
        if case_study.nb_brothers == 1:
            live_with.append(u'son frère')
        elif case_study.nb_brothers > 1:
            live_with.append(u'ses %s frères' % case_study.nb_brothers)
        if case_study.nb_sisters == 1:
            live_with.append(u'sa soeur')
        elif case_study.nb_sisters > 1:
            live_with.append(u'ses %s soeurs' % case_study.nb_sisters)
        guardian_str = self._gen_list_string(live_with, ', ', ' et ')
        string = '%s vit avec %s. ' % (child.firstname, guardian_str)
        string += self._get_guardians_jobs_fr(cr, uid, child, case_study, male_guardian, female_guardian, context)
        return string

    def _get_guardians_jobs_fr(self, cr, uid, child, case_study, m_g, f_g, context=None):
        ''' Generate the guardians jobs description part. '''
        string = ''
        if case_study.male_guardian_ids:
            props = [emp.value_en for emp in case_study.male_guardian_ids]
            job = [emp.value_fr if emp.value_fr else emp.value_en
                        for emp in case_study.male_guardian_ids
                        if not emp.value_en.endswith('mployed')]
            if 'isunemployed' in props:
                string += u"Son %s n'a pas d'emploi." % m_g
            elif job:
                string += u"Son %s est %s. " % (m_g, job[0])
        if case_study.female_guardian_ids:
            props = [emp.value_en for emp in case_study.female_guardian_ids]
            job = [emp.value_fr if emp.value_fr else emp.value_en
                        for emp in case_study.female_guardian_ids
                        if not emp.value_en.endswith('mployed')]
            if 'isunemployed' in props:
                string += u"Sa %s n'a pas d'emploi." % m_g
            elif job:
                string += u"Sa %s est %s. " % (f_g, job[0])
        return string

