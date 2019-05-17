# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestAllocationWizard(common.TransactionCase):
    def setUp(self):
        super(TestAllocationWizard, self).setUp()
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

        self.department = self.env['hr.department'].create({
            'name': 'Department 1'
        })

        self.category = self.env['hr.employee.category'].create({
            'name': 'Category 1'
        })

        self.employee_1 = self.env['hr.employee'].create({
            'name': 'Employee 1',
            'resource_calendar_id': self.calendar.id,
            'department_id': self.department.id
        })

        self.employee_2 = self.env['hr.employee'].create({
            'name': 'Employee 2',
            'resource_calendar_id': self.calendar.id,
            'category_ids': [(4, self.category.id)]
        })

        self.employee_3 = self.env['hr.employee'].create({
            'name': 'Employee 3',
            'resource_calendar_id': self.calendar.id,
            'department_id': self.department.id,
            'category_ids': [(4, self.category.id)]
        })

        self.status = self.env['hr.holidays.status'].create({
            'name': 'Status 1',
        })

        self.wizard = self.env['hr.holidays.allocation.wizard'].create({
            'holiday_status_id': self.status.id,
            'duration': 12
        })

    def test_populate(self):
        self.wizard.populate()
        self.assertIn(self.employee_1, self.wizard.employee_ids)
        self.assertIn(self.employee_2, self.wizard.employee_ids)
        self.assertIn(self.employee_3, self.wizard.employee_ids)
        self.wizard.write({'department_id': self.department.id})
        self.wizard.populate()
        self.assertIn(self.employee_1, self.wizard.employee_ids)
        self.assertNotIn(self.employee_2, self.wizard.employee_ids)
        self.assertIn(self.employee_3, self.wizard.employee_ids)
        self.wizard.write({'category_id': self.category.id})
        self.wizard.populate()
        self.assertNotIn(self.employee_1, self.wizard.employee_ids)
        self.assertNotIn(self.employee_2, self.wizard.employee_ids)
        self.assertIn(self.employee_3, self.wizard.employee_ids)
        self.wizard.write({'department_id': False})
        self.wizard.populate()
        self.assertNotIn(self.employee_1, self.wizard.employee_ids)
        self.assertIn(self.employee_2, self.wizard.employee_ids)
        self.assertIn(self.employee_3, self.wizard.employee_ids)

    def test_create(self):
        self.wizard.write({
            'category_id': self.category.id,
            'department_id': self.department.id
        })
        self.wizard.populate()
        self.wizard.create_allocations()
        allocation = self.env['hr.holidays'].search([
            ('employee_id', '=', self.employee_3.id),
            ('type', '=', 'add'),
            ('state', '=', 'validate'),
        ])
        self.assertTrue(allocation)

        status2 = self.env['hr.holidays.status'].create({
            'name': 'Status 2',
            'double_validation': True,
            'count_in_hours': True,
        })
        self.wizard.write({'holiday_status_id': status2.id})
        self.wizard.create_allocations()
        allocation = self.env['hr.holidays'].search([
            ('type', '=', 'add'),
            ('holiday_status_id', '=', status2.id),
            ('state', '=', 'validate'),
        ])
        self.assertTrue(allocation)
