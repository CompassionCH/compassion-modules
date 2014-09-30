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


class Child_description_de:

    @classmethod
    def gen_de_translation(
            cls, cr, uid, child, case_study, context=None):
        desc_de = cls._get_guardians_info_de(
            cr, uid, child, case_study, context)
        desc_de += cls._get_school_info_de(
            cr, uid, child, case_study, context)
        desc_de += cls._gen_christ_act_de(cr, uid, child, case_study, context)
        desc_de += cls._gen_family_act_info_de(
            cr, uid, child, case_study, context)
        desc_de += cls._gen_hobbies_info_de(
            cr, uid, child, case_study, context)
        return desc_de

    @classmethod
    def _gen_christ_act_de(cls, cr, uid, child, case_study, context=None):
        ''' Generate the christian activities description part.
        '''
        if child.gender == 'M':
            pronom = 'er'
            pronom_maj = 'Er'
        else:
            pronom = 'sie'
            pronom = 'Sie'

        if not case_study.christian_activities_ids:
            return ''
        activities = [
            activity.value_de if activity.value_de else activity.value_en
            for activity in case_study.christian_activities_ids]
        activities_str = cls._gen_list_string(activities, ', ', ' und ')
        string = u"In der Kirche macht %s %s. " % (
            pronom, activities_str)
        return string

    @classmethod
    def _gen_family_act_info_de(
            cls, cr, uid, child, case_study, context=None):
        ''' Generate the family duties description part. There are 2 kind of
            activities:
             - Standards : introduced by 'erledigt' and having  # erledigt or hilft
                the determinant in value_de
             - Specials : having the action verb included in value_de
        '''
        if not case_study.family_duties_ids:
            return ''
        specials = ['carries water', 'animal care', 'running errands',
                    'buying/selling in market'
                    'gathers firewood', 'teaching others']
        activities = [activity.value_de if activity.value_de
                      else activity.value_en
                      for activity in case_study.family_duties_ids
                      if activity.value_en not in specials]
        if len(activities):
            #activities[0] = u'aide à faire %s' % activities[0]
            activities[0] = u'erledigt %s' % activities[0]
        activities.extend([activity.value_de if activity.value_de
                           else activity.value_en
                           for activity in case_study.family_duties_ids
                           if activity.value_en in specials])
        activities_str = cls._gen_list_string(activities, ', ', ' et ')
        string = u"Zu Hause, %s %s. " % (child.firstname, activities_str)
        return string

    @classmethod
    def _gen_hobbies_info_de(cls, cr, uid, child, case_study, context=None):
        ''' Generate the hobbies description part.
             There are 2 kind of hobbies :
             - games, which are introduced by 'jouer' and having
                the determinant included in value_de
             - verbs, which are simply printed without any decoration.
        '''
        if not case_study.hobbies_ids:
            return ''
        verbs = ['art/drawing', 'bicycling', 'jump rope', 'listening to music'
                 'musical instrument', 'reading', 'running'
                 'singing', 'story telling', 'swimming', 'walking']
        activities = [activity.value_de if activity.value_de
                      else activity.value_en
                      for activity in case_study.hobbies_ids
                      if activity.value_en not in verbs]
        if len(activities):
            activities[0] = u'spielen %s' % activities[0]
        activities.extend([activity.value_de if activity.value_de
                           else activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in verbs])
        activities_str = cls._gen_list_string(activities, ', ', ' und ')
        string = u"%s liebe %s. " % ('Il' if child.gender == 'M'
                                             else 'Elle', activities_str)
        return string

    @classmethod
    def _get_school_info_de(cls, cr, uid, child, case_study, context=None):
        ''' Generate the school description part. Description includes :
             - If child is attending school
             - Reason why not attending school if relevant and existing
             - US school level if relevant
             - School performance if relevant and existing
             - School favourite subject if relevant and existing
        '''
        ordinals = {
            '1': u'erste',
            '2': u'zweite',
            '3': u'dreite',
            '4': u'vierte',
            '5': u'fünfte',
            '6': u'sechste',
            '7': u'siebste',
            '8': u'achte',
            '9': u'neunte',
            '10': u'zehnte',
            '11': u'elfte',
            '12': u'zwölfte',
            '13': u'dreizehnte',
            '14': u'vierzehnte',
            'PK': u'pre kindergarten',
            'K': u'kindergarten',
            'P': u'primär',
            }
                    # the value of us_school_level can also be blank
        string = u'Er' if child.gender == 'M' else u'Sie'
        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    string += (u' ist in der %s Klasse (US)'  # or Dieses erste Jahr. ?
                               % ordinals[case_study.us_school_level])
                except:
                    string += (u' est en %s (US)'
                               % ordinals[case_study.us_school_level])
            else:
                string += u' va à l\'école'
            if case_study.school_performance:
                string += u' et %s a des résultats %s. ' % (child.firstname,
                          case_study.school_performance[0].value_de
                          if case_study.school_performance[0].value_de
                          else case_study.school_performance[0].value_en)
            elif case_study.school_best_subject:
                string += u' et aime bien %s. ' \
                          % (case_study.school_best_subject[0].value_de
                             if case_study.school_best_subject[0].value_de
                             else case_study.school_best_subject[0].value_en)
            else:
                string += '.'
        else:
            string += ' ne va pas à l\'école'  # TODO reason

        return string

    @classmethod
    def _gen_list_string(cls, list, separator, last_separator):
        string = separator.join(list[:-1])
        if len(list) > 1:
            string += last_separator
        string += list[-1]
        return string

    @classmethod
    def _get_guardians_info_de(cls, cr, uid, child, case_study, context=None):
        ''' Generate the guardian description part. Guardians jobs are
            also included here.
        '''
        if not case_study.guardians_ids:
            return ''
        male_values = ['father', 'uncle', 'brother', 'grandfather',
                       'stepfather', 'godfather']
        plur_values = ['friends', 'other relatives', 'foster parents']
        live_with = []
        male_guardian = ''
        female_guardian = ''
        for guardian in case_study.guardians_ids:
            value = (guardian.value_de if guardian.value_de
                     else guardian.value_en)
            if guardian.value_en in male_values:
                if value == 'stepfather' or value == 'Stiefvater':
                    live_with.append(u'seinem %s' % value)
                else:
                    live_with.append(u'sein %s' % value)
                male_guardian = value if not male_guardian else male_guardian
            elif guardian.value_en in plur_values:
                if  value == 'friends' or value == 'Freunde':
                    live_with.append(u'ihre %s' % value)
                elif value == 'other relatives' or value == 'andere Verwandte':
                    live_with.append(u' %s' % value)
                #elif value == 'foster parents' or value == 'Pflegeeltern':
                else:
                    live_with.append(u' %s' % value)
            else:
                if female_guardian == 'institutional worker':
                    live_with.append(u'einem Institut')  # find better "institut"
                else:
                    if value == 'institutional worker':
                        live_with.append(u'einem Institut')
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
                    else:
                        live_with.append(u'ihre %s' % value)
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
        if case_study.nb_brothers == 1:
            live_with.append(u'sein Bruder')
        elif case_study.nb_brothers > 1:
            live_with.append(u'seine %s Brüder' % case_study.nb_brothers)
        if case_study.nb_sisters == 1:
            live_with.append(u'ihren Schwester')
        elif case_study.nb_sisters > 1:
            live_with.append(u'ihren %s Schwester' % case_study.nb_sisters)
        if 'un institut' in live_with:
            guardian_str = '%s mit %s' % (live_with[0], live_with[1])
        else:
            guardian_str = cls._gen_list_string(live_with, ', ', ' und ')
        if 'institut' in guardian_str:
            string = '%s lebt in %s. ' % (child.firstname, guardian_str)
        else:
            string = '%s lebt mit %s. ' % (child.firstname, guardian_str)
        string += cls._get_guardians_jobs_de(cr, uid, child, case_study,
                                             male_guardian, female_guardian,
                                             context)
        return string

    @classmethod
    def _get_guardians_jobs_de(cls, cr, uid, child,
                               case_study, m_g, f_g, context=None):
        ''' Generate the guardians jobs description part. '''
        if case_study.male_guardian_ids or case_study.female_guardian_ids:
            props_m = [emp.value_en for emp in case_study.male_guardian_ids]
            job_m = [emp.value_de if emp.value_de else emp.value_en
                     for emp in case_study.male_guardian_ids
                     if not emp.value_en.endswith('mployed')]
            props_f = [emp.value_en for emp in case_study.female_guardian_ids]
            job_f = [emp.value_de if emp.value_de else emp.value_en
                     for emp in case_study.female_guardian_ids
                     if not emp.value_en.endswith('mployed')]
            if f_g == 'institutional worker':
                string = u""
            else:
                if ('isunemployed' in props_m) and job_f:
                    string = (u"Ihre %s ist %s und sein %s arbeitslos ist."
                              % (f_g, job_f[0], m_g))
                elif job_m and ('isunemployed' in props_f):
                    string = (u"Sein %s ist %s und ihre %s arbeitslos ist."
                              % (m_g, job_m[0], f_g))
                elif ('isunemployed' in props_m) and ('isunemployed'
                                                      in props_f):
                    if f_g == "mother" and m_g == "father":
                        string = u"Ihre Eltern arbeitslos sind."
                    else:
                        string = (u"Sein %s und ihre %s arbeitslos sind."
                                  % (m_g, f_g))
                elif job_m and job_f:
                    if ((job_f[0][0:7] == job_m[0][0:7])
                            and (f_g == u"Mutter" and m_g == u"Vater")):
                        string = u"Ihre Eltern sind %ss." % job_m[0]
                    else:
                        string = (u"Ihre %s ist %s und sein %s ist %s."
                                  % (f_g, job_f[0], m_g, job_m[0]))
        return string
