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


class ProjectDescriptionDe:

    @classmethod
    def gen_de_translation(cls, project):
        desc_de = cls._gen_intro_de(project)
        desc_de += cls._gen_build_mat_de(project)
        desc_de += cls._gen_primary_diet_de(project)
        desc_de += cls._gen_health_prob_de(project)
        desc_de += cls._gen_primary_occup_de(project)
        desc_de += u'\r\n\r\n'
        desc_de += cls._get_needs_de(project)
        return desc_de

    @classmethod
    def _gen_list_string(cls, word_list, separator=', ',
                         last_separator=' und '):
        res = u''
        if word_list:
            res = separator.join(word_list[:-1])
            if len(word_list) > 1:
                res += last_separator
            res += word_list[-1]

        return res

    @classmethod
    def _gen_intro_de(cls, project):
        """ Generate the project name, the localization and infos
            about the community
        """
        # has_terrain = project.community_terrain and project.community_terrain
        #     != 'Other'
        res = (u"Ihr Patenkind lebt in {0}, Heimat von ungefähr {1} "
               u"Einwohnern. ".format(
                project.city,
                str(project.community_population)))

        return res

    @classmethod
    def _gen_build_mat_de(cls, project):
        """ Generate house build materials, there are no specificities
            in this part
        """
        floor_mat = project.typical_floor_material != 'Other' and \
            project.translate('typical_floor_material')
        wall_mat = project.typical_wall_material != 'Other' and \
            project.translate('typical_wall_material')
        roof_mat = project.typical_roof_material != 'Other' and \
            project.translate('typical_roof_material')

        if not (floor_mat or wall_mat or roof_mat):
            return ""

        res = u"Die Häuser {verb} für gewöhnlich "
        verb = u'sind'
        if floor_mat:
            res += u"auf {floor} gebaut"
        if wall_mat:
            if floor_mat:
                res += u" und haben {wall}"
            else:
                verb = u'haben'
                res += u"{wall}"
        if roof_mat:
            if wall_mat:
                res += u", sowie {roof}. "
            elif floor_mat:
                res += u" und haben {roof}. "
            else:
                verb = u'haben'
                res += u"{roof}. "
        else:
            res += u". "

        return res.format(verb=verb, wall=wall_mat, floor=floor_mat,
                          roof=roof_mat)

    @classmethod
    def _gen_primary_diet_de(cls, project):
        """ Generate spoken languages(s) and primary diet, there are
            no specificities in this part
        """
        primary_diets = project.primary_diet_ids.mapped('value')

        if project.primary_language_id:
            res = u"Die meist gesprochene Sprache ist {0}. ".format(
                _(project.primary_language_id.name))
        else:
            res = ""

        res += (u"Die regionale Ernährung besteht hauptsächlich aus {0}. "
                .format(cls._gen_list_string(primary_diets)))

        return res

    @classmethod
    def _gen_health_prob_de(cls, project):
        """ Generate health problems of this region, there
            are no specificities in this part
        """
        health_prob = project.field_office_id.high_risk_ids.mapped('value')

        if health_prob:
            health_desc = (
                u"Verbreitete Gesundheitsprobleme sind {0}. ".format(
                    cls._gen_list_string(health_prob))
                if len(health_prob) > 1 else
                u"Ein verbeitetes Gesundheitsproblem ist {0}. "
                u"".format(health_prob[0]))

        else:
            health_desc = ""

        return health_desc

    @classmethod
    def _gen_primary_occup_de(cls, project):
        """ Generate primary occupation and monthly income, check if need to
            round the income
        """
        primary_occup = project.primary_adults_occupation_ids.mapped('value')
        monthly_income = int(round(project.monthly_income))

        if primary_occup:
            if project.unemployment_rate > 0.5:
                res = (
                    u"Die meisten Erwachsenen in %s sind arbeitslos"
                    ", doch einige arbeiten als %s "
                    "und verdienen etwa %s Dollar pro Monat. " % (
                        project.community_name,
                        primary_occup[0],
                        monthly_income))
            else:
                res = (
                    u"Die meisten Erwachsenen in %s sind %s "
                    "und verdienen etwa %s Dollar pro Monat. " % (
                        project.community_name,
                        primary_occup[0],
                        monthly_income))
        else:
            res = (u"Das durchschnittseinkommen eines arbeiters ist "
                   u"ungefähr %s Dollar pro Monat. " % monthly_income)

        return res

    @classmethod
    def _get_needs_de(cls, project):
        """ Create the needs' description pattern to fill by hand
        """
        school_costs = cls._gen_list_string(
            project.school_cost_paid_ids.mapped('value'))
        school_paid = \
            u"Ihre Patenschaft erlaubt den Mitarbeitern des " \
            u"Projekt, " \
            u"Ihr Patenkind mit {} zu versorgen. ".format(school_costs) \
            if school_costs else u""
        need_desc = \
            u"{school_paid}Die Aktivitäten sind {icp_activities}.{" \
            u"parent_activities}"

        vals = {
            'school_paid': school_paid,
            'icp_activities': cls._gen_list_string(
                project.get_activities(max_per_type=2)),
            'parent_activities': u" Zusätzlich bieten die Projektmitarbeiter "
            u"verschiedene Treffen für die Eltern." if
            project.activities_for_parents else u""
        }

        return need_desc.format(**vals)
