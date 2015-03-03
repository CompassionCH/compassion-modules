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
from collections import OrderedDict
from datetime import datetime, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class Child_description_it:

    @classmethod
    def gen_it_translation(
            cls, cr, uid, child, case_study, context=None):
        desc_it = cls._get_guardians_info_it(
            cr, uid, child, case_study, context)
        desc_it += u'\r\n\r\n'
        desc_it += cls._get_school_info_it(
            cr, uid, child, case_study, context)
        desc_it += u'\r\n\r\n'
        desc_it += cls._gen_christ_act_it(cr, uid, child, case_study, context)
        desc_it += cls._gen_family_act_info_it(
            cr, uid, child, case_study, context)
        desc_it += cls._gen_hobbies_info_it(
            cr, uid, child, case_study, context)
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
    def _gen_list_string(cls, list):
        string = ''
        if list:
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
            '1': u'in terzo',
            '2': u'in quarto',
            '3': u'in quinto',
            '4': u'in sesto',
            '5': u'in settimo',
            '6': u'in ottavo',
            '7': u'in nono',
            '8': u'in decimo',
            '9': u'in undicesimo',
            '10': u'in primo anno di scuola superiore',
            '11': u'in secondo anno di scuola superiore',
            '12': u'in terzo anno di scuola superiore',
            '13': u'al liceo',
            '14': u'al liceo',
            'PK': u'nella scuola materna',
            'K': u'in secondo',
            'P': u'in primo',
        }
        # the value of us_school_level can also be blank
        string = child.firstname
        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    string += (u" è %s" % (
                        ordinals[case_study.us_school_level]))
                except:
                    string += (u" frequenta la scuola %s (US)"
                               % ordinals[case_study.us_school_level])
            else:
                string += u' frequenta la scuola'
            if case_study.school_performance:
                string += (u' e %s ha voti %s. ' % (
                    u'Lui' if child.gender == 'M' else u'Lei',
                           case_study.school_performance[0].value_it
                           if case_study.school_performance[0].value_it
                           else case_study.school_performance[0].value_en))

            if case_study.school_best_subject:
                string += u'%s piace %s. ' \
                          % (u'Li' if child.gender == 'M' else u'Le',
                             case_study.school_best_subject[0].value_it
                             if case_study.school_best_subject[0].value_it
                             else case_study.school_best_subject[0].value_en)
            else:
                string += '.'
        else:
            child_age = (
                date.today() - datetime.strptime(
                    child.birthdate, DF).date()).days / 365
            if child_age <= 5:
                string += " non frequenta la scuola."
            else:
                string += " non frequenta la scuola."
        return string

    @classmethod
    def _get_guardians_info_it(cls, cr, uid, child, case_study, context=None):
        ''' Generate the guardian description part. Guardians jobs are
            also included here.
        '''
        string = u''
        if not case_study.guardians_ids:
            return ''
        male_values = ['father', 'uncle', 'brother', 'grandfather',
                       'stepfather', 'godfather']
        plur_values = ['friends', 'other relatives', 'foster parents']

        prefix = [u'suo', u'sua', u'i suoi']

        live_with = OrderedDict()
        male_guardians = dict()
        female_guardians = dict()
        live_in_institut = False

        # Separate male_guardian female_guardians and add guardians to
        # live_with
        for guardian in case_study.guardians_ids:
            value = guardian.value_it or guardian.value_en

            if guardian.value_en != 'institutional worker':
                # Male guardian
                if guardian.value_en in male_values:
                    male_guardians[guardian.value_en] = value
                    # Except brother. Managed later
                    if guardian.value_en != 'brother':
                        live_with[guardian.value_en] = u'{} {}'.format(
                            prefix[0], value)
                # Plural guardian
                elif guardian.value_en in plur_values:
                    # Included in male_guardian and female_guardians
                    male_guardians[guardian.value_en] = value
                    female_guardians[guardian.value_en] = value
                    live_with[guardian.value_en] = u'{} {}'.format(
                        prefix[2], value)
                # Female guardian
                else:
                    female_guardians[guardian.value_en] = value
                    # Except sister. Managed later
                    if guardian.value_en != 'sister':
                        live_with[guardian.value_en] = u'{} {}'.format(
                            prefix[1], value)
            else:
                live_in_institut = True

        # Regroup parents and grandparents
        live_with = cls._regroup_parents(cr, uid, live_with, prefix, context)

        # Get number of brothers and sisters
        if case_study.nb_brothers == 1:
            live_with['brothers'] = u'{} fratello'.format(prefix[0])
        elif case_study.nb_brothers > 1:
            live_with['brothers'] = u'{} {} confratelli'.format(
                prefix[2], cls._number_to_string(case_study.nb_brothers))
        if case_study.nb_sisters == 1:
            live_with['sisters'] = u'{} sorella'.format(prefix[1])
        elif case_study.nb_sisters > 1:
            live_with['sisters'] = u'{} {} sorelle'.format(
                u'sue', cls._number_to_string(case_study.nb_sisters))

        # Live in institute or not
        if live_in_institut:
            string = '%s vit dans un internat avec %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))
        else:
            string = '%s vive con %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))

        string += cls._get_parents_info(
            cr, uid, child, case_study, context)
        # Generate guardians job
        string += cls._get_guardians_jobs_it(
            cr, uid, child, case_study,
            male_guardians.items()[0] if male_guardians else False,
            female_guardians.items()[0] if female_guardians else False,
            context)
        return string

    @classmethod
    def _regroup_parents(cls, cr, uid, dict, prefix, context=None):
        if (u'mother' in dict and
                u'father' in dict):
            dict.pop(u'mother')
            dict.pop(u'father')
            dict[u'parents'] = u'{} genitori'.format(prefix[2])
        if (u'grandmother' in dict and
                u'grandfather' in dict):
            dict.pop(u'grandmother')
            dict.pop(u'grandfather')
            dict[u'parents'] = u'{} nonni'.format(prefix[2])
        return dict

    @classmethod
    def _get_parents_info(cls, cr, uid, child,
                          case_study, context=None):
        # Comments for this function in child_description_fr
        string = u''

        props_m = [tag.value_en for tag in case_study.father_ids]
        props_f = [tag.value_en for tag in case_study.mother_ids]
        props_mf = set(props_m) & set(props_f)
        props = [props_m, props_f, props_mf]

        # Father info
        string += cls._get_parent_info_string(cr,
                                              uid, child, props, 0, context)

        # Mother info
        string += cls._get_parent_info_string(cr,
                                              uid, child, props, 1, context)

        # Parents info
        string = cls._get_parent_info_string(
            cr, uid, child, props, 2, context) or string

        return string

    @classmethod
    def _get_parent_info_string(
            cls, cr, uid, child, props, type, context=None):
        # Comments for this function in child_description_fr
        string = u''

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
    def _get_guardians_jobs_it(cls, cr, uid, child,
                               case_study, m_g, f_g, context=None):
        string = u""

        # Comments for this function in child_description_fr
        if case_study.male_guardian_ids or case_study.female_guardian_ids:

            props_en_m = [emp.value_en for emp in case_study.male_guardian_ids]
            props_en_f = [
                emp.value_en for emp in case_study.female_guardian_ids]
            props_en_mf = list(set(props_en_m) & set(props_en_f))
            props_en = [props_en_m, props_en_f, props_en_mf]

            props_de_m = [emp.value_de for emp in case_study.male_guardian_ids]
            props_de_f = [
                emp.value_de for emp in case_study.female_guardian_ids]
            props_de_mf = list(set(props_de_m) & set(props_de_f))
            props_de_mf = props_de_mf + \
                [False] * (len(props_en_mf) - len(props_de_mf))
            props_de = [props_de_m, props_de_f, props_de_mf]

            # Male job
            string += cls._get_guardian_job_string(
                cr, uid, child, props_en, props_de, m_g, f_g, 0, context)

            # Female job
            string += cls._get_guardian_job_string(
                cr, uid, child, props_en, props_de, m_g, f_g, 1, context)

            # Same job
            string = cls._get_guardian_job_string(
                cr, uid, child, props_en, props_de,
                m_g, f_g, 2, context) or string
        return string

    @classmethod
    def _get_mf_g(cls, cr, uid, child, m_g, f_g, context=None):
        # Comments for this function in child_description_fr
        mf_g = u''

        prefix_m = u'Suo'
        prefix_f = u'Sua'

        if (f_g[0] == u'grandmother' and m_g[0] == u'grandfather'):
            mf_g = u'{} nonni'.format(prefix_f)
        elif (f_g[0] == u'mother' and m_g[0] == u'father'):
            mf_g = u'{} genitori'.format(prefix_f)
        else:
            mf_g = u'{} {} et {} {}'.format(prefix_m, m_g[1], prefix_f, f_g[1])

        return mf_g

    @classmethod
    def _get_guardian_job_string(
            cls, cr, uid, child, props_en, props_de,
            m_g, f_g, type, context=None):
        # Comments for this function in child_description_fr
        string = u''

        prefix_f = u'Sua {}'.format(f_g[1] if f_g else u'madre')
        prefix_m = u'Suo {}'.format(m_g[1]if m_g else u'padre')

        prefix_mf = cls._get_mf_g(
            cr, uid, child, m_g, f_g, context) if f_g and m_g else None

        prefix = [prefix_m, prefix_f, prefix_mf]

        work_as = [
            u'lavora come', u'lavora come', u'lavoro come']
        is_employed = [u'lavora', u'lavora', u'lavoro']
        is_unemployed = [
            u"é disoccupato", u"é disoccupato", u"sono disoccupati"]

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
                        string += u' und {}'.format(
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
                        string += u' und {}'.format(
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
                        string += u' und'

                    string += u' {}'.format(
                        props_de[type][props_en[type].index(prop)] or prop)

        if string:
            string += u'. '

        return string
