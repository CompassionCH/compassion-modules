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

import pdb
import re
from openerp.osv import orm, fields
from openerp.tools.translate import _
from project_description_fr import Project_description_fr
from project_description_de import Project_description_de
from project_description_it import Project_description_it
import logging

logger = logging.getLogger(__name__)


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
        project_obj = self.pool.get('compassion.project')
        project = project_obj.browse(cr, uid, context.get('active_id'),
                                     context)
        if not project:
            raise orm.except_orm('ObjectError', _('No valid project id '
                                 'given !'))
        if isinstance(project, list):
            project = project[-1]

        remember_needs_en = (project_description_wizard._get_needs_en(
                             cr, uid, project, context))
        remember_needs_fr = (Project_description_fr._get_needs_pattern_fr(
                             cr, uid, context))
        remember_needs_de = (Project_description_de._get_needs_pattern_de(
                             cr, uid, context))
        remember_needs_it = (Project_description_it._get_needs_pattern_it(
                             cr, uid, context))
        keep_needs_en = keep_needs_fr = keep_needs_de = keep_needs_it = True

        if project.description_en:
            string = project.description_en
            match = re.search('per month.?\s?', string)
            remember_needs_en = string[match.end():]

        if project.description_fr:
            string = project.description_fr
            match = re.search('par mois.?\s?', string)
            remember_needs_fr = string[match.end():]

        if project.description_de:
            string = project.description_de
            match = re.search('pro Monat.?\s?', string)
            remember_needs_de = string[match.end():]

        if project.description_it:
            string = project.description_it
            match = re.search('mensile di.+?.\s', string)
            remember_needs_it = string[match.end():]

        self.write(cr, uid, ids, {
            'state': 'needs',
            'needs_desc_en': remember_needs_en,
            'needs_desc_fr': remember_needs_fr,
            'needs_desc_de': remember_needs_de,
            'needs_desc_it': remember_needs_it,
            'keep_needs_desc_en': keep_needs_en,
            'keep_needs_desc_fr': keep_needs_fr,
            'keep_needs_desc_de': keep_needs_de,
            'keep_needs_desc_it': keep_needs_it,
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
        project_id = ids
        project_obj = self.pool.get('compassion.project')
        project = project_obj.browse(cr, uid, context.get('active_id'),
                                     context)
        wizard = self.browse(cr, uid, ids, context)[0]
        if not project:
            raise orm.except_orm('ObjectError', _('No valid project '
                                                  'id given !'))
        if isinstance(project, list):
            project = project[-1]

        keep_desc_fr = keep_desc_de = keep_desc_it = True

        complete_desc_fr = project.description_fr
        complete_desc_de = project.description_de
        complete_desc_it = project.description_it

        if not project.description_fr:
            complete_desc_fr = (Project_description_fr.gen_fr_translation(
                                cr, uid, project_id, project, context) +
                                wizard.needs_desc_fr
                                if wizard.keep_needs_desc_fr else "")

        if not project.description_de:
            complete_desc_de = (Project_description_de.gen_de_translation(
                                cr, uid, project_id, project, context) +
                                wizard.needs_desc_de
                                if wizard.keep_needs_desc_de else "")

        if not project.description_it:
            complete_desc_it = (Project_description_it.gen_it_translation(
                                cr, uid, project_id, project, context) +
                                wizard.needs_desc_it
                                if wizard.keep_needs_desc_it else "")

        self.write(cr, uid, ids, {
            'state': 'descriptions',
            'desc_fr': complete_desc_fr,
            'desc_de': complete_desc_de,
            'desc_it': complete_desc_it,
            'keep_desc_fr': keep_desc_fr,
            'keep_desc_de': keep_desc_de,
            'keep_desc_it': keep_desc_it,
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

    @classmethod
    def _get_needs_en(cls, cr, uid, project, context=None):
        string = project.description_en
        match = re.search('per month.?\s?', string)
        return string[match.end():]

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
