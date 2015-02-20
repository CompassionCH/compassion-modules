# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester , Kevin Cristi, David Coninckx
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import pysftp
import requests

from openerp.osv import orm
from openerp.tools.config import config
from openerp.tools.translate import _


class Sync_typo3:

    @classmethod
    def request_to_typo3(self, request, request_type, context=None):
        filename = request_type+".sql"

        host = config.get('typo3_host')
        username = config.get('typo3_user')
        pwd = config.get('typo3_pwd')
        scripts_url = config.get('typo3_scripts_url')
        path = config.get('typo3_scripts_path')
        api_key = config.get('typo3_api_key')

        file_query = open(filename, "wb")
        file_query.write(request)
        file_query.close()

        if not (host and username and pwd and path and
                scripts_url and api_key):
            raise orm.except_orm('ConfigError',
                                 'Missing typo3 settings '
                                 'in conf file')
        with pysftp.Connection(host, username=username, password=pwd) as sftp:
            with sftp.cd(path):
                sftp.put(filename)

        return self._typo3_scripts_fetch(
            scripts_url, api_key, request_type+"_db")

    @classmethod
    def _typo3_scripts_fetch(self, url, api_key, action, args=None):
        full_url = url + "?apikey=" + api_key + "&action=" + action
        if args:
            for k, v in args.items():
                full_url += "&" + k + "=" + v
        r = requests.get(full_url)
        if not r.text or "Error" in r.text:
            raise orm.except_orm(
                _("Typo3 Error"),
                _("Impossible to communicate  with Typo3") + '\n' + r.text)
        return r.text

    @classmethod
    def add_child_photos(self, head_image, full_image):
        host = config.get('typo3_host')
        username = config.get('typo3_user')
        pwd = config.get('typo3_pwd')
        path = config.get('typo3_images_path')

        with pysftp.Connection(
            host, username=username,
                password=pwd) as sftp:
                    with sftp.cd(path):
                        sftp.put(head_image)
                        sftp.put(full_image)

    @classmethod
    def delete_child_photos(self, child_codes):
        scripts_url = config.get('typo3_scripts_url')
        api_key = config.get('typo3_api_key')

        self._typo3_scripts_fetch(scripts_url, api_key, "delete_photo",
                                  {"children": ",".join(child_codes)})
