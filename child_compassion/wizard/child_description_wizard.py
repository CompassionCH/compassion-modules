# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Kevin Cristi
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
from child_description_fr import Child_description_fr
from child_description_de import Child_description_de


class child_description_wizard(orm.TransientModel):
    _name = 'child.description.wizard'

    def _get_value_ids(self, cr, uid, ids, fieldname, args, context=None):
        property_id = context.get('property_id')
        if not property_id:
            return {id: [] for id in ids}

        query = '''SELECT rel.value_id
                   FROM child_property_to_value as rel,
                        compassion_translated_value as val
                   WHERE rel.property_id = %s
                   AND rel.value_id = val.id
                   AND val.is_tag = false
                   AND (
                        val.value_fr is Null
                        OR val.value_de is Null
                        OR val.value_it is Null)
                   ORDER BY val.value_en, val.property_name''' % property_id
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
        'keep_desc_fr': fields.boolean(_('Keep french description')),
        'desc_fr': fields.text(_('French description')),
        'keep_desc_de': fields.boolean(_('Keep german description')),
        'desc_de': fields.text(_('German description')),
        'keep_desc_it': fields.boolean(_('Keep italian description')),
        'desc_it': fields.text(_('Italian description')),
        'keep_desc_en': fields.boolean(_('Keep english description')),
        'desc_en': fields.text(_('English description')),
        'child_property_value_ids': fields.function(
            _get_value_ids, type='one2many',
            relation='compassion.translated.value',
            fnct_inv=_write_values),
        'state': fields.selection(
            [('values', _('Values completion')),
             ('descriptions', _('Descriptions correction'))],
            _('State'), required=True, readonly=True),
    }

    _defaults = {
        'state': 'values',
        'keep_desc_fr': False,
        'keep_desc_de': False,
        'keep_desc_it': False,
        'keep_desc_en': False,
        'child_property_value_ids': lambda self, cr, uid, context:
        self._get_default_ids(cr, uid, context),
    }

    def generate_descriptions(self, cr, uid, ids, context=None):
        child_obj = self.pool.get('compassion.child')
        child = child_obj.browse(cr, uid, context.get('child_id'), context)
        if not child:
            raise orm.except_orm('ObjectError', _('No valid child id given !'))
        if isinstance(child, list):
            child = child[0]
        case_study = child.case_study_ids[-1]
        self.write(cr, uid, ids, {
            'state': 'descriptions',
            'desc_fr': Child_description_fr.gen_fr_translation(
                cr, uid, child, case_study, context),
            'desc_de': Child_description_de.gen_de_translation(
                cr, uid, child, case_study, context),
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
        wizard = self.browse(cr, uid, ids, context)[0]
        vals = {}
        if wizard.keep_desc_fr:
            vals['desc_fr'] = wizard.desc_fr
        if wizard.keep_desc_de:
            vals['desc_de'] = wizard.desc_de
        if wizard.keep_desc_it:
            vals['desc_it'] = wizard.desc_it
        if wizard.keep_desc_en:
            vals['desc_en'] = wizard.desc_en

        if not vals:
            raise orm.except_orm('ValueError',
                                 _('No description selected. \
                                 Please select one or click cancel '
                                   'to abort current task.'))
        child_obj = self.pool.get('compassion.child')
        child_obj.write(cr, uid, context['child_id'], vals, context)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def fields_view_get(self, cr, uid, view_id=None,
                        view_type='form', context=None,
                        toolbar=False, submenu=False):
        ret = super(child_description_wizard, self).fields_view_get(
            cr, uid, view_id, view_type,
            context, toolbar, submenu)
        fr, de, it, en = self._get_helps(cr, uid, context)
        ret['fields']['desc_fr']['help'] = fr
        ret['fields']['desc_de']['help'] = de
        ret['fields']['desc_it']['help'] = it
        ret['fields']['desc_en']['help'] = en
        return ret

    def _get_helps(self, cr, uid, context=None):
        if not context or not context.get('child_id'):
            return '', '', '', ''
        child_obj = self.pool.get('compassion.child')
        child = child_obj.browse(
            cr, uid, context['child_id'], context=context)[0]
        return child.desc_fr, child.desc_de, child.desc_it, child.desc_en
