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


class Project_description_it:

    @classmethod
    def gen_it_translation(
            cls, cr, uid, project, context=None):
        desc_it = cls._gen_intro_it(
            cr, uid, project, context)
        desc_it += cls._gen_build_mat_it(
            cr, uid, project, context)
        desc_it += cls._gen_primary_diet_it(
            cr, uid, project, context)
        desc_it += cls._gen_health_prob_it(
            cr, uid, project, context)
        desc_it += cls._gen_primary_occup_it(
            cr, uid, project, context)

        return desc_it

    @classmethod
    def _gen_list_string(cls, list, separator, last_separator):
        string = separator.join(list[:-1])
        if len(list) > 1:
            string += last_separator
        string += list[-1]

        return string

    @classmethod
    def _gen_intro_it(cls, cr, uid, project, context=None):
        """ Generate the project name, the localization and infos
            about the community
        """
        string = (u"Centro: %s-%s, %s.\nLuogo: %s, %s, %s.\n"
                  u"Questo bambino vive in una comunitá del %s dove "
                  u"risiendono circa %s abitanti." % (
                      project.code[:2].upper(), project.code[2:],
                      project.name, project.community_name,
                      project.distance_from_closest_city,
                      project.country_common_name,
                      project.community_name, project.community_population))

        return string

    @classmethod
    def _gen_build_mat_it(cls, cr, uid, project, context=None):
        """ Generate house build materials, there are no specificities
            in this part
        """
        floor_mat = [mat.value_it if mat.value_it else mat.value_en
                     for mat in project.floor_material_ids]
        wall_mat = [mat.value_it if mat.value_it else mat.value_en
                    for mat in project.wall_material_ids]
        roof_mat = [mat.value_it if mat.value_it else mat.value_en
                    for mat in project.roof_material_ids]

        materials = []
        if floor_mat:
            materials.append(u"il pavimento in %s" % floor_mat[0])
        if wall_mat:
            materials.append(u"le mura in %s" % wall_mat[0])
        if roof_mat:
            materials.append(u"il tetto in %s" % roof_mat[0])
        if materials:
            string = (u"Le case hanno " +
                      cls._gen_list_string(materials, ', ', ' e ') + ". ")
        else:
            string = ""

        return string

    @classmethod
    def _gen_primary_diet_it(cls, cr, uid, project, context=None):
        """ Generate spoken languages(s) and primary diet, there are
            no specificities in this part
        """
        primary_diet = [diet.value_it if diet.value_it else diet.value_en
                        for diet in project.primary_diet_ids]
        spoken_languages = [lang.value_it if lang.value_it else lang.value_en
                            for lang in project.spoken_languages_ids]

        if spoken_languages:
            string = u"La lingua parlata é il %s. " % (spoken_languages[0])
        else:
            string = ""

        string += (u"La dieta regionale consiste di: %s. " % (
                   cls._gen_list_string(primary_diet, ', ', ' e ')))

        return string

    @classmethod
    def _gen_health_prob_it(cls, cr, uid, project, context=None):
        """ Generate health problemes of this region, there
            are no specificities in this part
        """
        health_prob = [prob.value_it if prob.value_it else prob.value_en
                       for prob in project.health_problems_ids]

        if health_prob:
            sing_plur_subj = (u"Le malattie"
                              if len(health_prob) > 1 else u"La malattia")
            sing_plur_verb = (u"sono " +
                              cls._gen_list_string(health_prob, ', ', ' e ')
                              if len(health_prob) > 1 else u"è " +
                              health_prob[0])
            string = (u"%s piú comuni in questa zona %s. " % (sing_plur_subj,
                      sing_plur_verb))
        else:
            string = ""

        return string

    @classmethod
    def _gen_primary_occup_it(cls, cr, uid, project, context=None):
        """ Generate primary occupation and monthly income, check if need to
            round the income
        """
        primary_occup = [occup.value_it if occup.value_it else occup.value_en
                         for occup in project.primary_occupation_ids]
        monthly_income = int(round(project.monthly_income))

        if primary_occup:
            string = (u"La maggior parte degli adulti é disoccupata ma alcuni "
                      u"svolgono %s, con un guadagno mensile di $%s. " % (
                          primary_occup[0], monthly_income))
        else:
            string = (u"Lo stipendio medio di un operaio è di circa "
                      u"$%s al mese. " % monthly_income)

        return string

    @classmethod
    def _get_needs_pattern_it(cls, cr, uid, project, context=None):
        """ Create the needs' description pattern to fill by hand
        """
        string = (u"Questa comunitá ha bisogno di (...). Grazie al suo "
                  u"sostegno il personale del %s di (...) potrá "
                  u"offrire al bambino un'educazione cristiana, " +
                  "(...).") % (project.name)

        return string
