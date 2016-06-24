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


class ProjectDescriptionIt:

    @classmethod
    def gen_it_translation(cls, project):
        desc_it = cls._gen_intro_it(project)
        desc_it += cls._gen_build_mat_it(project)
        desc_it += cls._gen_primary_diet_it(project)
        desc_it += cls._gen_health_prob_it(project)
        desc_it += cls._gen_primary_occup_it(project)
        desc_it += u'\r\n\r\n'
        desc_it += cls._get_needs_it(project)

        return desc_it

    @classmethod
    def _gen_list_string(cls, word_list, separator=', ', last_separator=' e '):
        res = ''
        if word_list:
            res = separator.join(word_list[:-1])
            if len(word_list) > 1:
                res += last_separator
            res += word_list[-1]

        return res

    @classmethod
    def _gen_intro_it(cls, project):
        """ Generate the project name, the localization and infos
            about the community
        """
        res = (u"Questo bambino vive in una comunitá del %s dove "
               u"risiendono circa %s abitanti. " % (
                project.city, str(project.community_population)))

        return res

    @classmethod
    def _gen_build_mat_it(cls, project):
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
            materials.append(u"il pavimento in " + floor_mat)
        if wall_mat:
            materials.append(u"le mura in " + wall_mat)
        if roof_mat:
            materials.append(u"il tetto in " + roof_mat)

        if materials:
            res = (u"Le case hanno " +
                   cls._gen_list_string(materials) + ". ")
        else:
            res = ""

        return res

    @classmethod
    def _gen_primary_diet_it(cls, project):
        """ Generate spoken languages(s) and primary diet, there are
            no specificities in this part
        """
        primary_diets = project.primary_diet_ids.mapped('value')

        if project.primary_language_id:
            res = (u"La lingua parlata é il "
                   u"%s. " % _(project.primary_language_id.name))
        else:
            res = ""

        res += (u"La dieta regionale consiste di: %s. " % (
            cls._gen_list_string(primary_diets)))

        return res

    @classmethod
    def _gen_health_prob_it(cls, project):
        """ Generate health problemes of this region, there
            are no specificities in this part
        """
        health_prob = project.field_office_id.high_risk_ids.mapped('value')

        if health_prob:
            sing_plur_subj = (u"Le malattie"
                              if len(health_prob) > 1 else u"La malattia")

            sing_plur_verb = (u"sono " +
                              cls._gen_list_string(health_prob)
                              if len(health_prob) > 1 else u"è " +
                                                           health_prob[0])

            res = (u"%s piú comuni in questa zona %s. " % (
                sing_plur_subj, sing_plur_verb))
        else:
            res = ""

        return res

    @classmethod
    def _gen_primary_occup_it(cls, project):
        """ Generate primary occupation and monthly income, check if need to
            round the income
        """
        primary_occup = project.primary_adults_occupation_ids.mapped('value')
        monthly_income = int(round(project.monthly_income))

        if primary_occup:
            if project.unemployment_rate > 0.5:
                res = (
                    u"La maggior parte degli adulti é disoccupata ma alcuni "
                    "svolgono %s, con un guadagno mensile di $%s. " % (
                        primary_occup[0], monthly_income))
            else:
                res = (
                    u"La maggior parte degli adulti lavora come "
                    "%s, con un guadagno mensile di $%s. " % (
                        primary_occup[0], monthly_income))
        else:
            res = (u"Lo stipendio medio di un operaio è di circa "
                   u"$%s al mese. " % monthly_income)

        return res

    @classmethod
    def _get_needs_it(cls, project):
        """ Create the needs' description pattern to fill by hand
        """
        need_desc = \
            u"Grazie al suo sostegno il personale del Project " \
            u"potrá {school_paid}. Activities: "\
            u"{icp_activities}.{parent_activities}"

        vals = {
            'school_paid': cls._gen_list_string(
                project.school_cost_paid_ids.mapped('value')),
            'icp_activities': cls._gen_list_string(
                project.get_activities(max_per_type=2)),
            'parent_activities': u" Le genitori. " if
            project.activities_for_parents else u""
        }

        return need_desc.format(**vals)
