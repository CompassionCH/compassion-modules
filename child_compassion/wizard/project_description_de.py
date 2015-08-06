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
    def gen_de_translation(cls, project):
        desc_de = cls._gen_intro_de(project)
        desc_de += cls._gen_build_mat_de(project)
        desc_de += cls._gen_primary_diet_de(project)
        desc_de += cls._gen_health_prob_de(project)
        desc_de += cls._gen_primary_occup_de(project)

        return desc_de

    @classmethod
    def _gen_list_string(cls, word_list, separator, last_separator):
        res = ''
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
        project_community_name = project.community_name.split('-')[0]
        res = (u"Ihr Patenkind lebt in %s, "
               u"Heimat von ungefähr %s Einwohnern. " % (
                   project_community_name,
                   project.community_population))

        return res

    @classmethod
    def _gen_build_mat_de(cls, project):
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
        wall = unicode(cls._gen_list_string(wall_mat, ', ', ' oder '))
        floor = unicode(cls._gen_list_string(floor_mat, ', ', ' oder '))
        roof = unicode(cls._gen_list_string(roof_mat, ', ', ' oder '))
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

        return res.format(verb=verb, wall=wall, floor=floor, roof=roof)

    @classmethod
    def _gen_primary_diet_de(cls, project):
        """ Generate spoken languages(s) and primary diet, there are
            no specificities in this part
        """
        res_desc = u""
        primary_diet = [diet.get_translated_value('de')
                        for diet in project.primary_diet_ids]

        spoken_languages = [lang.get_translated_value('de')
                            for lang in project.spoken_languages_ids]

        if spoken_languages:
            res_desc += u"Die meist gesprochene Sprache ist {0}. ".format(
                spoken_languages[0])

        res_desc += u"Die regionale Ernährung besteht hauptsächlich " \
            u"aus {0}. ".format(
                cls._gen_list_string(primary_diet, ', ', ' und '))

        return res_desc

    @classmethod
    def _gen_health_prob_de(cls, project):
        """ Generate health problems of this region, there
            are no specificities in this part
        """
        health_prob = [prob.get_translated_value('de')
                       for prob in project.health_problems_ids]
        health_desc = u""
        if len(health_prob) == 1:
            health_desc = u"Ein verbeitetes Gesundheitsproblem ist {0}. "
        elif len(health_prob) > 1:
            health_desc = u"Verbreitete Gesundheitsprobleme sind {0}. "
        else:
            return health_desc

        return health_desc.format(cls._gen_list_string(
            health_prob, ', ', ' und '))

    @classmethod
    def _gen_primary_occup_de(cls, project):
        """ Generate primary occupation and monthly income, check if need to
            round the income
        """
        primary_occup = [occup.get_translated_value('de')
                         for occup in project.primary_occupation_ids]

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
    def _get_needs_pattern_de(cls, project):
        """ Create the needs' description pattern to fill by hand
        """
        res = (u"Diese Region braucht (...). Ihre Patenschaft erlaubt "
               u"den Mitarbeitern des {0}, Ihr Patenkind "
               u"mit Bibel- und Schulunterricht, Hygieneschulungen, "
               u"medizinischen Untersuchungen, ........................., "
               u"zu versorgen. Zusätzlich bieten die Projektmitarbeiter "
               u"verschiedene Treffen für die Eltern oder "
               u"Erziehungsberechtigten Ihres Patenkindes an.").format(
            project.name)

        return res
