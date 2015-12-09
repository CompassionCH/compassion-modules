# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
"""
This module reads a zip file containing scans of mail and finds the relation
between the database and the mail.
"""
import base64
import zipfile
import os
import tempfile
import shutil

from ..tools import import_letter_functions as func
from openerp import api, fields, models, _, exceptions


class ImportLettersHistory(models.Model):
    """
    Keep history of imported letters.
    This class allows the user to import some letters (individually or in a
    zip file) in the database by doing an automatic analysis.
    The code is reading QR codes in order to detect child and partner codes
    for every letter, using the zxing library for code detection.
    """
    _name = "import.letters.history"
    _description = _("""History of the letters imported from a zip
    or a PDF/TIFF""")
    _order = "create_date desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    state = fields.Selection([
        ("draft", _("Draft")),
        ("open", _("Open")),
        ("ready", _("Ready")),
        ("done", _("Done"))], compute="_set_ready")
    nber_letters = fields.Integer(
        'Number of letters', readonly=True, compute="_count_nber_letters")
    is_mandatory_review = fields.Boolean(
        'Mandatory Review',
        states={'done': [('readonly', True)]})
    data = fields.Many2many('ir.attachment', string="Add a file")
    import_line_ids = fields.One2many(
        'import.letter.line', 'import_id', 'Files to process',
        ondelete='cascade')
    letters_ids = fields.One2many(
        'sponsorship.correspondence', 'import_id', 'Imported letters',
        readonly=True)
    force_template = fields.Many2one('sponsorship.correspondence.template',
                                     'Force Template')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends("import_line_ids", "import_line_ids.status",
                 "letters_ids", "data")
    def _set_ready(self):
        """ Check in which state self is by counting the number of elements in
        each Many2many
        """
        for import_letters in self:
            if import_letters.letters_ids:
                import_letters.state = "done"
            elif import_letters.import_line_ids:
                check = True
                for i in import_letters.import_line_ids:
                    if i.status != "ok":
                        check = False
                if check:
                    import_letters.state = "ready"
                else:
                    import_letters.state = "open"
            else:
                import_letters.state = "draft"

    @api.multi
    @api.onchange("data", "import_line_ids", "letters_ids")
    def _count_nber_letters(self):
        """
        Counts the number of scans. If a zip file is given, the number of
        scans inside is counted.
        """
        for inst in self:
            if inst.state == "open" or inst.state == "ready":
                inst.nber_letters = len(inst.import_line_ids)
            elif inst.state == "done":
                inst.nber_letters = len(inst.letters_ids)
            elif inst.state is False or inst.state == "draft":
                # counter
                tmp = 0
                # loop over all the attachments
                for attachment in inst.data:
                    # pdf or tiff case
                    if func.check_file(attachment.name) == 1:
                        tmp += 1
                    # zip case
                    elif func.isZIP(attachment.name):
                        # create a tempfile and read it
                        with tempfile.NamedTemporaryFile(
                                suffix='.zip') as zip_file:
                            zip_file.write(base64.b64decode(
                                attachment.with_context(
                                    bin_size=False).datas))
                            zip_file.flush()
                            # catch ALL the exceptions that can be raised
                            # by class zipfile
                            try:
                                zip_ = zipfile.ZipFile(zip_file.name, 'r')
                                list_file = zip_.namelist()
                                # loop over all files in zip
                                for tmp_file in list_file:
                                    tmp += (func.check_file(tmp_file) == 1)
                            except zipfile.BadZipfile:
                                raise exceptions.Warning(
                                    _('Zip file corrupted (' +
                                      attachment.name + ')'))
                            except zipfile.LargeZipFile:
                                raise exceptions.Warning(
                                    _('Zip64 is not supported(' +
                                      attachment.name + ')'))

                inst.nber_letters = tmp
            else:
                raise exceptions.Warning(
                    _("State: '{}' not implemented".format(inst.state)))

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def button_import(self):
        for letters_import in self:
            if letters_import.data:
                letters_import._run_analyze()
        return True

    @api.multi
    def button_save(self):
        """
        save the import_line as a sponsorship_correspondence
        """
        # check if all the imports are OK
        for letters_h in self:
            if letters_h.state != "ready":
                raise exceptions.Warning(_("Some letters are not ready"))
        # save the imports
        for letters in self:
            ids = letters.import_line_ids.get_letter_data(
                mandatory_review=letters.is_mandatory_review)
            # letters_ids should be empty before this line
            letters.write({'letters_ids': ids})
            letters.import_line_ids.letter_image.unlink()
            letters.import_line_ids.unlink()
        return True

    @api.multi
    def button_review(self):
        """ Returns a form view for import lines in order to browse them """
        self.ensure_one()
        return {
            'name': _('Review Imports'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'import.letters.review',
            'context': self.with_context(
                line_ids=self.import_line_ids.ids).env.context,
            'target': 'current',
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _run_analyze(self):
        """
        Analyze each attachment:
        - check for duplicate file names and skip them
        - decompress zip file if necessary
        - call _analyze_attachment for every resulting file
        """
        self.ensure_one()
        # keep track of file names to detect duplicates
        file_name_history = []
        for attachment in self.data:
            if attachment.name not in file_name_history:
                file_name_history.append(attachment.name)
                # check for zip
                if func.check_file(attachment.name) == 2:
                    # create a temp file
                    with tempfile.NamedTemporaryFile(
                            suffix='.zip') as zip_file:
                        # write data in tempfile
                        zip_file.write(base64.b64decode(
                            attachment.with_context(
                                bin_size=False).datas))
                        zip_file.flush()
                        zip_ = zipfile.ZipFile(
                            zip_file, 'r')
                        # loop over files inside zip
                        directory = tempfile.mkdtemp()
                        for f in zip_.namelist():
                            zip_.extract(
                                f, directory)
                            absname = directory + '/' + f
                            if os.path.isfile(absname):
                                # remove if PDF is working
                                if func.isPDF(absname):
                                    raise exceptions.Warning(
                                        _("PDF not implemented yet"))
                                filename = f.split('/')[-1]
                                self._analyze_attachment(absname,
                                                         filename)
                        shutil.rmtree(directory)
                # case with normal format ([PDF,]TIFF)
                elif func.check_file(attachment.name) == 1:
                    # remove if PDF is working
                    if func.isPDF(attachment.name):
                        raise exceptions.Warning(
                            _("PDF not implemented yet"))
                    ext = os.path.splitext(attachment.name)[1]
                    with tempfile.NamedTemporaryFile(
                            suffix=ext) as file_:
                        file_.write(base64.b64decode(
                            attachment.with_context(
                                bin_size=False).datas))
                        file_.flush()
                        self._analyze_attachment(file_.name,
                                                 attachment.name)
                else:
                    raise exceptions.Warning(
                        'Still a file in a non-accepted format')
            else:
                raise exceptions.Warning(_('Two files are the same'))
        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()

    def _analyze_attachment(self, file_, filename):
        line_vals, document_vals, file_data = func.analyze_attachment(
            self.env, file_, filename, self.force_template)
        letters_line = self.env['import.letter.line'].create(line_vals)
        document_vals.update({
            'res_id': letters_line.id,
            'res_model': 'import.letter.line'
        })
        letters_line.letter_image = self.env[
            'ir.attachment'].create(document_vals)
        letters_line.letter_image_preview = base64.b64encode(file_data)
        self.import_line_ids += letters_line
