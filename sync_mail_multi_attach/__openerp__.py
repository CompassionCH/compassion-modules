# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#    Copyright (C) 2011-today Synconics Technologies Pvt. Ltd. (<http://www.synconics.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Mail Multi Attachments", 
    "version": "1.0", 
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'https://www.synconics.com',
    "category": "Social Network",
    "summary": "Upload & Download multiple attachments in the mail at once",
    "description": """
    This module enables the feature to upload & download multiple attachments in the mail at once. You need to create only one mail, attach more than one files and send to individual or group of recipient.
    
If there is a multiple attachments, you can download all the attachments as a .Zip file using new icon "Download All" (displayed in orange color).

The "Attach a file" link will lead you to the file browser - from where you can select more than one file and click on "Open" button. The attached files will visible in group/individual as it is posted.
    """,
    "depends": ["mail"],
    'data': ["views/mail_multi_attach.xml"],
    'qweb': ['static/src/xml/*.xml'],
    "installable": True, 
    "auto_install": False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: