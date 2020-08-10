odoo.define('hr_attendance_management.attendance', function (require) {
    "use strict";

    var hr_attendance = require('hr_attendance.my_attendances');
    var greeting_message = require('hr_attendance.greeting_message');
    var rpc = require('web.rpc');

    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    var initialize_storage = function() {
        // Store balance when we check in
        window.localStorage.setItem('worked_today', $('#worked_today').text());
        window.localStorage.setItem('balance_today', $('#balance_today').text());

        // We store the time of the check in
        var now = new Date();
        window.localStorage.setItem('initial_hours', now.getHours());
        window.localStorage.setItem('initial_minutes', now.getMinutes());
        window.localStorage.setItem('initial_seconds', now.getSeconds());

        // We may end up here before initialization of the variables, because of
        // asynchronous calls to method of the server
        return window.localStorage.getItem('worked_today') === "";
    }

    var compute_hours = function(item_name) {
        var compute_diff_minutes = function() {
            var init_hours = window.localStorage.getItem('initial_hours');
            var init_minutes = window.localStorage.getItem('initial_minutes');
            var init_seconds = window.localStorage.getItem('initial_seconds');
            var now = new Date();
            var now_hours = now.getHours();
            var now_minutes = now.getMinutes();
            var now_seconds = now.getSeconds();

            return Math.trunc(((now_seconds - init_seconds) +
                (now_minutes - init_minutes) * 60 +
                (now_hours - init_hours) * 3600) / 60);
        }

        var displayed_time = window.localStorage.getItem(item_name);
        var matches = displayed_time.match(/^-?(\d{2}):(\d{2})$/);

        if (matches !== null) {
            var hours = parseInt(matches[1]);
            var minutes = parseInt(matches[2]);
            var total_minutes = (minutes + (hours * 60)) *
                (matches[0].substring(0, 1) === '-' ? -1 : 1);

            var new_minutes = compute_diff_minutes();
            if (new_minutes < 0) {
                return; // We don't want to decrease working time
            }
            var negative = total_minutes + new_minutes < 0;
            var new_total = Math.abs(total_minutes + new_minutes);

            var new_hours = ('0' + Math.trunc(new_total / 60)).slice(-2);
            var new_minutes = ('0' + (new_total % 60)).slice(-2);

            $('#' + item_name).text((negative ? '-' : '') +
                new_hours + ':' + new_minutes);
            if (item_name !== 'worked_today') {
                $('#' + item_name).parent().get(0).style.color = negative ?
                    'red' : 'green';
            }
        }
    }

    var start_dynamic_hours = function() {
        var interval_id = setInterval(
            function() {
                if (window.localStorage.getItem('init_time') === 'true') {
                    var still_need_init = initialize_storage();
                    window.localStorage.setItem('init_time', still_need_init);
                }
                if ($('#state').text() === 'checked in') {
                    compute_hours('worked_today');
                    compute_hours('balance_today');
                }
            }, 1000
        );
        window.localStorage.setItem('interval_id', interval_id);
    }

    var stop_dynamic_hours = function() {
        var interval_id = window.localStorage.getItem('interval_id');
        if (interval_id) {
            clearInterval(interval_id);
            window.localStorage.removeItem('interval_id');
        }
    }

    // We look for URL changes, corresponding we leave the actual page
    window.addEventListener('popstate', function (event) {
        stop_dynamic_hours();
    });

    // We look for focus on page, we want to retrigger the function
    window.onfocus = function() {
        stop_dynamic_hours();
        start_dynamic_hours();
    }


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
            });

            // We make sure to remove any existing interval
            stop_dynamic_hours();
            window.localStorage.setItem('init_time', true);
            start_dynamic_hours();

            return result;
        },
        update_attendance: function () {
            window.localStorage.setItem('init_time', true);
            var loc_id = parseInt($('#location').val(), 10);
            this.getSession().user_context.default_location_id = loc_id;
            var self = this;
            // We bypass parent method in order to add context in the request
            this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
                context: this.getSession().user_context
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
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
