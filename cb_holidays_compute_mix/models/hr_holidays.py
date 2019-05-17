# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil import tz


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    _order = 'create_date desc'

    def _default_employee(self):
        return self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)

    employee_id = fields.Many2one(
        required=True, default=lambda self: self._default_employee()
    )

    time_description = fields.Char(
        string='Time',
        compute='_compute_time_description',
        readonly=True,
    )

    count_in_hours = fields.Boolean(
        related='holiday_status_id.count_in_hours',
        readonly=True)

    date_from_full = fields.Date(
        compute="_compute_date_from_full",
        inverse="_inverse_date_from_full",
        readonly=True,
        states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)]
        },
    )
    date_to_full = fields.Date(
        compute="_compute_date_to_full",
        inverse="_inverse_date_to_full",
        readonly=True,
        states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)]
        },
    )

    number_of_hours_temp = fields.Float(
        string='Allocation in Hours',
        digits=(2, 2),
        readonly=True,
        states={'draft': [('readonly', False)],
                'confirm': [('readonly', False)]}
    )
    number_of_hours = fields.Float(
        compute='_compute_number_of_hours',
        store=True
    )
    virtual_hours = fields.Float(
        compute='_compute_number_of_hours',
        store=True
    )
    working_hours = fields.Float(digits=(2, 2))

    # Supporting field for avoiding limitation on storing readonly fields
    number_of_days_temp_related = fields.Float(
        related="number_of_days_temp", readonly=True,
    )
    # Supporting field for avoiding limitation on storing readonly fields
    number_of_hours_related = fields.Float(
        related="number_of_hours_temp", readonly=True,
    )

    ####################################################
    # Date Swaps methods
    ####################################################

    @api.depends('date_from')
    def _compute_date_from_full(self):
        for record in self.filtered('date_from'):
            tz_name = record.employee_id.user_id.tz or record.env.user.tz
            dt = fields.Datetime.from_string(record.date_from).replace(
                tzinfo=tz.tzutc(),
            ).astimezone(tz.gettz(tz_name)).date()
            record.date_from_full = fields.Date.to_string(dt)

    @api.depends('date_to')
    def _compute_date_to_full(self):
        for record in self.filtered('date_to'):
            tz_name = record.employee_id.user_id.tz or record.env.user.tz
            dt = fields.Datetime.from_string(record.date_to).replace(
                tzinfo=tz.tzutc(),
            ).astimezone(tz.gettz(tz_name)).date()
            record.date_to_full = fields.Date.to_string(dt)

    def _inverse_date_from_full(self):
        for record in self.filtered(
                lambda r: not r.count_in_hours and r.date_from_full):
            tz_name = record.employee_id.user_id.tz or record.env.user.tz
            dt = fields.Datetime.from_string(record.date_from_full).replace(
                hour=0, minute=0, second=0, microsecond=0,
                tzinfo=tz.gettz(tz_name),
            ).astimezone(tz.tzutc())
            record.date_from = fields.Datetime.to_string(dt)
            record._onchange_date_to()

    def _inverse_date_to_full(self):
        for record in self.filtered(
                lambda r: not r.count_in_hours and r.date_to_full):
            tz_name = record.employee_id.user_id.tz or record.env.user.tz
            dt = fields.Datetime.from_string(record.date_to_full).replace(
                hour=23, minute=59, second=59, microsecond=999999,
                tzinfo=tz.gettz(tz_name),
            ).astimezone(tz.tzutc())
            record.date_to = fields.Datetime.to_string(dt)
            record._onchange_date_to()

    @api.onchange('count_in_hours')
    def _onchange_count_in_hours(self):
        self._inverse_date_to_full()
        self._inverse_date_from_full()
        for record in self.filtered('count_in_hours'):
            tz_name = record.env.user.tz
            dt = fields.Datetime.from_string(fields.Datetime.now())
            dt = dt.replace(tzinfo=tz.gettz(tz_name), second=0, microsecond=0)
            record.date_from = fields.Datetime.to_string(dt)
            record.date_to = fields.Datetime.to_string(dt)
            if record.employee_id:
                record._set_number_of_hours_temp()

    @api.onchange('date_from_full')
    def _onchange_date_from_full(self):
        self._inverse_date_from_full()
        self._onchange_date_to()

    @api.onchange('date_to_full')
    def _onchange_date_to_full(self):
        self._inverse_date_to_full()
        self._onchange_date_to()

    ####################################################
    # Compute methods
    ####################################################

    @api.onchange('employee_id', 'holiday_status_id', 'date_from', 'date_to')
    def _recompute_number_of_days(self):
        # Check in context what form is open: add or remove
        if self.env.context.get('default_type', '') == 'add':
            return
        self._onchange_date_to()
        self.department_id = None
        self.number_of_hours_temp = 0.0
        if self.employee_id:
            self._set_number_of_hours_temp()
            self.department_id = self.employee_id.department_id

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """If we dont exclude rest days, the holiday time is just the time
        difference between the start and the end.
        """
        if not self.holiday_status_id.exclude_rest_days:
            employee_id = None
        return super(HrHolidays, self)._get_number_of_days(
            date_from, date_to, employee_id,
        )

    @api.multi
    def _set_number_of_hours_temp(self):
        self.ensure_one()
        self.number_of_hours_temp = self._compute_work_hours()

    @api.multi
    def _compute_work_hours(self):
        self.ensure_one()
        employee = self.employee_id
        work_hours = 0.0
        if self.date_from and self.date_to:
            from_dt = fields.Datetime.from_string(self.date_from)
            to_dt = fields.Datetime.from_string(self.date_to)
            emp_work_hours = employee.iter_work_hours_count(from_dt, to_dt)
            work_hours_data = [item for item in emp_work_hours]
            for index, (day, work_hours_count) in enumerate(work_hours_data):
                work_hours += work_hours_count

        return work_hours

    @api.depends('number_of_hours_temp', 'state')
    def _compute_number_of_hours(self):
        for rec in self:
            number_of_hours = rec.number_of_hours_temp
            if rec.type == 'remove':
                number_of_hours = -rec.number_of_hours_temp

            rec.virtual_hours = number_of_hours
            if rec.state not in ('validate',):
                number_of_hours = 0.0
            rec.number_of_hours = number_of_hours

    @api.constrains(
        'state',
        'number_of_days_temp',
        'number_of_hours_temp',
        'holiday_type',
        'type',
        'employee_id',
        'holiday_status_id')
    def _check_holidays(self):
        super(HrHolidays,
              self.filtered(lambda r: not r.count_in_hours))._check_holidays()
        for holiday in self.filtered(lambda r: r.count_in_hours):
            if holiday.holiday_type != 'employee' or holiday.type != 'remove':
                continue
            if holiday.employee_id and not holiday.holiday_status_id.limit:
                leave_hours = holiday.holiday_status_id.get_hours(
                    holiday.employee_id
                )
                remaining = leave_hours['remaining_hours']
                virt_remaining = leave_hours['virtual_remaining_hours']
                if remaining < 0 or virt_remaining < 0:
                    # Raising a warning gives a more user-friendly
                    # feedback than the default constraint error
                    raise ValidationError(_(
                        'The number of remaining hours is not sufficient for '
                        'this leave type.\nPlease check for allocation'
                        'requests awaiting validation.'))

    @api.constrains('number_of_hours_temp')
    def _check_number_of_hours_temp(self):
        for holiday in self:
            if holiday.type == 'remove' and holiday.number_of_hours_temp < 0:
                raise ValidationError(
                    _('Hours of a leave request cannot be a negative number.')
                )

    @api.depends('holiday_status_id', 'number_of_days_temp',
                 'number_of_hours_temp')
    def _compute_time_description(self):
        for record in self:
            if record.count_in_hours:
                record.time_description = "%.2f hour(s)" % \
                                          record.number_of_hours_temp
            else:
                record.time_description = "%.2f day(s)" %\
                                          record.number_of_days_temp

    @api.multi
    def name_get(self):
        res = super(
            HrHolidays,
            self.filtered(
                lambda r: not r.count_in_hours and r.holiday_status_id
                and r.employee_id)
        ).name_get()

        for leave in self.filtered(
                lambda r: r.count_in_hours and r.holiday_status_id
                and r.employee_id):
            res.append((leave.id, _("%s on %s : %.2f hour(s)") % (
                leave.employee_id.name,
                leave.holiday_status_id.name,
                leave.number_of_hours_temp
            )))
        for leave in self.filtered(
                lambda r: not r.holiday_status_id or not r.employee_id):
            res.append((leave.id, _('Leave Request')))
        return res

    @api.multi
    def _prepare_create_by_category(self, employee):
        self.ensure_one()
        values = super(HrHolidays, self)._prepare_create_by_category(employee)
        values.update({
            'number_of_hours_temp': self.number_of_hours_temp,
        })
        return values
