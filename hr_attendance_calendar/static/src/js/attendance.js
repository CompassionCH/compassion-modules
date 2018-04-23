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

                    // auto-counter
                    $('#moment_pl').html(Date.now());
                    setInterval(function () {
                        if ($('#moment_pl').length) {
                            var moment_start = moment(new Date(parseInt($('#moment_pl').text(), 10)));
                            var diff_minutes = moment().diff(moment_start, 'minutes');

                            ['worked_today', 'balance_today'].forEach(
                                function (el) {
                                    var matches = $('#' + el + '_pl').text().match(/^-?(\d{2}):(\d{2})$/);

                                    if (matches !== null && $('#state').text() === 'checked in') {
                                        var hours = parseInt(matches[1], 10);
                                        var minutes = parseInt(matches[2], 10);

                                        var total_minutes = (minutes + (hours * 60)) * (matches[0].substring(0, 1) === '-' ? -1 : 1);// eslint-disable-line no-extra-parens
                                        var negative = total_minutes + diff_minutes < 0;

                                        var new_total = Math.abs(total_minutes + diff_minutes);
                                        var new_hours = ('0' + Math.trunc(new_total / 60)).slice(-2); // eslint-disable-line no-extra-parens
                                        var new_minutes = ('0' + (new_total % 60)).slice(-2); // eslint-disable-line no-extra-parens

                                        $('#' + el).text((negative ? '-' : '') + new_hours + ':' + new_minutes);

                                        if (el !== 'worked_today') {
                                            $('#' + el).parent().get(0).style.color = negative ? 'red' : 'green';
                                        }
                                    }
                                });
                        }
                    }, 20000);
                });

            return result;
        },
    });
});
