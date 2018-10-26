# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo import api, models, fields


COLOR_SEQUENCE = [
    'darkblue',
    'darkred',
    'darkgreen',
    'darkslateblue',
    'firebrick',
    'mediumorchid',
    'orangered',
    'saddlebrown',
    'seagreen',
    'tomato',
    'darkslategrey',
    'blueviolet',
    'burlywood',
    'cadetblue',
    'coral',
    'darksalmon',
    'goldenrod',
]


class CommunicationKeyword(models.Model):
    _name = 'partner.communication.keyword'
    _description = 'Communication keyword'
    _order = 'is_visible desc,position asc'

    name = fields.Char(help='Friendly name for the keyword')
    revision_id = fields.Many2one(
        'partner.communication.revision',
        'Template',
        required=True,
        ondelete='cascade'
    )
    type = fields.Selection(
        [('if', 'If Condition'),
         ('var', 'Variable'),
         ('code', 'Keyword'),
         ('for', 'Loop'),
         ('for_ul', 'Loop'),
         ],
        readonly=True
    )
    raw_code = fields.Char(
        required=True,
        help='contains the raw template code, for instance : '
             '* %if object.test_value:'
             '* %for test in  object.tests:'
             '* ${object.variable}'
             '* % set variable = object.variable'
    )
    short_code = fields.Char(
        compute='_compute_short_code', store=True,
        inverse='_inverse_short_code')
    html_id = fields.Char()
    replacement = fields.Char(
        compute='_compute_replacement',
        help='HTML replacement for the simplified text'
    )
    is_visible = fields.Boolean(
        compute='_compute_is_visible', store=True,
        help='Is the keyword visible in the simple text?'
    )
    position = fields.Integer(
        help='Position in the original mail.template text'
    )
    index = fields.Integer(
        help='Counts the number of keywords of the same type in the revision'
    )
    nested_position = fields.Integer(
        help='Counts the nested if or for, to recover them in order'
    )
    true_text = fields.Text(
        help='Text to display when the if-clause is true'
    )
    false_text = fields.Text(
        help='Text to display when the if-clause is false')
    final_text = fields.Text(
        help='Final text for using in the mail.template',
        compute='_compute_final_text'
    )
    edit_value = fields.Boolean(
        default=True,
        help='Set this value to true or false to edit the corresponding '
             'part of the text on the template.'
    )
    edit_changed = fields.Integer(
        readonly=True,
        help='Internally used to check if edit value has been changed.'
    )
    color = fields.Char()

    _sql_constraints = [
        ('unique_keyword', 'unique(raw_code,type,index,revision_id)',
         'this keyword already exists')
    ]

    @api.multi
    @api.depends('raw_code')
    def _compute_short_code(self):
        for keyword in self:
            if keyword.type == 'var':
                raw = keyword.raw_code.split('=')[0].split('% set ')[-1]
                keyword.short_code = 'var-' + raw.strip().replace('.', '-')
            else:
                raw = keyword.raw_code
                if keyword.type in ('if', 'for', 'for_ul'):
                    raw = raw.split(' ')[2]
                if 'get_list(' in raw or 'get(' in raw or 'mapped(' in raw:
                    # Methods taking a field as parameter, we use the field as
                    # shortcode
                    match = re.search(r"(get|get_list|mapped)\('(.*?)'", raw)
                    keyword.short_code = match.group(2).split(
                        '.')[-1].replace(' ', '_')
                else:
                    if 'if' in raw:
                        # Takes one of the side of the clause
                        parts = raw.strip('${}').split(' if ')
                        raw = parts[0].strip("'") or parts[1].split(
                            'else ')[-1].strip("'")
                    match = re.search(r"\w+", raw.split('.')[-1])
                    keyword.short_code = match.group(0)

    @api.multi
    def _inverse_short_code(self):
        return True

    @api.multi
    def _compute_final_text(self):
        for keyword in self:
            if keyword.type == 'if':
                final_text = u'\n' + keyword.raw_code + u'\n\t' + \
                    keyword.true_text
                if keyword.false_text:
                    final_text += u'\n\t% else:\n\t' + keyword.false_text
                final_text += u'\n% endif \n'
                keyword.final_text = final_text
            elif 'for' in keyword.type:
                final_text = u'\n' + keyword.raw_code + u'\n\t' + \
                    keyword.true_text
                final_text += u'\n% endfor \n'
                if keyword.type == 'for_ul':
                    final_text = u'<ul>{}</ul>'.format(final_text)
                keyword.final_text = final_text
            elif keyword.type == 'var':
                keyword.final_text = u'\n' + keyword.raw_code + u'\n'
            else:
                keyword.final_text = keyword.raw_code

    @api.multi
    def _compute_replacement(self):
        for keyword in self:
            if keyword.type in ('if', 'for'):
                s = u'<span id="{}" style="color: {};">{}</span>'
                keyword.replacement = s.format(
                    keyword.html_id, keyword.color, keyword.get_text())
            elif keyword.type == 'for_ul':
                s = u'<ul id="{}" style="color: {};">{}</ul>'
                keyword.replacement = s.format(
                    keyword.html_id, keyword.color, keyword.get_text())
            elif keyword.type == 'var':
                keyword.replacement = u'<span id="{}"></span>'.format(
                    keyword.html_id)
            elif keyword.type == 'code':
                s = u'<span id="{}" style="color: white; background-color: ' \
                    u'{};">[{}]</span>'
                keyword.replacement = s.format(
                    keyword.html_id, keyword.color, keyword.short_code)

    @api.depends('revision_id.simplified_text')
    @api.multi
    def _compute_is_visible(self):
        filter_html = re.compile(r'<.*?>')
        for keyword in self.filtered('revision_id.simplified_text'):
            if keyword.type in ('if', 'for', 'for_ul'):
                visible_text = keyword.get_text()
            else:
                visible_text = filter_html.sub('', keyword.replacement)
            keyword.is_visible = visible_text and visible_text in \
                keyword.revision_id.simplified_text

    @api.model
    def create(self, vals):
        """ Assign color at creation. """
        count = self.search_count([
            ('revision_id', '=', vals['revision_id']),
            ('type', '=', vals['type'])
        ])
        vals['index'] = count + 1
        if 'color' not in vals:
            vals['color'] = COLOR_SEQUENCE[count % len(COLOR_SEQUENCE)]
        keyword = super(CommunicationKeyword, self).create(vals)
        # Define html_id once
        keyword.html_id = str(count+1) + '-' + keyword.short_code
        return keyword

    @api.multi
    def unlink(self):
        # Update indexes
        other_kw = self.env[self._name]
        for keyword in self:
            other_kw |= self.search([
                ('type', '=', keyword.type),
                ('revision_id', '=', keyword.revision_id.id),
                ('index', '>', keyword.index),
                ('id', 'not in', self.ids)
            ])
        res = super(CommunicationKeyword, self).unlink()
        for keyword in other_kw.sorted('index'):
            keyword.index -= 1
        return res

    @api.multi
    def toggle_edit_value(self):
        set_true = self.search([
            ('id', 'in', self.ids),
            ('type', '=', 'if'),
            ('edit_value', '=', False)])
        set_false = (self - set_true).filtered(lambda k: k.type == 'if')
        vals = {'edit_value': True}
        for keyword in set_true:
            vals['edit_changed'] = keyword.edit_changed + 1
            keyword.write(vals)
        vals['edit_value'] = False
        for keyword in set_false:
            vals['edit_changed'] = keyword.edit_changed + 1
            keyword.write(vals)
        return True

    @api.multi
    def set_text(self, text, edit_value):
        """
        Used to set the text in the right if clause
        :param text: The text to save
        :param edit_value: True for setting true_text / False for false_sext
        :return: None
        """
        self.ensure_one()
        if text == "[{}]".format(self.short_code):
            text = False
        field = 'true_text' if (edit_value or
                                'for' in self.type) else 'false_text'
        return self.write({field: text and text.strip('[]')})

    @api.multi
    def get_text(self):
        """ Returns the text of the clause depending on its edit_value. """
        self.ensure_one()
        if self.edit_value or 'for' in self.type:
            return self.true_text
        else:
            return self.false_text or "[{}]".format(self.short_code)
