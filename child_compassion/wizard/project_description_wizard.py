# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Kevin Cristi, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
from project_description_fr import Project_description_fr
from project_description_de import Project_description_de
from project_description_it import Project_description_it


class project_description_wizard(orm.TransientModel):
    _name = 'project.description.wizard'

    def _get_project_id(self, cr, uid, context=None):
        # Retrieve the id of the project from context
        return context.get('active_id', False)

    def _get_value_ids(self, cr, uid, ids, fieldname, args, context=None):
        project_id = context.get('active_id')
        if not project_id:
            return {id: [] for id in ids}

        query = '''SELECT rel.value_id
                   FROM project_property_to_value as rel,
                        compassion_translated_value as val
                   WHERE rel.project_id = %s
                   AND rel.value_id = val.id
                   AND val.is_tag = false
                   AND (
                        val.value_fr is Null
                        OR val.value_de is Null
                        OR val.value_it is Null)
                   ORDER BY val.value_en, val.property_name''' % project_id
        cr.execute(query)
        value_ids = [x[0] for x in cr.fetchall()]
        return {id: value_ids for id in ids}

    def _get_default_ids(self, cr, uid, context=None):
        return self._get_value_ids(cr, uid, [0], '', '', context)[0]

    def _write_values(self, cr, uid, id, name, value, inv_arg, context=None):
        value_obj = self.pool.get('compassion.translated.value')
        for line in value:
            if line[0] == 1:  # on2many update
                value_id = line[1]
                value_obj.write(cr, uid, [value_id], line[2])
        return True

    def _get_needs(self, cr, uid, lang, context):
        """ Returns the needs descrption of the given language.
        It will either generate it from a pattern or retrieve the
        last saved description if one exist. """
        project = self.pool.get('compassion.project').browse(
            cr, uid, context.get('active_id'), context)
        res = False
        if lang == 'fr':
            res = project.needs_fr or \
                Project_description_fr._get_needs_pattern_fr(cr, uid, project,
                                                             context)
        elif lang == 'de':
            res = project.needs_de or \
                Project_description_de._get_needs_pattern_de(cr, uid, project,
                                                             context)
        elif lang == 'it':
            res = project.needs_it or \
                Project_description_it._get_needs_pattern_it(cr, uid, project,
                                                             context)

        return res + '\n\n'     # Fix for display of the textfield

    def _get_desc(self, cr, uid, lang, context):
        project = self.pool.get('compassion.project').browse(
            cr, uid, context.get('active_id'), context)
        res = False
        if lang == 'fr':
            res = Project_description_fr.gen_fr_translation(
                cr, uid, project, context)
        elif lang == 'de':
            res = Project_description_de.gen_de_translation(
                cr, uid, project, context)
        elif lang == 'it':
            res = Project_description_it.gen_it_translation(
                cr, uid, project, context)
        elif lang == 'en':
            res = project.description_en

        return res + '\n\n'     # Fix for display of the textfield

    _columns = {
        'project_id': fields.many2one('compassion.project', 'Project code'),
        # Complete descriptions
        'keep_desc_fr': fields.boolean(_('Update french description')),
        'keep_desc_de': fields.boolean(_('Update german description')),
        'keep_desc_it': fields.boolean(_('Update italian description')),
        'desc_fr': fields.text(_('French description')),
        'desc_de': fields.text(_('German description')),
        'desc_it': fields.text(_('Italian description')),
        'desc_en': fields.text(_('English description')),
        # Needs descriptions
        'needs_desc_fr': fields.text(_('French needs description')),
        'needs_desc_de': fields.text(_('German needs description')),
        'needs_desc_it': fields.text(_('Italian needs description')),
        'project_property_value_ids': fields.function(
            _get_value_ids, type='one2many',
            relation='compassion.translated.value',
            fnct_inv=_write_values),
    }

    _defaults = {
        'project_id': _get_project_id,
        'desc_fr': lambda self, cr, uid, context: self._get_desc(
            cr, uid, 'fr', context),
        'desc_de': lambda self, cr, uid, context: self._get_desc(
            cr, uid, 'de', context),
        'desc_it': lambda self, cr, uid, context: self._get_desc(
            cr, uid, 'it', context),
        'desc_en': lambda self, cr, uid, context: self._get_desc(
            cr, uid, 'en', context),
        'needs_desc_fr': lambda self, cr, uid, context: self._get_needs(
            cr, uid, 'fr', context),
        'needs_desc_de': lambda self, cr, uid, context: self._get_needs(
            cr, uid, 'de', context),
        'needs_desc_it': lambda self, cr, uid, context: self._get_needs(
            cr, uid, 'it', context),
        'project_property_value_ids': lambda self, cr, uid, context:
        self._get_default_ids(cr, uid, context),
    }

    def generate_descriptions(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids, context)[0]
        project = wizard.project_id

        desc_fr = Project_description_fr.gen_fr_translation(
            cr, uid, project, context)
        desc_de = Project_description_de.gen_de_translation(
            cr, uid, project, context)
        desc_it = Project_description_it.gen_it_translation(
            cr, uid, project, context)

        self.write(cr, uid, ids, {
            'desc_fr': desc_fr,
            'desc_de': desc_de,
            'desc_it': desc_it,
            'desc_en': project.description_en.replace(
                wizard.needs_desc_en, ''),
            }, context)

        return {
            'name': _('Descriptions generation'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': ids[0],
            'context': context,
            'target': 'new',
            }

    def validate_descriptions(self, cr, uid, ids, context=None):
        """ Save the selected descriptions in the project. """
        wizard = self.browse(cr, uid, ids, context)[0]
        vals = dict()
        if wizard.keep_desc_fr:
            vals['description_fr'] = wizard.desc_fr + \
                wizard.needs_desc_fr.strip('\n')
            vals['needs_fr'] = wizard.needs_desc_fr
        if wizard.keep_desc_de:
            vals['description_de'] = wizard.desc_de + \
                wizard.needs_desc_de.strip('\n')
            vals['needs_de'] = wizard.needs_desc_de
        if wizard.keep_desc_it:
            vals['description_it'] = wizard.desc_it + \
                wizard.needs_desc_it.strip('\n')
            vals['needs_it'] = wizard.needs_desc_it

        if not vals:
            raise orm.except_orm(
                'ValueError',
                _('No description selected. Please select one or click cancel'
                  ' to abort current task.'))
        wizard.project_id.write(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
