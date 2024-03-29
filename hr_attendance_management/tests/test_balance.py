# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta

from odoo.tests import SavepointCase

logger = logging.getLogger(__name__)


class TestAnnualBalance(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.jack = cls.env.ref("hr.employee_fme")
        cls.gilles = cls.env.ref("hr.employee_qdp")
        cls.pieter = cls.env.ref("hr.employee_admin")
        cls.michael = cls.env.ref("hr.employee_niv")

        # Add work schedule (8h/work days) for Gilles, Jack and Michael
        cls.gilles.calendar_id = cls.env.ref("resource.resource_calendar_std")
        cls.jack.calendar_id = cls.env.ref("resource.resource_calendar_std")
        cls.michael.calendar_id = cls.env.ref("resource.resource_calendar_std")

        cls.config = cls.env["res.config.settings"].create({})

        # Create attendance days for employees
        attendances = cls.env["hr.attendance"].search([], order="check_in")
        cls.all_attendances = attendances

        cls.monday = datetime.today().date() - timedelta(
            days=datetime.now().weekday() + 7
        )
        cls.tuesday = cls.monday + timedelta(days=1)
        cls.wednesday = cls.monday + timedelta(days=2)
        cls.thursday = cls.monday + timedelta(days=3)
        cls.friday = cls.monday + timedelta(days=4)
        cls.saturday = cls.monday + timedelta(days=5)

    ##########################################################################
    #                           ATTENDANCE DAY                               #
    ##########################################################################

    def create_att_day_for_date_with_supp_hours(self, date, employee, hours=0):
        """
        Create an attendance for last friday from 09:00 to 17:30 for a
        duration of 8 hours and 30 minutes. A break of 30 minutes is created by
        the system, thereby the paid hours should be 8 hours and the rule
        break 7-9.
        :return: None
        """

        start_01 = date.strftime("%Y-%m-%d 08:00:00")
        stop_01 = date.strftime("%Y-%m-%d 12:00:00")
        # 4h in the morning
        start_02 = date.strftime("%Y-%m-%d 12:30:00")
        stop_hour_2 = f"{16 + hours}:30"
        stop_02 = date.strftime("%Y-%m-%d " + stop_hour_2)
        # 4h in the afternoon
        self.env["hr.attendance"].create(
            {"check_in": start_01, "check_out": stop_01, "employee_id": employee.id, }
        )
        self.env["hr.attendance"].create(
            {"check_in": start_02, "check_out": stop_02, "employee_id": employee.id, }
        )

    def clean_employee_work_history(self, employee):
        employee.period_ids.unlink()

        all_att = self.env["hr.attendance"].search(
            [("employee_id", "=", employee.id)]
        )
        if all_att:
            all_att.unlink()

        all_att_days = self.env["hr.attendance.day"].search(
            [("employee_id", "=", employee.id)]
        )
        if all_att_days:
            all_att_days.unlink()

    def test_annual_no_limit(self):

        self.clean_employee_work_history(self.jack)
        self.clean_employee_work_history(self.michael)

        self.config.max_extra_hours = 2
        self.config.set_max_extra_hours()
        self.assertEqual(self.config.get_max_extra_hours(), 2)
        self.config.free_break = 0.25
        self.config.set_free_break()
        self.assertEqual(self.config.get_free_break(), 0.25)

        self.michael.extra_hours_continuous_cap = False
        self.jack.extra_hours_continuous_cap = True
        for person in [self.jack, self.michael]:
            self.create_att_day_for_date_with_supp_hours(self.monday, person, 1)
            self.create_att_day_for_date_with_supp_hours(self.tuesday, person, 1)
            self.create_att_day_for_date_with_supp_hours(self.wednesday, person, 1)
            self.create_att_day_for_date_with_supp_hours(self.thursday, person, 1)
            self.create_att_day_for_date_with_supp_hours(self.friday, person, 1)

        # Both jack and michael have worked 5 days with 1 hours extra hours
        # each day.
        self.assertEqual(self.jack.balance, 2)
        self.assertEqual(self.jack.extra_hours_lost, 3)
        self.assertEqual(self.michael.balance, 5)
        self.assertEqual(self.michael.extra_hours_lost, 0)
        # Upon switching to continuous computation, michael should loose up to
        # limit of extra hours.
        self.michael.extra_hours_continuous_cap = True
        self.michael._compute_balance()
        self.assertEqual(self.michael.balance, 2)
        self.assertEqual(self.michael.extra_hours_lost, 3)
        # Switching back should come back to 2.5 extra hours.
        self.michael.extra_hours_continuous_cap = False
        self.michael._compute_balance()
        self.assertEqual(self.michael.balance, 5)
        self.assertEqual(self.michael.extra_hours_lost, 0)

        # self.assertRaises(ValidationError, change_date_and_raises(364))

        # Execute cron
        self.env["hr.employee.period"].search(
            [("employee_id", "=", self.jack.id)]
        ).unlink()
        self.env["hr.employee.period"].search(
            [("employee_id", "=", self.michael.id)]
        ).unlink()
        # michael extra hours should be affected by the yearly cutoff
        self.assertEqual(self.jack.balance, 2)
        self.assertEqual(self.michael.balance, 5)
        # self.assertRaises(ValidationError, change_date_and_raises(2))

        # Now will modify an attendance in the recent past and see if the
        # update catch it correctly.
        for person in [self.michael, self.jack]:
            person.attendance_days_ids[-1].attendance_ids[
                0
            ].check_out = person.attendance_days_ids[-1].attendance_ids[
                0
            ].check_out + timedelta(
                hours=3
            )
        self.assertEqual(self.jack.balance, 2)
        self.assertEqual(self.michael.balance, 7.75)
