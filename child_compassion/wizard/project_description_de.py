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


class Project_description_de:

    @classmethod
    def gen_de_translation(
            cls, cr, uid, project, context=None):
        desc_de = cls._gen_intro_de(
            cr, uid, project, context)
        desc_de += cls._gen_build_mat_de(
            cr, uid, project, context)
        desc_de += cls._gen_primary_diet_de(
            cr, uid, project, context)
        desc_de += cls._gen_health_prob_de(
            cr, uid, project, context)
        desc_de += cls._gen_primary_occup_de(
            cr, uid, project, context)

        return desc_de

    @classmethod
    def _gen_list_string(cls, list, separator, last_separator):
        string = ''
        if list:
            string = separator.join(list[:-1])
            if len(list) > 1:
                string += last_separator
            string += list[-1]

        return string

    @classmethod
    def _gen_intro_de(cls, cr, uid, project, context=None):
        """ Generate the project name, the localization and infos
            about the community
        """
        terrain_desc = [desc.get_translated_value('de')
                        for desc in project.terrain_description_ids]
        project_community_name = project.community_name.split('-')[0]
        string = (u"Ihr Patenkind lebt in %s%s "
                  u"von ungefähr %s Einwohnern. " % (
                      project_community_name,
                      "" if not terrain_desc else
                      " einer " + terrain_desc[0],
                      project.community_population))

        return string

    @classmethod
    def _gen_build_mat_de(cls, cr, uid, project, context=None):
        """ Generate house build materials, there are no specificities
            in this part
        """
        floor_mat = [mat.get_translated_value('de')
                     for mat in project.floor_material_ids]

        wall_mat = [mat.get_translated_value('de')
                    for mat in project.wall_material_ids]

        roof_mat = [mat.get_translated_value('de')
                    for mat in project.roof_material_ids]

        if not (floor_mat or wall_mat or roof_mat):
            return ""

        res = u"Die Häuser {verb} für gewöhnlich "
        verb = u'sind'
        wall = unicode(cls._gen_list_string(wall_mat, ', ', ' und '))
        floor = unicode(cls._gen_list_string(floor_mat, ', ', ' und '))
        roof = unicode(cls._gen_list_string(roof_mat, ', ', ' und '))
        if floor_mat:
            res += u"auf {floor} erbaut"
        if wall_mat:
            if floor_mat:
                res += u" und haben {wall}"
            else:
                verb = u'haben'
                res += u"{wall}"
        if roof_mat:
            if wall_mat:
                res += u", sowie {roof}."
            elif floor_mat:
                res += u" und haben {roof}."
            else:
                verb = u'haben'
                res += u"{roof}."
        else:
            res += u"."

        return res.format(verb=verb, wall=wall, floor=floor, roof=roof)

    @classmethod
    def _gen_primary_diet_de(cls, cr, uid, project, context=None):
        """ Generate spoken languages(s) and primary diet, there are
            no specificities in this part
        """
        primary_diet = [diet.get_translated_value('de')
                        for diet in project.primary_diet_ids]

        spoken_languages = [lang.get_translated_value('de')
                            for lang in project.spoken_languages_ids]

        string = (u"Die ethnischen Mehrheiten %s %s" % (
                  u"sind" if len(spoken_languages) > 1 else u"ist",
                  cls._gen_list_string(spoken_languages, ', ', ' und ')))

        if spoken_languages:
            string += (u" und die meist gesprochene Sprache ist %s. " % (
                       spoken_languages[0]))
        else:
            string += ". "

        string += (u"Die regionale Ernährung besteht aus %s. " % (
                   cls._gen_list_string(primary_diet, ', ', ' und ')))

        return string

    @classmethod
    def _gen_health_prob_de(cls, cr, uid, project, context=None):
        """ Generate health problems of this region, there
            are no specificities in this part
        """
        health_prob = [prob.get_translated_value('de')
                       for prob in project.health_problems_ids]

        if health_prob:
            string = (u"Verbreitete Gesundheitsprobleme %s %s. " % (
                      u"sind" if len(health_prob) > 1 else u"ist",
                      cls._gen_list_string(health_prob, ', ', ' und ')))
        else:
            string = ""

        return string

    @classmethod
    def _gen_primary_occup_de(cls, cr, uid, project, context=None):
        """ Generate primary occupation and monthly income, check if need to
            round the income
        """
        primary_occup = [occup.get_translated_value('de')
                         for occup in project.primary_occupation_ids]

        monthly_income = int(round(project.monthly_income))
        if primary_occup:
            if project.unemployment_rate > 0.5:
                string = (
                    u"Die meisten Erwachsenen in %s sind arbeitslos"
                    ", doch einige arbeiten als %s "
                    "und verdienen etwa %s Dollar pro Monat. " % (
                        project.closest_city,
                        primary_occup[0],
                        monthly_income))
            else:
                string = (
                    u"Die meisten Erwachsenen in %s sind %s "
                    "und verdienen etwa %s Dollar pro Monat. " % (
                        project.closest_city,
                        primary_occup[0],
                        monthly_income))
        else:
            string = (u"Das durchschnittseinkommen eines arbeiters ist "
                      u"ungefähr %s Dollar pro Monat. " % monthly_income)

        return string

    @classmethod
    def _get_needs_pattern_de(cls, cr, uid, project, context=None):
        """ Create the needs' description pattern to fill by hand
        """
        string = (u"Diese Region braucht (...). Ihre Patenschaft erlaubt "
                  u"den Mitarbeitern des {0}, Ihr Patenkind "
                  u"mit Bibel- und Schulunterricht, Hygieneunterricht, "
                  u"medizinischen Untersuchungen, ........................., "
                  u"zu versorgen. Zusätzlich bieten die Zentrumsangestellten "
                  u"verschiedene Treffen für die Eltern oder "
                  u"Erziehungsberechtigten Ihres Patenkindes an.").format(
            project.name)

        return string
