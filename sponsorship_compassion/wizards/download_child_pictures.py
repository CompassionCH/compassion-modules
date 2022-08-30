##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
import requests
from io import BytesIO
from zipfile import ZipFile

from odoo import models, api, fields

logger = logging.getLogger(__name__)


class DownloadChildPictures(models.TransientModel):
    _name = "child.pictures.download.wizard"
    _description = "Child Picture Download Wizard"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    fname = fields.Char(default=lambda s: s.get_file_name())
    type = fields.Selection(
        [("headshot", "Headshot"), ("fullshot", "Fullshot")], default="headshot"
    )
    child_ids = fields.Many2many("compassion.child", default=lambda s: s._get_children())
    height = fields.Integer()
    width = fields.Integer()
    download_data = fields.Binary(readonly=True)
    preview = fields.Char(compute="_compute_preview", store=True)
    information = fields.Text(readonly=True)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.model
    def get_file_name(self):
        return str(fields.Date.context_today(self)) + "_child_pictures.zip"

    def get_picture_url(self, raw_url, pic_type, width, height):
        if pic_type.lower() == "headshot":
            cloudinary = "g_face,c_thumb,h_" + str(height) + ",w_" + str(width)
        elif pic_type.lower() == "fullshot":
            cloudinary = "w_" + str(width) + ",h_" + str(height) + ",c_fit"

        image_split = raw_url.split("/")
        ind = image_split.index("media.ci.org")
        image_split[ind + 1] = cloudinary
        url = "/".join(image_split)
        return url

    def get_pictures(self):
        """ Create the zip archive from the selected letters. """
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zip_data:
            found = 0
            for child in self.child_ids.filtered("image_url"):
                child_code = child.local_id
                url = self.get_picture_url(
                    raw_url=child.image_url,
                    pic_type=self.type,
                    height=self.height,
                    width=self.width,
                )
                data = base64.encodebytes(requests.get(url).content)

                _format = url.split(".")[-1]
                fname = f"{child.sponsor_ref or ''}_{child_code}.{_format}"

                zip_data.writestr(fname, base64.b64decode(data))
                found += 1

        zip_buffer.seek(0)
        if found:
            self.download_data = base64.b64encode(zip_buffer.read())

        self.information = "Zip file contains " + str(found) + " " "pictures.\n\n"
        self._check_picture_availability()
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_id": self.id,
            "res_model": self._name,
            "context": self.env.context,
            "target": "new",
        }

    @api.onchange("type")
    def _type_onchange(self):
        if self.type == "headshot":
            self.height = 400
            self.width = 300
        else:
            self.height = 1200
            self.width = 800

    @api.depends("height", "width")
    def _compute_preview(self):
        for child in self.child_ids.filtered("image_url"):
            self.preview = self.get_picture_url(child.image_url, self.type, self.width, self.height)
            if self.preview:
                break
        else:
            self.preview = False

    def _check_picture_availability(self):
        # Search children having a 'image_url' returning False
        children_with_no_url = self.child_ids.filtered(lambda c: not c.image_url)
        # If there is some, we will print their corresponding childe_code
        if children_with_no_url:
            child_codes = children_with_no_url.mapped("local_id")
            self.information += (
                "No image url for child(ren):\n\t" + "\n\t".join(
                    child_codes) + "\n\n"
            )

        # Now we want children having an invalid 'image_url'.
        children_with_invalid_url = []
        for child in self.child_ids.filtered("image_url"):
            url = self.get_picture_url(
                raw_url=child.image_url, pic_type="fullshot", height=1, width=1
            )
            if not requests.get(url).content:
                # Not good, the url doesn't lead to an image
                children_with_invalid_url += [child.local_id]
        if children_with_invalid_url:
            self.information += "Invalid image url for child(ren):\n\t" + "\n\t".join(
                children_with_invalid_url
            )

    def _get_children(self):
        res_model = self.env.context.get("active_model")
        res_ids = self.env.context.get("active_ids")
        children = self.env["compassion.child"]
        if not res_model or not res_ids:
            return children
        res_obj = self.env[res_model].browse(res_ids)
        if res_model == "res.partner":
            children = res_obj.mapped("sponsored_child_ids")
        elif res_model == "recurring.contract":
            children = res_obj.mapped("child_id")
        elif res_model == "compassion.child":
            children = res_obj
        return children
