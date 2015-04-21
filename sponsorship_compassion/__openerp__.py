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
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    @author: Cyril Sester, Emanuel Cino
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
    'name': 'Compassion Sponsorships',
    'version': '1.4',
    'category': 'Other',
    'description': """
Compassion Sponsorships
=======================
Sponsorship management module. This module makes the link between child and
contracts. It also customize contracts to fit the child sponsorship context.

Installation
============
This modules requires en_US, fr_CH, de_DE, it_IT and es_ES to be installed
on the server.

To check installed locales:

* locale -a

To add a new locale :

* /usr/share/locales/install-language-pack <ISO-locale-name>
* dpkg-reconfigure locales

Usage
=====

To use this module, you need to:

* go to Sponsorship -> Sponsorships

Known issues / Roadmap
======================

* Contracts and Sponsorships will be better differenciated.

Credits
=======

Contributors
------------

* Cyril Sester <cyril.sester@outlook.com>
* Emanuel Cino <ecino@compassion.ch>
    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['contract_compassion', 'l10n_ch_payment_slip', 'crm',
                'l10n_ch', 'account_cancel', 'account_banking_mandate',
                'account_asset_compassion', 'partner_compassion',
                'web_m2x_options', 'account_invoice_split_invoice'],
    'data': [
        'view/contract_view.xml',
        'view/end_sponsorship_wizard_view.xml',
        'view/invoice_line_view.xml',
        'view/res_partner_view.xml',
        'view/generate_gift_view.xml',
        'view/activate_contract_view.xml',
        'view/account_invoice_split_wizard_view.xml',
        'view/suspension_wizard_view.xml',
        'view/child_view.xml',
        'data/product.xml',
        'data/payment_terms.xml',
        'data/lang.xml',
        'data/sequence.xml',
        'data/analytic_accounting.xml',
        'data/friday_invoicer_cron.xml',
        'security/ir.model.access.csv',
        'workflow/contract_workflow.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
