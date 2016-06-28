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
from datetime import datetime, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class ChildDescriptionDe(object):

    @classmethod
    def gen_de_translation(cls, child):
        desc_de = cls._get_guardians_info_de(child)
        desc_de += u'\r\n\r\n'
        desc_de += cls._get_school_info_de(child)
        desc_de += cls._get_illness(child)
        desc_de += u'\r\n\r\n'
        desc_de += cls._gen_christ_act_de(child)
        desc_de += cls._gen_family_act_info_de(child)
        desc_de += cls._gen_hobbies_info_de(child)
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
    def _gen_list_string(cls, word_list):
        res = ''
        if word_list:
            res = ', '.join(word_list[:-1])
            if len(word_list) > 1:
                res += ' und '
            res += word_list[-1]
        return res

    @classmethod
    def _gen_christ_act_de(cls, child):
        ''' Generate the christian activities description part.
        '''
        if not child.christian_activity_ids:
            return ''
        activities = child.christian_activity_ids.mapped('value')
        activities_str = cls._gen_list_string(activities)
        res = u"In der Kirche macht %s %s %s" % (
            'er' if child.gender == 'M'
            else 'sie', activities_str, 'mit. '
            if activities_str > 1 else '. ')
        return res

    @classmethod
    def _gen_family_act_info_de(cls, child):
        ''' Generate the family duties description part.
            In German, it always starts with "Zu Hause hilft sie/er"
            It's followed by the family duties.
        '''
        if not child.duty_ids:
            return ''
        activities = child.duty_ids.mapped('value')
        activities_str = cls._gen_list_string(activities)
        res = (u"Zu Hause hilft %s %s. " % (
            'er' if child.gender == 'M' else 'sie', activities_str))
        return res

    @classmethod
    def _gen_hobbies_info_de(cls, child):
        ''' Generate the hobbies description part.
            There are 3 groups of hobbies:
            - hobbies starting with "Sie/Er spielt gerne" (sesg)
            - hobbies starting with "Sie/Er" (se)
            - hobbies starting with "Sie/Er" and finishing with "gerne" (se_g)
        '''
        if not child.hobby_ids:
            return ''
        gender_pronoun = 'Er' if child.gender == 'M' else 'Sie'

        activities = child.hobby_ids.mapped('value')

        res = u"{0} mag {1}.".format(
            gender_pronoun, cls._gen_list_string(activities))

        return res

    @classmethod
    def _get_school_info_de(cls, child):
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
            '5': u'siebten Klasse',
            '6': u'achten Klasse',
            '7': u'neunten Klasse',
            '8': u'zehnten Klasse',
            '9': u'elften Klasse',
            '10': u'ersten Jahr der High School',
            '11': u'zweiten Jahr der High School',
            '12': u'dreiten Jahr der High School',
            '13': u'High School',
            '14': u'High School',
            'PK': u'im Kindergarten',
            'K': u'in der zweiten Klasse',
            'P': u'in der ersten Klasse',
        }

        # the value of us_school_level can also be blank
        res = child.firstname
        if not child.not_enrolled_reason:
            if child.us_grade_level and child.us_grade_level in ordinals:
                try:
                    int(child.us_grade_level)
                    res += (u' ist in der %s'
                            % ordinals[child.us_grade_level])
                except:
                    res += (u' ist %s'
                            % ordinals[child.us_grade_level])
            else:
                res += u' geht zur Schule'
            if child.academic_performance:
                res += (u' und hat %s Ergebnisse. ' % (
                    child.translate('academic_performance')))
            else:
                res += '.'
            if child.major_course_study:
                res += u'%s mag %s. ' % (
                    u'Er' if child.gender == 'M' else u'Sie',
                    child.translate('major_course_study'))

        else:
            child_age = (
                date.today() - datetime.strptime(
                    child.birthdate, DF).date()).days / 365
            if child_age <= 5:
                res += ' geht noch nicht in die Schule.'
            else:
                res += ' geht nicht in die Schule.'

        return res

    @classmethod
    def _get_guardians_info_de(cls, child):
        ''' Generate the guardian description part. Guardians jobs are
            also included here. (comments in child_description_fr)
        '''
        res = u''
        household = child.household_id
        if not household:
            return ''

        live_with = list()
        prefix = [u'seinem', u'seiner', u'seinen', u'einem'] \
            if child.gender == 'M' else [u'ihrem', u'ihrer', u'einem',
                                         u'ihren']
        caregivers = household.get_caregivers()
        if household.father_living_with_child and \
                household.mother_living_with_child:
            live_with.append(prefix[2] + u' Eltern')
            caregivers = caregivers.remove('Father')
            caregivers = caregivers.remove('Mother')
        if caregivers.contains(['Grandmother', 'Grandfather']):
            live_with.append(prefix[2] + u' Grosseltern')
            caregivers = caregivers.remove('Grandfather')
            caregivers = caregivers.remove('Grandmother')
        if caregivers.contains(['Step Father', 'Step Mother']):
            live_with.append(prefix[2] + u' Stiefeltern')
            caregivers = caregivers.remove('Step Father')
            caregivers = caregivers.remove('Step Mother')

        for caregiver in caregivers:
            role = caregiver.translate('role')
            if caregiver.male_role:
                live_with.append("{0} {1}".format(prefix[0], role))
            elif caregiver.female_role:
                live_with.append("{0} {1}".format(prefix[1], role))
            elif caregiver.other_role:
                live_with.append("{0} {1}".format(prefix[2], role))

        # Get number of brothers and sisters
        if household.nb_brothers == 1:
            live_with.append(u'{0} Bruder'.format(prefix[0]))
        elif household.nb_brothers > 1:
            live_with.append(u'{0} {1} Brüdern'.format(
                prefix[3], cls._number_to_string(household.nb_brothers)))
        if household.nb_sisters == 1:
            live_with.append(u'{0} Schwester'.format(prefix[1]))
        elif household.nb_sisters > 1:
            live_with.append(u'{0} {1} Schwestern'.format(
                prefix[3], cls._number_to_string(household.nb_sisters)))

        if live_with:
            res = u'%s lebt mit %s. ' % (
                child.firstname, cls._gen_list_string(live_with))

        res += cls._get_parents_info(child, household)

        res += cls._get_guardians_jobs(child, household)

        return res

    @classmethod
    def _get_parents_info(cls, child, household):
        res = u''

        prefix = [u'Sein', u'Seine'] \
            if child.gender == 'M' else [u'Ihr', u'Ihre']
        if household.father_alive == 'No' and household.mother_alive == 'No':
            res += prefix[1] + u" Eltern sind gestorben"
        elif household.father_alive == 'No':
            res += prefix[0] + u" Vater ist gestorben"
        elif household.mother_alive == 'No':
            res += prefix[1] + u" Mutter ist gestorben"
        elif household.marital_status != 'Unknown':
            res += prefix[1] + u' Eltern ' + household.translate(
                'marital_status')

        # Endpoint
        if res:
            res += u'. '
        return res

    @classmethod
    def _get_guardians_jobs(cls, child, household):
        res = u""

        male_guardian = household.get_male_guardian()
        female_guardian = household.get_female_guardian()
        male_job_desc = ''
        female_job_desc = ''

        if male_guardian:
            job_desc = ""
            prefix = u'Sein' if child.gender == 'M' else u'Ihr'
            if household.male_guardian_job_type == 'Not Employed':
                job_desc = u"ist arbeitslos"
            elif household.male_guardian_job and \
                    household.male_guardian_job \
                    not in ('Unknown', 'Other'):
                job_desc = household.translate('male_guardian_job')
                if household.male_guardian_job_type == 'Sometimes Employed':
                    job_desc += u' parttime'
            if job_desc:
                male_job_desc = u"{0} {1} {2}".format(
                    prefix, male_guardian, job_desc)

        if female_guardian:
            job_desc = ""
            prefix = u'seine' if child.gender == 'M' else u'ihre'
            if household.female_guardian_job_type == 'Not Employed':
                job_desc = u"ist arbeitslos"
            elif household.female_guardian_job and \
                    household.female_guardian_job \
                    not in ('Unknown', 'Other'):
                job_desc = household.translate('female_guardian_job')
                if household.female_guardian_job_type == 'Sometimes ' \
                                                         'Employed':
                    job_desc += u' parttime'
            if job_desc:
                if household.female_guardian_job == \
                        household.male_guardian_job:
                    female_job_desc = u', sowie {0} {1}'.format(
                        prefix, female_guardian)
                else:
                    female_job_desc = u"{0} {1} {2}".format(
                        u' und ' + prefix if male_job_desc else prefix,
                        female_guardian, job_desc)

        if male_job_desc and female_job_desc:
            res = male_job_desc + female_job_desc + '.'
        elif male_job_desc:
            res = male_job_desc + '.'
        elif female_job_desc:
            res = female_job_desc.capitalize() + '.'

        return res

    @classmethod
    def _get_illness(cls, child):
        if child.chronic_illness_ids or child.physical_disability_ids:
            res = u'\r\n\r\n{firstname} hat {illness}.'
            illness = child.chronic_illness_ids.mapped(
                'value') + child.physical_disability_ids.mapped('value')
            return res.format(firstname=child.firstname, illness=illness)
        return u''
