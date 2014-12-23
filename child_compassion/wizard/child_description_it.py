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


class Child_description_it:

    @classmethod
    def gen_it_translation(
            cls, cr, uid, child, case_study, context=None):
        desc_it = cls._get_guardians_info_it(
            cr, uid, child, case_study, context)
        desc_it += cls._get_school_info_it(
            cr, uid, child, case_study, context)
        desc_it += cls._gen_christ_act_it(cr, uid, child, case_study, context)
        desc_it += cls._gen_family_act_info_it(
            cr, uid, child, case_study, context)
        desc_it += cls._gen_hobbies_info_it(
            cr, uid, child, case_study, context)
        return desc_it

    @classmethod
    def _gen_list_string(cls, list):
        string = ', '.join(list[:-1])
        if len(list) > 1:
            string += ' e '
        string += list[-1]
        return string

    @classmethod
    def _gen_christ_act_it(cls, cr, uid, child, case_study, context=None):
        ''' Generate the christian activities description part.
            There are 2 groups of biblical activities:
            - activities starting with "lei/egli va" (v)
            - activities starting with "lei/egli è in" (ei)
            Words as 'un', 'una', 'a', 'al'... are included
            in value_it field.
        '''
        if not case_study.christian_activities_ids:
            return ''
        hobbies_v = [
            'sunday school/church', 'bible class', 'camp',
            'vacation bible school',
        ]
        hobbies_ei = [
            'youth group', 'choir',
        ]
        activities_v = [
            activity.value_it if activity.value_it else activity.value_en
            for activity in case_study.christian_activities_ids
            if activity.value_en in hobbies_v]
        activities_ei = [
            activity.value_it if activity.value_it else activity.value_en
            for activity in case_study.christian_activities_ids
            if activity.value_en in hobbies_ei]
        string = ''
        gender_pronoun = u'egli' if child.gender == 'M' else u'lei'
        if activities_v:
            string_v = u'%s va ' % gender_pronoun
            string = string_v + cls._gen_list_string(activities_v) + '. '
        if activities_ei:
            string_ei = u'%s è in ' % gender_pronoun
            string = string_ei + cls._gen_list_string(activities_ei) + '. '
        return u'Come parte della Chiesa, ' + string

    @classmethod
    def _gen_family_act_info_it(
            cls, cr, uid, child, case_study, context=None):
        ''' Generate the family duties description part.
            In Italian, it always starts with "A casa, aiuta
            con lavori domestici come "
            It's followed by the family duties.
        '''
        if not case_study.family_duties_ids:
            return ''
        activities = ([activity.value_it if activity.value_it
                       else activity.value_en
                       for activity in case_study.family_duties_ids])
        activities_str = cls._gen_list_string(activities)
        string = ((u"A casa, aiuta con lavori domestici come %s. ") % (
            activities_str))
        return string

    @classmethod
    def _gen_hobbies_info_it(cls, cr, uid, child, case_study, context=None):
        ''' Generates the hobbies description part.
        '''
        if not case_study.hobbies_ids:
            return ''
        activities = [activity.value_it if activity.value_it
                      else activity.value_en
                      for activity in case_study.hobbies_ids]
        string = ''
        if activities:
            pronoun = u'Li' if child.gender == 'M' else u'Le'
            if len(activities) > 1:
                string = (u'%s piacciono: ' +
                          cls._gen_list_string(activities) + '. ') % pronoun
            else:
                string = u'%s piace: %s.' % (pronoun, activities[0])
        return string

    @classmethod
    def _get_school_info_it(cls, cr, uid, child, case_study, context=None):
        ''' Generate the school description part. Description includes :
             - If child is attending school
             - Reason why not attending school if relevant and existing
             - US school level if relevant
             - School performance if relevant and existing
             - School favourite subject if relevant and existing
        '''
        ordinals = {
            '1': u'primo',
            '2': u'secondo',
            '3': u'terzo',
            '4': u'quarto',
            '5': u'quinto',
            '6': u'sesto',
            '7': u'settimo',
            '8': u'ottavo',
            '9': u'nono',
            '10': u'decimo',
            '11': u'undicesimo',
            '12': u'dodicesimo',
            '13': u'tredicesimo',
            '14': u'quattordicesimo',
            'PK': u'pre-asilo',
            'K': u'asilo',
            'P': u'primario',
            }
        # the value of us_school_level can also be blank
        string = u'Lui' if child.gender == 'M' else u'Lei'
        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    string += (u" è %s anno della scuola (US)" % (
                        ordinals[case_study.us_school_level]))
                except:
                    string += (u" frequenta la scuola %s (US)"
                               % ordinals[case_study.us_school_level])
            else:
                string += u' frequenta la scuola'
            if case_study.school_performance:
                string += (u' e %s ha voti %s. ' % (child.firstname,
                           case_study.school_performance[0].value_it
                           if case_study.school_performance[0].value_it
                           else case_study.school_performance[0].value_en))
            elif case_study.school_best_subject:
                string += u' e %s piace: %s. ' \
                          % (u'li' if child.gender == 'M' else u'le',
                             case_study.school_best_subject[0].value_it
                             if case_study.school_best_subject[0].value.it
                             else case_study.school_best_subject[0].value_en)
            else:
                string += '.'
        else:
            string += " non frequenta la scuola."
        return string

    @classmethod
    def _get_guardians_info_it(cls, cr, uid, child, case_study, context=None):
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
            value = (guardian.value_it if guardian.value_it
                     else guardian.value_en)
            if guardian.value_en in male_values:
                child_to_guardian_pronoun = u'suo'
                live_with.append(u'%s %s' % (child_to_guardian_pronoun, value))
                male_guardian = value if not male_guardian else male_guardian
            elif guardian.value_en in plur_values:
                live_with.append(u'%s %s' % (u'suoi', value))
            else:
                if female_guardian == 'institutional worker':
                    live_with.append(u'un instituto')
                else:
                    if value == 'institutional worker':
                        live_with.append(u'un instituto')
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
                    else:
                        live_with.append(u'%s %s' % (u'sua', value))
                        female_guardian = (value if not female_guardian
                                           else female_guardian)
        if case_study.nb_brothers == 1:
            live_with.append(u'%s fratello' % (u'suo'))
        elif case_study.nb_brothers > 1:
            live_with.append(u'%s %s fratelli'
                             % (u'suoi', case_study.nb_brothers))
        if case_study.nb_sisters == 1:
            live_with.append(u'%s sorella' % (u'sua'))
        elif case_study.nb_sisters > 1:
            live_with.append(u'%s %s sorelle'
                             % (u'sue', case_study.nb_sisters))
        if 'un instituto' in live_with:
            guardian_str = '%s con %s' % (live_with[0], live_with[1])
        else:
            guardian_str = cls._gen_list_string(live_with)
        if 'instituto' in guardian_str:
            string = '%s vive in %s. ' % (child.firstname, guardian_str)
        else:
            string = '%s vive con %s. ' % (child.firstname, guardian_str)
        string += cls._get_guardians_jobs_it(cr, uid, child, case_study,
                                             male_guardian, female_guardian,
                                             context)
        return string

    @classmethod
    def _get_guardians_jobs_it(cls, cr, uid, child,
                               case_study, m_g, f_g, context=None):
        ''' Generate the guardians jobs description part. '''
        if case_study.male_guardian_ids or case_study.female_guardian_ids:
            props_m = [emp.value_en for emp in case_study.male_guardian_ids]
            job_m = [emp.value_it if emp.value_it else emp.value_en
                     for emp in case_study.male_guardian_ids
                     if not emp.value_en.endswith('mployed')]
            props_f = [emp.value_en for emp in case_study.female_guardian_ids]
            job_f = [emp.value_it if emp.value_it else emp.value_en
                     for emp in case_study.female_guardian_ids
                     if not emp.value_en.endswith('mployed')]
            string = u""
            if f_g == 'institutional worker':
                string = u""
            else:
                if ('isunemployed' in props_m) and job_f:
                    string = (
                        u" %s %s è %s %s e %s %s è disoccupato."
                        % (u'sua', f_g, u'una', job_f[0], u'suo', m_g))
                elif job_m and ('isunemployed' in props_f):
                    string = (
                        u"%s %s è %s %s e %s %s è disoccupato."
                        % (u'suo', m_g, u'un', job_m[0], u'sua', f_g))
                elif ('isunemployed' in props_m) and ('isunemployed'
                                                      in props_f):
                    if f_g == "mother" and m_g == "father":
                        string = (u"%s genitori sono disoccupati."
                                  % (u'Suoi'))
                    else:
                        string = (u"%s %s e %s %s sono disoccupati."
                                  % (u'Suo', m_g, u'sua', f_g))
                elif job_m and job_f:
                    if ((job_f == job_m)
                            and (f_g == u'mother' and m_g == u'father')):
                        job_plur = job_m[0]
                        if job_plur[-2] == 'c' or job_plur[-2] == 'g':
                            job_plur = job_plur[:-1] + u'hi'
                        else:
                            job_plur = job_plur[:-1] + u'i'
                        string = (
                            u"%s %s e %s %s sono %s."
                            % (u'Sua', f_g, u'suo', m_g, job_plur))
                    else:
                        string = (
                            u"%s %s è %s e %s %s è %s."
                            % (u'Sua', f_g, job_f[0], u'suo', m_g, job_m[0]))
        return string
