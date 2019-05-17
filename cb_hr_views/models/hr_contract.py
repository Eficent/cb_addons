# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrContract(models.Model):

    _inherit = 'hr.contract'

    working_hours_type = fields.Selection(
        selection=[('full', 'Full Time'),
                   ('part', 'Part time'),
                   ('reduced', 'Reduced')],
        string='Working Hours Type',
        default='full',
        track_visibility="onchange",
    )
    percentage_of_reduction = fields.Integer(
        'Percentage of Reduction',
        track_visibility="onchange",
    )

    substituting_id = fields.Many2one(
        'hr.employee',
        'Substituting',
        track_visibility="onchange",
    )

    substitute_contract = fields.Boolean(
        related='type_id.substitute_contract',
        track_visibility="onchange",
    )

    resource_calendar_id = fields.Many2one(required=False, default=False)

    # Track Visibility
    type_id = fields.Many2one(track_visibility='onchange')
    job_id = fields.Many2one(track_visibility='onchange')
    company_id = fields.Many2one(track_visibility='onchange')
    date_start = fields.Date(track_visibility='onchange')
    date_end = fields.Date(track_visibility='onchange')
    trial_date_end = fields.Date(track_visibility='onchange')
    department_id = fields.Many2one(track_visibility='onchange')
    employee_id = fields.Many2one(track_visibility='onchange')
    name = fields.Char(track_visibility='onchange')

    @api.onchange('type_id')
    def _onchange_type_id(self):
        for record in self:
            if not record.type_id.substitute_contract:
                record.substituting_id = False

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for record in self.filtered('employee_id'):
            record.employee_id._compute_contract_id()
        return res


class ContractType(models.Model):

    _inherit = 'hr.contract.type'
    substitute_contract = fields.Boolean(
        string='Substitute Contract',
        help='Check if this is a substitution contract'
    )
