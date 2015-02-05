# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester , Kevin Cristi
#
#    The licence is in the file __openerp__.py
#
##############################################################################


class Child_description_fr:

    @classmethod
    def gen_fr_translation(
            cls, cr, uid, child, case_study, context=None):
        desc_fr = cls._get_guardians_info_fr(
            cr, uid, child, case_study, context)
        desc_fr += cls._get_school_info_fr(
            cr, uid, child, case_study, context)
        desc_fr += cls._gen_christ_act_fr(cr, uid, child, case_study, context)
        desc_fr += cls._gen_family_act_info_fr(
            cr, uid, child, case_study, context)
        desc_fr += cls._gen_hobbies_info_fr(
            cr, uid, child, case_study, context)
        return desc_fr

    @classmethod
    def _gen_list_string(cls, list):
        string = ', '.join(list[:-1])
        if len(list) > 1:
            string += ' et '
        string += list[-1]
        return string

    @classmethod
    def _gen_christ_act_fr(cls, cr, uid, child, case_study, context=None):
        ''' Generate the christian activities description part.
            Words as 'à', 'aux', ... are included in value_fr field.
        '''
        if not case_study.christian_activities_ids:
            return ''
        activities = [
            activity.value_fr if activity.value_fr else activity.value_en
            for activity in case_study.christian_activities_ids]
        activities_str = cls._gen_list_string(activities)
        string = u"A l'Église, %s participe %s. " % (
            child.firstname, activities_str)
        return string

    @classmethod
    def _gen_family_act_info_fr(
            cls, cr, uid, child, case_study, context=None):
        ''' Generate the family duties description part. There are 2 kind of
            activities:
             - Standards : introduced by 'aide à faire' and having
                the determinant in value_fr
             - Specials : having the action verb included in value_fr
        '''
        if not case_study.family_duties_ids:
            return ''
        specials = ['carries water', 'animal care', 'running errands',
                    'buying/selling in market'
                    'gathers firewood', 'teaching others']
        activities = [activity.value_fr if activity.value_fr
                      else activity.value_en
                      for activity in case_study.family_duties_ids
                      if activity.value_en not in specials]
        if len(activities):
            activities[0] = u'aide à faire %s' % activities[0]
        activities.extend([activity.value_fr if activity.value_fr
                           else activity.value_en
                           for activity in case_study.family_duties_ids
                           if activity.value_en in specials])
        activities_str = cls._gen_list_string(activities)
        string = u"A la maison, %s %s. " % (child.firstname, activities_str)
        return string

    @classmethod
    def _gen_hobbies_info_fr(cls, cr, uid, child, case_study, context=None):
        ''' Generate the hobbies description part.
             There are 2 kind of hobbies :
             - games, which are introduced by 'jouer' and having
                the determinant included in value_fr
             - verbs, which are simply printed without any decoration.
        '''
        if not case_study.hobbies_ids:
            return ''
        verbs = ['art/drawing', 'bicycling', 'jump rope', 'listening to music'
                 'musical instrument', 'reading', 'running'
                 'singing', 'story telling', 'swimming', 'walking']
        activities = [activity.value_fr if activity.value_fr
                      else activity.value_en
                      for activity in case_study.hobbies_ids
                      if activity.value_en not in verbs]
        if len(activities):
            activities[0] = u'jouer %s' % activities[0]
        activities.extend([activity.value_fr if activity.value_fr
                           else activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in verbs])
        activities_str = cls._gen_list_string(activities)
        string = u"%s aime beaucoup %s. " % ('Il' if child.gender == 'M'
                                             else 'Elle', activities_str)
        return string

    @classmethod
    def _get_school_info_fr(cls, cr, uid, child, case_study, context=None):
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
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    string += (u' est en %s année (US)'
                               % ordinals[case_study.us_school_level])
                except:
                    string += (u' est en %s (US)'
                               % ordinals[case_study.us_school_level])
            else:
                string += u" va à l'école"
            if case_study.school_performance:
                string += (u' et %s a des résultats %s. ' % (child.firstname,
                           case_study.school_performance[0].value_fr
                           if case_study.school_performance[0].value_fr
                           else case_study.school_performance[0].value_en))
            elif case_study.school_best_subject:
                string += u' et aime bien %s. ' \
                          % (case_study.school_best_subject[0].value_fr
                             if case_study.school_best_subject[0].value_fr
                             else case_study.school_best_subject[0].value_en)
            else:
                string += '.'
        else:
            string += u" ne va pas à l'école"  # TODO reason
        return string

    @classmethod
    def _get_guardians_info_fr(cls, cr, uid, child, case_study, context=None):
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
            value = (guardian.value_fr if guardian.value_fr
                     else guardian.value_en)
            if guardian.value_en in male_values:
                live_with.append(u'son %s' % value)
                male_guardian = value if not male_guardian else male_guardian
            elif guardian.value_en in plur_values:
                live_with.append(u'des %s' % value)
            else:
                if female_guardian == 'institutional worker':
                    live_with.append(u'un institut')  # find better "institut"
                else:
                    if value == 'institutional worker':
                        live_with.append(u'un institut')
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
                    else:
                        live_with.append(u'sa %s' % value)
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
        if case_study.nb_brothers == 1:
            live_with.append(u'son frère')
        elif case_study.nb_brothers > 1:
            live_with.append(u'ses %s frères' % case_study.nb_brothers)
        if case_study.nb_sisters == 1:
            live_with.append(u'sa soeur')
        elif case_study.nb_sisters > 1:
            live_with.append(u'ses %s soeurs' % case_study.nb_sisters)
        if 'un institut' in live_with:
            guardian_str = '%s avec %s' % (live_with[0], live_with[1])
        else:
            guardian_str = cls._gen_list_string(live_with)
        if 'institut' in guardian_str:
            string = '%s vit dans %s. ' % (child.firstname, guardian_str)
        else:
            string = '%s vit avec %s. ' % (child.firstname, guardian_str)
        string += cls._get_guardians_jobs_fr(cr, uid, child, case_study,
                                             male_guardian, female_guardian,
                                             context)
        return string

    @classmethod
    def _get_guardians_jobs_fr(cls, cr, uid, child,
                               case_study, m_g, f_g, context=None):
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

            string = u""

            if f_g != 'institutional worker':
                if ('isunemployed' in props_m) and job_f:
                    string = (u"Sa %s est %s et son %s n'a pas d'emploi."
                              % (f_g, job_f[0], m_g))

                elif job_m and ('isunemployed' in props_f):
                    string = (u"Son %s est %s et sa %s n'a pas d'emploi."
                              % (m_g, job_m[0], f_g))

                elif ('isunemployed' in props_m) and ('isunemployed'
                                                      in props_f):
                    if f_g == "mother" and m_g == "father":
                        string = u"Ses parents n'ont pas d'emploi."

                    else:
                        string = (u"Son %s et sa %s n'ont pas d'emploi."
                                  % (m_g, f_g))

                elif job_m and job_f:

                    if ((job_f[0][0:7] == job_m[0][0:7])
                            and (f_g == u"mère" and m_g == u"père")):

                        string = u"Ses parents sont %ss." % job_m[0]

                    else:

                        string = (u"Sa %s est %s et son %s est %s."
                                  % (f_g, job_f[0], m_g, job_m[0]))

        return string
