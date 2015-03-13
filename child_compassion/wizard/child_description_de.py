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


class Child_description_de:
    @classmethod
    def _get_translated_value(cls, value):
        id = value.value_en
        translated_value = value.value_de or value.value_en
        color = 'red' if not value.value_de else 'blue'
        return u'<span id="{}" style="color:{}">{}</span>'.format(
            id, color, translated_value)

    @classmethod
    def gen_de_translation(
            cls, cr, uid, child, case_study, context=None):
        desc_de = cls._get_guardians_info_de(
            cr, uid, child, case_study, context)
        desc_de += u'\r\n\r\n'
        desc_de += cls._get_school_info_de(
            cr, uid, child, case_study, context)
        desc_de += u'\r\n\r\n'
        desc_de += cls._gen_christ_act_de(cr, uid, child, case_study, context)
        desc_de += cls._gen_family_act_info_de(
            cr, uid, child, case_study, context)
        desc_de += cls._gen_hobbies_info_de(
            cr, uid, child, case_study, context)
        return desc_de

    @classmethod
    def _number_to_string(cls, number):
        conversion_dict = {
            1: u'eins',
            2: u'zwei',
            3: u'drei',
            4: u'vier',
            5: u'fünf',
            6: u'sechs',
            7: u'sieben',
            8: u'acht',
            9: u'neun'
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
            cls._get_translated_value(activity)
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
            In German, it always starts with "Zu Hause hilft sie/er"
            It's followed by the family duties.
        '''
        if not case_study.family_duties_ids:
            return ''
        activities = ([cls._get_translated_value(activity)
                       for activity in case_study.family_duties_ids])
        activities_str = cls._gen_list_string(activities)
        string = (u"Zu Hause hilft %s %s. " % (
            'er' if child.gender == 'M' else 'sie', activities_str))
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
        gender_pronoun = 'Er' if child.gender == 'M' else 'Sie'

        activities = [
            cls._get_translated_value(activity)
            for activity in case_study.hobbies_ids]

        string = u"{} mag {}".format(
            gender_pronoun, cls._gen_list_string(activities))

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
            '1': u'dritten Klasse',
            '2': u'vierten Klasse',
            '3': u'fünften Klasse',
            '4': u'sechsten Klasse',
            '5': u'siebsten Klasse',
            '6': u'achten Klasse',
            '7': u'neunten Klasse',
            '8': u'zehnten Klasse',
            '9': u'elften Klasse',
            '10': u'ersten Jahr der High School',
            '11': u'zweiten Jahr der High School',
            '12': u'dreiten Jahr der High School',
            '13': u'der High School',
            '14': u'der High School',
            'PK': u'Kindergarten',
            'K': u'zweiten Klasse',
            'P': u'ersten Klasse',
        }

        # the value of us_school_level can also be blank
        string = child.firstname
        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    string += (u' ist in der %s'
                               % ordinals[case_study.us_school_level])
                except:
                    string += (u' ist in der %s'
                               % ordinals[case_study.us_school_level])
            else:
                string += u' geht zur Schule'
            if case_study.school_performance:
                string += (u' und hat %s Ergebnisse. ' % (
                    cls._get_translated_value(
                        case_study.school_performance[0])))
            else:
                string += '.'
            if case_study.school_best_subject:
                string += u'%s mag %s. ' % (
                    u'Er' if child.gender == 'M' else u'Sie',
                    cls._get_translated_value(
                        case_study.school_best_subject[0]))

        else:
            child_age = (
                date.today() - datetime.strptime(
                    child.birthdate, DF).date()).days / 365
            if child_age <= 5:
                string += ' geht noch nicht in die Schule.'
            else:
                string += ' geht nicht in die Schule.'

        return string

    @classmethod
    def _get_guardians_info_de(cls, cr, uid, child, case_study, context=None):
        ''' Generate the guardian description part. Guardians jobs are
            also included here. (comments in child_description_fr)
        '''
        string = u''
        if not case_study.guardians_ids:
            return ''
        male_values = ['father', 'uncle', 'brother', 'grandfather',
                       'stepfather', 'godfather']
        plur_values = ['friends', 'other relatives', 'foster parents']
        if child.gender == 'M':
            prefix = [u'seinem', u'seiner', u'seinen']
        else:
            prefix = [u'ihrem', u'ihrer', u'ihren']

        live_with = OrderedDict()
        male_guardians = dict()
        female_guardians = dict()
        live_in_institut = False

        for guardian in case_study.guardians_ids:
            value = cls._get_translated_value(guardian)

            if guardian.value_en != 'institutional worker':
                if guardian.value_en in male_values:
                    male_guardians[guardian.value_en] = value
                    if guardian.value_en != 'brother':
                        live_with[guardian.value_en] = u'{} {}'.format(
                            prefix[0], value)
                elif guardian.value_en in plur_values:
                    male_guardians[guardian.value_en] = value
                    female_guardians[guardian.value_en] = value
                    live_with[guardian.value_en] = u'{} {}'.format(
                        prefix[2], value)
                else:
                    female_guardians[guardian.value_en] = value
                    if guardian.value_en != 'sister':
                        live_with[guardian.value_en] = u'{} {}'.format(
                            prefix[1], value)
            else:
                live_in_institut = True

        # Regroup parents and grandparents
        live_with = cls._regroup_parents(cr, uid, live_with, prefix, context)

        if case_study.nb_brothers == 1:
            live_with['brothers'] = u'{} Bruder'.format(prefix[0])
        elif case_study.nb_brothers > 1:
            live_with['brothers'] = u'{} {} Brüder'.format(
                prefix[2], cls._number_to_string(case_study.nb_brothers))
        if case_study.nb_sisters == 1:
            live_with['sisters'] = u'{} Schwester'.format(prefix[1])
        elif case_study.nb_sisters > 1:
            live_with['sisters'] = u'{} {} Schwestern'.format(
                prefix[2], cls._number_to_string(case_study.nb_sisters))

        if live_in_institut:
            string = '%s lebt in einem Internat mit %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))
        else:
            string = '%s lebt mit %s. ' % (
                child.firstname, cls._gen_list_string(live_with.values()))
        string += cls._get_parents_info(
            cr, uid, child, case_study, context)
        string += cls._get_guardians_jobs_de(
            cr, uid, child, case_study,
            male_guardians.items()[0] if male_guardians else False,
            female_guardians.items()[0] if female_guardians else False,
            context)
        return string

    @classmethod
    def _regroup_parents(cls, cr, uid, dict, prefix, context=None):
        if (u'mother' in dict and u'father' in dict):
            dict.pop(u'mother')
            dict.pop(u'father')
            dict[u'parents'] = u'{} Eltern'.format(prefix[2])
        if (u'grandmother' in dict and u'grandfather' in dict):
            dict.pop(u'grandmother')
            dict.pop(u'grandfather')
            dict[u'parents'] = u'{} Großeltern'.format(prefix[2])
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

        if (child.gender == 'M'):
            prefix = [u'Sein Vater', u'Sein Mutter', u'Seine Eltern']
        else:
            prefix = [u'Ihr Vater', u'Ihre Mutter', u'Ihre Eltern']

        be = [u'ist', u'ist', u'sind']
        dead = [u'ist gestorben', u'ist gestorben', u'sind gestorben']
        support = [u'unterstüzt die Familie finanziell',
                   u'unterstüzt die Familie finanziell',
                   u'unterstüzt die Familie finanziell']

        status_tags = {
            u'inprison': [u'im Gefängnis', u'im Gefängnis', u'im Gefängnis'],
            u'mentallyill': [u'seelisch krank',
                             u'seelisch krank',
                             u'seelisch krank'],
            u'chronicallyill': [u'kronisch krank',
                                u'kronisch krank',
                                u'kronisch krank'],
            u'handicapped': [u'behindert', u'behindert', u'behindert'],
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
    def _get_guardians_jobs_de(cls, cr, uid, child,
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

        if child.gender == 'M':
            prefix_m = u'Sein'
            prefix_f = u'Seine'
        else:
            prefix_m = u'Ihr'
            prefix_f = u'Ihre'

        if (f_g[0] == u'grandmother' and m_g[0] == u'grandfather'):
            mf_g = u'{} Großeltern'.format(prefix_f)
        elif (f_g[0] == u'mother' and m_g[0] == u'father'):
            mf_g = u'{} Eltern'.format(prefix_f)
        else:
            mf_g = u'{} {} et {} {}'.format(prefix_m, m_g[1], prefix_f, f_g[1])

        return mf_g

    @classmethod
    def _get_guardian_job_string(
            cls, cr, uid, child, props_en, props_de,
            m_g, f_g, type, context=None):
        # Comments for this function in child_description_fr
        string = u''

        if(child.gender == 'M'):
            prefix_f = u'Seine {}'.format(f_g[1] if f_g else u'Mutter')
            prefix_m = u'Sein {}'.format(m_g[1]if m_g else u'Vater')
        else:
            prefix_f = u'Ihre {}'.format(f_g[1] if f_g else u'Mutter')
            prefix_m = u'Ihr {}'.format(m_g[1]if m_g else u'Vater')

        prefix_mf = cls._get_mf_g(
            cr, uid, child, m_g, f_g, context) if f_g and m_g else None

        prefix = [prefix_m, prefix_f, prefix_mf]

        work_as = [
            u'arbeitet als', u'arbeitet als', u'arbeiten als']
        is_employed = [u'arbeitet', u'arbeitet', u'arbeiten']
        is_unemployed = [
            u"ist arbeitslos", u"ist arbeitslos", u"sind arbeitslos"]

        job_tags_work_as = {
            'isafarmer': [u'Landwirt', u'Landwirtin', u'fermiers'],
            'isateacher': [u'Lehrer', u'Lehrerin', u'enseignants'],
            'sellsinmarket': [u'Marktverkäufer',
                              u'Marktverkäuferin',
                              u'Marktverkäufer'],
        }
        job_tags_isemployed = {
            'isachurchworker': u'in der Kirche',
            'isaprojectworker': u'im Kinderprojektzentrum',
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

                    prop_de = props_de[type][props_en[type].index(prop)]
                    color = 'red' if not prop_de else 'blue'
                    translated_prop = prop_de or prop

                    string += (u' <span id="{}" style="color:{}">{}'
                               '</span>').format(prop, color, translated_prop)

        if string:
            string += u'. '

        return string
