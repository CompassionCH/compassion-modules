# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester , Kevin Cristi, David Coninckx
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from collections import OrderedDict
from datetime import datetime, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class Child_description_fr:

    @classmethod
    def gen_fr_translation(
            cls, child, case_study):
        desc_fr = cls._get_guardians_info_fr(child, case_study)
        desc_fr += u'\r\n\r\n'
        desc_fr += cls._get_school_info_fr(child, case_study)
        desc_fr += u'\r\n\r\n'
        desc_fr += cls._gen_christ_act_fr(child, case_study)
        desc_fr += cls._gen_family_act_info_fr(child, case_study)
        desc_fr += cls._gen_hobbies_info_fr(child, case_study)
        return desc_fr

    @classmethod
    def _number_to_string(cls, number):
        conversion_dict = {
            1: u'un',
            2: u'deux',
            3: u'trois',
            4: u'quatre',
            5: u'cinq',
            6: u'six',
            7: u'sept',
            8: u'huit',
            9: u'neuf'
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
                res += ' et '
            res += word_list[-1]
        return res

    @classmethod
    def _gen_christ_act_fr(cls, child, case_study):
        ''' Generate the christian activities description part.
            Words as 'à', 'aux', ... are included in value_fr field.
        '''
        if not case_study.christian_activities_ids:
            return ''
        activities = [
            activity.get_translated_value('fr')
            for activity in case_study.christian_activities_ids]
        activities_str = cls._gen_list_string(activities)
        res = u"A l'Église, %s participe %s. " % (
            'il' if child.gender == 'M' else 'elle', activities_str)
        return res

    @classmethod
    def _gen_family_act_info_fr(
            cls, child, case_study):
        ''' Generate the family duties description part. There are 2 kind of
            activities:
             - Standards : introduced by 'aide à faire' and having
                the determinant in value_fr
             - Specials : having the action verb included in value_fr
        '''
        if not case_study.family_duties_ids:
            return ''

        activities = [activity.get_translated_value('fr')
                      for activity in case_study.family_duties_ids]

        res = u"A la maison, %s aide %s. " % (
            'il' if child.gender == 'M' else 'elle',
            cls._gen_list_string(activities))
        return res

    @classmethod
    def _gen_hobbies_info_fr(cls, child, case_study):
        ''' Generate the hobbies description part.
             There are 2 kind of hobbies :
             - games, which are introduced by 'jouer' and having
                the determinant included in value_fr
             - verbs, which are simply printed without any decoration.
        '''
        if not case_study.hobbies_ids:
            return ''

        activities = [activity.get_translated_value('fr')
                      for activity in case_study.hobbies_ids]

        res = u"%s aime %s. " % (
            'Il' if child.gender == 'M'
            else 'Elle', cls._gen_list_string(activities))
        return res

    @classmethod
    def _get_school_info_fr(cls, child, case_study):
        ''' Generate the school description part. Description includes :
             - If child is attending school
             - Reason why not attending school if relevant and existing
             - US school level if relevant
             - School performance if relevant and existing
             - School favourite subject if relevant and existing
        '''
        ordinals = {
            '1': u'en troisième année',
            '2': u'en quatrième année',
            '3': u'en cinquième année',
            '4': u'en sixième année',
            '5': u'en septième année',
            '6': u'en huitième année',
            '7': u'en neuvième année',
            '8': u'en dixième année',
            '9': u'en onzième année',
            '10': u'en première année de lycée',
            '11': u'en deuxième année de lycée',
            '12': u'en troisième année de lycée',
            '13': u'au lycée',
            '14': u'au lycée',
            'PK': u'à la crèche',
            'K': u'en deuxième année',
            'P': u'en première année',
        }
        # the value of us_school_level can also be blank
        res = child.firstname

        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    res += (u' est %s'
                            % ordinals[case_study.us_school_level])
                except:
                    res += (u' est %s'
                            % ordinals[case_study.us_school_level])
            else:
                res += u" va à l'école"
            if case_study.school_performance:
                res += u' et %s a des résultats %s. ' % (
                    u'il' if child.gender == 'M' else u'elle',
                    case_study.school_performance[0].get_translated_value(
                        'fr'))
            if case_study.school_best_subject:
                res += u'%s aime bien %s. ' % (
                    u'Il' if child.gender == 'M' else u'Elle',
                    case_study.school_best_subject[0].get_translated_value(
                        'fr'))
            else:
                res += '.'
        else:
            child_age = (
                date.today() - datetime.strptime(
                    child.birthdate, DF).date()).days / 365
            if child_age <= 5:
                res += u" ne va pas encore à l'école."
            else:
                res += u" ne va pas à l'école."
        return res

    @classmethod
    def _get_guardians_info_fr(cls, child, case_study):
        ''' Generate the guardian description part. Guardians jobs are
            also included here.
        '''
        res = u''
        if not case_study.guardians_ids:
            return ''
        male_values = ['father', 'uncle', 'brother', 'grandfather',
                       'stepfather', 'godfather']
        plur_values = ['friends', 'other relatives', 'foster parents']
        prefix = [u'son', u'sa', u'ses']
        live_with = OrderedDict()
        male_guardians = OrderedDict()
        female_guardians = OrderedDict()
        live_in_institut = False

        # Separate male_guardian female_guardians and add guardians to
        # live_with
        for guardian in case_study.guardians_ids:
            value = guardian.get_translated_value('fr')

            if guardian.value_en != 'institutional worker':
                # Male guardian
                if guardian.value_en in male_values:
                    male_guardians[guardian.value_en] = value
                    # Except brother. Managed later
                    if guardian.value_en != 'brother':
                        live_with[guardian.value_en] = u'{0} {1}'.format(
                            prefix[0], value)
                # Plural guardian
                elif guardian.value_en in plur_values:
                    # Included in male_guardian and female_guardians
                    male_guardians[guardian.value_en] = value
                    female_guardians[guardian.value_en] = value
                    live_with[guardian.value_en] = u'{0} {1}'.format(
                        prefix[2], value)
                # Female guardian
                else:
                    female_guardians[guardian.value_en] = value
                    # Except sister. Managed later
                    if guardian.value_en != 'sister':
                        live_with[guardian.value_en] = u'{0} {1}'.format(
                            prefix[1], value)
            else:
                live_in_institut = True

        # Regroup parents and grandparents
        live_with = cls._regroup_parents(live_with)

        # Get number of brothers and sisters
        if case_study.nb_brothers == 1:
            live_with['brothers'] = u'{0} frère'.format(prefix[0])
        elif case_study.nb_brothers > 1:
            live_with['brothers'] = u'{0} {1} frères'.format(
                prefix[2], cls._number_to_string(case_study.nb_brothers))
        if case_study.nb_sisters == 1:
            live_with['sisters'] = u'{0} soeur'.format(prefix[1])
        elif case_study.nb_sisters > 1:
            live_with['sisters'] = u'{0} {1} soeurs'.format(
                prefix[2], cls._number_to_string(case_study.nb_sisters))

        # Live in institute or not
        if live_in_institut:
            res = '%s vit dans un internat avec %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))
        else:
            res = '%s vit avec %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))

        res += cls._get_parents_info(
            child, case_study)
        # Generate guardians job

        res += cls._get_guardians_jobs_fr(
            child, case_study,
            male_guardians.items()[0] if male_guardians else False,
            female_guardians.items()[0] if female_guardians else False)
        return res

    @classmethod
    def _regroup_parents(cls, live_with):
        if (u'mother' in live_with and
                u'father' in live_with):
            live_with.pop(u'mother')
            live_with.pop(u'father')
            live_with[u'parents'] = u'ses parents'
        if (u'grandmother' in live_with and
                u'grandfather' in live_with):
            live_with.pop(u'grandmother')
            live_with.pop(u'grandfather')
            live_with[u'grandparents'] = u'ses grand-parents'
        return live_with

    @classmethod
    def _get_parents_info(cls, child,
                          case_study):
        res = u''

        # Get tags for female/male and same tags
        props_m = [tag.value_en for tag in case_study.father_ids]
        props_f = [tag.value_en for tag in case_study.mother_ids]
        props_mf = set(props_m) & set(props_f)
        props = [props_m, props_f, props_mf]

        # Father info
        res += cls._get_parent_info_string(props, 0)

        # Mother info
        res += cls._get_parent_info_string(props, 1)

        # Parents info
        res = cls._get_parent_info_string(
            props, 2) or res

        return res

    @classmethod
    def _get_parent_info_string(cls, props, parent):
        res = u''

        # Initialize specific strings to language
        prefix = [u'Son père', u'Sa mère', u'Ses parents']
        be = [u'est', u'est', u'sont']
        dead = [u'est décédé', u'est décédée', u'sont décédés']
        support = [u'soutient financièrement la famille',
                   u'soutient financièrement la famille',
                   u'soutiennent financièrement la famille']
        status_tags = {
            u'inprison': [u'en prison', u'en prison', u'en prison'],
            u'mentallyill': [u'mentalement malade',
                             u'mentalement malade',
                             u'mentalement malades'],
            u'chronicallyill': [u'chroniquement malade',
                                u'chroniquement malade',
                                u'chroniquement malades'],
            u'handicapped': [u'handicapé', u'handicapée', u'handicapés'],
        }
        # Boolean to generate res with more than one tags
        multiple_status = False

        for prop in props[parent]:
            if prop in status_tags:
                if not multiple_status:
                    res += u'{0} {1} {2}'.format(
                        prefix[parent], be[parent], status_tags[prop][parent])
                    multiple_status = True
                else:
                    res += u' et {0}'.format(status_tags[prop])

        # Specific check on alive and supportingchild for both guardians
        if (parent == 2):
            if ('alive' not in props[0] and
                    'alive' not in props[1]):
                res = u'{0} {1}'.format(prefix[parent], dead[parent])
            if 'supportingchild' in props[parent] and \
               'livingwithchild' not in props[0] and \
               'livingwithchild' not in props[1]:
                res += u'{0} {1}'.format(prefix[parent], support[parent])
        # Check on alive and supportingchild
        else:
            if 'supportingchild' in props[parent] and \
               'livingwithchild' not in props[parent]:
                res += u'{0} {1}'.format(prefix[parent], support[parent])
            if ('alive' not in props[parent] and parent != 2):
                res = u'{0} {1}'.format(prefix[parent], dead[parent])

        # Endpoint
        if res:
            res += u'. '
        return res

    @classmethod
    def _get_guardians_jobs_fr(cls, child,
                               case_study, m_g, f_g):
        ''' Generate the guardians jobs description part. '''
        res = u""

        # Check if guardian has tags
        if case_study.male_guardian_ids or case_study.female_guardian_ids:

            # Establish tags in both language for male, female and both of them
            props_en_m = [emp.value_en for emp in case_study.male_guardian_ids]
            props_en_f = [
                emp.value_en for emp in case_study.female_guardian_ids]
            props_en_mf = list(set(props_en_m) & set(props_en_f))
            props_en = [props_en_m, props_en_f, props_en_mf]

            props_fr_m = [emp.value_fr for emp in case_study.male_guardian_ids]
            props_fr_f = [
                emp.value_fr for emp in case_study.female_guardian_ids]
            props_fr_mf = list(set(props_fr_m) & set(props_fr_f))
            props_fr_mf = props_fr_mf + \
                [False] * (len(props_en_mf) - len(props_fr_mf))
            props_fr = [props_fr_m, props_fr_f, props_fr_mf]

            # Male job
            res += cls._get_guardian_job_string(
                props_en, props_fr, m_g, f_g, 0)

            # Female job
            res += cls._get_guardian_job_string(
                props_en, props_fr, m_g, f_g, 1)

            # Same job
            res = cls._get_guardian_job_string(
                props_en, props_fr, m_g, f_g, 2) or res

        return res

    @classmethod
    def _get_mf_g(cls, m_g, f_g):
        # Generate prefix to define both guardians
        mf_g = u''

        # Case grandmother and grandfather
        if (f_g[0] == u'grandmother' and m_g[0] == u'grandfather'):
            mf_g = u'Ses grand-parents'
        # Case mother and father
        elif (f_g[0] == u'mother' and m_g[0] == u'father'):
            mf_g = u'Ses parents'
        # Case friends, foster parents or other relatives
        elif(f_g[0] == m_g[0]):
            mf_g = u'Ses {0}'.format(m_g)
        else:
            mf_g = u'Son {0} et sa {1}'.format(m_g[1], f_g[1])

        return mf_g

    @classmethod
    def _get_guardian_job_string(
            cls, props_en, props_fr,
            m_g, f_g, parent):
        res = u''

        # Initialize prefix specific to language
        prefix_f = u'Sa {0}'.format(f_g[1] if f_g else u'mère')
        prefix_m = u'Son {0}'.format(m_g[1] if m_g else u'père')
        prefix_mf = cls._get_mf_g(
            m_g, f_g) if f_g and m_g else None

        prefix = [prefix_m, prefix_f, prefix_mf]

        # Initialize specific strings to language
        work_as = [
            u'travaille comme', u'travaille comme', u'travaillent comme']
        is_employed = [u'est employé', u'est employée', u'sont employés']
        is_unemployed = [
            u"n'a pas d'emploi", u"n'a pas d'emploi", u"n'ont pas d'emploi"]

        job_tags_work_as = {
            'isafarmer': [u'fermier', u'fermière', u'fermiers'],
            'isateacher': [u'enseignant', u'enseignante', u'enseignants'],
            'sellsinmarket': [u'vendeur au marché',
                              u'vendeuse au marché',
                              u'vendeurs au marché'],
        }
        job_tags_isemployed = {
            'isachurchworker': u'à l\'église',
            'isaprojectworker': u'au centre d\'accueil',
        }

        unconsidered_tag = [u'isattimesemployed', u'isemployed']

        # Case unemployed
        if ('isunemployed' in props_en[parent]):
            res += u'{0} {1}'.format(prefix[parent], is_unemployed[parent])
        else:
            multiple_job_work_as = False

            # Work as
            for job_tag_work_as in job_tags_work_as:
                if job_tag_work_as in props_en[parent]:
                    # Multiple job check
                    if not multiple_job_work_as:
                        res += u'{0} {1} {2}'.format(
                            prefix[parent], work_as[parent],
                            job_tags_work_as[job_tag_work_as][parent])
                        multiple_job_work_as = True
                    else:
                        res += u' et {0}'.format(
                            job_tags_work_as[job_tag_work_as][parent])

            multiple_job_isemployed = False

            # Is employed
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
                        res += u' et {0}'.format(
                            job_tags_isemployed[job_tag_isemployed])

            multiple_job = False

            # Other employments that requires translation
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
                        res += u' et'

                    color = 'red' if not props_fr[parent][
                        props_en[parent].index(prop)] else 'blue'
                    translated_prop = props_fr[parent][
                        props_en[parent].index(prop)] or prop

                    res += (u' <span id="{0}" style="color:{1}">{2}'
                            '</span>').format(prop, color, translated_prop)

        # Endpoint
        if res:
            res += u'. '

        return res
