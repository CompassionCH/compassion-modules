# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Kevin Cristi <kcristi@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


class Child_description_en:

    @classmethod
    def gen_en_translation(
            cls, cr, uid, child, case_study, context=None):
        desc_en = cls._get_guardians_info_en(
            cr, uid, child, case_study, context)
        desc_en += cls._get_school_info_en(
            cr, uid, child, case_study, context)
        desc_en += cls._gen_christ_act_en(cr, uid, child, case_study, context)
        desc_en += cls._gen_family_act_info_en(
            cr, uid, child, case_study, context)
        desc_en += cls._gen_hobbies_info_en(
            cr, uid, child, case_study, context)
        return desc_en

    @classmethod
    def _gen_christ_act_en(cls, cr, uid, child, case_study, context=None):
        ''' Generate the christian activities description part.
        '''
        if not case_study.christian_activities_ids:
            return ''
        activities = [
            activity.value_en
            for activity in case_study.christian_activities_ids]
        activities_str = cls._gen_list_string(activities, ', ', ' and ')
        string = (u"As part of the Church, %s %s %s" % (
                  'he' if child.gender == 'M' else 'she', activities_str
                  if activities_str > 1 else '. '))
        return string

    @classmethod
    def _gen_family_act_info_en(
            cls, cr, uid, child, case_study, context=None):
        ''' Generate the family duties description part.
            In English, it always starts with "At home, she/he helps to"
            It's followed by the family duties.
        '''
        if not case_study.family_duties_ids:
            return ''
        activities = ([activity.value_en
                       for activity in case_study.family_duties_ids])
        activities_str = cls._gen_list_string(activities, ', ', ' and ')
        string = (u"At home, %s helps with family jobs such as %s. " % (
                  'he' if child.gender == 'M'
                  else 'she', activities_str))
        return string

    @classmethod
    def _gen_hobbies_info_en(cls, cr, uid, child, case_study, context=None):
        ''' Generates the hobbies description part.
            There are 4 groups of hobbies :
            - hobbies starting with "She/He enjoys playing with" (shepw)
            - hobbies starting with "She/He enjoys playing" (shep)
            - hobbies starting with "She/He enjoys to" (shet)
            - hobbies starting with "She/He enjoys" (she)
        '''

        if not case_study.hobbies_ids:
            return ''
        hobbies_shepw = [
            'cars', 'jacks', 'dolls', 'marbles','musical instrument',
            ]
        hobbies_shep = [
            'baseball', 'basketball', 'hide and seek', 'other ball games',
            'ping pong', 'soccer/footbal', 'volleyball',
            ]
        hobbies_shet = [
            'jump rope', 'play house',
            ]
        hobbies_she = [
            'art/drawing', 'bicycling', 'group games', 'listening to music',
            'story telling', 'rolling a hoop', 'reading', 'running',
            'other sports or hobbies', 'singing', 'swimming', 'walking',
            ]
        activities_shepw = [activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in (hobbies_shepw)]
        activities_shep = [activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in (hobbies_shep)]
        activities_shet = [activity.value_en
                         for activity in case_study.hobbies_ids
                         if activity.value_en in (hobbies_shet)]
        activities_she = [activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in (hobbies_she)]
        string = ''
        if activities_shepw:
            string_shepw = u"%s enjoys playing with " % (
                'He' if child.gender == 'M' else 'She')
            if len(activities_shepw) == 1:
                string_shepw += activities_shepw[0]
            else:
                num_loop = 0
                for activity in activities_shepw:
                    num_loop += 1
                    if num_loop == 1:
                        string_shepw += activity
                    elif num_loop == len(activities_shepw):
                        string_shepw += " and " + activity
                    else:
                        string_shepw += ", " + activity
            string_shepw += u". "
            string += string_shepw

        if activities_shep:
            string_shep = u"%s enjoys playing " % (
                'He' if child.gender == 'M' else 'She')
            if len(activities_shep) == 1:
                string_shep += activities_shep[0]
            else:
                num_loop = 0
                for activity in activities_shep:
                    num_loop += 1
                    if num_loop == 1:
                        string_shep += activity
                    elif num_loop == len(activities_shep):
                        string_shep += " and " + activity
                    else:
                        string_shep += ", " + activity
            string_shep += u". "
            string += string_shep

        if activities_shet:
            string_shet = u"%s enjoys to " % (
                'He' if child.gender == 'M' else 'She')
            if len(activities_shet) == 1:
                string_shet += activities_shet[0]
            else:
                num_loop = 0
                for activity in activities_shet:
                    num_loop += 1
                    if num_loop == 1:
                        string_shet += activity
                    elif num_loop == len(activities_shet):
                        string_shet += " and " + activity
                    else:
                        string_shet += ", " + activity
            string_shet += u". "
            string += string_shet

        if activities_she:
            string_she = u"%s enjoys " % (
                'He' if child.gender == 'M' else 'She')
            if len(activities_she) == 1:
                string_she += activities_she[0]
            else:
                num_loop = 0
                for activity in activities_she:
                    num_loop += 1
                    if num_loop == 1:
                        string_she += activity
                    elif num_loop == len(activities_she):
                        string_she += " and " + activity
                    else:
                        string_she += ", " + activity
            string_she += u". "
            string += string_she
        return string

    @classmethod
    def _get_school_info_en(cls, cr, uid, child, case_study, context=None):
        ''' Generate the school description part. Description includes :
             - If child is attending school
             - Reason why not attending school if relevant and existing
             - US school level if relevant
             - School performance if relevant and existing
             - School favourite subject if relevant and existing
        '''
        ordinals = {
            '1': u'first',
            '2': u'second',
            '3': u'third',
            '4': u'fourth',
            '5': u'fifth',
            '6': u'sixth',
            '7': u'seventh',
            '8': u'eighth',
            '9': u'ninth',
            '10': u'tenth',
            '11': u'eleventh',
            '12': u'twelfth',
            '13': u'thirteenth',
            '14': u'fourteenth',
            'PK': u'pre-Kindergarten',
            'K': u'Kindergarten',
            'P': u'Primary',
            }
        # the value of us_school_level can also be blank
        string = u'He' if child.gender == 'M' else u'She'
        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    string += (u" 's in the %s year (US)"
                               % ordinals[case_study.us_school_level])
                except:
                    string += (u" 's in %s (US)"
                               % ordinals[case_study.us_school_level])
            else:
                string += u' goes to school'
            if case_study.school_performance:
                string += (u' and %s has %s marks. ' % (child.firstname,
                           case_study.school_performance[0].value_en))
            elif case_study.school_best_subject:
                string += u' and likes: %s. ' \
                          % (case_study.school_best_subject[0].value_en)
            else:
                string += '.'
        else:
            string += " doesn't go to school."  # TODO reason
        return string

    @classmethod
    def _gen_list_string(cls, list, separator, last_separator):
        string = separator.join(list[:-1])
        if len(list) > 1:
            string += last_separator
        string += list[-1]
        return string

    ########################## START HERE #####################################
    @classmethod
    def _get_guardians_info_en(cls, cr, uid, child, case_study, context=None):
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
            value = guardian.value_en
            if guardian.value_en in male_values:
                child_to_guardian_pronoun = (u'his' if child.gender == 'M'
                                             else u'her')
                live_with.append(u'%s %s' % (child_to_guardian_pronoun, value))
                male_guardian = value if not male_guardian else male_guardian
            elif guardian.value_en in plur_values:
                if value == 'friends':
                    live_with.append(u'%s %s'
                                     % (u'his' if child.gender == 'M'
                                        else u'her', value))
                elif (value == 'other relatives'):
                    live_with.append(value)
                elif value == 'foster parents':
                    live_with.append(u'%s %s'
                                     % (u'his' if child.gender == 'M'
                                        else u'', value))
                else:
                    live_with.append(u' %s' % value)
            else:
                if female_guardian == 'institutional worker':
                    live_with.append(u'an institution')  # find btr "institut"
                else:
                    if value == 'institutional worker':
                        live_with.append(u'an institution')
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
                    else:
                        live_with.append(u'%s %s'
                                         % (u'his' if child.gender == 'M'
                                            else u'her', value))
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
        if case_study.nb_brothers == 1:
            live_with.append(u'%s brother' % (u'his' if child.gender == 'M'
                                             else u'her'))
        elif case_study.nb_brothers > 1:
            live_with.append(u'%s %s brothers'
                             % (u'his' if child.gender == 'M'
                                else u'her', case_study.nb_brothers))
        if case_study.nb_sisters == 1:
            live_with.append(u'%s sister'
                             % (u'his' if child.gender == 'M'
                                else u'her'))
        elif case_study.nb_sisters > 1:
            live_with.append(u'%s %s sisters'
                             % (u'his' if child.gender == 'M'
                                else u'her', case_study.nb_sisters))
        if 'an institution' in live_with:
            guardian_str = '%s with %s' % (live_with[0], live_with[1])
        else:
            guardian_str = cls._gen_list_string(live_with, ', ', ' and ')
        if 'institution' in guardian_str:
            string = '%s lives in %s. ' % (child.firstname, guardian_str)
        else:
            string = '%s lives with %s. ' % (child.firstname, guardian_str)
        string += cls._get_guardians_jobs_en(cr, uid, child, case_study,
                                             male_guardian, female_guardian,
                                             context)
        return string

    @classmethod
    def _get_guardians_jobs_en(cls, cr, uid, child,
                               case_study, m_g, f_g, context=None):
        ''' Generate the guardians jobs description part. '''
        if case_study.male_guardian_ids or case_study.female_guardian_ids:
            props_m = [emp.value_en for emp in case_study.male_guardian_ids]
            job_m = [emp.value_en for emp in case_study.male_guardian_ids
                     if not emp.value_en.endswith('mployed')]
            props_f = [emp.value_en for emp in case_study.female_guardian_ids]
            job_f = [emp.value_en for emp in case_study.female_guardian_ids
                     if not emp.value_en.endswith('mployed')]
            if f_g == 'institutional worker':
                string = u""
            else:
                if ('isunemployed' in props_m) and job_f:
                    string = (
                        u" %s %s is %s %s and %s %s is unemployed."
                        % (u'his' if child.gender == 'M' else u'her',
                           f_g, u'an' if job_f[0][0] in 'aeiou' else u'a',
                           job_f[0], u'his' if child.gender == 'M'
                           else u'her', m_g))
                elif job_m and ('isunemployed' in props_f):
                    string = (
                        u"%s %s is %s %s and %s %s is unemployed."
                        % (u'his' if child.gender == 'M' else u'her',
                           m_g, u'an' if job_m[0][0] in 'aeiou' else u'a',
                           job_m[0], u'his' if child.gender == 'M'
                           else u'her', f_g))
                elif ('isunemployed' in props_m) and ('isunemployed'
                                                      in props_f):
                    if f_g == "mother" and m_g == "father":
                        string = (u"%s parents are unemployed."
                                  % (u'His' if child.gender == 'M'
                                     else u'Her'))
                    else:
                        string = (u"%s %s and %s %s are unemployed."
                                  % (u'His' if child.gender == 'M'
                                     else u'Her', m_g, u'his'
                                     if child.gender == 'M'
                                     else u'her', f_g))
                elif job_m and job_f:
                    if ((job_f == job_m)
                            and (f_g == u'mother' and m_g == u'father')):
                        string = (
                            u"%s %s and %s %s are %ss."
                            % (u'His' if child.gender == 'M'
                               else u'Her', f_g, u'his'
                               if child.gender == 'M'
                               else u'her', m_g, job_m[0]))
                    else:
                        string = (
                            u"%s %s is %s %s and %s %s is %s %s."
                            % (u'His' if child.gender == 'M' else u'Her', f_g,
                               u'an' if job_f[0][0] in 'aeiou' else u'a',
                               job_f[0], u'his' if child.gender == 'M'
                               else u'her', m_g,
                               u'an' if job_m[0][0] in 'aeiou' else u'a',
                               job_m[0]))
        return string
