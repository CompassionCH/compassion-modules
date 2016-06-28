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


class ChildDescriptionIt(object):

    @classmethod
    def gen_it_translation(cls, child):
        desc_it = cls._get_guardians_info_it(child)
        desc_it += u'\r\n\r\n'
        desc_it += cls._get_school_info_it(child)
        desc_it += cls._get_illness(child)
        desc_it += u'\r\n\r\n'
        desc_it += cls._gen_christ_act_it(child)
        desc_it += cls._gen_family_act_info_it(child)
        desc_it += cls._gen_hobbies_info_it(child)
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
    def _gen_christ_act_it(cls, child):
        ''' Generate the christian activities description part.
            There are 2 groups of biblical activities:
            - activities starting with "lei/egli va" (v)
            - activities starting with "lei/egli è in" (ei)
            Words as 'un', 'una', 'a', 'al'... are included
            in value_it field.
        '''
        if not child.christian_activity_ids:
            return ''
        activities = child.christian_activity_ids.mapped('value')
        activities_str = cls._gen_list_string(activities)
        res = u"In chiesa, frequenta %s. " % activities_str
        return res

    @classmethod
    def _gen_family_act_info_it(cls, child):
        ''' Generate the family duties description part.
        '''
        if not child.duty_ids:
            return ''
        activities = child.duty_ids.mapped('value')
        activities_str = cls._gen_list_string(activities)
        res = ((u"A casa, aiuta: %s. ") % activities_str)
        return res

    @classmethod
    def _gen_hobbies_info_it(cls, child):
        ''' Generates the hobbies description part.
        '''
        if not child.hobby_ids:
            return ''
        activities = child.hobby_ids.mapped('value')
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
    def _get_school_info_it(cls, child):
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
        if not child.not_enrolled_reason:
            if child.us_grade_level and child.us_grade_level in ordinals:
                res += (u" frequenta %s" % (
                    ordinals[child.us_grade_level]))
            else:
                res += u' frequenta la scuola'
            if child.academic_performance:
                res += (u' ed ha voti %s. ' % (
                    child.translate('academic_performance')))
            else:
                res += '.'

            if child.major_course_study:
                res += u'%s piace: %s. ' % (
                    u'A lui' if child.gender == 'M' else u'A lei',
                    child.translate('major_course_study'))
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
    def _get_guardians_info_it(cls, child):
        ''' Generate the guardian description part. Guardians jobs are
            also included here.
        '''
        res = u''
        household = child.household_id
        if not household:
            return ''

        live_with = list()
        caregivers = household.get_caregivers()
        if household.father_living_with_child and \
                household.mother_living_with_child:
            live_with.append(u'i suoi genitori')
            caregivers = caregivers.remove('Father')
            caregivers = caregivers.remove('Mother')
        if caregivers.contains(['Grandmother', 'Grandfather']):
            live_with.append(u'i suoi nonni')
            caregivers = caregivers.remove('Grandfather')
            caregivers = caregivers.remove('Grandmother')
        if caregivers.contains(['Step Father', 'Step Mother']):
            live_with.append(u'i suoi beau-parents')
            caregivers = caregivers.remove('Step Father')
            caregivers = caregivers.remove('Step Mother')

        prefix = [u'suo', u'sua', u'uno', u'i suoi']
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
            live_with.append(u'{0} fratello'.format(prefix[0]))
        elif household.nb_brothers > 1:
            live_with.append(u'{0} {1} fratelli'.format(
                prefix[3], cls._number_to_string(household.nb_brothers)))
        if household.nb_sisters == 1:
            live_with.append(u'{0} sorella'.format(prefix[1]))
        elif household.nb_sisters > 1:
            live_with.append(u'{0} {1} sorelle'.format(
                prefix[3], cls._number_to_string(household.nb_sisters)))

        if live_with:
            res = u'%s vive con %s. ' % (
                child.firstname, cls._gen_list_string(live_with))

        res += cls._get_parents_info(household)

        res += cls._get_guardians_jobs(household)

        return res

    @classmethod
    def _get_parents_info(cls, household):
        res = u''

        if household.father_alive == 'No' and household.mother_alive == 'No':
            res += u"Suoi genitori sono deceduto"
        elif household.father_alive == 'No':
            res += u"Suo padre è deceduto"
        elif household.mother_alive == 'No':
            res += u"Sua madre è deceduto"
        elif household.marital_status != 'Unknown':
            res += u'Suoi genitori ' + household.translate('marital_status')

        # Endpoint
        if res:
            res += u'. '
        return res

    @classmethod
    def _get_guardians_jobs(cls, household):
        res = u""

        male_guardian = household.get_male_guardian()
        female_guardian = household.get_female_guardian()
        male_job_desc = ''
        female_job_desc = ''

        if male_guardian:
            job_desc = ""
            if household.male_guardian_job_type == 'Not Employed':
                job_desc = u"è disoccupato"
            elif household.male_guardian_job and \
                    household.male_guardian_job \
                    not in ('Unknown', 'Other'):
                job_desc = household.translate('male_guardian_job')
                if household.male_guardian_job_type == 'Sometimes Employed':
                    job_desc += u' part-time'
            if job_desc:
                male_job_desc = u"Suo {0} {1}".format(male_guardian, job_desc)

        if female_guardian:
            job_desc = ""
            if household.female_guardian_job_type == 'Not Employed':
                job_desc = u"è disoccupata"
            elif household.female_guardian_job and \
                    household.female_guardian_job \
                    not in ('Unknown', 'Other'):
                job_desc = household.translate('female_guardian_job')
                if household.female_guardian_job_type == 'Sometimes ' \
                                                         'Employed':
                    job_desc += u' part-time'
            if job_desc:
                if household.female_guardian_job == \
                        household.male_guardian_job:
                    female_job_desc = u'anche sua {0}'.format(female_guardian)
                else:
                    female_job_desc = u"{0} {1} {2}".format(
                        u'e sua' if male_job_desc else u'Sua',
                        female_guardian, job_desc)

        if male_job_desc and female_job_desc:
            res = male_job_desc + female_job_desc + '.'
        elif male_job_desc:
            res = male_job_desc + '.'
        elif female_job_desc:
            res = female_job_desc + '.'

        return res

    @classmethod
    def _get_illness(cls, child):
        if child.chronic_illness_ids or child.physical_disability_ids:
            res = u'\r\n\r\n{firstname} ha {illness}.'
            illness = child.chronic_illness_ids.mapped(
                'value') + child.physical_disability_ids.mapped('value')
            return res.format(firstname=child.firstname, illness=illness)
        return u''
