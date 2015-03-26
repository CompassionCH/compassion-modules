# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Kevin Cristi, David Coninckx
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
from child_description_fr import Child_description_fr
from child_description_de import Child_description_de
from child_description_en import Child_description_en
from child_description_it import Child_description_it
import re


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
                   -- AND (
                   --     val.value_fr is Null
                   --     OR val.value_de is Null
                   --     OR val.value_it is Null)
                   ORDER BY val.property_name, val.value_en''' % property_id
        cr.execute(query)

        value_ids = [x[0] for x in cr.fetchall()]
        return {id: value_ids for id in ids}

    def _get_default_ids(self, cr, uid, context=None):

        return self._get_value_ids(cr, uid, [0], '', '', context)[0]

    def _write_values(self, cr, uid, ids, name, value, inv_arg, context=None):
        value_obj = self.pool.get('compassion.translated.value')
        for line in value:
            if line[0] == 1:  # on2many update
                value_id = line[1]
                value_obj.write(cr, uid, [value_id], line[2])
        return True

    def _get_desc(self, cr, uid, lang, context):
        child = self.pool.get('compassion.child').browse(
            cr, uid, context.get('child_id'), context)
        case_study = child.case_study_ids[0]
        res = False
        if lang == 'fr':
            res = Child_description_fr.gen_fr_translation(
                cr, uid, child, case_study, context)
        elif lang == 'de':
            res = Child_description_de.gen_de_translation(
                cr, uid, child, case_study, context)
        elif lang == 'it':
            res = Child_description_it.gen_it_translation(
                cr, uid, child, case_study, context)
        elif lang == 'en':
            res = Child_description_en.gen_en_translation(
                cr, uid, child, case_study, context)
        return res + '\n\n'     # Fix for displaying the textfield

    def _get_comments(self, cr, uid, ids, fieldname, args, context=None):
        child = self.pool.get('compassion.child').browse(
            cr, uid, context.get('active_id'), context)
        if child and child.case_study_ids:
            res = child.case_study_ids[0].comments
        else:
            res = False
        return {id: res for id in ids}

    _columns = {
        'child_id': fields.many2one('compassion.child', 'Child'),
        'keep_desc_fr': fields.boolean(_('Update french description')),
        'desc_fr': fields.html(_('French description')),
        'keep_desc_de': fields.boolean(_('Update german description')),
        'desc_de': fields.html(_('German description')),
        'keep_desc_it': fields.boolean(_('Update italian description')),
        'desc_it': fields.html(_('Italian description')),
        'keep_desc_en': fields.boolean(_('Update english description')),
        'desc_en': fields.html(_('English description')),
        'child_property_value_ids': fields.function(
            _get_value_ids, type='one2many',
            relation='compassion.translated.value',
            fnct_inv=_write_values),
        'comments': fields.function(_get_comments, type='text',
                                    string=_('Comments'), readonly=True),
        'case_study_id': fields.many2one('compassion.child.property',
                                         'Case Study'),
    }

    _defaults = {
        'child_id': lambda self, cr, uid, context: context.get('child_id'),
        'case_study_id': lambda self, cr, uid, context: context.get(
            'property_id'),
        'keep_desc_fr': False,
        'keep_desc_de': False,
        'keep_desc_it': False,
        'keep_desc_en': False,
        'desc_fr': lambda self, cr, uid, context: self._get_desc(
            cr, uid, 'fr', context),
        'desc_de': lambda self, cr, uid, context: self._get_desc(
            cr, uid, 'de', context),
        'desc_en': lambda self, cr, uid, context: self._get_desc(
            cr, uid, 'en', context),
        'desc_it': lambda self, cr, uid, context: self._get_desc(
            cr, uid, 'it', context),
        'child_property_value_ids': lambda self, cr, uid, context:
        self._get_default_ids(cr, uid, context),
        'comments': lambda self, cr, uid, context:
        self._get_comments(cr, uid, [0], '', '', context)[0]
    }

    def generate_descriptions(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        child = wizard.child_id
        if not child:
            raise orm.except_orm('ObjectError', _('No valid child id given !'))
        case_study = child.case_study_ids[0]

        self.write(cr, uid, ids, {
            'desc_fr': Child_description_fr.gen_fr_translation(
                cr, uid, child, case_study, context),
            'desc_de': Child_description_de.gen_de_translation(
                cr, uid, child, case_study, context),
            'desc_en': Child_description_en.gen_en_translation(
                cr, uid, child, case_study, context),
            'desc_it': Child_description_it.gen_it_translation(
                cr, uid, child, case_study, context),
        }, context)

        return {
            'name': _('Descriptions generation'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'auto_description_form',
            'view_type': 'form',
            'context': context,
            'target': 'new',
        }

    def validate_descriptions(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids, context)[0]
        vals = dict()
        p = re.compile(r'<.*?>')  # Remove HTML markers
        if wizard.keep_desc_fr:
            vals['desc_fr'] = p.sub('', wizard.desc_fr.strip('\n'))
        if wizard.keep_desc_de:
            vals['desc_de'] = p.sub('', wizard.desc_de.strip('\n'))
        if wizard.keep_desc_it:
            vals['desc_it'] = p.sub('', wizard.desc_it.strip('\n'))
        if wizard.keep_desc_en:
            vals['desc_en'] = p.sub('', wizard.desc_en.strip('\n'))

        if not vals:
            raise orm.except_orm('ValueError',
                                 _('No description selected. \
                                 Please select one or click cancel '
                                   'to abort current task.'))
        wizard.child_id.case_study_ids[0].write(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
