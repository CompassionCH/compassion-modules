# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
import re #regexp module (standard)

class child_description_wizard(orm.TransientModel):
    _name = 'child.description.wizard'
    
    def _get_value_ids(self, cr, uid, ids, fieldname, args, context=None):
        property_id = context.get('property_id')
        if not property_id:
            return dict([(id, []) for id in ids])

        value_obj = self.pool.get('compassion.child.property.value')
        query = '''SELECT rel.value_id 
                   FROM child_property_to_value as rel, 
                        compassion_child_property_value as val 
                   WHERE rel.property_id = %s 
                   AND rel.value_id = val.id
                   AND val.is_tag = false
                   AND (
                        val.value_fr is Null 
                        OR val.value_de is Null 
                        OR val.value_it is Null)
                   ORDER BY val.value_en, val.property_name''' % property_id
        cr.execute(query)
        value_ids = [x[0] for x in cr.fetchall()]
        return dict([(id, value_ids) for id in ids])

    def _get_default_ids(self, cr, uid, context=None):
        return self._get_value_ids(cr, uid, [0], '', '', context)[0]

    def _write_values(self, cr, uid, id, name, value, inv_arg, context=None):
        value_obj = self.pool.get('compassion.child.property.value')
        for line in value:
            if line[0] == 1: # on2many update
                value_id = line[1]
                value_obj.write(cr, uid, [value_id], line[2])
        return True
    
    _columns = {
        'keep_desc_fr': fields.boolean(_('Keep french description')),
        'desc_fr': fields.text(_('French description')),
        'keep_desc_de': fields.boolean(_('Keep german description')),
        'desc_de': fields.text(_('German description')),
        'keep_desc_it': fields.boolean(_('Keep italian description')),
        'desc_it': fields.text(_('Italian description')),
        'keep_desc_en': fields.boolean(_('Keep english description')),
        'desc_en': fields.text(_('English description')),
        'child_property_value_ids': fields.function(_get_value_ids, type='one2many',
                                                    relation='compassion.child.property.value',
                                                    fnct_inv=_write_values),
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
        'child_property_value_ids': lambda self, cr, uid, context: \
                                        self._get_default_ids(cr, uid, context),
    }

    def generate_descriptions(self, cr, uid, ids, context=None):
        child_obj = self.pool.get('compassion.child')
        child = child_obj.browse(cr, uid, context.get('child_id'), context)
        if not child:
            raise orm.except_orm('ObjectError', _('No valid child id given !'))
        if isinstance(child, list):
            child = child[0]
        case_study = child.case_study_ids[-1]
        self.write(cr, uid, ids, {
            'state': 'descriptions',
            'desc_fr': self.gen_fr_translation(cr, uid, child, case_study, context)
            }, context)
            
        return {
            'name': _('Descriptions generation'),
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

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None,
                        toolbar=False, submenu=False):
        ret = super(child_description_wizard, self).fields_view_get(cr, uid, view_id, view_type, 
                                                                    context, toolbar, submenu)
        fr, de, it, en = self._get_helps(cr, uid, context)
        ret['fields']['desc_fr']['help'] = fr
        ret['fields']['desc_de']['help'] = de
        ret['fields']['desc_it']['help'] = it
        ret['fields']['desc_en']['help'] = en
        return ret

    def _get_helps(self, cr, uid, context=None):
        if not context or not context.get('child_id'):
            return '', '', '', ''
        child_obj = self.pool.get('compassion.child')
        child = child_obj.browse(cr, uid, context['child_id'], context=context)[0]
        return child.desc_fr, child.desc_de, child.desc_it, child.desc_en

    ##################################################
    #              Common description                #
    #                     tools                      #
    ##################################################
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
        ordinals = {
                    '1': u'première',
                    '2': u'deuxième',
                    '3': u'troisième',
                    '4': u'quatrième',
                    '5': u'cinquième',
                    '6': u'sixième',
                    '7': u'septième',
                    '8': u'huitième',
                    '9': u'neuvième',
                    '10': u'dixième',
                    '11': u'onzième',
                    '12': u'douzième',
                    '13': u'treizième',
                    '14': u'quatorzième',
                    'PK': u'première enfantine',
                    'K': u'deuxième enfantine', 
                    'P': u'primaire',
                    }
                    # the value of us_school_level can also be blank
        string = u'Il' if child.gender == 'M' else u'Elle'
        if case_study.attending_school_flag:
            if case_study.us_school_level and case_study.us_school_level in ordinals:
                try:
                    int(case_study.us_school_level)
                    string += u' est en %s année (US)' % ordinals[case_study.us_school_level]
                except:
                    string += u' est en %s (US)' % ordinals[case_study.us_school_level]
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
        plur_values = ['friends', 'other relatives', 'foster parents']
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
                if female_guardian == 'institutional worker':
                    live_with.append(u'un institut') # find better word than "institut"
                else:
                    if value == 'institutional worker':
                        live_with.append(u'un institut')
                        female_guardian = value if not female_guardian else female_guardian
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
        if 'un institut' in live_with:
            guardian_str = '%s avec %s' %(live_with[0], live_with[1])
        else:
            guardian_str = self._gen_list_string(live_with, ', ', ' et ')
        if 'institut' in guardian_str:
            string = '%s vit dans %s. ' % (child.firstname, guardian_str)
        else:
            string = '%s vit avec %s. ' % (child.firstname, guardian_str)
        string += self._get_guardians_jobs_fr(cr, uid, child, case_study, male_guardian, female_guardian, context)
        return string       
        
    def _get_guardians_jobs_fr(self, cr, uid, child, case_study, m_g, f_g, context=None):
        ''' Generate the guardians jobs description part. '''
        if case_study.male_guardian_ids or case_study.female_guardian_ids:
            props_m = [emp.value_en for emp in case_study.male_guardian_ids]
            job_m = [emp.value_fr if emp.value_fr else emp.value_en
                        for emp in case_study.male_guardian_ids
                        if not emp.value_en.endswith('mployed')]
            props_f = [emp.value_en for emp in case_study.female_guardian_ids]
            job_f = [emp.value_fr if emp.value_fr else emp.value_en
                        for emp in case_study.female_guardian_ids
                        if not emp.value_en.endswith('mployed')]
            if f_g == 'institutional worker':
                string = u""
            else:
                if ('isunemployed' in props_m) and job_f:
                    string = u"Sa %s est %s et son %s n'a pas d'emploi." %(f_g, job_f[0], m_g)
                elif job_m and ('isunemployed' in props_f):
                    string = u"Son %s est %s et sa %s n'a pas d'emploi." %(m_g, job_m[0], f_g)
                elif ('isunemployed' in props_m) and ('isunemployed' in props_f):
                    if f_g == "mother" and m_g == "father":
                        string = u"Ses parents n'ont pas d'emploi."
                    else:
                        string = u"Son %s et sa %s n'ont pas d'emploi." %(m_g, f_g)
                elif job_m and job_f:
                    if (job_f[0][0:7] == job_m[0][0:7]) and (f_g == u"mère" and m_g == u"père"):
                        string = u"Ses parents sont %ss." %job_m[0]
                    else:
                        string = u"Sa %s est %s et son %s est %s." %(f_g, job_f[0], m_g, job_m[0])
        return string
