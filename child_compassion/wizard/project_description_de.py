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


class Project_description_de:

    @classmethod
    def gen_de_translation(
            cls, cr, uid, project_id, project, context=None):
        desc_de = cls._gen_intro_de(
            cr, uid, project_id, project, context)
        desc_de += cls._gen_build_mat_de(
            cr, uid, project_id, project, context)
        desc_de += cls._gen_primary_diet_de(
            cr, uid, project_id, project, context)
        desc_de += cls._gen_health_prob_de(
            cr, uid, project_id, project, context)
        desc_de += cls._gen_primary_occup_de(
            cr, uid, project_id, project, context)

        return desc_de

    @classmethod
    def _gen_list_string(cls, list, separator, last_separator):
        string = separator.join(list[:-1])
        if len(list) > 1:
            string += last_separator
        string += list[-1]

        return string

    @classmethod
    def _gen_intro_de(cls, cr, uid, project_id, project, context=None):
        """ Generate the project name, the localization and infos
            about the community
        """
        terrain_desc = [desc.value_de if desc.value_de else desc.value_en
                        for desc in project.terrain_description_ids]
        string = (u"Projekt: %s-%s, %s.\nOrt: %s, %s, %s.\n"
                  u"Das von Ihnen unterstütze Kind lebt in %s einer %s "
                  u"mit ungefähr %s Einwohnern. " % (
                      project.code[:2].upper(), project.code[2:],
                      project.name, project.community_name,
                      project.distance_from_closest_city,
                      project.country_common_name,
                      project.community_name, terrain_desc[0],
                      project.community_population))

        return string

    @classmethod
    def _gen_build_mat_de(cls, cr, uid, project_id, project, context=None):
        """ Generate house build materials, there are no specificities
            in this part
        """
        floor_mat = [mat.value_de if mat.value_de else mat.value_en
                     for mat in project.floor_material_ids]

        wall_mat = [mat.value_de if mat.value_de else mat.value_en
                    for mat in project.wall_material_ids]

        roof_mat = [mat.value_de if mat.value_de else mat.value_en
                    for mat in project.roof_material_ids]

        string = (u"Die Häuser sind typischerweise mit %s gebaut "
                  u"und haben %s, sowie %s. " % (
                      wall_mat[0], floor_mat[0], roof_mat[0]))

        return string

    @classmethod
    def _gen_primary_diet_de(cls, cr, uid, project_id, project, context=None):
        """ Generate spoken languages(s) and primary diet, there are
            no specificities in this part
        """
        primary_diet = [diet.value_de if diet.value_de else diet.value_en
                        for diet in project.primary_diet_ids]

        spoken_languages = [lang.value_de if lang.value_de else lang.value_en
                            for lang in project.spoken_languages_ids]

        string = (u"Die ethnischen Merheiten %s %s und die meist "
                  u"gesprochene Sprache ist %s. Die regionale "
                  u"Ernährung beinhaltet %s. " % (
                      u"sind" if len(spoken_languages) > 1 else u"ist",
                      cls._gen_list_string(spoken_languages, ', ', ' und '),
                      spoken_languages[0],
                      cls._gen_list_string(primary_diet, ', ', ' und ')))

        return string

    @classmethod
    def _gen_health_prob_de(cls, cr, uid, project_id, project, context=None):
        """ Generate health problemes of this region, there
            are no specificities in this part
        """
        health_prob = [prob.value_de if prob.value_de else prob.value_en
                       for prob in project.health_problems_ids]

        string = (u"Verbereitete Gesundheitsporbleme %s %s. " % (
                  u"sind" if len(health_prob) > 1 else u"ist",
                  cls._gen_list_string(health_prob, ', ', ' und ')))

        return string

    @classmethod
    def _gen_primary_occup_de(cls, cr, uid, project_id, project, context=None):
        """ Generate primary occupation and monthly income, check if need to
            round the income
        """
        primary_occup = [occup.value_de if occup.value_de else occup.value_en
                         for occup in project.primary_occupation_ids]

        if project.monthly_income % 1 > 0.5:
            monthly_income = (project.monthly_income +
                              (1 - project.monthly_income % 1))

        monthly_income = int(project.monthly_income)
        string = (u"Die Mehrheit der Erwachsenen von Lome ist %s und "
                  u"verdienen etwa %s Dollar pro Monat. " % (
                      primary_occup[0], monthly_income))

        return string

    @classmethod
    def _get_needs_pattern_de(cls, cr, uid, context=None):
        """ Create the needs' description pattern to fill by hand
        """
        string = (u"Diese Region braucht (...). Ihre Patenschaft erlaubt "
                  u"den Mitarbeitern des (Projektcentrum...), Ihr Patenkind "
                  u"mit (...). Zusätzlich bieten die Zentrumsangestellten "
                  u"verschiedene Treffen für die Eltern oder "
                  u"Erziehungsberechtigten Ihres Patenkindes an.")

        return string
