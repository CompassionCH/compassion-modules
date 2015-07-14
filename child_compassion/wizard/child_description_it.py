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


class Child_description_it:

    @classmethod
    def gen_it_translation(
            cls, child, case_study):
        desc_it = cls._get_guardians_info_it(child, case_study)
        desc_it += u'\r\n\r\n'
        desc_it += cls._get_school_info_it(child, case_study)
        desc_it += u'\r\n\r\n'
        desc_it += cls._gen_christ_act_it(child, case_study)
        desc_it += cls._gen_family_act_info_it(child, case_study)
        desc_it += cls._gen_hobbies_info_it(child, case_study)
        return desc_it

    @classmethod
    def _number_to_string(cls, number):
        conversion_dict = {
            1: u'uno',
            2: u'due',
            3: u'tre',
            4: u'quattro',
            5: u'cinque',
            6: u'sei',
            7: u'sette',
            8: u'otto',
            9: u'nove'
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
                res += ' e '
            res += word_list[-1]
        return res

    @classmethod
    def _gen_christ_act_it(cls, child, case_study):
        ''' Generate the christian activities description part.
            There are 2 groups of biblical activities:
            - activities starting with "lei/egli va" (v)
            - activities starting with "lei/egli è in" (ei)
            Words as 'un', 'una', 'a', 'al'... are included
            in value_it field.
        '''
        if not case_study.christian_activities_ids:
            return ''
        activities = [
            activity.get_translated_value('it')
            for activity in case_study.christian_activities_ids]
        activities_str = cls._gen_list_string(activities)
        res = u"In chiesa, frequenta %s. " % (activities_str)
        return res

    @classmethod
    def _gen_family_act_info_it(cls, child, case_study):
        ''' Generate the family duties description part.
        '''
        if not case_study.family_duties_ids:
            return ''
        activities = ([activity.get_translated_value('it')
                       for activity in case_study.family_duties_ids])
        activities_str = cls._gen_list_string(activities)
        res = ((u"A casa, aiuta: %s. ") % (
            activities_str))
        return res

    @classmethod
    def _gen_hobbies_info_it(cls, child, case_study):
        ''' Generates the hobbies description part.
        '''
        if not case_study.hobbies_ids:
            return ''
        activities = [activity.get_translated_value('it')
                      for activity in case_study.hobbies_ids]
        res = ''
        if activities:
            pronoun = u'A lui' if child.gender == 'M' else u'A lei'
            if len(activities) > 1:
                res = (u'%s piace: ' +
                       cls._gen_list_string(activities) + '. ') % pronoun
            else:
                res = u'%s piace: %s.' % (pronoun, activities[0])
        return res

    @classmethod
    def _get_school_info_it(cls, child, case_study):
        ''' Generate the school description part. Description includes :
             - If child is attending school
             - Reason why not attending school if relevant and existing
             - US school level if relevant
             - School performance if relevant and existing
             - School favourite subject if relevant and existing
        '''
        ordinals = {
            '1': u'il terzo anno di scuola',
            '2': u'il quarto anno di scuola',
            '3': u'il quinto anno di scuola',
            '4': u'il sesto anno di scuola',
            '5': u'il settimo anno di scuola',
            '6': u"l'ottavo anno di scuola",
            '7': u'il nono anno di scuola',
            '8': u'il decimo anno di scuola',
            '9': u"l'undicesimo anno di scuola'",
            '10': u'il primo anno di scuola superiore',
            '11': u'il secondo anno di scuola superiore',
            '12': u'il terzo anno di scuola superiore',
            '13': u'il liceo',
            '14': u'il liceo',
            'PK': u'la scuola materna',
            'K': u'il secondo anno di scuola',
            'P': u'il primo anno di scuola',
        }
        # the value of us_school_level can also be blank
        res = child.firstname
        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                res += (u" frequenta %s" % (
                    ordinals[case_study.us_school_level]))
            else:
                res += u' frequenta la scuola'
            if case_study.school_performance:
                res += (u' ed ha voti %s. ' % (
                    case_study.school_performance[0].get_translated_value(
                        'it')))
            else:
                res += '.'

            if case_study.school_best_subject:
                res += u'%s piace: %s. ' % (
                    u'A lui' if child.gender == 'M' else u'A lei',
                    case_study.school_best_subject[0].get_translated_value(
                        'it'))
            else:
                res += '.'
        else:
            child_age = (
                date.today() - datetime.strptime(
                    child.birthdate, DF).date()).days / 365
            if child_age <= 5:
                res += " non frequenta la scuola."
            else:
                res += " non frequenta la scuola."
        return res

    @classmethod
    def _get_guardians_info_it(cls, child, case_study):
        ''' Generate the guardian description part. Guardians jobs are
            also included here.
        '''
        res = u''
        if not case_study.guardians_ids:
            return ''
        male_values = ['father', 'uncle', 'brother', 'grandfather',
                       'stepfather', 'godfather']
        plur_values = ['friends', 'other relatives', 'foster parents']

        prefix = [u'suo', u'sua', u'i suoi']

        live_with = OrderedDict()
        male_guardians = OrderedDict()
        female_guardians = OrderedDict()
        live_in_institut = False

        # Separate male_guardian female_guardians and add guardians to
        # live_with
        for guardian in case_study.guardians_ids:
            value = guardian.get_translated_value('it')

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
        live_with = cls._regroup_parents(live_with, prefix)

        # Get number of brothers and sisters
        if case_study.nb_brothers == 1:
            live_with['brothers'] = u'{0} fratello'.format(prefix[0])
        elif case_study.nb_brothers > 1:
            live_with['brothers'] = u'{0} {1} fratelli'.format(
                prefix[2], cls._number_to_string(case_study.nb_brothers))
        if case_study.nb_sisters == 1:
            live_with['sisters'] = u'{0} sorella'.format(prefix[1])
        elif case_study.nb_sisters > 1:
            live_with['sisters'] = u'{0} {1} sorelle'.format(
                u'sue', cls._number_to_string(case_study.nb_sisters))

        # Live in institute or not
        if live_in_institut:
            res = '%s vive in un collegio con %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))
        else:
            res = '%s vive con %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))

        res += cls._get_parents_info(
            child, case_study)
        # Generate guardians job
        res += cls._get_guardians_jobs_it(
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
            live_with[u'parents'] = u'{0} genitori'.format(prefix[2])
        if (u'grandmother' in live_with and
                u'grandfather' in live_with):
            live_with.pop(u'grandmother')
            live_with.pop(u'grandfather')
            live_with[u'grandparents'] = u'{0} nonni'.format(prefix[2])
        return live_with

    @classmethod
    def _get_parents_info(cls, child, case_study):
        # Comments for this function in child_description_fr
        res = u''

        props_m = [tag.value_en for tag in case_study.father_ids]
        props_f = [tag.value_en for tag in case_study.mother_ids]
        props_mf = set(props_m) & set(props_f)
        props = [props_m, props_f, props_mf]

        # Father info
        res += cls._get_parent_info_string(child, props, 0)

        # Mother info
        res += cls._get_parent_info_string(child, props, 1)

        # Parents info
        res = cls._get_parent_info_string(child, props, 2) or res

        return res

    @classmethod
    def _get_parent_info_string(cls, child, props, parent):
        # Comments for this function in child_description_fr
        res = u''

        prefix = [u'Suo padre', u'Sua madre', u'Suoi genitori']

        be = [u'è', u'è', u'sono']
        dead = [u'é deceduto', u'é deceduto', u'sono deceduto']
        support = [u'sostiene finanziariamente la famiglia',
                   u'sostiene finanziariamente la famiglia',
                   u'sostiene finanziariamente la famiglia']

        status_tags = {
            u'inprison': [u'in prigione', u'in prigione', u'in prigione'],
            u'mentallyill': [u'mentalmente malato',
                             u'mentalmente malato',
                             u'mentalmente malato'],
            u'chronicallyill': [u'malato permanente',
                                u'malato permanente',
                                u'malato permanente'],
            u'handicapped': [u'disabile', u'disabile', u'disabilitati'],
        }

        multiple_status = False

        for prop in props[parent]:
            if prop in status_tags:
                if not multiple_status:
                    res += u'{0} {1} {2}'.format(
                        prefix[parent], be[parent], status_tags[prop][parent])
                    multiple_status = True
                else:
                    res += u' e {0}'.format(status_tags[prop])
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
    def _get_guardians_jobs_it(cls, child, case_study, m_g, f_g):
        res = u""

        # Comments for this function in child_description_fr
        if case_study.male_guardian_ids or case_study.female_guardian_ids:

            props_en_m = [emp.value_en for emp in case_study.male_guardian_ids]
            props_en_f = [
                emp.value_en for emp in case_study.female_guardian_ids]
            props_en_mf = list(set(props_en_m) & set(props_en_f))
            props_en = [props_en_m, props_en_f, props_en_mf]

            props_it_m = [emp.value_it for emp in case_study.male_guardian_ids]
            props_it_f = [
                emp.value_it for emp in case_study.female_guardian_ids]
            props_it_mf = list(set(props_it_m) & set(props_it_f))
            props_it_mf = props_it_mf + \
                [False] * (len(props_en_mf) - len(props_it_mf))
            props_it = [props_it_m, props_it_f, props_it_mf]

            # Male job
            res += cls._get_guardian_job_string(
                child, props_en, props_it, m_g, f_g, 0)

            # Female job
            res += cls._get_guardian_job_string(
                child, props_en, props_it, m_g, f_g, 1)

            # Same job
            res = cls._get_guardian_job_string(
                child, props_en, props_it,
                m_g, f_g, 2) or res
        return res

    @classmethod
    def _get_mf_g(cls, child, m_g, f_g):
        # Comments for this function in child_description_fr
        mf_g = u''

        prefix_m = u'Suo'
        prefix_f = u'Sua'
        prefix_p = u'I suoi'

        if (f_g[0] == u'grandmother' and m_g[0] == u'grandfather'):
            mf_g = u'{0} nonni'.format(prefix_f)
        elif (f_g[0] == u'mother' and m_g[0] == u'father'):
            mf_g = u'{0} genitori'.format(prefix_p)
        else:
            mf_g = u'{0} {1} e {2} {3}'.format(prefix_m, m_g[1], prefix_f,
                                               f_g[1])

        return mf_g

    @classmethod
    def _get_guardian_job_string(
            cls, child, props_en, props_it, m_g, f_g, parent):
        # Comments for this function in child_description_fr
        res = u''

        prefix_f = u'Sua {0}'.format(f_g[1] if f_g else u'madre')
        prefix_m = u'Suo {0}'.format(m_g[1]if m_g else u'padre')

        prefix_mf = cls._get_mf_g(
            child, m_g, f_g) if f_g and m_g else None

        prefix = [prefix_m, prefix_f, prefix_mf]
        prefix = [prefix_m, prefix_f, prefix_mf]

        work_as = [
            u'lavora come', u'lavora come', u'lavorano come']
        is_employed = [u'lavora', u'lavora', u'lavorano']
        is_unemployed = [
            u"è disoccupato", u"è disoccupata", u"sono disoccupati"]

        job_tags_work_as = {
            'isafarmer': [u'agricoltore', u'agricoltore', u'agricoltori'],
            'isateacher': [u'insegante', u'insegante', u'insegnanti'],
            'sellsinmarket': [u' venditore al mercato',
                              u' venditrice al mercato',
                              u'venditori al mercato'],
        }
        job_tags_isemployed = {
            'isachurchworker': u'in chiesa',
            'isaprojectworker': u'al centro progetto',
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
                        res += u' e {0}'.format(
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
                        res += u' e {0}'.format(
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
                        res += u' und'

                    prop_it = props_it[parent][props_en[parent].index(prop)]
                    color = 'red' if not prop_it else 'blue'
                    translated_prop = prop_it or prop

                    res += (u' <span id="{0}" style="color:{1}">{2}'
                            '</span>').format(prop, color, translated_prop)

        if res:
            res += u'. '

        return res
