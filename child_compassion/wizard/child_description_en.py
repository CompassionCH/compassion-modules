# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Kevin Cristi, David Coninckx
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from collections import OrderedDict
from datetime import datetime, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class Child_description_en:

    @classmethod
    def gen_en_translation(cls, child, case_study):
        desc_en = cls._get_guardians_info_en(child, case_study)
        desc_en += u'\r\n\r\n'
        desc_en += cls._get_school_info_en(child, case_study)
        desc_en += u'\r\n\r\n'
        desc_en += cls._gen_christ_act_en(child, case_study)
        desc_en += cls._gen_family_act_info_en(child, case_study)
        desc_en += cls._gen_hobbies_info_en(child, case_study)
        return desc_en

    @classmethod
    def _number_to_string(cls, number):
        conversion_dict = {
            1: u'one',
            2: u'two',
            3: u'three',
            4: u'four',
            5: u'five',
            6: u'six',
            7: u'seven',
            8: u'height',
            9: u'nine'
        }
        if number in conversion_dict:
            return conversion_dict[number]
        else:
            return str(number)

    @classmethod
    def _gen_list_string(cls, word_list):
        res = ''
        if word_list:
            res = ', '.join(word_list[:-1])
            if len(word_list) > 1:
                res += ' and '
            res += word_list[-1]
        return res

    @classmethod
    def _gen_christ_act_en(cls, child, case_study):
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
        res = ''
        gender_pronoun = 'he' if child.gender == 'M' else 'she'
        if activities_gt:
            string_gt = u'%s goes to ' % gender_pronoun
            res = string_gt + cls._gen_list_string(activities_gt) + '. '
        if activities_iia:
            string_iia = u'%s is in a ' % gender_pronoun
            res = string_iia + cls._gen_list_string(activities_iia) + '. '
        res = u'As part of the Church, ' + res
        return res

    @classmethod
    def _gen_family_act_info_en(
            cls, child, case_study):
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
        res = u"At home, %s helps with family jobs such as %s. " % (
            'he' if child.gender == 'M'
            else 'she', activities_str)
        return res

    @classmethod
    def _gen_hobbies_info_en(cls, child, case_study):
        ''' Generates the hobbies description part.
            There are 4 groups of hobbies :
            - hobbies starting with "She/He enjoys playing with" (shepw)
            - hobbies starting with "She/He enjoys playing" (shep)
            - hobbies starting with "She/He enjoys to" (shet)
            - hobbies starting with "She/He enjoys" (she)
        '''
        if not case_study.hobbies_ids:
            return ''

        activities = [activity.value_en
                      for activity in case_study.hobbies_ids]
        gender_pronoun = 'He' if child.gender == 'M' else 'She'

        return u"{0} enjoys {1}".format(
            gender_pronoun, cls._gen_list_string(activities))

    @classmethod
    def _get_school_info_en(cls, child, case_study):
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
        res = child.firstname
        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    res += (u"'s in the %s year (US)"
                            % ordinals[case_study.us_school_level])
                except:
                    res += (u"'s in %s (US)"
                            % ordinals[case_study.us_school_level])
            else:
                res += u' goes to school'
            if case_study.school_performance:
                res += (u' and %s has %s marks. ' % (
                    u'he' if child.gender == 'M' else u'she',
                    case_study.school_performance[0].value_en))
            if case_study.school_best_subject:
                res += u'%s likes %s. ' \
                    % (u'He' if child.gender == 'M' else u'She',
                       case_study.school_best_subject[0].value_en)
            else:
                res += '.'
        else:
            child_age = (
                date.today() - datetime.strptime(
                    child.birthdate, DF).date()).days / 365
            if child_age <= 5:
                res += u" doesn't go to school for now."
            else:
                res += u" doesn't go to school."
        return res

    @classmethod
    def _get_guardians_info_en(cls, child, case_study):
        ''' Generate the guardian description part. Guardians jobs are
            also included here. (comments in child_description_fr)
        '''
        res = u''
        if not case_study.guardians_ids:
            return ''
        male_values = ['father', 'uncle', 'brother', 'grandfather',
                       'stepfather', 'godfather']
        plur_values = ['friends', 'other relatives', 'foster parents']
        if child.gender == 'M':
            prefix = [u'his', u'his', u'his']
        else:
            prefix = [u'her', u'her', u'her']

        live_with = OrderedDict()
        male_guardians = OrderedDict()
        female_guardians = OrderedDict()
        live_in_institut = False

        for guardian in case_study.guardians_ids:
            value = guardian.value_en

            if guardian.value_en != 'institutional worker':
                if guardian.value_en in male_values:
                    male_guardians[guardian.value_en] = value
                    if guardian.value_en != 'brother':
                        live_with[guardian.value_en] = u'{0} {1}'.format(
                            prefix[0], value)
                elif guardian.value_en in plur_values:
                    male_guardians[guardian.value_en] = value
                    female_guardians[guardian.value_en] = value
                    live_with[guardian.value_en] = u'{0} {1}'.format(
                        prefix[2], value)
                else:
                    female_guardians[guardian.value_en] = value
                    if guardian.value_en != 'sister':
                        live_with[guardian.value_en] = u'{0} {1}'.format(
                            prefix[1], value)
            else:
                live_in_institut = True

        # Regroup parents and grandparents
        live_with = cls._regroup_parents(live_with, prefix)

        if case_study.nb_brothers == 1:
            live_with['brothers'] = u'{0} brother'.format(
                prefix[0])
        elif case_study.nb_brothers > 1:
            live_with['brothers'] = u'{0} {1} brother'.format(
                prefix[2], cls._number_to_string(case_study.nb_brothers))
        if case_study.nb_sisters == 1:
            live_with['sisters'] = u'{0} sister'.format(
                prefix[1])
        elif case_study.nb_sisters > 1:
            live_with['sisters'] = u'{0} {1} sister'.format(
                prefix[2], cls._number_to_string(case_study.nb_sisters))

        if live_in_institut:
            res = '%s lives in boarding with %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))
        else:
            res = '%s lives with %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))

        res += cls._get_parents_info(
            child, case_study)
        res += cls._get_guardians_jobs_en(
            child, case_study,
            male_guardians.items()[0] if male_guardians else False,
            female_guardians.items()[0] if female_guardians else False)
        return res

    @classmethod
    def _regroup_parents(cls, live_with, prefix):
        if (u'mother' in live_with and
                u'father' in live_with):
            live_with.pop(u'mother')
            live_with.pop(u'father')
            live_with[u'parents'] = u'{0} parents'.format(prefix[2])
        if (u'grandmother' in live_with and
                u'grandfather' in live_with):
            live_with.pop(u'grandmother')
            live_with.pop(u'grandfather')
            live_with[u'grandparents'] = u'{0} grandparents'.format(prefix[2])
        return live_with

    @classmethod
    def _get_parents_info(cls, child,
                          case_study):
        # Comments for this function in child_description_fr
        res = u''

        props_m = [tag.value_en for tag in case_study.father_ids]
        props_f = [tag.value_en for tag in case_study.mother_ids]
        props_mf = set(props_m) & set(props_f)
        props = [props_m, props_f, props_mf]

        # Father info
        res += cls._get_parent_info_string(
            child, props, 0)

        # Mother info
        res += cls._get_parent_info_string(
            child, props, 1)

        # Parents info
        res = cls._get_parent_info_string(
            child, props, 2) or res

        return res

    @classmethod
    def _get_parent_info_string(
            cls, child, props, parent):
        # Comments for this function in child_description_fr
        res = u''

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

        for prop in props[parent]:
            if prop in status_tags:
                if not multiple_status:
                    res += u'{0} {1} {2}'.format(
                        prefix[parent], be[parent], status_tags[prop][parent])
                    multiple_status = True
                else:
                    res += u' and {0}'.format(status_tags[prop])
        if (parent == 2):
            if ('alive' not in props[0] and
                    'alive' not in props[1]):
                res = u'{0} {1}'.format(prefix[parent], dead[parent])
            if 'supportingchild' in props[parent] and \
               'livingwithchild' not in props[0] and \
               'livingwithchild' not in props[1]:
                res += u'{0} {1}'.format(prefix[parent], support[parent])
        else:
            if 'supportingchild' in props[parent] and \
               'livingwithchild' not in props[parent]:
                res += u'{0} {1}'.format(prefix[parent], support[parent])
            if ('alive' not in props[parent] and parent != 2):
                res = u'{0} {1}'.format(prefix[parent], dead[parent])

        if res:
            res += u'. '
        return res

    @classmethod
    def _get_guardians_jobs_en(cls, child,
                               case_study, m_g, f_g):
        # Comments for this function in child_description_fr
        res = u''
        if case_study.male_guardian_ids or case_study.female_guardian_ids:

            props_en_m = [emp.value_en for emp in case_study.male_guardian_ids]
            props_en_f = [
                emp.value_en for emp in case_study.female_guardian_ids]
            props_en_mf = list(set(props_en_m) & set(props_en_f))
            props_en = [props_en_m, props_en_f, props_en_mf]

            # Male job
            res += cls._get_guardian_job_string(
                child, props_en, props_en, m_g, f_g, 0)

            # Female job
            res += cls._get_guardian_job_string(
                child, props_en, props_en, m_g, f_g, 1)

            # Same job
            res = cls._get_guardian_job_string(
                child, props_en, props_en,
                m_g, f_g, 2) or res
        return res

    @classmethod
    def _get_mf_g(cls, child, m_g, f_g):
        # Comments for this function in child_description_fr
        mf_g = u''

        if child.gender == 'M':
            prefix_m = u'His'
            prefix_f = u'His'
        else:
            prefix_m = u'Her'
            prefix_f = u'Her'

        if (f_g[0] == u'grandmother' and m_g[0] == u'grandfather'):
            mf_g = u'{0} grandparents'.format(prefix_f)
        elif (f_g[0] == u'mother' and m_g[0] == u'father'):
            mf_g = u'{0} parents'.format(prefix_f)
        else:
            mf_g = u'{0} {1} and {2} {3}'.format(
                prefix_m, m_g[1], prefix_f, f_g[1])

        return mf_g

    @classmethod
    def _get_guardian_job_string(
            cls, child, props_en, props_de,
            m_g, f_g, parent):
        # Comments for this function in child_description_fr
        res = u''

        if(child.gender == 'M'):
            prefix_f = u'His {0}'.format(f_g[1] if f_g else u'mother')
            prefix_m = u'His {0}'.format(m_g[1]if m_g else u'father')
        else:
            prefix_f = u'Her {0}'.format(f_g[1] if f_g else u'mother')
            prefix_m = u'Her {0}'.format(m_g[1]if m_g else u'father')

        prefix_mf = cls._get_mf_g(
            child, m_g, f_g) if f_g and m_g else None

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

        unconsidered_tag = [u'isattimesemployed', u'isemployed']

        # Case unemployed
        if ('isunemployed' in props_en[parent]):
            res += u'{0} {1}'.format(prefix[parent], is_unemployed[parent])
        else:
            multiple_job_work_as = False
            for job_tag_work_as in job_tags_work_as:
                if job_tag_work_as in props_en[parent]:
                    # Multiple job check
                    if not multiple_job_work_as:
                        res += u'{0} {1} {2}'.format(
                            prefix[parent], work_as[parent],
                            job_tags_work_as[job_tag_work_as][parent])
                        multiple_job_work_as = True
                    else:
                        res += u' and {0}'.format(
                            job_tags_work_as[job_tag_work_as][parent])

            multiple_job_isemployed = False
            for job_tag_isemployed in job_tags_isemployed:
                if job_tag_isemployed in props_en[parent]:
                    # Multiple job check
                    if (not multiple_job_isemployed and not
                            multiple_job_work_as):
                        res += u'{0} {1} {2}'.format(
                            prefix[parent], is_employed[parent],
                            job_tags_isemployed[job_tag_isemployed])
                        multiple_job_isemployed = True
                    else:
                        res += u' and {0}'.format(
                            job_tags_isemployed[job_tag_isemployed])

            multiple_job = False
            for prop in props_en[parent]:
                if (prop not in unconsidered_tag and
                        prop not in job_tags_work_as and
                        prop not in job_tags_isemployed):
                    # Multiple job check
                    if (not multiple_job_work_as and not
                            multiple_job_isemployed and not
                            multiple_job):
                        res += prefix[parent]
                        multiple_job = True
                    else:
                        res += u' and'

                    res += u' {0}'.format(
                        props_de[parent][props_en[parent].index(prop)] or prop)

        if res:
            res += u'. '

        return res
