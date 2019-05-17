# Copyright 2019 Creu Blanca
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class HrHolidaysPendingEmployees(models.TransientModel):

    _name = 'hr.holidays.pending.employees'

    holiday_status_id = fields.Many2one(
        'hr.holidays.status', string='Holiday Type',
        domain=[('limit', '=', False)]
    )

    pending_employees_ids = fields.One2many(
        'hr.holidays.pending.employees.line',
        string='Holiday Type',
        inverse_name='wizard_id',
        readonly=True,
        compute='_compute_pending_employees'
    )

    @api.depends('holiday_status_id')
    def _compute_pending_employees(self):
        if not self.holiday_status_id:
            self.pending_employees_ids.unlink()
            return
        vals_list = []
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            if self.holiday_status_id.count_in_hours:
                data_days = self.holiday_status_id.get_hours(employee)
                remaining_leaves = data_days.get('remaining_hours', 0)
                time = ' hours'
            else:
                data_days = self.holiday_status_id.get_days(employee.id)
                result = data_days.get(self.holiday_status_id.id, {})
                remaining_leaves = result.get('remaining_leaves', 0)
                time = ' days'
            if remaining_leaves > 0:
                vals_list.append((0, 0, {
                    'employee_id': employee.id,
                    'remaining': str(remaining_leaves) + time
                }))
        self.pending_employees_ids = vals_list


class HrHolidaysPendingEmployeesLine(models.TransientModel):

    _name = 'hr.holidays.pending.employees.line'

    wizard_id = fields.Many2one('hr.holidays.pending.employees')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one(
        related='employee_id.department_id', string='Department'
    )
    job_id = fields.Many2one(
        related='employee_id.job_id', string='Job Position'
    )
    manager_id = fields.Many2one(
        related='employee_id.parent_id', string='Manager'
    )
    remaining = fields.Char('Remaining')
