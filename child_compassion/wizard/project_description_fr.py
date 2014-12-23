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


class Project_description_fr:

    @classmethod
    def gen_fr_translation(
            cls, cr, uid, project, context=None):
        desc_fr = cls._gen_intro_fr(
            cr, uid, project, context)
        desc_fr += cls._gen_build_mat_fr(
            cr, uid, project, context)
        desc_fr += cls._gen_primary_diet_fr(
            cr, uid, project, context)
        desc_fr += cls._gen_health_prob_fr(
            cr, uid, project, context)
        desc_fr += cls._gen_primary_occup_fr(
            cr, uid, project, context)
        return desc_fr

    @classmethod
    def _gen_list_string(cls, list, separator, last_separator):
        string = separator.join(list[:-1])
        if len(list) > 1:
            string += last_separator
        string += list[-1]

        return string

    @classmethod
    def _gen_intro_fr(cls, cr, uid, project, context=None):
        """ Generate the project name, the localization and infos
            about the community
        """
        terrain_desc = [desc.value_fr if desc.value_fr else desc.value_en
                        for desc in project.terrain_description_ids]
        string = (u"Project: %s-%s, %s.\nEmplacement: %s, %s, %s.\n"
                  u"L'enfant que vous parrainez, vit à %s dans une "
                  u"région %s. %s compte environ %s habitants. " % (
                      project.code[:2].upper(), project.code[2:],
                      project.name, project.community_name,
                      project.distance_from_closest_city,
                      project.country_common_name,
                      project.community_name, terrain_desc[0],
                      project.community_name, project.community_population))

        return string

    @classmethod
    def _gen_build_mat_fr(cls, cr, uid, project, context=None):
        """ Generate house build materials, there are no specificities
            in this part
        """
        floor_mat = [mat.value_fr if mat.value_fr else mat.value_en
                     for mat in project.floor_material_ids]

        wall_mat = [mat.value_fr if mat.value_fr else mat.value_en
                    for mat in project.wall_material_ids]

        roof_mat = [mat.value_fr if mat.value_fr else mat.value_en
                    for mat in project.roof_material_ids]

        string = (u"Les maison typiques sont construites de sols en %s, "
                  u"de murs en %s et de toits en %s. " % (
                      floor_mat[0], wall_mat[0], roof_mat[0]))

        return string

    @classmethod
    def _gen_primary_diet_fr(cls, cr, uid, project, context=None):
        """ Generate primary diet, there are no specificities in this part
        """
        primary_diet = [diet.value_fr if diet.value_fr else diet.value_en
                        for diet in project.primary_diet_ids]

        spoken_languages = [lang.value_fr if lang.value_fr else lang.value_en
                            for lang in project.spoken_languages_ids]

        string = (u"La langue la plus parlée à cet endroit est le %s. "
                  u"La nourriture de base se compose de %s. " % (
                      spoken_languages[0],
                      cls._gen_list_string(primary_diet, ', ',
                                           ' et ')))

        return string

    @classmethod
    def _gen_health_prob_fr(cls, cr, uid, project, context=None):
        """ Generate health problemes of this region, there
            are no specificities in this part
        """
        health_prob = [prob.value_fr if prob.value_fr else prob.value_en
                       for prob in project.health_problems_ids]

        sing_plur_subj = (u"Les problèmes"
                          if len(health_prob) > 1 else u"Le problème")

        sing_plur_verb = (u"sont " +
                          cls._gen_list_string(health_prob, ', ', ' et ')
                          if len(health_prob) > 1 else u"est" +
                          health_prob[0])

        string = (u"%s de santé de la région %s. " % (sing_plur_subj,
                  sing_plur_verb))

        return string

    @classmethod
    def _gen_primary_occup_fr(cls, cr, uid, project, context=None):
        """ Generate primary occupation and monthly income, check if need to
            round the income
        """
        primary_occup = [occup.value_fr if occup.value_fr else occup.value_en
                         for occup in project.primary_occupation_ids]

        monthly_income = int(round(project.monthly_income))
        string = (u"La plupart des adultes travaillent comme %s et gagnent "
                  u"environ $%s par mois. " % (
                      primary_occup[0], monthly_income))

        return string

    @classmethod
    def _get_needs_pattern_fr(cls, cr, uid, project, context=None):
        """ Create the needs' description pattern to fill by hand
        """
        string = (u"Cette communauté a besoin (de...). Votre parrainage "
                  u"permet au personnel du %s d'offrir à cet "
                  u"enfant (des enseignements bibliques...). (Des rencontres "
                  u"sont aussi organisées...)." % project.name)

        return string
