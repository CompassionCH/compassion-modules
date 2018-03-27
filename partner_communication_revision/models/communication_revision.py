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
import regex as re

from odoo import api, models, _, fields
from odoo.exceptions import UserError

try:
    from pyquery import PyQuery
    from bs4 import BeautifulSoup
except ImportError:
    raise UserError(_("Please install python pyquery and bs4"))


def safe_replace(original, to_replace, replacement):
    """
    Utility that will replace the string except in the HTML tag attributes
    :param original: original string
    :param to_replace: string to replace
    :param replacement: replacement string
    :return: new string with the replacement done
    """
    def _replace(match):
        if match.group(1):
            return match.group(0)
        else:
            return replacement
    replace_regex = re.escape(to_replace.replace('\\', ''))
    in_attr = r'((?:<[^<>]*?"[^<>]*?){1}' + replace_regex + \
        r'(?:[^<>]*?"[^<>]*?>){1})'
    regex = in_attr + r'|(' + replace_regex + r')'
    return re.sub(regex, _replace, original)


class CommunicationRevision(models.Model):
    _name = 'partner.communication.revision'
    _rec_name = 'config_id'
    _description = 'Communication template revision'
    _order = 'config_id asc,revision_number desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    config_id = fields.Many2one(
        'partner.communication.config',
        'Communication type',
        required=True,
        ondelete='cascade'
    )
    model = fields.Char(related='config_id.model_id.model', readonly=True)
    lang = fields.Selection('select_lang', required=True)
    revision_number = fields.Float(default=1.0)
    revision_date = fields.Date(default=fields.Date.today())
    body_html = fields.Html(related='config_id.email_template_id.body_html')
    simplified_text = fields.Html(sanitize=False)
    preview_text = fields.Html()
    keyword_ids = fields.One2many(
        'partner.communication.keyword', 'revision_id', 'Keywords'
    )
    edit_keyword_ids = fields.One2many(
        'partner.communication.keyword',
        compute='_compute_keyword_ids', inverse='_inverse_keyword_ids',
        string='Keywords'
    )
    if_keyword_ids = fields.One2many(
        'partner.communication.keyword',
        compute='_compute_keyword_ids', inverse='_inverse_keyword_ids',
        string='Conditional text'
    )
    for_keyword_ids = fields.One2many(
        'partner.communication.keyword',
        compute='_compute_keyword_ids', inverse='_inverse_keyword_ids',
        string='Loops'
    )

    _sql_constraints = [
        ('unique_revision', 'unique(config_id,lang)',
         'You can only have one revision per language'),
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def select_lang(self):
        langs = self.env['res.lang'].search([])
        return [(lang.code, lang.name) for lang in langs]

    @api.multi
    def _compute_keyword_ids(self):
        for revision in self:
            revision.edit_keyword_ids = revision.keyword_ids.filtered(
                lambda k: k.type == 'code' and k.is_visible)
            revision.if_keyword_ids = revision.keyword_ids.filtered(
                lambda k: k.type == 'if' and k.is_visible)
            revision.for_keyword_ids = revision.keyword_ids.filtered(
                lambda k: 'for' in k.type and k.is_visible)

    @api.multi
    def _inverse_keyword_ids(self):
        return True

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        """
        Push back the enhanced text in translation of the mail.template.
        Update revision date and number depending on edit mode.
        """
        if 'simplified_text' not in vals or self.env.context.get('no_update'):
            return super(CommunicationRevision, self).write(vals)

        for revision in self.filtered('simplified_text'):
            super(CommunicationRevision, revision).write(vals)

            # 2. Push back the template text
            # Set the conditionals texts
            revision.with_context(save_mode=True).refresh_text()
            translation = self.env['ir.translation'].search([
                ('lang', '=', revision.lang),
                ('name', 'like', 'body_html'),
                ('res_id', '=', revision.config_id.email_template_id.id)
            ])
            translation.value = revision._enhance_text()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def edit_revision(self):
        """
        View helper to open a revision in edit mode.
        This will increment a small step in the
        revision number but not change the revision date.
        :return: action window
        """
        self.ensure_one()
        new_revision_number = self.revision_number + 0.01
        self.revision_number = new_revision_number
        return self._open_revision()

    @api.multi
    def new_revision(self):
        """
        View helper to open a revision in edit mode.
        This will increase the revision number and the date meaning we will
        modify the text model more than just a few corrections.
        :return: action window
        """
        self.ensure_one()
        this_revision_number = self.revision_number + 1.0
        current_revision_number = self.config_id.revision_number
        new_revision_number = max([
            this_revision_number, current_revision_number])
        revision_vals = {
            'revision_number': int(new_revision_number),
            'revision_date': fields.Date.today()
        }
        if new_revision_number > current_revision_number:
            self.config_id.write(revision_vals)
        self.write(revision_vals)
        return self._open_revision()

    @api.multi
    def show_revision(self):
        self.ensure_one()
        return self._open_revision(readonly=True)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def refresh_text(self):
        """
        Save the current text in the if clause and refresh the selected
        clauses.
        """
        text = PyQuery(self.simplified_text)
        for key in self.keyword_ids.filtered(
                lambda k: k.type in ('if', 'for', 'for_ul')):
            text_selector = text('#' + key.html_id)
            current_text = text_selector.html()
            # Save the current text in the correct if clause
            if key.edit_changed % 2 == 0:
                edit_value = key.edit_value
            else:
                edit_value = not key.edit_value
            if current_text is not None:
                key.set_text(current_text, edit_value)
            if key.edit_changed and not self._context.get('save_mode'):
                # Now we fetch the current clause text
                text_selector.html(key.get_text())
                key.write({'edit_changed': 0})
        self.with_context(no_update=True).simplified_text = text.html()
        return True

    @api.multi
    def open_preview(self):
        preview_model = 'partner.communication.revision.preview'
        preview = self.env[preview_model].create({'revision_id': self.id})
        return {
            'name': 'Preview',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': preview_model,
            'res_id': preview.id,
            'context': self.with_context({
                'revision_id': self.id,
                'lang': self.lang
            }).env.context,
            'target': 'new',
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _open_revision(self, readonly=False):
        """
        Fetches the text from the mail.template and open the revision view
        :param readonly: Should we open the readonly view or not
        :return: action for opening the revision view
        """
        text = self.with_context(lang=self.lang).body_html
        self.with_context(
            no_update=True).simplified_text = self._simplify_text(text)
        form_view = 'partner_communication_revision.revision_form'
        if readonly:
            form_view += '_readonly'
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'target': 'current',
            'context': self.with_context(form_view_ref=form_view).env.context
        }

    @api.multi
    def _simplify_text(self, text):
        """
        Converts the mail_template raw text to a simplified version,
        readable to any user.
        :return: the simplified text
        """
        self.ensure_one()
        previous_keywords = self.keyword_ids
        found_keywords = self.env['partner.communication.keyword']
        simplified_text, keywords = self._replace_setters(text)
        found_keywords |= keywords
        simplified_text, keywords = self._replace_inline_code(simplified_text)
        found_keywords |= keywords
        nested_position = 1
        if_keyword_index = 1
        for_keyword_index = 1
        while '% if' in simplified_text:
            simplified_text, keywords = self._replace_if(
                simplified_text, nested_position, if_keyword_index)
            found_keywords |= keywords
            if_keywords = keywords.filtered(lambda k: k.type == 'if')
            if_keyword_index += len(if_keywords)
            for_keyword_index += len(keywords - if_keywords)
            nested_position += 1
        nested_position = 1
        while '% for' in simplified_text:
            simplified_text, keywords = self._replace_for(
                simplified_text, nested_position, for_keyword_index)
            found_keywords |= keywords
            for_keyword_index += len(keywords)
            nested_position += 1
        # Remove invalid keywords that are no more in the template
        (previous_keywords - found_keywords).unlink()
        return simplified_text

    def _replace_inline_code(self, text):
        """
        Finds and replace the ${} portions of the mail.template.
        It will create keyword records
        :param text: mail.template text
        :return: simplified text
        """
        code_regex = r'\$\{.+?\}'
        simple_text = self._replace_keywords(text, 'code', code_regex)
        return simple_text

    def _replace_setters(self, text):
        """
        Finds and replace the % set var = object
        of the mail.template text. It will create keyword records.
        :param text: mail.template text
        :return: simplified text without the setters code, found keywords
        """
        return self._replace_keywords(text, 'var', r'% set (.+?)=(.*)', True)

    def _replace_keywords(self, text, kw_type, pattern, is_black=False):
        """
        Finds and replace keywords
        :param text: mail.template text
        :param kw_type: keyword type
        :param pattern: pattern used for finding the keywords in the template
        :param is_black: set to true to force the color black for the keyword
        :return: simplified text without the keywords code, found keywords
        """
        setter_pattern = re.compile(pattern)
        simple_text = text
        keywords = self.env['partner.communication.keyword']
        keyword_number = 1
        # Find first match
        for match in setter_pattern.finditer(text):
            raw_code = match.group(0).strip()
            if not raw_code:
                continue
            keyword = self.keyword_ids.filtered(
                lambda k: k.raw_code == raw_code
                and (k.index == keyword_number if kw_type == 'var' else 1))
            if not keyword:
                vals = {
                    'raw_code': raw_code,
                    'type': kw_type,
                    'revision_id': self.id,
                    'position': match.start()
                }
                if is_black:
                    vals['color'] = 'black'
                keyword = keywords.create(vals)
                # Recompute replacement html
                keyword.env.invalidate_all()
            keywords += keyword
            keyword_number += 1
            simple_text = safe_replace(
                simple_text, raw_code, keyword.replacement)
        return simple_text, keywords

    def _replace_if(self, text, nested_position, keyword_number=1):
        """
        Finds and replace the % if: ... % endif
        of the mail.template. It will create keyword records for
        each if found.
        :param text: mail.template text
        :param nested_position: counts how nested if the current pass
        :param keyword_number: counts how many if we found
        :return: simplified text without the if code, keywords found
        """
        # Scan for non-nested % if, % else codes
        if_pattern = re.compile(r'(% if .*?:)(.*?)(% endif)', flags=re.DOTALL)
        simple_text = text
        keywords = self.env['partner.communication.keyword']
        for match in if_pattern.finditer(text, overlapped=True):
            raw_code = match.group(1).strip()
            if_text = match.group(2)
            start_if = match.start()
            end_if = match.end()
            # Nested ifs : we first convert the sub-ifs and then finish
            # with the root if
            number_nested = if_text.count('% if')
            if number_nested > 0:
                continue
            keyword = self.keyword_ids.filtered(
                lambda k: k.raw_code == raw_code and k.index == keyword_number)

            # Convert nested for loops in if text
            if_text, for_keywords = self._replace_for(if_text, 1)
            keywords += for_keywords

            if_parts = if_text.split('% else:')
            true_text = if_parts[0]
            false_text = if_parts[1].strip() if len(if_parts) > 1 else False
            if not keyword:
                # Create a new keyword object by extracting the text
                keyword = self.keyword_ids.create({
                    'raw_code': raw_code,
                    'revision_id': self.id,
                    'true_text': true_text.strip(),
                    'false_text': false_text,
                    'type': 'if',
                    'position': start_if,
                    'nested_position': nested_position
                })
            else:
                keyword.write({
                    'true_text': true_text,
                    'false_text': false_text,
                    'position': start_if,
                    'nested_position': nested_position
                })
            keywords += keyword
            keyword_number += 1
            simple_text = simple_text.replace(text[start_if:end_if],
                                              keyword.replacement)
        return simple_text, keywords

    def _replace_for(self, text, nested_position, keyword_number=1):
        """
        Finds and replace the % for: ... % endfor loops
        of the mail.template. It will create keyword records for
        each loop found.
        :param text: mail.template text
        :param nested_position: counts how nested if the current pass
        :param keyword_number: counts how many for we found
        :return: simplified text without the if code, keywords found
        """
        # Scan for the % if, % else codes
        loop_regex = r'(% for .*?:)(.*?)(% endfor)'
        ul_loop_regex = r'(<ul[^<]*?)(% for .*?:)(.*?)(% endfor)(.*?</ul>)'
        regex = ul_loop_regex + '|' + loop_regex
        for_pattern = re.compile(regex, flags=re.DOTALL)
        simple_text = text
        keywords = self.env['partner.communication.keyword']
        for match in for_pattern.finditer(text, overlapped=True):
            ul_text = match.group(3)
            if ul_text:
                for_type = 'for_ul'
                raw_code = match.group(2).strip()
                for_text = ul_text
            else:
                for_type = 'for'
                raw_code = match.group(6).strip()
                for_text = match.group(7)
            start_for = match.start()
            end_for = match.end()
            # Nested for : skip to next for loop which is not encapsulating
            # another loop. The while loop will take care of it later.
            number_nested = for_text.count('% for')
            if number_nested > 0:
                continue
            keyword = self.keyword_ids.filtered(
                lambda k: k.raw_code == raw_code and k.index == keyword_number)
            if not keyword:
                # Create a new keyword object by extracting the text
                keyword = self.keyword_ids.create({
                    'raw_code': raw_code,
                    'revision_id': self.id,
                    'true_text': for_text.strip(),
                    'type': for_type,
                    'position': start_for,
                    'nested_position': nested_position
                })
            else:
                keyword.write({
                    'true_text': for_text,
                    'type': for_type,
                    'position': start_for,
                    'nested_position': nested_position
                })
            keywords += keyword
            keyword_number += 1
            simple_text = simple_text.replace(text[start_for:end_for],
                                              keyword.replacement)
        return simple_text, keywords

    @api.multi
    def _enhance_text(self):
        """
        Transforms a simplified text into a valid mail.template text.
        :return: mail.template text
        """
        self.ensure_one()
        # Parse and set back the keywords into raw template code
        html_text = PyQuery(self.simplified_text.replace('\n', ''))

        def sort_keywords(kw):
            # Replace first if-clause, then for-clause, then var, then code
            index = kw.position
            if kw.type == 'if':
                index += 3*len(self.body_html) * kw.nested_position
            elif 'for' in kw.type:
                index += 2*len(self.body_html) * kw.nested_position
            elif kw.type == 'var':
                index += len(self.body_html)
            return index

        keywords = self.keyword_ids.sorted(sort_keywords, reverse=True)
        # Replace automatic-generated keywords
        for keyword in keywords:
            keyword_text = html_text('#' + keyword.html_id)
            keyword_text.replace_with(keyword.final_text)

        # Replace user added keywords
        template_text = html_text.html()
        for keyword in keywords.filtered(lambda k: k.type == 'code'):
            to_replace = u"[{}]".format(keyword.short_code)
            template_text = template_text.replace(to_replace, keyword.raw_code)
        final_text = PyQuery(BeautifulSoup(template_text).prettify())
        return final_text('body').html()
