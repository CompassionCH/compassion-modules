# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester , Kevin Cristi, David Coninckx, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from datetime import datetime, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class ChildDescriptionFr(object):

    @classmethod
    def gen_fr_translation(cls, child):
        desc_fr = cls._get_guardians_info_fr(child)
        desc_fr += u'\r\n\r\n'
        desc_fr += cls._get_school_info_fr(child)
        desc_fr += u'\r\n\r\n'
        desc_fr += cls._gen_christ_act_fr(child)
        desc_fr += cls._gen_family_act_info_fr(child)
        desc_fr += cls._gen_hobbies_info_fr(child)
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
    def _gen_christ_act_fr(cls, child):
        ''' Generate the christian activities description part.
            Words as 'à', 'aux', ... are included in value_fr field.
        '''
        if not child.christian_activity_ids:
            return ''
        activities = child.christian_activity_ids.mapped('name')
        activities_str = cls._gen_list_string(activities)
        res = u"A l'Église, %s participe %s. " % (
            'il' if child.gender == 'M' else 'elle', activities_str)
        return res

    @classmethod
    def _gen_family_act_info_fr(cls, child):
        ''' Generate the family duties description part. There are 2 kind of
            activities:
             - Standards : introduced by 'aide à faire' and having
                the determinant in value_fr
             - Specials : having the action verb included in value_fr
        '''
        if not child.duty_ids:
            return ''

        activities = child.duty_ids.mapped('name')
        res = u"A la maison, %s aide %s. " % (
            'il' if child.gender == 'M' else 'elle',
            cls._gen_list_string(activities))
        return res

    @classmethod
    def _gen_hobbies_info_fr(cls, child):
        ''' Generate the hobbies description part.
             There are 2 kind of hobbies :
             - games, which are introduced by 'jouer' and having
                the determinant included in value_fr
             - verbs, which are simply printed without any decoration.
        '''
        if not child.hobby_ids:
            return ''

        activities = child.hobby_ids.mapped('name')

        res = u"%s aime %s. " % (
            'Il' if child.gender == 'M'
            else 'Elle', cls._gen_list_string(activities))
        return res

    @classmethod
    def _get_school_info_fr(cls, child):
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

        if not child.not_enrolled_reason:
            if child.us_grade_level and child.us_grade_level in ordinals:
                try:
                    int(child.us_grade_level)
                    res += (u' est %s'
                            % ordinals[child.us_grade_level])
                except:
                    res += (u' est %s'
                            % ordinals[child.us_grade_level])
            else:
                res += u" va à l'école"
            if child.academic_performance:
                res += u' et %s a des résultats %s. ' % (
                    u'il' if child.gender == 'M' else u'elle',
                    child.translate('academic_performance'))
            if child.major_course_study:
                res += u'%s aime bien %s. ' % (
                    u'Il' if child.gender == 'M' else u'Elle',
                    child.translate('major_course_study'))
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
    def _get_guardians_info_fr(cls, child):
        """
        Generate the guardian description part. Guardians jobs are
        also included here.
        """
        res = u''
        household = child.household_id
        if not household:
            return ''

        live_with = list()
        caregivers = household.get_caregivers()
        if household.father_living_with_child and \
                household.mother_living_with_child:
            live_with.append(u'ses parents')
            caregivers = caregivers.remove('Father')
            caregivers = caregivers.remove('Mother')
        if caregivers.contains(['Grandmother', 'Grandfather']):
            live_with.append(u'ses grand-parents')
            caregivers = caregivers.remove('Grandfather')
            caregivers = caregivers.remove('Grandmother')
        if caregivers.contains(['Step Father', 'Step Mother']):
            live_with.append(u'ses beau-parents')
            caregivers = caregivers.remove('Step Father')
            caregivers = caregivers.remove('Step Mother')

        prefix = [u'son', u'sa', u'un']
        for caregiver in caregivers:
            role = caregiver.translate('role')
            if caregiver.male_role:
                live_with.append("{0} {1}".format(prefix[0], role))
            elif caregiver.female_role:
                live_with.append("{0} {1}".format(prefix[1], role))
            elif caregiver.other_role:
                live_with.append("{0} {1}".format(prefix[2], role))

        # Get number of brothers and sisters
        # if household.nb_brothers == 1:
        #     live_with['brothers'] = u'{0} frère'.format(prefix[0])
        # elif household.nb_brothers > 1:
        #     live_with['brothers'] = u'{0} {1} frères'.format(
        #         prefix[2], cls._number_to_string(household.nb_brothers))
        # if household.nb_sisters == 1:
        #     live_with['sisters'] = u'{0} soeur'.format(prefix[1])
        # elif household.nb_sisters > 1:
        #     live_with['sisters'] = u'{0} {1} soeurs'.format(
        #         prefix[2], cls._number_to_string(household.nb_sisters))

        res = u'%s vit avec %s. ' % (
            child.firstname, cls._gen_list_string(live_with))

        res += cls._get_parents_info(household)

        res += cls._get_guardians_jobs(household)

        return res

    @classmethod
    def _get_parents_info(cls, household):
        res = u''

        if household.father_alive == 'No' and household.mother_alive == 'No':
            res += u"Ses parents sont décédés"
        elif household.father_alive == 'No':
            res += u"Son père est décédé"
        elif household.mother_alive == 'No':
            res += u"Sa mère est décédée"
        elif household.marital_status != 'Unknown':
            res += u'Ses parents ' + household.translate('marital_status')

        # Endpoint
        if res:
            res += u'. '
        return res

    @classmethod
    def _get_guardians_jobs(cls, household):
        """ Generate the guardians jobs description part. """
        res = u""

        male_guardian = household.get_male_guardian()
        female_guardian = household.get_female_guardian()
        male_job_desc = ''
        female_job_desc = ''

        if male_guardian:
            job_desc = ""
            if household.male_guardian_job_type == 'Not Employed':
                job_desc = u"n'a pas d'emploi"
            elif household.male_guardian_job and \
                    household.male_guardian_job \
                    not in ('Unknown', 'Other'):
                job_desc = household.translate('male_guardian_job')
                if household.male_guardian_job_type == 'Sometimes Employed':
                    job_desc += u' à temps partiel'
            if job_desc:
                male_job_desc = u"Son {0} {1}".format(male_guardian, job_desc)

        if female_guardian:
            job_desc = ""
            if household.female_guardian_job_type == 'Not Employed':
                job_desc = u"n'a pas d'emploi"
            elif household.female_guardian_job and \
                    household.female_guardian_job \
                    not in ('Unknown', 'Other'):
                job_desc = household.translate('female_guardian_job')
                if household.female_guardian_job_type == 'Sometimes ' \
                                                         'Employed':
                    job_desc += u' à temps partiel'
            if job_desc:
                if household.female_guardian_job == \
                        household.male_guardian_job:
                    female_job_desc = u'sa {0} aussi'.format(female_guardian)
                else:
                    female_job_desc = u"sa {0} {1}".format(female_guardian,
                                                           job_desc)

        if male_job_desc and female_job_desc:
            res = male_job_desc + ' et ' + female_job_desc + '.'
        elif male_job_desc:
            res = male_job_desc + '.'
        elif female_job_desc:
            res = female_job_desc.capitalize() + '.'

        return res
