# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Copyright Compassion Suisse
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
from openerp.osv import orm


class compassion_child(orm.Model):

    """ Add allocation and deallocation methods on the children. """
    _inherit = 'compassion.child'

    def allocate(self, cr, uid, child_reference, context=None):
        child_id = self.create(
            cr, uid, {'code': child_reference, 'name': '/'}, context=context)
        return self.update(cr, uid, child_id, context=context)

    def deallocate(self, cr, uid, id, context=None):
        # TODO : should be done from GP or see what to do.
        return True

    def depart(self, cr, uid, id, context=None):
        # TODO : terminate the contract, mark the child as departed and the
        # user should do the right communication from GP.
        return True

    def update(self, cr, uid, id, context=None):
        """ When we receive a notification that child has been updated, we fetch the last case study. """
        # TODO : uncomment when merged with branch child_compassion.
        # self.get_last_case_study(self, cr, uid, id, context=context)
        return True

compassion_child()


class compassion_project(orm.Model):

    """ Add update method. """
    _inherit = 'compassion.project'

    def update(self, cr, uid, id, context=None):
        # TODO : add a method that calls webservice like get_last_case_study.
        return True
