# Copyright 2015 iDT LABS (http://www.@idtlabs.sl)
# Copyright 2017 Tecnativa - Pedro M. Baeza
# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common
from mock import patch


class TestHolidaysComputeDays(common.TransactionCase):
    def setUp(self):
        super(TestHolidaysComputeDays, self).setUp()
        self.HrHolidays = self.env['hr.holidays']
        self.calendar = self.env['resource.calendar'].create({
            'name': 'Calendar',
            'attendance_ids': [],
        })
        for day in range(5):  # From monday to friday
            self.calendar.attendance_ids = [
                (0, 0, {
                    'name': 'Attendance',
                    'dayofweek': str(day),
                    'hour_from': '08',
                    'hour_to': '12',
                }),
                (0, 0, {
                    'name': 'Attendance',
                    'dayofweek': str(day),
                    'hour_from': '14',
                    'hour_to': '18',
                }),
            ]
        self.employee = self.env['hr.employee'].create({
            'name': 'Employee 1',
            'resource_calendar_id': self.calendar.id,
        })
        self.holiday_type = self.env['hr.holidays.status'].create({
            'name': 'Leave Type Test',
            'exclude_rest_days': True,
        })
        self.holiday_type_no_excludes = self.env['hr.holidays.status'].create({
            'name': 'Leave Type Test Without excludes',
            'exclude_rest_days': False,
        })
        self.holiday_type_hours = self.env['hr.holidays.status'].create({
            'name': 'Leave Type Test',
            'count_in_hours': True,
        })
        # Remove timezone for controlling data better
        self.env.user.tz = False

    def test_onchange_dates(self):
        with patch('odoo.fields.Datetime.now') as p:
            p.return_value = '1946-12-20 12:00:00'
            holidays = self.HrHolidays.new({
                'date_from_full': '1946-12-20',
                'date_to_full': '1946-12-21',
                'holiday_status_id': self.holiday_type.id,
                'employee_id': self.employee.id,
            })
            holidays._onchange_count_in_hours()
            self.assertEqual(holidays.date_from, '1946-12-20 00:00:00')
            self.assertEqual(holidays.date_to, '1946-12-21 23:59:59')
            holidays = self.HrHolidays.new({
                'date_from_full': '1946-12-20',
                'date_to_full': '1946-12-21',
                'holiday_status_id': self.holiday_type_hours.id,
                'employee_id': self.employee.id,
            })
            holidays._onchange_count_in_hours()
            self.assertEqual(holidays.date_from, '1946-12-20 12:00:00')
            self.assertEqual(holidays.date_to, '1946-12-20 12:00:00')

    def test_compute_dates(self):
        holidays = self.HrHolidays.new({
            'date_from': '1946-12-20 08:10:00',
            'date_to': '1946-12-21 15:45:30',
            'holiday_status_id': self.holiday_type_no_excludes.id,
            'employee_id': self.employee.id,
        })
        self.assertEqual(holidays.date_from_full, '1946-12-20')
        self.assertEqual(holidays.date_to_full, '1946-12-21')
        self.assertEqual(
            holidays._get_number_of_days(
                '1946-12-20 08:10:00', '1946-12-20 05:10:00', self.employee.id
            ), 0)

    def test_number_days_not_excluding(self):
        holidays = self.HrHolidays.new({
            'date_from': '1946-12-22 00:00:00',  # Monday
            'date_to': '1946-12-29 23:59:59',  # Sunday
            'holiday_status_id': self.holiday_type_no_excludes.id,
            'employee_id': self.employee.id,
        })
        holidays._onchange_date_from_full()
        holidays._onchange_date_to_full()
        self.assertEqual(holidays.number_of_days_temp, 8.0)

    def test_others(self):
        holidays = self.HrHolidays.new({
            'date_from': '1946-12-27 09:00:00',  # Monday
            'date_to': '1946-12-27 12:00:00',  # Sunday
            'holiday_status_id': self.holiday_type_hours.id,
            'employee_id': self.employee.id,
        })
        holidays._set_number_of_hours_temp()
        values = holidays._prepare_create_by_category(self.employee)
        self.assertTrue(values.get('number_of_hours_temp'))
        holidays._compute_time_description()
        self.assertEqual(holidays.time_description, '3.00 hour(s)')
        holidays = self.HrHolidays.new({
            'date_from': '1946-12-22 00:00:00',  # Monday
            'date_to': '1946-12-24 23:59:59',  # Sunday
            'holiday_status_id': self.holiday_type_no_excludes.id,
            'employee_id': self.employee.id,
        })
        holidays._onchange_date_to()
        holidays._compute_time_description()
        self.assertEqual(holidays.time_description, '3.00 day(s)')
        action = self.employee.action_view_leaves_left()
        self.assertTrue(action)
