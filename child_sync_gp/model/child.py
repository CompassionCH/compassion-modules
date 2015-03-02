# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm
from openerp.tools.config import config

from smb.SMBConnection import SMBConnection
from smb.smb_structs import OperationFailure
from tempfile import TemporaryFile

from . import gp_connector
import base64


class child_compassion(orm.Model):
    _inherit = 'compassion.child'

    def create(self, cr, uid, vals, context=None):
        new_id = super(child_compassion, self).create(cr, uid, vals, context)
        child = self.browse(cr, uid, new_id, context)
        gp_connect = gp_connector.GPConnect()
        gp_connect.upsert_child(uid, child)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        """Update GP with the last information of the child."""
        res = super(child_compassion, self).write(cr, uid, ids, vals, context)
        if not isinstance(ids, list):
            ids = [ids]
        gp_connect = gp_connector.GPConnect()

        for child in self.browse(cr, uid, ids, context):
            gp_connect.upsert_child(uid, child)
            if 'state' in vals:
                gp_connect.set_child_sponsor_state(child)
            if 'code' in vals:
                # Update the Sponsorships related to this child in GP
                con_obj = self.pool.get('recurring.contract')
                con_ids = con_obj.search(
                    cr, uid, [('child_id', '=', child.id)], context=context)
                if con_ids:
                    gp_connect.update_child_sponsorship(child.code, con_ids)

        return res


class child_pictures(orm.Model):
    _inherit = 'compassion.child.pictures'

    def create(self, cr, uid, vals, context=None):
        """Push a new picture to GP."""
        pic_id = super(child_pictures, self).create(cr, uid, vals, context)
        pic_data = self.get_picture(cr, uid, [pic_id], 'fullshot', '',
                                    context)[pic_id]

        if pic_data:
            # Retrieve configuration
            smb_user = config.get('smb_user')
            smb_pass = config.get('smb_pwd')
            smb_ip = config.get('smb_ip')
            child_obj = self.pool.get('compassion.child')
            child = child_obj.browse(cr, uid, vals['child_id'], context)
            # In GP, pictures are linked to Case Study
            if not child.case_study_ids:
                child_obj._get_case_study(cr, uid, child, context)
                child = child_obj.browse(cr, uid, child.id, context)
            date_cs = child.case_study_ids[0].info_date.replace('-', '')
            gp_pic_path = "{}{}/".format(config.get('gp_pictures'),
                                         child.code[:2])
            file_name = "{}_{}.jpg".format(child.code, date_cs)
            picture_file = TemporaryFile()
            picture_file.write(base64.b64decode(pic_data))
            picture_file.flush()
            picture_file.seek(0)

            # Upload file to shared folder
            smb_conn = SMBConnection(smb_user, smb_pass, 'openerp', 'nas')
            if smb_conn.connect(smb_ip, 139):
                try:
                    smb_conn.storeFile(
                        'GP', gp_pic_path + file_name, picture_file)
                except OperationFailure:
                    # Directory may not exist
                    smb_conn.createDirectory('GP', gp_pic_path)
                    smb_conn.storeFile(
                        'GP', gp_pic_path + file_name, picture_file)

        return pic_id


class child_property(orm.Model):
    """ Upsert Case Studies """
    _inherit = 'compassion.child.property'

    def create(self, cr, uid, vals, context=None):
        new_id = super(child_property, self).create(cr, uid, vals, context)
        case_study = self.browse(cr, uid, new_id, context)
        gp_connect = gp_connector.GPConnect()
        gp_connect.upsert_case_study(uid, case_study)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        gp_connect = gp_connector.GPConnect()
        super(child_property, self).write(cr, uid, ids, vals, context)
        for case_study in self.browse(cr, uid, ids, context):
            gp_connect.upsert_case_study(uid, case_study)
        return True
