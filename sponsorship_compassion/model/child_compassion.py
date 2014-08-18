# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Cyril Sester. Copyright Compassion Suisse
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
from openerp.osv import orm, fields
from openerp.tools.translate import _


class compassion_child(orm.Model):
    """ A sponsored child """
    _name = 'compassion.child'
    _columns = {
        'name': fields.char(_("Name"),size=128,required=True),
        'code': fields.char(_("Child code"),size=128,required=True),
        'unique_id': fields.char(_("Unique ID"),size=128),
        'birthdate': fields.date(_("Birthdate")),
        'type': fields.selection((('CDSP', 'CDSP'), ('LDP', 'LDP')), _('Type of sponsorship program'),required=True),
        'date': fields.date(_("Allocation date"), help=_("The date at which Compass allocated this child to Switzerland")),
    }
    
    _defaults = {
        'type' : 'CDSP'
    }
    
compassion_child()