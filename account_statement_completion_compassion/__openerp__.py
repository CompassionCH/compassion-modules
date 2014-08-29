# -*- coding: utf-8 -*-
##############################################################################
#
#    Authors: Emanuel Cino
#    Copyright (c) 2014 Compassion Suisse (http://www.compassion.ch)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
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
    "name": "Account Statement Completion Rules for Compassion CH",
    "version": "0.6",
    "author": "Emanuel Cino",
    "category": "Finance",
    "website": "http://www.compassion.ch",
    "depends": ['account_statement_base_completion',
                'sponsorship_compassion',
                'account_banking_payment',
                ],
    "data": ['statement_view.xml', 'data.xml'],
    "css": ["static/src/css/sheet.css"],
    "description": """

Account Statement Completion Rules for Compassion CH
=========================

- Add three completion methods :
    1. Completion method based on the BVR reference of the contract or the invoice.
    2. Completion method based on the reference of the partner
    3. Completion method for Raiffaisen statements (supplier invoices) based only on the amount.

- The first rule is applied. If no contract or invoice is found with same BVR reference, then second rule is applied, and an invoice is generated on-the-fly for gifts or funds donations.
- The third rule is useful only for supplier invoices.

""",
    "demo": [],
    "test": [],
    "active": False,
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
