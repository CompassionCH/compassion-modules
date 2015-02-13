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
        desc_en += cls._get_parents_info(
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
    def _gen_list_string(cls, list):
        string = ', '.join(list[:-1])
        if len(list) > 1:
            string += ' and '
        string += list[-1]
        return string

    @classmethod
    def _gen_christ_act_en(cls, cr, uid, child, case_study, context=None):
        ''' Generate the christian activities description part.
            There are 2 groups of biblical activities:
            - activities starting with "she/he goes to" (gt)
            - activities starting with "she/he is in a" (iia)
        '''
        if not case_study.christian_activities_ids:
            return ''
        hobbies_gt = [
            'sunday school/church', 'bible class', 'camp',
            'vacation bible school',
        ]
        hobbies_iia = [
            'youth group', 'choir',
        ]
        activities_gt = [
            activity.value_en
            for activity in case_study.christian_activities_ids
            if activity.value_en in hobbies_gt]
        activities_iia = [
            activity.value_en
            for activity in case_study.christian_activities_ids
            if activity.value_en in hobbies_iia]
        string = ''
        gender_pronoun = 'he' if child.gender == 'M' else 'she'
        if activities_gt:
            string_gt = u'%s goes to ' % gender_pronoun
            string = string_gt + cls._gen_list_string(activities_gt) + '. '
        if activities_iia:
            string_iia = u'%s is in a ' % gender_pronoun
            string = string_iia + cls._gen_list_string(activities_iia) + '. '
        string = u'As part of the Church, ' + string
        return string

    @classmethod
    def _gen_family_act_info_en(
            cls, cr, uid, child, case_study, context=None):
        ''' Generate the family duties description part.
            In English, it always starts with "At home, she/he helps
            with family jobs such as"
            It's followed by the family duties.
        '''
        if not case_study.family_duties_ids:
            return ''
        activities = ([activity.value_en
                       for activity in case_study.family_duties_ids])
        activities_str = cls._gen_list_string(activities)
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
            'cars', 'jacks', 'dolls', 'marbles', 'musical instrument',
        ]
        hobbies_shep = [
            'baseball', 'basketball', 'hide and seek', 'other ball games',
            'ping pong', 'soccer/football', 'volleyball',
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
                            if activity.value_en in hobbies_shepw]
        activities_shep = [activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in hobbies_shep]
        activities_shet = [activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in hobbies_shet]
        activities_she = [activity.value_en
                          for activity in case_study.hobbies_ids
                          if activity.value_en in hobbies_she]
        string = ''
        gender_pronoun = 'He' if child.gender == 'M' else 'She'
        if activities_shepw:
            string_shepw = u"%s enjoys playing with " % gender_pronoun
            string = (string_shepw + cls._gen_list_string(
                      activities_shepw) + '. ')
        if activities_shep:
            string_shep = u"%s enjoys playing " % gender_pronoun
            string = (string_shep + cls._gen_list_string(activities_shep)
                      + '. ')
        if activities_shet:
            string_shet = u"%s enjoys to " % gender_pronoun
            string = (string_shet + cls._gen_list_string(activities_shet)
                      + '. ')
        if activities_she:
            string_she = u"%s enjoys " % gender_pronoun
            string = (string_she + cls._gen_list_string(activities_she)
                      + '. ')
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
                    string += (u"'s in the %s year (US)"
                               % ordinals[case_study.us_school_level])
                except:
                    string += (u"'s in %s (US)"
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
            string += " doesn't go to school."
        return string

    @classmethod
    def _get_guardians_info_en(cls, cr, uid, child, case_study, context=None):
        ''' Generate the guardian description part. Guardians jobs are
            also included here.
        '''
        string = u''
        if not case_study.guardians_ids:
            return ''
        male_values = ['father', 'uncle', 'brother', 'grandfather',
                       'stepfather', 'godfather']
        plur_values = ['friends', 'other relatives', 'foster parents']
        if child.gender == 'M':
            prefix = [u'his', u'his', u'his']
        else:
            prefix = [u'her', u'her', u'her']

        live_with = list()
        male_guardians = list()
        female_guardians = list()
        live_in_institut = False

        for guardian in case_study.guardians_ids:
            value = guardian.value_en

            if value != 'institutional worker':
                if guardian.value_en in male_values:
                    male_guardians.append([guardian.value_en, value])
                    if guardian.value_en != 'brother':
                        live_with.append(u'{} {}'.format(prefix[0], value))
                elif guardian.value_en in plur_values:
                    male_guardians.append([guardian.value_en, value])
                    female_guardians.append([guardian.value_en, value])
                    live_with.append(u'{} {}'.format(prefix[2], value))
                else:
                    female_guardians.append([guardian.value_en, value])
                    if guardian.value_en != 'sister':
                        live_with.append(u'{} {}'.format(prefix[1], value))
            else:
                live_in_institut = True

        if case_study.nb_brothers == 1:
            live_with.append(u'{} brother'.format(prefix[0]))
        elif case_study.nb_brothers > 1:
            live_with.append(
                u'{} {} brother'.format(prefix[2], case_study.nb_brothers))
        if case_study.nb_sisters == 1:
            live_with.append(u'{} sister'.format(prefix[1]))
        elif case_study.nb_sisters > 1:
            live_with.append(
                u'{} {} sister'.format(prefix[2], case_study.nb_sisters))

        if live_in_institut:
            string = '%s lives in boarding with %s. ' % (
                child.firstname, cls._gen_list_string(live_with))
        else:
            string = '%s lives with %s. ' % (
                child.firstname, cls._gen_list_string(live_with))

        string += cls._get_guardians_jobs_en(
            cr, uid, child, case_study,
            male_guardians[0] if male_guardians else False,
            female_guardians[0] if female_guardians else False,
            context)
        return string

    @classmethod
    def _get_parents_info(cls, cr, uid, child,
                          case_study, context=None):
        string = u''

        props_m = [tag.value_en for tag in case_study.father_ids]
        props_f = [tag.value_en for tag in case_study.mother_ids]
        props_mf = set(props_m) & set(props_f)
        props = [props_m, props_f, props_mf]

        # Father info
        string += cls._get_parent_info_string(
            cr, uid, child, props, 0, context)

        # Mother info
        string += cls._get_parent_info_string(
            cr, uid, child, props, 1, context)

        # Parents info
        string += cls._get_parent_info_string(
            cr, uid, child, props, 2, context)

        return string

    @classmethod
    def _get_parent_info_string(
            cls, cr, uid, child, props, type, context=None):
        string = u''

        if (child.gender == 'M'):
            prefix = [u'His father', u'His mother', u' His parents']
        else:
            prefix = [u'Her father', u'Her mother', u' Her parents']

        be = [u'is', u'is', u'are']
        dead = [u'died', u'died', u'died']
        support = [u'support financially the family',
                   u'support financially the family',
                   u'support financially the family']

        status_tags = {
            u'inprison': [u'in prison', u'in prison', u'in prison'],
            u'mentallyill': [u'mentally ill',
                             u'mentally ill',
                             u'mentally ill'],
            u'chronicallyill': [u'chronically ill',
                                u'chronically ill',
                                u'chronically ill'],
            u'handicapped': [u'handicapped', u'handicapped', u'handicapped'],
        }

        multiple_status = False

        for prop in props[type]:
            if prop in status_tags:
                if not multiple_status:
                    string += u'{} {} {}'.format(
                        prefix[type], be[type], status_tags[prop][type])
                    multiple_status = True
                else:
                    string += u' et {}'.format(status_tags[prop])
        if (type == 2):
            if ('alive' not in props[0] and
               'alive' not in props[1]):
                string = u'{} {}'.format(prefix[type], dead[type])
            if 'supportingchild' in props[type] and \
               'livingwithchild' not in props[0] and \
               'livingwithchild' not in props[1]:
                string += u'{} {}'.format(prefix[type], support[type])
        else:
            if 'supportingchild' in props[type] and \
               'livingwithchild' not in props[type]:
                string += u'{} {}'.format(prefix[type], support[type])
            if ('alive' not in props[type] and type != 2):
                string = u'{} {}'.format(prefix[type], dead[type])

        if string:
            string += u'. '
        return string

    @classmethod
    def _get_guardians_jobs_en(cls, cr, uid, child,
                               case_study, m_g, f_g, context=None):
        if case_study.male_guardian_ids or case_study.female_guardian_ids:

            props_en_m = [emp.value_en for emp in case_study.male_guardian_ids]
            props_en_f = [
                emp.value_en for emp in case_study.female_guardian_ids]
            props_en_mf = list(set(props_en_m) & set(props_en_f))
            props_en = [props_en_m, props_en_f, props_en_mf]

            string = u""
            # Male job
            string += cls._get_guardian_job_string(
                cr, uid, child, props_en, props_en, m_g, f_g, 0, context)

            # Female job
            string += cls._get_guardian_job_string(
                cr, uid, child, props_en, props_en, m_g, f_g, 1, context)

            # Same job
            string = cls._get_guardian_job_string(
                cr, uid, child, props_en, props_en,
                m_g, f_g, 2, context) or string
        return string

    @classmethod
    def _get_mf_g(cls, cr, uid, child, m_g, f_g, context=None):
        mf_g = u''

        if child.gender == 'M':
            prefix_m = u'His'
            prefix_f = u'His'
        else:
            prefix_m = u'Her'
            prefix_f = u'Her'

        if (f_g[0] == u'grandmother' and m_g[0] == u'grandfather'):
            mf_g = u'{} grandparents'.format(prefix_f)
        elif (f_g[0] == u'mother' and m_g[0] == u'father'):
            mf_g = u'{} parents'.format(prefix_f)
        else:
            mf_g = u'{} {} and {} {}'.format(
                prefix_m, m_g[1], prefix_f, f_g[1])

        return mf_g

    @classmethod
    def _get_guardian_job_string(
            cls, cr, uid, child, props_en, props_de,
            m_g, f_g, type, context=None):
        string = u''

        if(child.gender == 'M'):
            prefix_f = u'His {}'.format(f_g[1] if f_g else u'mother')
            prefix_m = u'His {}'.format(m_g[1]if m_g else u'father')
        else:
            prefix_f = u'Her {}'.format(f_g[1] if f_g else u'mother')
            prefix_m = u'Her {}'.format(m_g[1]if m_g else u'father')

        prefix_mf = cls._get_mf_g(
            cr, uid, child, m_g, f_g, context) if f_g and m_g else None

        prefix = [prefix_m, prefix_f, prefix_mf]

        work_as = [
            u'work as', u'work as', u'work as']
        is_employed = [u'is employed', u'is employed', u'is employed']
        is_unemployed = [
            u"is unemployed", u"is unemployed", u"is unemployed"]

        job_tags_work_as = {
            'isafarmer': [u'Farmer', u'Farmer', u'Farmers'],
            'isateacher': [u'Teacher', u'Teacher', u'Teachers'],
            'sellsinmarket': [u'market vendor',
                              u'market vendor',
                              u'market vendors'],
        }
        job_tags_isemployed = {
            'isachurchworker': u'at church',
            'isaprojectworker': u'at the reception center',
        }
        # laborer_tag = {
        # 'isalaborer': [u'est ouvrier', u'est ouvrière', u'sont ouvriers']
        # }
        unconsidered_tag = [u'isattimesemployed', u'isemployed']

        # Case unemployed
        if ('isunemployed' in props_en[type]):
            string += u'{} {}'.format(prefix[type], is_unemployed[type])
        else:
            multiple_job_work_as = False
            for job_tag_work_as in job_tags_work_as:
                if job_tag_work_as in props_en[type]:
                    # Multiple job check
                    if not multiple_job_work_as:
                        string += u'{} {} {}'.format(
                            prefix[type], work_as[type],
                            job_tags_work_as[job_tag_work_as][type])
                        multiple_job_work_as = True
                    else:
                        string += u' and {}'.format(
                            job_tags_work_as[job_tag_work_as][type])

            multiple_job_isemployed = False
            for job_tag_isemployed in job_tags_isemployed:
                if job_tag_isemployed in props_en[type]:
                    # Multiple job check
                    if (not multiple_job_isemployed and not
                            multiple_job_work_as):
                        string += u'{} {} {}'.format(
                            prefix[type], is_employed[type],
                            job_tags_isemployed[job_tag_isemployed])
                        multiple_job_isemployed = True
                    else:
                        string += u' and {}'.format(
                            job_tags_isemployed[job_tag_isemployed])

            multiple_job = False
            for prop in props_en[type]:
                if (prop not in unconsidered_tag and
                        prop not in job_tags_work_as and
                        prop not in job_tags_isemployed):
                    # Multiple job check
                    if (not multiple_job_work_as and not
                            multiple_job_isemployed and not
                            multiple_job):
                        string += prefix[type]
                        multiple_job = True
                    else:
                        string += u' and'

                    string += u' {}'.format(
                        props_de[type][props_en[type].index(prop)] or prop)

        if string:
            string += u'. '

        return string
