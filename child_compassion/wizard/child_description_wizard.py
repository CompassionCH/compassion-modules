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

from openerp import models, fields, api, exceptions, _
from child_description_fr import Child_description_fr
from child_description_de import Child_description_de
from child_description_en import Child_description_en
from child_description_it import Child_description_it
import re


class child_description_wizard(models.TransientModel):
    _name = 'child.description.wizard'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    child_id = fields.Many2one(
        'compassion.child', 'Child',
        default=lambda self: self.env.context.get('child_id'))
    keep_desc_fr = fields.Boolean('Update french description')
    desc_fr = fields.Html(
        'French description', default=lambda self: self._get_desc('fr'))
    keep_desc_de = fields.Boolean('Update german description')
    desc_de = fields.Html(
        'German description', default=lambda self: self._get_desc('de'))
    keep_desc_it = fields.Boolean('Update italian description')
    desc_it = fields.Html(
        'Italian description', default=lambda self: self._get_desc('it'))
    keep_desc_en = fields.Boolean('Update english description')
    desc_en = fields.Html(
        'English description', default=lambda self: self._get_desc('en'))
    child_property_value_ids = fields.Many2many(
        'compassion.translated.value', compute='_get_value_ids',
        inverse='_write_values', default=lambda self: self._get_value_ids())
    comments = fields.Text(
        'Comments', compute='_set_comments',
        default=lambda self: self._set_comments(), readonly=True)
    case_study_id = fields.Many2one(
        'compassion.child.property', 'Case Study',
        default=lambda self: self.env.context.get('property_id'))

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_value_ids(self):
        property_id = self.env.context.get('property_id')
        if not property_id:
            return False

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
        self.env.cr.execute(query)

        value_ids = [x[0] for x in self.env.cr.fetchall()]
        self.write({'child_property_value_ids': [(6, 0, value_ids)]})
        return value_ids

    def _write_values(self):
        # Values are automatically propagated into related objects
        return True

    @api.model
    def _get_desc(self, lang):
        child = self.env['compassion.child'].browse(
            self.env.context.get('child_id'))
        case_study = child.case_study_ids[0]
        res = False
        if lang == 'fr':
            res = Child_description_fr.gen_fr_translation(
                child, case_study)
        elif lang == 'de':
            res = Child_description_de.gen_de_translation(
                child, case_study)
        elif lang == 'it':
            res = Child_description_it.gen_it_translation(
                child, case_study)
        elif lang == 'en':
            res = Child_description_en.gen_en_translation(
                child, case_study)
        return res + '\n\n'     # Fix for displaying the textfield

    def _set_comments(self):
        child = self.env['compassion.child'].browse(
            self.env.context.get('active_id'))
        if child and child.case_study_ids:
            res = child.case_study_ids[0].comments
        else:
            res = False
        self.write({'comments': res})
        return res

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def generate_descriptions(self):
        self.ensure_one()
        child = self.child_id
        if not child:
            raise exceptions.Warning(
                'ObjectError',
                _('No valid child id given !'))
        case_study = child.case_study_ids[0]

        self.write({
            'desc_fr': Child_description_fr.gen_fr_translation(
                child, case_study),
            'desc_de': Child_description_de.gen_de_translation(
                child, case_study),
            'desc_en': Child_description_en.gen_en_translation(
                child, case_study),
            'desc_it': Child_description_it.gen_it_translation(
                child, case_study),
        })

        return {
            'name': _('Descriptions generation'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'auto_description_form',
            'view_type': 'form',
            'target': 'new',
        }

    @api.multi
    def validate_descriptions(self):
        self.ensure_one()
        vals = dict()
        p = re.compile(r'<.*?>')  # Remove HTML markers
        if self.keep_desc_fr:
            vals['desc_fr'] = p.sub('', self.desc_fr.strip('\n'))
        if self.keep_desc_de:
            vals['desc_de'] = p.sub('', self.desc_de.strip('\n'))
        if self.keep_desc_it:
            vals['desc_it'] = p.sub('', self.desc_it.strip('\n'))
        if self.keep_desc_en:
            vals['desc_en'] = p.sub('', self.desc_en.strip('\n'))

        if not vals:
            raise exceptions.Warning(
                'ValueError',
                _('No description selected. Please select one or click cancel'
                  'to abort current task.'))
        self.child_id.case_study_ids[0].write(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
