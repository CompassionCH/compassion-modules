# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Kevin Cristi
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import re
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

    _columns = {
        'project_id': fields.many2one('compassion.project', 'Project code'),
        'keep_desc_fr': fields.boolean(_('Keep french description')),
        'desc_fr': fields.text(_('French description')),
        'keep_desc_de': fields.boolean(_('Keep german description')),
        'desc_de': fields.text(_('German description')),
        'keep_desc_it': fields.boolean(_('Keep italian description')),
        'desc_it': fields.text(_('Italian description')),
        'keep_desc_en': fields.boolean(_('Keep english description')),
        'desc_en': fields.text(_('English description')),
        'keep_needs_desc_en': fields.boolean(_('Keep english needs '
                                               'description')),
        'needs_desc_en': fields.text(_('English needs description')),
        'keep_needs_desc_fr': fields.boolean(_('Keep french needs '
                                               'description')),
        'needs_desc_fr': fields.text(_('French needs description')),
        'keep_needs_desc_de': fields.boolean(_('Keep german needs '
                                               'description')),
        'needs_desc_de': fields.text(_('German needs description')),
        'keep_needs_desc_it': fields.boolean(_('Keep italian needs '
                                               'description')),
        'needs_desc_it': fields.text(_('Italian needs description')),
        'project_property_value_ids': fields.function(
            _get_value_ids, type='one2many',
            relation='compassion.translated.value',
            fnct_inv=_write_values),
        'state': fields.selection(
            [('values', _('Values completion')),
             ('needs', _('Needs completion')),
             ('descriptions', _('Descriptions correction'))],
            _('State'), required=True, readonly=True),
    }

    _defaults = {
        'project_id': _get_project_id,
        'state': 'values',
        'keep_desc_fr': False,
        'keep_desc_de': False,
        'keep_desc_it': False,
        'keep_desc_en': False,
        'keep_needs_desc_fr': False,
        'keep_needs_desc_de': False,
        'keep_needs_desc_it': False,
        'keep_needs_desc_en': False,
        'project_property_value_ids': lambda self, cr, uid, context:
        self._get_default_ids(cr, uid, context),
    }

    def generate_needs_descriptions(self, cr, uid, ids, context=None):
        """ This method generates the last part, called "needs",
            of the project description.
            But if this part already exists, it will retrieve it.
        """
        project_obj = self.pool.get('compassion.project')
        project = project_obj.browse(cr, uid, context.get('active_id'),
                                     context)
        if not project:
            raise orm.except_orm('ObjectError', _('No valid project id '
                                 'given !'))
        if isinstance(project, list):
            project = project[-1]

        if project.description_en:
            string = project.description_en
            match = re.search('per month.?\s?', string)
            needs_en = string[match.end():]

        if project.needs_fr:
            remember_needs_fr = project.needs_fr
        else:
            remember_needs_fr = (
                Project_description_fr._get_needs_pattern_fr(
                    cr, uid, project, context))

        if project.needs_de:
            remember_needs_de = project.needs_de
        else:
            remember_needs_de = (
                Project_description_de._get_needs_pattern_de(
                    cr, uid, project, context))

        if project.needs_it:
            remember_needs_it = project.needs_it
        else:
            remember_needs_it = (
                Project_description_it._get_needs_pattern_it(
                    cr, uid, project, context))

        self.write(cr, uid, ids, {
            'state': 'needs',
            'needs_desc_en': needs_en,
            'needs_desc_fr': remember_needs_fr,
            'needs_desc_de': remember_needs_de,
            'needs_desc_it': remember_needs_it,
            'keep_needs_desc_fr': True,
            'keep_needs_desc_de': True,
            'keep_needs_desc_it': True,
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

    def generate_descriptions(self, cr, uid, ids, context=None):
        project_obj = self.pool.get('compassion.project')
        project = project_obj.browse(cr, uid, context.get('active_id'),
                                     context)
        wizard = self.browse(cr, uid, ids, context)[0]
        if not project:
            raise orm.except_orm('ObjectError', _('No valid project '
                                                  'id given !'))
        if isinstance(project, list):
            project = project[-1]

        complete_desc_fr = self._get_needs_desc(
            wizard.needs_desc_fr, wizard.keep_needs_desc_fr,
            project.description_fr,
            Project_description_fr.gen_fr_translation(cr, uid,
                                                      project, context))

        complete_desc_de = self._get_needs_desc(
            wizard.needs_desc_de, wizard.keep_needs_desc_de,
            project.description_de,
            Project_description_de.gen_de_translation(cr, uid,
                                                      project, context))

        complete_desc_it = self._get_needs_desc(
            wizard.needs_desc_it, wizard.keep_needs_desc_it,
            project.description_it,
            Project_description_it.gen_it_translation(cr, uid,
                                                      project, context))

        project.write({
            'needs_fr': wizard.needs_desc_fr,
            'needs_de': wizard.needs_desc_de,
            'needs_it': wizard.needs_desc_it,
            })

        self.write(cr, uid, ids, {
            'state': 'descriptions',
            'desc_fr': complete_desc_fr,
            'desc_de': complete_desc_de,
            'desc_it': complete_desc_it,
            'keep_desc_fr': True,
            'keep_desc_de': True,
            'keep_desc_it': True,
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

    def _get_needs_desc(self, needs, keep_needs, desc, desc_trans):
        """ This method:
            - display a pattern of "project needs" of the project
              description (it's a cloze text to fill in).
            - store the modified pattern
            - verify if checkboxes about "project needs" are checked
            - verify if "project needs" fields are filled
            - return the appropriate project description
        """
        if not desc:
            if ((keep_needs and not needs) or (keep_needs and
               (needs in desc_trans)) or not keep_needs):
                complete_desc = desc_trans
            else:
                complete_desc = desc_trans + needs
        elif not keep_needs:
            complete_desc = desc
        else:
            try:
                complete_desc = desc + needs
            except TypeError:
                complete_desc = desc
        return complete_desc

    def validate_descriptions(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids, context)[0]
        vals = {}
        if wizard.keep_desc_fr:
            vals['description_fr'] = wizard.desc_fr
        if wizard.keep_desc_de:
            vals['description_de'] = wizard.desc_de
        if wizard.keep_desc_it:
            vals['description_it'] = wizard.desc_it
        if wizard.keep_desc_en:
            vals['description_en'] = wizard.desc_en

        if not vals:
            raise orm.except_orm('ValueError',
                                 _('No description selected. \
                                 Please select one or click cancel '
                                   'to abort current task.'))
        wizard.project_id.write(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
