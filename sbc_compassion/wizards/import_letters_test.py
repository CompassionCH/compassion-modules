# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammann@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import models, fields, _, api
from ..tools import import_letter_functions as func


class TestImportLetters(models.TransientModel):
    """ Class testing the letters import by highlighting the keypoints of
    the import (image used, keypoints found for the templates, showing only
    the line not well detected, the subset used for the QR code, the languages,
    the templates).
    A csv file need to be written in the same way than
    sbc_compassion/tests/testdata/import/travis_file.csv
    """
    _inherit = 'import.letters.history'
    _name = 'test.import.letters.history'
    _description = _("""Module testing the import of
    letters (import.letters.history)""")
    csv_file_ids = fields.Many2many(
        'ir.attachment', relation='test_import_ir_attachment',
        string="Add a CSV file")
    nber_test = fields.Integer("NBER OF FILE")
    test_ok = fields.Char("Test passed", compute="_set_ready")
    template_ok = fields.Char("Template passed", compute="_set_ready")
    qr_ok = fields.Char("QR code passed",  compute="_set_ready")
    lang_ok = fields.Char("Languages passed", compute="_set_ready")
    test_import_line_ids = fields.One2many(
        'test.import.letter.line', 'test_import_id', 'Files to process',
        ondelete='cascade')

    def _analyze_attachment(self, file_, filename):
        # first save the value of nber_letters
        # (this function does not create a import.letter.line, therefore,
        # the computation is wrong later)
        self.nber_test = self.nber_letters
        line_vals, document_vals = func.analyze_attachment(
            self.env, file_, filename, self.force_template, test=True)

        for i in xrange(0, len(line_vals)):
            error = func.testline(self.env, line_vals[i], self.csv_file_ids,
                                  document_vals[i]['name'])
            if error:
                line_vals[i].update({
                    'error': error
                })
            # create all the data
            letters_line = self.env['test.import.letter.line'].create(
                line_vals[i])
            document_vals[i].update({
                'res_id': letters_line.id,
                'res_model': 'test.import.letter.line'
            })
            letters_line.letter_image = self.env[
                'ir.attachment'].create(document_vals[i])
            letters_line._check_status()
            self.test_import_line_ids += letters_line

    @api.multi
    @api.depends("test_import_line_ids", "test_ok")
    def _set_ready(self):
        """ Check in which state self is by counting the number of elements in
        each Many2many and delete the lines that have been correctly analyzed
        """
        for import_letters in self:
            if import_letters.nber_test:
                import_letters.state = 'open'
                import_letters = func.update_stat_text(import_letters)
            else:
                import_letters.state = 'draft'


class TestImportLettersLine(models.TransientModel):
    """ Add a few fields to the lines in order to show the problems in the import
    """
    _inherit = 'import.letter.line'
    _name = 'test.import.letter.line'
    qr_preview = fields.Binary("QR code preview")
    lang_preview = fields.Binary("Languages preview")
    template_preview = fields.Binary("Template preview")
    test_letter_language = fields.Text("Language")
    test_import_id = fields.Many2one('test.import.letters.history')
    error = fields.Text("Error")
