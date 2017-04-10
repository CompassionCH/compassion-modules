# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import os

from pyquery import PyQuery
from openerp import api, models, fields, _

NOMINATIVE = 0
ACCUSATIVE = 1
DATIVE = 2

SINGULAR = 0
PLURAL = 1

DIR = os.path.join(os.path.dirname(__file__)) + '/../static/src/html/'

__template_file = open(DIR + 'child_description_template.html')
HTML_TEMPLATE = __template_file.read()
__template_file.close()


class ChildDescription(models.TransientModel):
    _name = 'compassion.child.description'
    _description = 'Child Description Generator'

    child_id = fields.Many2one(
        'compassion.child', required=True, ondelete='cascade')
    desc_fr = fields.Html()
    desc_de = fields.Html()
    desc_it = fields.Html()
    desc_en = fields.Html()

    # language mappings are like this : {'M': [values], 'F': [values]}
    # where [values] is a list of list
    # [[singular_nominative, singular_accusative, singular_dative],
    #  [plural_nominative, plural_accusative, plural_dative]
    # ] values
    his_lang = {
        'fr_CH': {
            'M': [['son'] * 3, ['ses'] * 3],
            'F': [['sa'] * 3, ['ses'] * 3],
        },
        'de_DE': {
            'M': [['sein', 'seinen', 'seinem'], ['seine', 'seinen', 'seinen']],
            'F': [['seine', 'seine', 'seiner'], ['seine', 'seinen',
                                                 'seinen']],
        },
        'it_IT': {
            'M': [['suo'] * 3, ['i suoi'] * 3],
            'F': [['sua'] * 3, ['i suoi'] * 3],
        },
        'en_US': {
            'M': [['his'] * 3] * 2,
            'F': [['her'] * 3] * 2,
        },
    }

    he_lang = {
        'fr_CH': {'M': [['il'] * 3, ['ils'] * 3],
                  'F': [['elle'] * 3, ['elles'] * 3]},
        'de_DE': {'M': [['er'] * 3, ['sie'] * 3],
                  'F': [['sie'] * 3, ['sie'] * 3]},
        'it_IT': {'M': [[''] * 3, [''] * 3],
                  'F': [[''] * 3, [''] * 3]},
        'en_US': {'M': [['he'] * 3, ['they'] * 3],
                  'F': [['she'] * 3, ['they'] * 3]},
    }

    home_based_lang = {
        'fr_CH': {
            'M': u'{preferred_name} suit le programme à la maison pour enfants en '
                 u'bas-âge.',
            'F': u'{preferred_name} suit le programme à la maison pour enfants en '
                 u'bas-âge.',
        },
        'de_DE': {
            'M': u'{preferred_name} wird zu Hause im Programm für kleine Kinder '
                 u'begleitet.',
            'F': u'{preferred_name} wird zu Hause im Programm für kleine Kinder '
                 u'begleitet.',
        },
        'it_IT': {
            'M': u'{preferred_name} segue il programma a casa per i bambini '
                 u'piccoli.',
            'F': u'{preferred_name} segue il programma a casa per i bambini '
                 u'piccoli.',
        },
        'en_US': {
            'M': u'{preferred_name} follows the home based program for small kids.',
            'F': u'{preferred_name} follows the home based program for small kids.',
        }
    }

    school_yes_lang = {
        'fr_CH': {
            'M': u"{preferred_name} va à {level}",
            'F': u"{preferred_name} va à {level}.",
        },
        'de_DE': {
            'M': u'{preferred_name} geht in {level}.',
            'F': u'{preferred_name} geht in {level}.',
        },
        'it_IT': {
            'M': u'{preferred_name} frequenta {level}.',
            'F': u'{preferred_name} frequenta {level}.',
        },
        'en_US': {
            'M': u'{preferred_name} does attend {level}.',
            'F': u"{preferred_name} does attend {level}.",
        }
    }

    school_no_lang = {
        'fr_CH': {
            'M': u"{preferred_name} ne va pas à l'école.",
            'F': u"{preferred_name} ne va pas à l'école.",
        },
        'de_DE': {
            'M': u'{preferred_name} geht nicht zur Schule.',
            'F': u'{preferred_name} geht nicht zur Schule.',
        },
        'it_IT': {
            'M': u'{preferred_name} non frequenta la scuola.',
            'F': u'{preferred_name} non frequenta la scuola.',
        },
        'en_US': {
            'M': u"{preferred_name} doesn't attend school.",
            'F': u"{preferred_name} doesn't attend school.",
        }
    }

    duties_intro_lang = {
        'fr_CH': {
            'M': u"À la maison, il participe aux tâches suivantes :",
            'F': u"À la maison, elle participe aux tâches suivantes :",
        },
        'de_DE': {
            'M': u'Er hilft zu Hause:',
            'F': u'Sie hilft zu Hause:',
        },
        'it_IT': {
            'M': u'A casa aiuta nei seguenti compiti:',
            'F': u'A casa aiuta nei seguenti compiti:',
        },
        'en_US': {
            'M': u"He helps with the following duties at home:",
            'F': u"She helps with the following duties at home:",
        }
    }

    church_intro_lang = {
        'fr_CH': {
            'M': u"À l'église, il participe aux activités suivantes :",
            'F': u"À l'église, elle participe aux activités suivantes :",
        },
        'de_DE': {
            'M': u'In der Kirche macht er mit bei:',
            'F': u'In der Kirche macht sie mit bei:',
        },
        'it_IT': {
            'M': u'In chiesa partecipa alle seguenti attività:',
            'F': u'In chiesa partecipa alle seguenti attività:',
        },
        'en_US': {
            'M': u"He is engaged with his church in the following activities:",
            'F': u"She is engaged with her church in the following "
                 u"activities:",
        }
    }

    hobbies_intro_lang = {
        'fr_CH': {
            'M': u"Ses activités favorites sont :",
            'F': u"Ses activités favorites sont :",
        },
        'de_DE': {
            'M': u'Er mag gern:',
            'F': u'Sie mag gern:',
        },
        'it_IT': {
            'M': u'A {preferred_name} piace:',
            'F': u'A {preferred_name} piace:',
        },
        'en_US': {
            'M': u"{preferred_name}'s favourite interests include:",
            'F': u"{preferred_name}'s favourite interests include:",
        }
    }

    illness_intro_lang = {
        'fr_CH': {
            'M': u"{preferred_name} souffre de :",
            'F': u"{preferred_name} souffre de :",
        },
        'de_DE': {
            'M': u'{preferred_name} leidet unter:',
            'F': u'{preferred_name} leidet unter:',
        },
        'it_IT': {
            'M': u'{preferred_name} soffre di:',
            'F': u'{preferred_name} soffre di:',
        },
        'en_US': {
            'M': u"{preferred_name} has the following chronic illnesses:",
            'F': u"{preferred_name} has the following chronic illnesses:",
        }
    }

    handicap_intro_lang = {
        'fr_CH': {
            'M': u"{preferred_name} souffre de handicaps :",
            'F': u"{preferred_name} souffre de handicaps :",
        },
        'de_DE': {
            'M': u'{preferred_name} hat folgende Behinderung:',
            'F': u'{preferred_name} hat folgende Behinderung:',
        },
        'it_IT': {
            'M': u'{preferred_name} ha le seguenti disabilità fisiche:',
            'F': u'{preferred_name} ha le seguenti disabilità fisiche:',
        },
        'en_US': {
            'M': u"{preferred_name} has the following physical disabilities:",
            'F': u"{preferred_name} has the following physical disabilities:",
        }
    }

    def he(self, gender, number=SINGULAR, tense=NOMINATIVE):
        return self.he_lang[self.env.lang][gender][number][tense]

    def his(self, gender, number=SINGULAR, tense=NOMINATIVE):
        result = self.his_lang[self.env.lang][gender][number][tense]
        if self.env.lang == 'de_DE':
            # In german, "sein" becomes "ihr"
            result = self.child_id.get(result)
        return result

    @api.model
    def create(self, vals):
        """ This will automatically generate all descriptions and save them
        in the related child.
        """
        generator = super(ChildDescription, self).create(vals)
        generator.desc_fr = generator.with_context(
            lang='fr_CH')._generate_translation()
        generator.desc_de = generator.with_context(
            lang='de_DE')._generate_translation()
        generator.desc_it = generator.with_context(
            lang='it_IT')._generate_translation()
        generator.desc_en = generator.with_context(
            lang='en_US')._generate_translation()
        generator.child_id.write({
            'desc_fr': generator.desc_fr,
            'desc_de': generator.desc_de,
            'desc_it': generator.desc_it,
            'desc_en': generator.desc_en,
        })

        return generator

    def _generate_translation(self):
        """ Generate child description. """
        desc = PyQuery(HTML_TEMPLATE)

        # 1. Program type only if Home Based + Birthday estimate
        ########################################################
        child = self.child_id
        if child.cdsp_type == 'Home Based':
            desc('.program_type').html(
                self.home_based_lang[self.env.lang][child.gender].format(
                    firstname=child.preferred_name)
            )
        else:
            desc('#program_type').remove()
        if child.estimated_birthdate:
            desc('.birthday_estimate').html(
                _("* The birthday is an estimation.")
            )
        else:
            desc('#birthday_estimate').remove()

        # 2. Household
        ##############
        household = child.household_id.with_context(active_gender=child.gender)
        live_with = self._live_with()
        desc('#live_with').html(live_with)

        if not household.father_living_with_child:
            f_alive = desc('.father').children('.is_alive')
            f_alive[0].text = _('Father alive')
            f_alive[1].text = household.translate('father_alive')
        else:
            desc('.father').remove()
        self._job(desc('.father_job'), 'father')

        if not household.mother_living_with_child:
            m_alive = desc('.mother').children('.is_alive')
            m_alive[0].text = _('Mother alive')
            m_alive[1].text = household.translate('mother_alive')
        else:
            desc('.mother').remove()
        self._job(desc('.mother_job'), 'mother')

        if household.nb_brothers:
            desc('.brothers')[0].text = _("Number of brothers")
            desc('.brothers')[1].text = str(household.nb_brothers)
        else:
            desc('.brothers').remove()
        if household.nb_sisters:
            desc('.sisters')[0].text = _("Number of sisters")
            desc('.sisters')[1].text = str(household.nb_sisters)
        else:
            desc('.sisters').remove()

        # 3. Schooling
        ##############
        if child.education_level and child.education_level != 'Not Enrolled':
            desc('#school_attending').html(
                self.school_yes_lang[self.env.lang][child.gender].format(
                    firstname=child.preferred_name,
                    level=child.translate('education_level'))
            )
            if child.academic_performance:
                desc('.school_performance')[0].text = _('School performance')
                desc('.school_performance')[1].text = child.translate(
                    'academic_performance')
            else:
                desc('#school_performance').remove()
            if child.major_course_study:
                desc('.school_subject')[0].text = _('Best school subject')
                desc('.school_subject')[1].text = child.translate(
                    'major_course_study')
            else:
                desc('#school_subject').remove()
            if child.vocational_training_type and \
                    child.vocational_training_type.lower() not in (
                            'not enrolled', 'other'):
                desc('.vocational_training')[0].text = _('Vocational training')
                desc('.vocational_training')[1].text = child.translate(
                    'vocational_training_type')
            else:
                desc('#vocational_training').remove()
        else:
            desc('#school_attending').html(
                self.school_no_lang[self.env.lang][child.gender].format(
                    firstname=child.preferred_name)
            )
            desc('.school').remove()

        # 4. House duties
        #################
        if child.duty_ids:
            desc('#house_duties_intro').html(
                self.duties_intro_lang[self.env.lang][child.gender])
            desc('#house_duties_list').html(''.join(
                ['<li>' + duty.value + '</li>' for duty in child.duty_ids[:3]]
            ))
        else:
            desc('.house_duties').remove()

        # 5. Church activities
        ######################
        if child.christian_activity_ids:
            desc('#church_activities_intro').html(
                self.church_intro_lang[self.env.lang][child.gender])
            desc('#church_activities_list').html(''.join(
                ['<li>' + activity.value + '</li>' for activity in
                 child.christian_activity_ids[:3]]))
        else:
            desc('.church_activities').remove()

        # 6. Hobbies
        ############
        if child.hobby_ids:
            desc('#hobbies_intro').html(
                self.hobbies_intro_lang[self.env.lang][child.gender].format(
                    firstname=child.preferred_name))
            desc('#hobbies_list').html(''.join(
                ['<li>' + hobby.value + '</li>'
                 for hobby in child.hobby_ids[:3]]))
        else:
            desc('.hobbies').remove()

        # 7. Health
        ###########
        if child.chronic_illness_ids:
            desc('#chronic_illness_intro').html(
                self.illness_intro_lang[self.env.lang][child.gender].format(
                    firstname=child.preferred_name))
            desc('#chronic_illness_list').html(''.join(
                ['<li>' + illness.value + '</li>' for illness in
                 child.chronic_illness_ids]))
        else:
            desc('.chronic_illness').remove()

        if child.physical_disability_ids:
            desc('#handicap_intro').html(
                self.illness_intro_lang[self.env.lang][child.gender].format(
                    firstname=child.preferred_name))
            desc('#handicap_list').html(''.join(
                ['<li>' + handicap.value + '</li>' for handicap in
                 child.physical_disability_ids]))
        else:
            desc('.handicap').remove()

        return desc.html()

    def _gender(self, default):
        """ In all languages except English, the gender is defined
        by the complement. For English, the gender is taken by the subject.
        """
        return self.child_id.gender if self.env.lang == 'en_US' else default

    def _he(self):
        """ Utility to quickly return he or she. """
        return self.he(self.child_id.gender)

    def _live_with(self):
        """ Generates the small 'Live with' sentence. """
        household = self.child_id.household_id
        father_with_child = household.father_living_with_child
        mother_with_child = household.mother_living_with_child
        youth = household.youth_headed_household
        live_with = self.child_id.preferred_name + ' ' + _('lives') + ' '
        if father_with_child and mother_with_child:
            live_with += _('with') + ' ' + self.his(
                self.child_id.gender, PLURAL, DATIVE) + ' ' + _('parents')
        elif father_with_child:
            live_with += _('with') + ' ' + self.his(
                self._gender('M'), tense=DATIVE) + ' ' + _('father')
        elif mother_with_child:
            live_with += _('with') + ' ' + self.his(
                self._gender('F'), tense=DATIVE) + ' ' + _('mother')
        elif youth:
            live_with += _('in a youth headed house.')
        else:
            caregiver = household.primary_caregiver_id
            if caregiver:
                caregiver_role = household.primary_caregiver
                if caregiver_role == 'Beneficiary - Male':
                    caregiver_role = _('brother')
                if caregiver_role == 'Beneficiary - Female':
                    caregiver_role = _('sister')
                live_with += _('with') + ' ' + self.his(
                    self._gender(caregiver.gender), tense=DATIVE
                ) + ' ' + caregiver_role
            else:
                live_with += _('in an institution.')

        if household.primary_caregiver_id and not youth:
            if self.env.lang == 'de_DE':
                live_with += ' zusammen'
            live_with += '.'

        return live_with

    def _job(self, desc, guardian):
        """ Generates the job part of the guardians. """
        at = self.env['ir.advanced.translation']
        household = self.child_id.household_id
        en = household.with_context(lang='en_US')
        if guardian == 'father':
            job_type = household.male_guardian_job_type
            # job_type_field = 'male_guardian_job_type'
            # job_type_label = _('Father occupation')
            job = at.get(en.translate('male_guardian_job'))
            job_label = _('Father job')
        elif guardian == 'mother':
            job_type = household.female_guardian_job_type
            # job_type_field = 'female_guardian_job_type'
            # job_type_label = _('Mother occupation')
            job = at.get(en.translate('female_guardian_job'), female=True)
            job_label = _('Mother job')

        # f_job_type = desc.children('.job_type')
        # f_job_type[0].text = job_type_label
        # f_job_type[1].text = household.translate(job_type_field)

        if job_type == 'Not Employed' or not job:
            desc.remove()
        else:
            f_job = desc.children('.job')
            f_job[0].text = job_label
            f_job[1].text = job
