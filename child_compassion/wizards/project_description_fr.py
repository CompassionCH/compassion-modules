# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Kevin Cristi, David Coninckx, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import _


class ProjectDescriptionFr:

    @classmethod
    def gen_fr_translation(cls, project):
        desc_fr = cls._gen_intro_fr(project)
        desc_fr += cls._gen_build_mat_fr(project)
        desc_fr += cls._gen_primary_diet_fr(project)
        desc_fr += cls._gen_health_prob_fr(project)
        desc_fr += cls._gen_primary_occup_fr(project)
        desc_fr += u'\r\n\r\n'
        desc_fr += cls._get_needs_fr(project)
        return desc_fr

    @classmethod
    def _gen_list_string(cls, word_list, separator=', ',
                         last_separator=' et '):
        res = u''
        if word_list:
            res = separator.join(word_list[:-1])
            if len(word_list) > 1:
                res += last_separator
            res += word_list[-1]

        return res

    @classmethod
    def _gen_intro_fr(cls, project):
        """ Generate the project name, the localization and infos
            about the community
        """
        has_terrain = project.community_terrain and project.community_terrain\
            != 'Other'
        res = (u"Cet enfant vit à {0}"
               u"{1}. {2} compte environ {3} habitants. ".format(
                   project.city,
                   "" if not has_terrain else
                   u" dans une région " +
                   project.translate('community_terrain'),
                   project.city, str(project.community_population)))

        return res

    @classmethod
    def _gen_build_mat_fr(cls, project):
        """ Generate house build materials, there are no specificities
            in this part
        """
        floor_mat = project.typical_floor_material != 'Other' and \
            project.translate('typical_floor_material')
        wall_mat = project.typical_wall_material != 'Other' and \
            project.translate('typical_wall_material')
        roof_mat = project.typical_roof_material != 'Other' and \
            project.translate('typical_roof_material')

        materials = list()
        if floor_mat:
            materials.append(u"de sols en " + floor_mat)
        if wall_mat:
            materials.append(u"de murs en " + wall_mat)
        if roof_mat:
            materials.append(u"de toits en " + roof_mat)

        if materials:
            res = (u"Les maisons typiques sont construites " +
                   cls._gen_list_string(materials) + ". ")
        else:
            res = ""

        return res

    @classmethod
    def _gen_primary_diet_fr(cls, project):
        """ Generate primary diet, there are no specificities in this part
        """
        primary_diets = project.primary_diet_ids.mapped('value')

        if project.primary_language_id:
            res = (u"La langue commune de la région est "
                   u"le %s. " % _(project.primary_language_id.name))
        else:
            res = ""

        res += (u"La nourriture de base se compose de %s. " % (
                cls._gen_list_string(primary_diets)))

        return res

    @classmethod
    def _gen_health_prob_fr(cls, project):
        """ Generate health problems of this region, there
            are no specificities in this part
        """
        health_prob = project.field_office_id.high_risk_ids.mapped('value')

        if health_prob:
            sing_plur_subj = (u"Les problèmes"
                              if len(health_prob) > 1 else u"Le problème")

            sing_plur_verb = (u"sont " +
                              cls._gen_list_string(health_prob)
                              if len(health_prob) > 1 else u"est" +
                              health_prob[0])

            res = (u"%s du pays %s. " % (
                sing_plur_subj, sing_plur_verb))
        else:
            res = ""

        return res

    @classmethod
    def _gen_primary_occup_fr(cls, project):
        """ Generate primary occupation and monthly income, check if need to
            round the income
        """
        primary_occup = project.primary_adults_occupation_ids.mapped('value')
        monthly_income = int(round(project.monthly_income))

        if primary_occup:
            if project.unemployment_rate > 0.5:
                res = (
                    u"La plupart des adultes sont sans emploi"
                    ", mais certains travaillent comme %s "
                    "et gagnent environ $%s par mois. " % (
                        primary_occup[0], monthly_income))
            else:
                res = (
                    u"La plupart des adultes travaillent comme %s et gagnent"
                    u" environ $%s par mois. " % (
                        primary_occup[0], monthly_income))
        else:
            res = (u"Le salaire moyen d'un travailleur est d'environ "
                   u"$%s par mois. " % monthly_income)

        return res

    @classmethod
    def _get_needs_fr(cls, project):
        """ Create the needs' description """
        school_costs = cls._gen_list_string(
            project.school_cost_paid_ids.mapped('value'))
        school_paid = u"Votre parrainage permet au " \
            u"personnel du centre d'accueil d'offrir à cet enfant " \
            u"{} pour l'école. ".format(school_costs) if school_costs else u""
        need_desc = \
            u"{school_paid}Le centre d'accueil organise " \
            u"de nombreuses activités dont " \
            u"{icp_activities}.{parent_activities}"

        vals = {
            'school_paid': school_paid,
            'icp_activities': cls._gen_list_string(
                project.get_activities(max_per_type=2)),
            'parent_activities': u" Des rencontres sont aussi organisées pour "
            u"les parents." if project.activities_for_parents else u""
        }

        return need_desc.format(**vals)
