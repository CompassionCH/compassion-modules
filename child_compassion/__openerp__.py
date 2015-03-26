# -*- encoding: utf-8 -*-
##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#                            in Jesus' name
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    @author: Cyril Sester <csester@compassion.ch>
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
    'name': 'Compassion Children',
    'version': '1.4.1',
    'category': 'Other',
    'description': """
Compassion Children
===================

Setup child and projects for sponsorship management.
Webservice information retrieving is also done in this module...

Installation
============

To install this module, you need to:

* install pysftp (sudo pip install pysftp)

Configuration
=============

To configure this module, you need to:

* add settings in .conf file of Odoo
* compass_url = <url to compass webservice>
* compass_api_key = <your developer key for compass webservices>

Usage
=====

To use this module, you need to:

* Go to Sponsorship -> Children

Known issues / Roadmap
======================

* Typo3 functionalities will be removed from this module

Credits
=======

Contributors
------------

* Cyril Sester <cyril.sester@outlook.com>
* Emanuel Cino <ecino@compassion.ch>
* Kevin Cristi <kcristi@compassion.ch>
* David Coninckx <david@coninckx.com>

    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['mail', 'web_m2x_options'],
    'data': [
        'security/sponsorship_groups.xml',
        'security/ir.model.access.csv',
        'view/child_depart_wizard_view.xml',
        'view/child_compassion_view.xml',
        'view/child_compassion_property_view.xml',
        'view/child_description_wizard_view.xml',
        'view/project_compassion_view.xml',
        'view/translated_values_view.xml',
        'view/country_compassion_view.xml',
        'view/delegate_child_wizard.xml',
        'view/undelegate_child_wizard.xml',
        'view/project_description_wizard_view.xml',
        'view/project_compassion_age_groups_view.xml',
        'workflow/child_workflow.xml',
    ],
    'css': ['static/src/css/child_compassion.css'],
    'js': ['static/src/js/child_description_wizard.js'],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
