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
    def _get_translated_value(cls, value):
        id = value.value_en
        translated_value = value.value_fr or value.value_en
        color = 'red' if not value.value_fr else 'blue'
        return u'<span id="{}" style="color:{}">{}</span>'.format(
            id, color, translated_value)

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
        string = ''
        if list:
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
        terrain_desc = [cls._get_translated_value(desc)
                        for desc in project.terrain_description_ids]
        project_community_name = project.community_name.split('-')[0]
        project_community_population = u"{:,}".format(
            project.community_population).replace(',', "'")
        string = (u"Cet enfant vit à {}"
                  u"{}. {} compte environ {} habitants. ".format(
                      project_community_name,
                      "" if not terrain_desc else u" dans une région " +
                      terrain_desc[0],
                      project_community_name, project_community_population))

        return string

    @classmethod
    def _gen_build_mat_fr(cls, cr, uid, project, context=None):
        """ Generate house build materials, there are no specificities
            in this part
        """
        floor_mat = [cls._get_translated_value(mat)
                     for mat in project.floor_material_ids]
        wall_mat = [cls._get_translated_value(mat)
                    for mat in project.wall_material_ids]
        roof_mat = [cls._get_translated_value(mat)
                    for mat in project.roof_material_ids]

        materials = []
        if floor_mat:
            materials.append(u"de sols en %s" % 
                cls._gen_list_string(floor_mat, ', ', ' et '))
        if wall_mat:
            materials.append(u"de murs en %s" % 
                cls._gen_list_string(wall_mat, ', ', ' et '))
        if roof_mat:
            materials.append(u"de toits en %s" % 
                cls._gen_list_string(roof_mat, ', ', ' et '))
        if materials:
            string = (u"Les maisons typiques sont construites " +
                      cls._gen_list_string(materials, ', ', ' et ') + ". ")
        else:
            string = ""

        return string

    @classmethod
    def _gen_primary_diet_fr(cls, cr, uid, project, context=None):
        """ Generate primary diet, there are no specificities in this part
        """
        primary_diet = [cls._get_translated_value(diet)
                        for diet in project.primary_diet_ids]
        spoken_languages = [cls._get_translated_value(lang)
                            for lang in project.spoken_languages_ids]

        if spoken_languages:
            string = (u"La langue commune de la region est "
                      u"le %s. " % (spoken_languages[0]))
        else:
            string = ""

        string += (u"La nourriture de base se compose de %s. " % (
                   cls._gen_list_string(primary_diet, ', ', ' et ')))

        return string

    @classmethod
    def _gen_health_prob_fr(cls, cr, uid, project, context=None):
        """ Generate health problemes of this region, there
            are no specificities in this part
        """
        health_prob = [cls._get_translated_value(prob)
                       for prob in project.health_problems_ids]

        if health_prob:
            sing_plur_subj = (u"Les problèmes"
                              if len(health_prob) > 1 else u"Le problème")

            sing_plur_verb = (u"sont " +
                              cls._gen_list_string(health_prob, ', ', ' et ')
                              if len(health_prob) > 1 else u"est" +
                              health_prob[0])

            string = (u"%s de santé de la région %s. " % (
                sing_plur_subj, sing_plur_verb))
        else:
            string = ""

        return string

    @classmethod
    def _gen_primary_occup_fr(cls, cr, uid, project, context=None):
        """ Generate primary occupation and monthly income, check if need to
            round the income
        """
        primary_occup = [cls._get_translated_value(occup)
                         for occup in project.primary_occupation_ids]
        monthly_income = int(round(project.monthly_income))

        if primary_occup:
            if project.unemployment_rate > 0.5:
                string = (
                    u"La plupart des adultes sont sans emploi"
                    ", mais certains travaillent comme %s "
                    "et gagnent environ $%s par mois. " % (
                        primary_occup[0], monthly_income))
            else:
                string = (
                    u"La plupart des adultes travaillent comme %s et gagnent"
                    u" environ $%s par mois. " % (
                        primary_occup[0], monthly_income))
        else:
            string = (u"Le salaire moyen d'un travailleur est d'environ "
                      u"$%s par mois. " % monthly_income)

        return string

    @classmethod
    def _get_needs_pattern_fr(cls, cr, uid, project, context=None):
        """ Create the needs' description pattern to fill by hand
        """
        string = (u"Cette communauté a besoin (de...). Votre parrainage "
                  u"permet au personnel du centre d'accueil %s d'offrir à cet "
                  u"enfant (des enseignements bibliques...). (Des rencontres "
                  u"sont aussi organisées...)." % project.name)

        return string
