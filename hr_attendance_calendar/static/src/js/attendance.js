odoo.define('hr_switzerland.attendance', function (require) {
"use strict";

    var core = require('web.core');

    var hr_attendance = require('hr_attendance.my_attendances');

    var Model = require('web.Model');

    var QWeb = core.qweb;
    var _t = core._t;

    hr_attendance.include({
        start: function () {
            var self = this;
            var result = this._super();
            var hr_employee = new Model('hr.employee');
            hr_employee.query(['attendance_state', 'name', 'extra_hours_formatted', 'today_hour_formatted', 'time_warning_balance', 'time_warning_today', 'extra_hours_today'])
                .filter([['user_id', '=', self.session.uid]])
                .all()
                .then(function (res) {
                    if (_.isEmpty(res) ) {
                        self.$('.o_hr_attendance_employee').append(_t("Error : Could not find employee linked to user"));
                        return;
                    }
                    self.employee = res[0];
                    self.$el.html(QWeb.render("HrAttendanceMyMainMenu", {widget: self}));
                });

            return result;
        },

    });
});
