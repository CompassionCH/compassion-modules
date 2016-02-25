# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier, Loic Hausammann <loic_hausammann@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
"""
This module reads a zip file containing scans of mail and finds the relation
between the database and the mail.
"""
import logging
import base64
import zipfile
import os
import tempfile
import shutil

from ..tools import import_letter_functions as func
from openerp import api, fields, models, _, exceptions

from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession

from openerp.tools.config import config
from smb.SMBConnection import SMBConnection

logger = logging.getLogger(__name__)


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
        ("pending", _("Analyzing")),
        ("open", _("Open")),
        ("ready", _("Ready")),
        ("done", _("Done"))], compute="_compute_state", store=True)
    import_completed = fields.Boolean()
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
                 "letters_ids", "data", "import_completed")
    def _compute_state(self):
        """ Check in which state self is by counting the number of elements in
        each Many2many
        """
        for import_letters in self:
            if import_letters.letters_ids:
                import_letters.state = "done"
            elif import_letters.import_completed:
                check = True
                for i in import_letters.import_line_ids:
                    if i.status != "ok":
                        check = False
                if check:
                    import_letters.state = "ready"
                else:
                    import_letters.state = "open"
            elif import_letters.import_line_ids:
                import_letters.state = "pending"
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
            if inst.state in ("open", "pending", "ready"):
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
        """
        Analyze the attachment in order to create the letter's lines
        """
        for letters_import in self:
            if letters_import.data:
                letters_import.state = 'pending'
                if self.env.context.get('async_mode', True):
                    for attachment in letters_import.data:
                        self._save_imported_letter(attachment)
                    session = ConnectorSession.from_env(self.env)
                    import_letters_job.delay(
                        session, self._name, letters_import.id)
                else:
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
            letters.mapped('import_line_ids.letter_image').unlink()
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
        logger.info("Imported letters analysis started...")
        progress = 1
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
                            logger.info(
                                "Analyzing letter {}/{}".format(
                                    progress, self.nber_letters))
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
                                # saved imported letter to a share location NAS folder
                                self._copy_imported_to_done_letter(attachment)
                            progress += 1
                        shutil.rmtree(directory)
                # case with normal format ([PDF,]TIFF)
                elif func.check_file(attachment.name) == 1:
                    logger.info("Analyzing letter {}/{}".format(
                        progress, self.nber_letters))
                    ext = os.path.splitext(attachment.name)[1]
                    with tempfile.NamedTemporaryFile(
                            suffix=ext) as file_:
                        file_.write(base64.b64decode(
                            attachment.with_context(
                                bin_size=False).datas))
                        file_.flush()
                        self._analyze_attachment(file_.name,
                                                 attachment.name)
                        # saved imported letter to a share location NAS folder
                        self._copy_imported_to_done_letter(attachment)
                    progress += 1
                else:
                    raise exceptions.Warning(
                        'Still a file in a non-accepted format')
            else:
                raise exceptions.Warning(_('Two files are the same'))

        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()
        self.import_completed = True
        logger.info("Imported letters analysis completed.")

    def _analyze_attachment(self, file_, filename):
        line_vals, document_vals = func.analyze_attachment(
            self.env, file_, filename, self.force_template)
        letters_line = self.env['import.letter.line'].create(line_vals)
        document_vals.update({
            'res_id': letters_line.id,
            'res_model': 'import.letter.line'
        })
        letters_line.letter_image = self.env['ir.attachment'].create(
            document_vals)
        self.import_line_ids += letters_line


    def _save_imported_letter(self, attachment):
        """
        Save attachment letter to a share location on NAS
            - attachment : the attachment to save 
        Done by M. Sandoz 02.2016
        """
        """ Store letter on a share location on NAS: """
        # Retrieve configuration
        smb_user = config.get('smb_user')
        smb_pass = config.get('smb_pwd')
        smb_ip = config.get('smb_ip')
        smb_port = int(config.get('smb_port', 0))
        if not (smb_user and smb_pass and smb_ip and smb_port):
            return False

        # Copy file in the imported letter folder
        smb_conn = SMBConnection(smb_user, smb_pass, 'openerp', 'nas')
        if smb_conn.connect(smb_ip, smb_port):
            logger.info("Try to save file {} !".format(attachment.name))
            ext = os.path.splitext(attachment.name)[1]
            with tempfile.NamedTemporaryFile(
                    suffix=ext) as file_:
                file_.write(base64.b64decode(
                    attachment.with_context(bin_size=False).datas))
                file_.flush()
                file_.seek(0)
                config_obj = self.env['ir.config_parameter']
                share_nas = (config_obj.search(
                    [('key', '=', 'sbc_compassion.share_on_nas')])[0]).value
                imported_letter_path = (config_obj.search(
                    [('key', '=', 'sbc_compassion.scan_letter_imported')])[0]).value + attachment.name
                smb_conn.storeFile(share_nas, imported_letter_path, file_)

        return True


    def _copy_imported_to_done_letter(self, attachment):
        """ 
        Copy letter from 'imported' folder to 'done' folder on  a share location on NAS
            - attachment: the attachment corresponding to the letter to copy
        Done by M. Sandoz 02.2016                 
        """
        # Retrieve configuration
        smb_user = config.get('smb_user')
        smb_pass = config.get('smb_pwd')
        smb_ip = config.get('smb_ip')
        smb_port = int(config.get('smb_port', 0))
        if not (smb_user and smb_pass and smb_ip and smb_port):
            return False

        smb_conn = SMBConnection(smb_user, smb_pass, 'openerp', 'nas')
        if smb_conn.connect(smb_ip, smb_port):
            logger.info("Try to copy file {} !".format(attachment.name))
            ext = os.path.splitext(attachment.name)[1]

            # Delete file in the imported letter folder
            config_obj = self.env['ir.config_parameter']
            share_nas = (config_obj.search(
                    [('key', '=', 'sbc_compassion.share_on_nas')])[0]).value
            imported_letter_path = (config_obj.search(
                [('key', '=', 'sbc_compassion.scan_letter_imported')])[0]).value + attachment.name
            try:
                smb_conn.deleteFiles(share_nas, imported_letter_path)
            except Exception as inst:
                logger.info('Failed to delete a file not on NAS')
            # Copy file in attachment in the done letter folder
            with tempfile.NamedTemporaryFile(
                    suffix=ext) as file_:
                file_.write(base64.b64decode(
                    attachment.with_context(bin_size=False).datas))
                file_.flush()
                file_.seek(0)
                done_letter_path = (config_obj.search(
                    [('key', '=', 'sbc_compassion.scan_letter_done')])[0]).value + attachment.name
                smb_conn.storeFile(share_nas, done_letter_path, file_)
        return True


##############################################################################
#                            CONNECTOR METHODS                               #
##############################################################################


def related_action_imports(session, job):
    import_model = job.args[1]
    import_id = job.args[2]
    action = {
        'type': 'ir.actions.act_window',
        'res_model': import_model,
        'view_type': 'form',
        'view_mode': 'form',
        'res_id': import_id,
    }
    return action


@job(default_channel='root.sbc_compassion')
@related_action(action=related_action_imports)
def import_letters_job(session, model_name, import_id):
    """Job for importing letters."""
    import_history = session.env[model_name].browse(import_id)
    import_history._run_analyze()
