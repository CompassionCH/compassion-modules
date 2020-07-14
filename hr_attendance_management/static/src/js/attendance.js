odoo.define('hr_attendance_management.attendance', function (require) {
    "use strict";

    var core = require('web.core');

    var hr_attendance = require('hr_attendance.my_attendances');
    var greeting_message = require('hr_attendance.greeting_message');
    var session = require('web.session');
    var rpc = require('web.rpc');

    var QWeb = core.qweb;
    var _t = core._t;

    window.localStorage.setItem('trigger_source', 'other');
    // We look for URL changes, corresponding we leave the actual page
    window.addEventListener('popstate', function (event) {
        var interval_id = window.localStorage.getItem('interval_id');
        var trigger_source = window.localStorage.getItem('trigger_source');

        // We don't clear the interval after the greeting message (the
        // start() function won't be called afterward in that case)
        if (interval_id && trigger_source !== 'back_from_update') {
            clearInterval(interval_id);
            window.localStorage.removeItem('interval_id');
        }

        // Check if we go to or leave greeting page
        if (trigger_source === 'from_update_attendance') {
            window.localStorage.setItem('trigger_source', 'back_from_update');
        } else if (trigger_source === 'back_from_update') {
            window.localStorage.setItem('trigger_source', 'other');
        }
    });


    hr_attendance.include({
        start: function () {
            var self = this;
            self.hr_location = [];
            var result = this._super();
            rpc.query({
                model: 'hr.employee',
                method: 'get_current_employee',
                args: [],
            })
            .then(function (employee) {
                if (_.isEmpty(employee) ) {
                    self.$('.o_hr_attendance_employee')
                    .append(_t("Error : Could not find" + "employee linked to user"));
                    return;
                }
                self.employee = employee[0]
                rpc.query({
                model: 'hr.attendance.location',
                method: 'search',
                args: [[]],
                })
                .then(function (location_ids) {
                    rpc.query({
                        model: 'hr.attendance.location',
                        method: 'read',
                        args: [location_ids, ['name']],
                    })
                     .then(function (result) {
                        self.hr_location = result;
                        self.$el.html(QWeb.render(
                            "HrAttendanceMyMainMenu",
                            {widget: self}));
                    });
                });
            })

            // Update worked hours dynamically
            var interval_id = setInterval(
                function() {
                    if ($('#state').text() === 'checked in') {
                        var start_time = window.localStorage.getItem('start_time')

                        ['worked_today', 'balance_today'].forEach(
                            function (el) {
                                var diff_minutes =
                                    moment().diff(moment(start_time), 'minutes');
                                var matches = $('#' + el)
                                    .text().match(/^-?(\d{2}):(\d{2})$/);

                                if (matches !== null && diff_minutes >= 1) {
                                    var hours = parseInt(matches[1]);
                                    var minutes = parseInt(matches[2]);

                                    var total_minutes = (minutes +
                                        (hours * 60)) *
                                        (matches[0].substring(0, 1) ===
                                         '-' ? -1 : 1);
                                    var negative = total_minutes +
                                        diff_minutes < 0;

                                    var new_total = Math.abs(total_minutes +
                                        diff_minutes);
                                    var new_hours =
                                        ('0' + Math.trunc(new_total / 60))
                                            .slice(-2);
                                    var new_minutes =
                                        ('0' + (new_total % 60)).slice(-2);

                                    $('#' + el).text((negative ? '-' : '') +
                                        new_hours + ':' + new_minutes);

                                    if (el !== 'worked_today') {
                                        $('#' + el).parent()
                                            .get(0).style.color =
                                        negative ? 'red' : 'green';
                                    }
                                    // We update the time for the next time difference
                                    window.localStorage.setItem('start_time', new Date())
                                }
                            }
                        );
                    }
                }, 5000
            )
            window.localStorage.setItem('interval_id', interval_id);
            // We save the time at which the widget was created
            window.localStorage.setItem('start_time', new Date());

            return result;
        },
        update_attendance: function () {
            // We don't want to clear interval because we stay on the same page
            window.localStorage.setItem('trigger_source', 'from_update_attendance');
            var loc_id = parseInt($('#location').val(), 10);
            session.user_context['default_location_id'] = loc_id;
            this._super();
        },
    });

    greeting_message.include({
        setAttendanceMessageTimeout: function (context) {
            return function () {
                setTimeout(function () {
                    context.do_action(context.next_action, {
                        clear_breadcrumbs: true,
                    });
                }, 5000);
            };
        },
    });
});
