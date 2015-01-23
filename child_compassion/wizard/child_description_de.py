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
    def _gen_list_string(cls, list):
        string = ', '.join(list[:-1])
        if len(list) > 1:
            string += ' und '
        string += list[-1]
        return string

    @classmethod
    def _gen_christ_act_de(cls, cr, uid, child, case_study, context=None):
        ''' Generate the christian activities description part.
        '''
        if not case_study.christian_activities_ids:
            return ''
        activities = [
            activity.value_de if activity.value_de else activity.value_en
            for activity in case_study.christian_activities_ids]
        activities_str = cls._gen_list_string(activities)
        string = (u"In der Kirche macht %s %s %s" % (
                  'er' if child.gender == 'M'
                  else 'sie', activities_str, 'mit. '
                  if activities_str > 1 else '. '))
        return string

    @classmethod
    def _gen_family_act_info_de(
            cls, cr, uid, child, case_study, context=None):
        ''' Generate the family duties description part.
            In German, it always starts with "Zu Hause hilft sie/er beim"
            It's followed by the family duties.
        '''
        if not case_study.family_duties_ids:
            return ''
        activities = ([activity.value_de if activity.value_de
                       else activity.value_en
                       for activity in case_study.family_duties_ids])
        activities_str = cls._gen_list_string(activities)
        string = (u"Zu Hause hilft %s beim %s. " % ('er' if child.gender == 'M'
                  else 'sie', activities_str))
        return string

    @classmethod
    def _gen_hobbies_info_de(cls, cr, uid, child, case_study, context=None):
        ''' Generate the hobbies description part.
            There are 3 groups of hobbies:
            - hobbies starting with "Sie/Er spielt gerne" (sesg)
            - hobbies starting with "Sie/Er" (se)
            - hobbies starting with "Sie/Er" and finishing with "gerne" (se_g)
        '''
        if not case_study.hobbies_ids:
            return ''
        hobbies_sesg = [
            'baseball', 'basketball', 'cars', 'group games',
            'hide and seek', 'jacks', 'other ball games', 'ping pong',
            'play house', 'soccer/football', 'volleyball',
            'dolls', 'marbles', 'rolling a hoop',
            ]
        hobbies_se = [
            'jump rope', 'listening to music', 'bicycling', 'story telling',
            ]
        hobbies_se_g = [
            'art/drawing', 'musical instrument', 'reading', 'running',
            'other sports or hobbies', 'singing', 'swimming', 'walking',
            ]
        activities_sesg = [activity.value_de if activity.value_de
                           else activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in hobbies_sesg]
        activities_se = [activity.value_de if activity.value_de
                         else activity.value_en
                         for activity in case_study.hobbies_ids
                         if activity.value_en in hobbies_se]
        activities_se_g = [activity.value_de if activity.value_de
                           else activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in hobbies_se_g]
        string = ''
        gender_pronoun = 'Er' if child.gender == 'M' else 'Sie'
        if activities_sesg:
            string_sesg = u"%s spielt gerne " % gender_pronoun
            activities_sesg_string = cls._gen_list_string(activities_sesg)
            string += string_sesg + activities_sesg_string + (u'. ')
        if activities_se:
            string_se = u"%s " % gender_pronoun
            activities_se_string = cls._gen_list_string(activities_se)
            string += string_se + activities_se_string + (u'. ')
        if activities_se_g:
            string_se_g = u"%s " % gender_pronoun
            activities_se_g_string = cls._gen_list_string(activities_se_g)
            string += string_se_g + activities_se_g_string + (u'. ')
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
            '1': u'ersten',
            '2': u'zweiten',
            '3': u'dreiten',
            '4': u'vierten',
            '5': u'fünften',
            '6': u'sechsten',
            '7': u'siebsten',
            '8': u'achten',
            '9': u'neunten',
            '10': u'zehnten',
            '11': u'elften',
            '12': u'zwölften',
            '13': u'dreizehnten',
            '14': u'vierzehnten',
            'PK': u'Spielgruppe',
            'K': u'Kindergarten',
            'P': u'Primarschule',
            }
        # the value of us_school_level can also be blank
        string = u'Er' if child.gender == 'M' else u'Sie'
        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    string += (u' ist in der %s Klasse (US)'
                               % ordinals[case_study.us_school_level])
                except:
                    string += (u' ist in der %s (US)'
                               % ordinals[case_study.us_school_level])
            else:
                string += u' geht zur Schule'
            if case_study.school_performance:
                string += (u' und %s hat %s Ergebnisse. ' % (child.firstname,
                           case_study.school_performance[0].value_de
                           if case_study.school_performance[0].value_de
                           else case_study.school_performance[0].value_en))
            elif case_study.school_best_subject:
                string += u' und mag: %s. ' \
                          % (case_study.school_best_subject[0].value_de
                             if case_study.school_best_subject[0].value_de
                             else case_study.school_best_subject[0].value_en)
            else:
                string += '.'
        else:
            string += ' geht nicht in die Schule.'
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
                child_to_guardian_pronoun = (u'seinem' if child.gender == 'M'
                                             else u'ihrem')
                live_with.append(u'%s %s' % (child_to_guardian_pronoun, value))
                male_guardian = value if not male_guardian else male_guardian
            elif guardian.value_en in plur_values:
                if value == 'friends' or value == 'Freunden':
                    live_with.append(u'%s %s'
                                     % (u'seinen' if child.gender == 'M'
                                        else u'ihren', value))
                elif (value == 'other relatives'
                      or value == 'anderen Verwandten'):
                    live_with.append(u'anderen  %s' % value)
                elif value == 'foster parents' or value == 'Pflegeeltern':
                    live_with.append(u'%s %s'
                                     % (u'seinen' if child.gender == 'M'
                                        else u'ihren', value))
                else:
                    live_with.append(u' %s' % value)
            else:
                if female_guardian == 'institutional worker':
                    live_with.append(u'einem Heim')  # find btr "institut"
                else:
                    if value == 'institutional worker':
                        live_with.append(u'einem Heim')
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
                    else:
                        live_with.append(u'%s %s'
                                         % (u'seiner' if child.gender == 'M'
                                            else u'ihrer', value))
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
        if case_study.nb_brothers == 1:
            live_with.append(u'%s Bruder' % (u'seinem' if child.gender == 'M'
                                             else u'ihrem'))
        elif case_study.nb_brothers > 1:
            live_with.append(u'%s %s Brüdern'
                             % (u'seinen' if child.gender == 'M'
                                else u'ihren', case_study.nb_brothers))
        if case_study.nb_sisters == 1:
            live_with.append(u'%s Schwester'
                             % (u'seiner' if child.gender == 'M'
                                else u'ihrer'))
        elif case_study.nb_sisters > 1:
            live_with.append(u'%s %s Schwestern'
                             % (u'seinen' if child.gender == 'M'
                                else u'ihren', case_study.nb_sisters))
        if 'einem Heim' in live_with:
            guardian_str = '%s mit %s' % (live_with[0], live_with[1])
        else:
            guardian_str = cls._gen_list_string(live_with)
        if 'Heim' in guardian_str:
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
            string = u""
            if f_g != 'institutional worker':
                if ('isunemployed' in props_m) and job_f:
                    string = (
                        u" %s %s arbeitet als %s und %s %s arbeitslos ist."
                        % (u'seiner' if child.gender == 'M' else u'ihr',
                           f_g, job_f[0], u'seine' if child.gender == 'M'
                           else u'ihre', m_g))
                elif job_m and ('isunemployed' in props_f):
                    string = (
                        u"%s %s arbeitet als %s und %s %s arbeitslos ist."
                        % (u'seiner' if child.gender == 'M'
                           else u'ihr', m_g, job_m[0], u'seine'
                           if child.gender == 'M' else u'ihre', f_g))
                elif ('isunemployed' in props_m) and ('isunemployed'
                                                      in props_f):
                    if f_g == "mother" and m_g == "father":
                        string = (u"%s Eltern arbeitslos sind."
                                  % (u'Seinen' if child.gender == 'M'
                                     else u'Ihren'))
                    else:
                        string = (u"%s %s und %s %s arbeitslos sind."
                                  % (u'Sein' if child.gender == 'M'
                                     else u'Ihr', m_g, u'seine'
                                     if child.gender == 'M'
                                     else u'ihre', f_g))
                elif job_m and job_f:
                    if ((job_f[0][0:7] == job_m[0][0:7])
                            and (f_g == u'Mutter' and m_g == u'Vater')):
                        string = (
                            u"%s %s und %s %s arbeitet als %s."
                            % (u'Seine' if child.gender == 'M'
                               else u'Ihre', f_g, u'sein'
                               if child.gender == 'M'
                               else u'ihr', m_g, job_m[0]))
                    else:
                        string = (
                            u"%s %s arbeitet als %s und %s %s arbeitet als %s."
                            % (u'Seine' if child.gender == 'M'
                               else u'Ihre', f_g, job_f[0], u'sein'
                               if child.gender == 'M'
                               else u'ihr', m_g, job_m[0]))
        return string
