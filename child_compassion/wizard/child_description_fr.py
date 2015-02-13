# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester , Kevin Cristi
#
#    The licence is in the file __openerp__.py
#
##############################################################################


class Child_description_fr:

    @classmethod
    def gen_fr_translation(
            cls, cr, uid, child, case_study, context=None):
        desc_fr = cls._get_guardians_info_fr(
            cr, uid, child, case_study, context)
        desc_fr += cls._get_parents_info(
            cr, uid, child, case_study, context)
        desc_fr += cls._get_school_info_fr(
            cr, uid, child, case_study, context)
        desc_fr += cls._gen_christ_act_fr(cr, uid, child, case_study, context)
        desc_fr += cls._gen_family_act_info_fr(
            cr, uid, child, case_study, context)
        desc_fr += cls._gen_hobbies_info_fr(
            cr, uid, child, case_study, context)
        return desc_fr

    @classmethod
    def _gen_list_string(cls, list):
        string = ', '.join(list[:-1])
        if len(list) > 1:
            string += ' et '
        string += list[-1]
        return string

    @classmethod
    def _gen_christ_act_fr(cls, cr, uid, child, case_study, context=None):
        ''' Generate the christian activities description part.
            Words as 'à', 'aux', ... are included in value_fr field.
        '''
        if not case_study.christian_activities_ids:
            return ''
        activities = [
            activity.value_fr if activity.value_fr else activity.value_en
            for activity in case_study.christian_activities_ids]
        activities_str = cls._gen_list_string(activities)
        string = u"A l'Église, %s participe %s. " % (
            child.firstname, activities_str)
        return string

    @classmethod
    def _gen_family_act_info_fr(
            cls, cr, uid, child, case_study, context=None):
        ''' Generate the family duties description part. There are 2 kind of
            activities:
             - Standards : introduced by 'aide à faire' and having
                the determinant in value_fr
             - Specials : having the action verb included in value_fr
        '''
        if not case_study.family_duties_ids:
            return ''
        specials = ['carries water', 'animal care', 'running errands',
                    'buying/selling in market'
                    'gathers firewood', 'teaching others']
        activities = [activity.value_fr if activity.value_fr
                      else activity.value_en
                      for activity in case_study.family_duties_ids
                      if activity.value_en not in specials]
        if len(activities):
            activities[0] = u'aide à faire %s' % activities[0]
        activities.extend([activity.value_fr if activity.value_fr
                           else activity.value_en
                           for activity in case_study.family_duties_ids
                           if activity.value_en in specials])
        activities_str = cls._gen_list_string(activities)
        string = u"A la maison, %s %s. " % (child.firstname, activities_str)
        return string

    @classmethod
    def _gen_hobbies_info_fr(cls, cr, uid, child, case_study, context=None):
        ''' Generate the hobbies description part.
             There are 2 kind of hobbies :
             - games, which are introduced by 'jouer' and having
                the determinant included in value_fr
             - verbs, which are simply printed without any decoration.
        '''
        if not case_study.hobbies_ids:
            return ''
        verbs = ['art/drawing', 'bicycling', 'jump rope', 'listening to music'
                 'musical instrument', 'reading', 'running'
                 'singing', 'story telling', 'swimming', 'walking']
        activities = [activity.value_fr if activity.value_fr
                      else activity.value_en
                      for activity in case_study.hobbies_ids
                      if activity.value_en not in verbs]
        if len(activities):
            activities[0] = u'jouer %s' % activities[0]
        activities.extend([activity.value_fr if activity.value_fr
                           else activity.value_en
                           for activity in case_study.hobbies_ids
                           if activity.value_en in verbs])
        activities_str = cls._gen_list_string(activities)
        string = u"%s aime beaucoup %s. " % ('Il' if child.gender == 'M'
                                             else 'Elle', activities_str)
        return string

    @classmethod
    def _get_school_info_fr(cls, cr, uid, child, case_study, context=None):
        ''' Generate the school description part. Description includes :
             - If child is attending school
             - Reason why not attending school if relevant and existing
             - US school level if relevant
             - School performance if relevant and existing
             - School favourite subject if relevant and existing
        '''
        ordinals = {
            '1': u'première',
            '2': u'deuxième',
            '3': u'troisième',
            '4': u'quatrième',
            '5': u'cinquième',
            '6': u'sixième',
            '7': u'septième',
            '8': u'huitième',
            '9': u'neuvième',
            '10': u'dixième',
            '11': u'onzième',
            '12': u'douzième',
            '13': u'treizième',
            '14': u'quatorzième',
            'PK': u'première enfantine',
            'K': u'deuxième enfantine',
            'P': u'primaire',
        }
        # the value of us_school_level can also be blank
        string = u'Il' if child.gender == 'M' else u'Elle'
        if case_study.attending_school_flag:
            if (case_study.us_school_level and case_study.us_school_level in
                    ordinals):
                try:
                    int(case_study.us_school_level)
                    string += (u' est en %s année (US)'
                               % ordinals[case_study.us_school_level])
                except:
                    string += (u' est en %s (US)'
                               % ordinals[case_study.us_school_level])
            else:
                string += u" va à l'école"
            if case_study.school_performance:
                string += u' et %s a des résultats %s. ' % (
                    child.firstname,
                    case_study.school_performance[0].value_fr or
                    case_study.school_performance[0].value_en)
            elif case_study.school_best_subject:
                string += u' et aime bien %s. ' \
                          % (case_study.school_best_subject[0].value_fr or
                             case_study.school_best_subject[0].value_en)
            else:
                string += '.'
        else:
            string += u" ne va pas à l'école"  # TODO reason
        return string

    @classmethod
    def _get_guardians_info_fr(cls, cr, uid, child, case_study, context=None):
        ''' Generate the guardian description part. Guardians jobs are
            also included here.
        '''
        if not case_study.guardians_ids:
            return ''
        male_values = ['father', 'uncle', 'brother', 'grandfather',
                       'stepfather', 'godfather']
        plur_values = ['friends', 'other relatives', 'foster parents']
        live_with = []
        male_guardian = dict()
        female_guardian = dict()
        for guardian in case_study.guardians_ids:
            value = (guardian.value_fr if guardian.value_fr
                     else guardian.value_en)
            if guardian.value_en in male_values:
                live_with.append(u'son %s' % value)
                male_guardian = [guardian.value_en, value]
            elif guardian.value_en in plur_values:
                live_with.append(u'des %s' % value)
            else:
                if female_guardian == 'institutional worker':
                    live_with.append(u'un institut')  # find better "institut"
                else:
                    if value == 'institutional worker':
                        live_with.append(u'un institut')
                        female_guardian = [guardian.value_en, value]
                    else:
                        live_with.append(u'sa %s' % value)
                        female_guardian = [guardian.value_en, value]
        if case_study.nb_brothers == 1:
            live_with.append(u'son frère')
        elif case_study.nb_brothers > 1:
            live_with.append(u'ses %s frères' % case_study.nb_brothers)
        if case_study.nb_sisters == 1:
            live_with.append(u'sa soeur')
        elif case_study.nb_sisters > 1:
            live_with.append(u'ses %s soeurs' % case_study.nb_sisters)
        if 'un institut' in live_with:
            guardian_str = '%s avec %s' % (live_with[0], live_with[1])
        else:
            guardian_str = cls._gen_list_string(live_with)
        if 'institut' in guardian_str:
            string = '%s vit dans %s. ' % (child.firstname, guardian_str)
        else:
            string = '%s vit avec %s. ' % (child.firstname, guardian_str)

        string += cls._get_guardians_jobs_fr(cr, uid, child, case_study,
                                             male_guardian, female_guardian,
                                             context)
        return string

    @classmethod
    def _get_parents_info(cls, cr, uid, child,
                          case_study, context=None):
        string = u''

        props_m = [tag.value_en for tag in case_study.father_ids]
        props_f = [tag.value_en for tag in case_study.mother_ids]
        props_mf = set(props_m) & set(props_f)
        props = [props_m, props_f, props_mf]

        # Father info
        string += cls._get_parent_info_string(cr, uid, props, 0, context)

        # Mother info
        string += cls._get_parent_info_string(cr, uid, props, 1, context)

        # Parents info
        string += cls._get_parent_info_string(cr, uid, props, 2, context)

        return string

    @classmethod
    def _get_parent_info_string(cls, cr, uid, props, type, context=None):
        string = u''

        prefix = [u'Son père', u'Sa mère', u'Ses parents']
        be = [u'est', u'est', u'sont']
        dead = [u'est décédé', u'est décédée', u'sont décédés']
        support = [u'soutient financièrement la famille',
                   u'soutient financièrement la famille',
                   u'soutiennent financièrement la famille']

        status_tags = {
            u'inprison': [u'en prison', u'en prison', u'en prison'],
            u'mentallyill': [u'mentalement malade',
                             u'mentalement malade',
                             u'mentalement malades'],
            u'chronicallyill': [u'chroniquement malade',
                                u'chroniquement malade',
                                u'chroniquement malades'],
            u'handicapped': [u'handicapé', u'handicapée', u'handicapés'],
        }

        multiple_status = False

        for prop in props[type]:
            if prop in status_tags:
                if not multiple_status:
                    string += u'{} {} {}'.format(
                        prefix[type], be[type], status_tags[prop][type])
                    multiple_status = True
                else:
                    string += u' et {}'.format(status_tags[prop])
        if (type == 2):
            if ('alive' not in props[0] and
               'alive' not in props[1]):
                string = u'{} {}'.format(prefix[type], dead[type])
            if 'supportingchild' in props[type] and \
               'livingwithchild' not in props[0] and \
               'livingwithchild' not in props[1]:
                string += u'{} {}'.format(prefix[type], support[type])
        else:
            if 'supportingchild' in props[type] and \
               'livingwithchild' not in props[type]:
                string += u'{} {}'.format(prefix[type], support[type])
            if ('alive' not in props[type] and type != 2):
                string = u'{} {}'.format(prefix[type], dead[type])

        if string:
            string += u'. '
        return string

    @classmethod
    def _get_guardians_jobs_fr(cls, cr, uid, child,
                               case_study, m_g, f_g, context=None):
        ''' Generate the guardians jobs description part. '''

        if case_study.male_guardian_ids or case_study.female_guardian_ids:

            props_en_m = [emp.value_en for emp in case_study.male_guardian_ids]
            props_en_f = [
                emp.value_en for emp in case_study.female_guardian_ids]
            props_en_mf = list(set(props_en_m) & set(props_en_f))
            props_en = [props_en_m, props_en_f, props_en_mf]

            props_fr_m = [emp.value_fr for emp in case_study.male_guardian_ids]
            props_fr_f = [
                emp.value_fr for emp in case_study.female_guardian_ids]
            props_fr_mf = list(set(props_fr_m) & set(props_fr_f))
            props_fr_mf = props_fr_mf + \
                [False] * (len(props_en_mf) - len(props_fr_mf))
            props_fr = [props_fr_m, props_fr_f, props_fr_mf]

            string = u""
            # Male job
            string += cls._get_guardian_job_string(
                cr, uid, props_en, props_fr, m_g, f_g, 0, context)

            # Female job
            string += cls._get_guardian_job_string(
                cr, uid, props_en, props_fr, m_g, f_g, 1, context)

            # Same job
            string = cls._get_guardian_job_string(
                cr, uid, props_en, props_fr, m_g, f_g, 2, context) or string

        return string

    @classmethod
    def _get_mf_g(cls, cr, uid, m_g, f_g, context=None):
        mf_g = u''

        if (f_g[0] == u'grandmother' and m_g[0] == u'grandfather'):
            mf_g = u'Ses grand-parents'
        elif (f_g[0] == u'mother' and m_g[0] == u'father'):
            mf_g = u'Ses parents'
        else:
            mf_g = u'Son {} et sa {}'.format(m_g[1], f_g[1])

        return mf_g

    @classmethod
    def _get_guardian_job_string(
            cls, cr, uid, props_en, props_fr,
            m_g, f_g, type, context=None):
        string = u''

        prefix_f = u'Sa {}'.format(f_g[1]) if f_g else None
        prefix_m = u'Son {}'.format(m_g[1])if m_g else None
        prefix_mf = cls._get_mf_g(
            cr, uid, m_g, f_g, context) if f_g and m_g else None

        prefix = [prefix_m, prefix_f, prefix_mf]

        work_as = [
            u'travaille comme', u'travaille comme', u'travaillent comme']
        is_employed = [u'est employé', u'est employée', u'sont employés']
        is_unemployed = [
            u"n'a pas d'emploi", u"n'a pas d'emploi", u"n'ont pas d'emploi"]

        job_tags_work_as = {
            'isafarmer': [u'fermier', u'fermière', u'fermiers'],
            'isateacher': [u'enseignant', u'enseignante', u'enseignants'],
            'sellsinmarket': [u'vendeur au marché',
                              u'vendeuse au marché',
                              u'vendeurs au marché'],
        }
        job_tags_isemployed = {
            'isachurchworker': u'à l\'église',
            'isaprojectworker': u'au centre d\'accueil',
        }
        # laborer_tag = {
        # 'isalaborer': [u'est ouvrier', u'est ouvrière', u'sont ouvriers']
        # }
        unconsidered_tag = [u'isattimesemployed', u'isemployed']

        # Case unemployed
        if ('isunemployed' in props_en[type]):
            string += u'{} {}'.format(prefix[type], is_unemployed[type])
        else:
            multiple_job_work_as = False
            for job_tag_work_as in job_tags_work_as:
                if job_tag_work_as in props_en[type]:
                    # Multiple job check
                    if not multiple_job_work_as:
                        string += u'{} {} {}'.format(
                            prefix[type], work_as[type],
                            job_tags_work_as[job_tag_work_as][type])
                        multiple_job_work_as = True
                    else:
                        string += u' et {}'.format(
                            job_tags_work_as[job_tag_work_as][type])

            multiple_job_isemployed = False
            for job_tag_isemployed in job_tags_isemployed:
                if job_tag_isemployed in props_en[type]:
                    # Multiple job check
                    if (not multiple_job_isemployed and not
                       multiple_job_work_as):
                        string += u'{} {} {}'.format(
                            prefix[type], is_employed[type],
                            job_tag_isemployed[type])
                        multiple_job_isemployed = True
                    else:
                        string += u' et {}'.format(job_tag_isemployed[type])

            multiple_job = False
            for prop in props_en[type]:
                if (prop not in unconsidered_tag and
                   prop not in job_tags_work_as and
                   prop not in job_tags_isemployed):
                    # Multiple job check
                    if (not multiple_job_work_as and not
                       multiple_job_isemployed and
                       multiple_job):
                            string += prefix[type]
                            multiple_job = True
                    else:
                        string += u' et'

                    string += u' {}'.format(
                        props_fr[type][props_en[type].index(prop)] or prop)

        if string:
            string += u'. '

        return string
