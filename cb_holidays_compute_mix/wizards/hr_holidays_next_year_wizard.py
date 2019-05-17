# Copyright 2019 Creu Blanca
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrHolidaysNextYearPublicHolidays(models.TransientModel):

    _name = "hr.holidays.next.year.public.holidays"

    pending_lines = fields.One2many(
        'hr.holidays.public.line.transient',
        inverse_name='wizard_id'
    )
    year = fields.Integer(string='Year', readonly=True)
    country_id = fields.Many2one('res.country',
                                 string='Country',
                                 readonly=True)

    @api.model
    def default_get(self, fields_list):
        rec = super().default_get(fields_list)
        last_year = self.env['hr.holidays.public'].search(
            [], order='year desc', limit=1) or False
        if not last_year:
            raise UserError(_(
                'No Public Holidays found as template. '
                'Please create the first Public Holidays manually.'))

        year = last_year.year + 1
        vals_list = []
        for line in last_year.line_ids.filtered(lambda r: r.variable_date):
            date = fields.Datetime.from_string(line.date)
            date = fields.Datetime.to_string(
                date.replace(year=year)
            )
            data = (0, 0, {'name': line.name,
                           'date': date,
                           'line_id': line.id
                           })
            vals_list.append(data)
        rec.update({
            'year': year,
            'pending_lines': vals_list,
            'country_id': last_year.country_id.id
        })
        return rec

    @api.multi
    def create_public_holidays(self):
        last_year = self.env['hr.holidays.public'].search(
            [], order='year desc', limit=1) or False
        calendar = self.env['hr.holidays.public'].create({
            'year': self.year,
            'country_id': self.country_id.id,
            'line_ids': []
        })
        for line in last_year.line_ids.filtered(
                lambda r: not r.variable_date):
            date = fields.Date.from_string(line.date)
            date = date.replace(year=self.year)
            new_vals = {
                'year_id': calendar.id,
                'date': fields.Date.to_string(date)
            }
            line.copy(new_vals)

        for line in self.pending_lines:
            new_vals = {
                'year_id': calendar.id,
                'name': line.name,
                'date': line.date
            }
            line.line_id.copy(new_vals)

        action = {
            'type': 'ir.actions.act_window',
            'name': 'New public holidays calendar',
            'view_mode': 'form',
            'res_model': 'hr.holidays.public',
            'res_id': calendar.id
        }
        return action


class PublicHolidaysLineTransient(models.TransientModel):

    _name = 'hr.holidays.public.line.transient'
    _order = 'date'

    name = fields.Char(string='Description')
    date = fields.Date(string='Date')
    wizard_id = fields.Many2one('hr.holidays.next.year.public.holidays')
    line_id = fields.Many2one('hr.holidays.public.line')
