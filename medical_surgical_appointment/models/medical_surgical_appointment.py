# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta


import logging
_logger = logging.getLogger(__name__)
try:
    from fuzzywuzzy import fuzz
except ImportError:
    _logger.debug('Can not import fuzzywuzzy.')
    fuzz = False


class MedicalSurgicalAppointment(models.Model):
    _name = 'medical.surgical.appointment'
    _rec_name = 'internal_identifier'
    _description = 'Medical Surgical Appointment'
    _inherit = ['medical.abstract', 'mail.thread', 'mail.activity.mixin']

    patient_id = fields.Many2one(
        string='Patient',
        comodel_name='medical.patient',
        track_visibility=True,
        ondelete='restrict', index=True,
        readonly=True, states={'draft': [('readonly', False)]},
        help='Patient Name',
    )

    selected_patient = fields.Boolean()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed_reservation', 'Confirmed Reservation'),
            ('confirmed_patient', 'Confirmed Patient'),
            ('arrived', 'Arrived'),
            ('cancelled', 'Cancelled'),
        ],
        required=True,
        default='draft',
        track_visibility='onchange',
    )

    firstname = fields.Char(
        string='First Name', readonly=True,
        states={'draft': [('readonly', False)]},
    )
    lastname = fields.Char(
        string='Last Name',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    lastname2 = fields.Char(
        string='Second Last Name',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    vat = fields.Char(
        string='VAT',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')],
        readonly=True, states={'draft': [('readonly', False)]},
    )

    birth_date = fields.Date(
        string='Birth Date',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    phone = fields.Char(
        string='Phone',
        readonly=True, states={'draft': [('readonly', False)]}
    )
    mobile = fields.Char(
        string='Mobile',
        readonly=True, states={'draft': [('readonly', False)]}
    )
    email = fields.Char(
        string='Email',
        readonly=True, states={'draft': [('readonly', False)]}
    )

    center_id = fields.Many2one(
        'res.partner',
        'Center',
        related="location_id.center_id",
        readonly=True,
        store=True,
    )
    location_id = fields.Many2one(
        string="Location",
        comodel_name='res.partner',
        domain=[
            ('is_location', '=', True),
            ('allow_surgical_appointment', '=', True)
        ],
        track_visibility=True,
        ondelete='restrict', index=True,
        required=True,
        readonly=True, states={'draft': [('readonly', False)]}
    )

    service_id = fields.Many2one(
        string='Service',
        comodel_name='product.product',
        ondelete='restrict', index=True,
        domain=[('type', '=', 'service'),
                ('allow_surgical_appointment', '=', True)],
        readonly=True, states={'draft': [('readonly', False)]}
    )

    start_date = fields.Datetime(
        string='Start Date',
        required=True,
        # maybe we should split it by date / time and keep
        # start_date as date + time ????
        track_visibility='onchange',
        readonly=True, states={'draft': [('readonly', False)]}
    )
    duration = fields.Float(
        string='Duration (in hours)',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]}
    )
    end_date = fields.Datetime(
        string='End Date',
        store=True,
        compute='_compute_end_date',
        track_visibility='onchange',
        readonly=True,
    )

    # Practitioners

    surgeon_id = fields.Many2one(
        'res.partner',
        domain=[('allow_surgical_appointment', '=', True),
                ('is_practitioner', '=', True)],
        string='Surgeon',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]}
    )
    aux_surgeon_id = fields.Many2one(
        'res.partner',
        domain=[('allow_surgical_appointment', '=', True),
                ('is_practitioner', '=', True)],
        string='Auxiliary Surgeon',
        readonly=True, states={'draft': [('readonly', False)]}
    )

    encounter_id = fields.Many2one(
        'medical.encounter',
    )

    # Coverage

    payor_id = fields.Many2one(
        string='Payor',
        comodel_name='res.partner',
        domain=[('is_payor', '=', True)],
        ondelete='restrict', index=True,
        track_visibility=True,
        help='Payer name',
        readonly=True, states={
            'confirmed_reservation': [('readonly', False)]}
    )

    sub_payor_id = fields.Many2one(
        'res.partner',
        "Sub payor",
        readonly=True, states={
            'confirmed_reservation': [('readonly', False)]}
    )

    coverage_template_id = fields.Many2one(
        string='Coverage Template',
        comodel_name='medical.coverage.template',
        ondelete='restrict', index=True,
        help='Coverage Template',
        readonly=True, states={
            'confirmed_reservation': [('readonly', False)]}
    )

    subscriber_id = fields.Char(
        string='Subscriber Id',
        readonly=True, states={
            'confirmed_reservation': [('readonly', False)]}
    )

    authorization_number = fields.Char(
        track_visibility=True,
        readonly=True, states={
            'confirmed_reservation': [('readonly', False)]}
    )

    patient_name = fields.Char(
        string='Patient Name',
        compute='_compute_patient_name',
        readonly=True, states={'draft': [('readonly', False)]}
    )
    patient_interned = fields.Boolean()
    service_patient_interned = fields.Boolean(
        related='service_id.patient_interned'
    )
    information = fields.Text(
        compute='_compute_information'
    )

    @api.depends('start_date', 'coverage_template_id', 'service_id', 'location_id')
    def _compute_information(self):
        for record in self:
            record.information = record._get_information()

    def _get_information(self):
        informations = []
        item = self.env['medical.coverage.agreement.item'].get_item(
            product=self.service_id, coverage_template=self.coverage_template_id,
            center=self.location_id.center_id, date=fields.Date.to_string(
                fields.Datetime.from_string(self.start_date).date()
            ),
        )
        if not item:
            informations.append(_('Not covered'))
        if item and item.authorization_method_id.authorization_required:
            informations.append(_('Authorization required'))
        return '\n'.join(informations)

    @api.depends('firstname', 'lastname', 'lastname2', 'patient_id')
    def _compute_patient_name(self):
        for record in self:
            firstname = record.firstname or ''
            lastname = record.lastname or ''
            lastname2 = record.lastname2 or ''
            record.patient_name = '%s %s %s' % (lastname, lastname2, firstname)

    @api.depends('start_date', 'duration')
    def _compute_end_date(self):
        for record in self:
            if record.start_date:
                hours = record.duration or 0.0
                record.end_date = fields.Datetime.to_string(
                    fields.Datetime.from_string(
                        record.start_date
                    ) + timedelta(hours=hours)
                )
            else:
                record.end_date = False

    @api.model
    def _get_internal_identifier(self, vals):
        return self.env['ir.sequence'].next_by_code(
            'medical.surgical.appointment') or '/'

    @api.onchange('payor_id')
    def _onchange_payor(self):
        for record in self:
            coverage_template = False
            sub_payor = False
            if record.payor_id:
                if len(record.payor_id.coverage_template_ids) == 1:
                    coverage_template = record.payor_id.coverage_template_ids
                if len(record.payor_id.sub_payor_ids) == 1:
                    sub_payor = record.payor_id.sub_payor_ids
            record.sub_payor_id = sub_payor
            record.coverage_template_id = coverage_template

    @api.onchange('service_id')
    def _onchange_service(self):
        for record in self.filtered('service_id'):
            if record.service_id:
                record.duration = (
                    record.service_id.surgical_appointment_time or 0
                )
                record.patient_interned = record.service_id.patient_interned
            else:
                record.patient_interned = False

    @api.multi
    def generate_encounter(self):
        self.ensure_one()
        if not self.env.context.get('generate_from_wizard', False) and (
            not self.check_patient() or not self.patient_id
        ):
            context = {'medical_appointment': self.id}
            return {
                'type': 'ir.actions.act_window',
                'name': 'Validate Patient',
                'res_model': 'medical.surgical.appointment.patient',
                'view_mode': 'form',
                'context': context,
                'target': 'new'
            }
        patient_vals = False
        if not self.patient_id:
            patient_vals = {
                'firstname': self.firstname,
                'lastname': self.lastname,
                'lastname2': self.lastname2,
                'vat': self.vat,
                'phone': self.phone,
                'mobile': self.mobile,
                'email': self.email,
                'gender': self.gender,
                'birth_date': self.birth_date,
            }
        result = self.env['medical.encounter'].create_encounter(
            patient=self.patient_id,
            patient_vals=patient_vals,
            center=self.center_id,
            careplan_data=[{
                'payor': self.payor_id,
                'sub_payor': self.sub_payor_id,
                'coverage_template': self.coverage_template_id,
                'coverage': False,
                'service': self.service_id.id,
                'performer': self.surgeon_id,
                'authorization_number': self.authorization_number,
                'subscriber_magnetic_str': self.subscriber_id
            }]
        )
        self.encounter_id = result['res_id']
        self.state = 'arrived'
        return result

    @api.multi
    def view_encounter(self):
        self.ensure_one()
        action = self.env.ref(
            'medical_administration_encounter.medical_encounter_action'
        )
        result = action.read()[0]
        result['views'] = [(False, 'form')]
        result['res_id'] = self.encounter_id.id
        return result

    @api.multi
    def view_patient(self):
        self.ensure_one()
        action = self.env.ref(
            'medical_administration.medical_patient_window_action'
        )
        result = action.read()[0]
        result['views'] = [(False, 'form')]
        result['target'] = 'new'
        result['res_id'] = self.patient_id.id
        return result

    # Workflow

    def confirm_reservation2confirm_patient(self):
        for record in self:
            if not record.patient_id:
                raise ValidationError(
                    _('Cannot confirm without selecting patient')
                )
            if record.state == 'confirmed_reservation':
                record.write({'state': 'confirmed_patient'})

    def waiting2confirm_reservation(self):
        for record in self:
            if record.state == 'draft':
                record.write({'state': 'confirmed_reservation'})

    def cancel_appointment(self):
        for record in self:
            if record.state != 'cancelled':
                record.write({'state': 'cancelled'})

    def back_to_draft(self):
        for record in self:
            if record.state != 'draft':
                record.write({'state': 'draft', 'selected_patient': False})

    @api.multi
    def generated_by_mistake(self):
        self.ensure_one()
        if self.encounter_id:
            self.encounter_id.state = 'cancelled'
            self.encounter_id = False
        self.state = 'confirmed'

    # Constrains

    @api.constrains('duration')
    def _check_duration(self):
        if self.filtered(lambda r: r.duration <= 0):
            raise ValidationError(
                _('Duration must be greater than 00:00')
            )

    @api.constrains('location_id', 'start_date', 'end_date', 'state')
    def _check_location_date(self):
        for record in self.filtered(lambda r: r.state != 'cancelled'):
            if self.search([
                ('id', '!=', record.id),
                ('location_id', '=', record.location_id.id),
                ('start_date', '<', record.end_date),
                ('end_date', '>', record.start_date),
                ('state', '!=', 'cancelled')
            ], limit=1):
                raise ValidationError(
                    _('Error! You cannot have two Appointments in'
                      ' the same location that overlap in time!'))

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        patient_id = self.env.context.get('patient_id', False)
        if patient_id:
            patient_id = self.env['medical.patient'].browse(patient_id)
            res['patient_id'] = patient_id.id
            res.update({
                'firstname': patient_id.firstname,
                'lastname': patient_id.lastname,
                'lastname2': patient_id.lastname2,
                'mobile': patient_id.mobile,
                'phone': patient_id.phone,
                'email': patient_id.email,
                'vat': patient_id.vat,
                'gender': patient_id.gender,
                'birth_date': patient_id.birth_date,
            })
        res['location_id'] = self.env.context.get('location_id', False)
        res['service_id'] = self.env.context.get('service_id', False)
        res['surgeon_id'] = self.env.context.get('surgeon_id', False)
        res['aux_surgeon_id'] = self.env.context.get('aux_surgeon_id', False)
        return res

    @api.model
    def create(self, vals):
        if 'patient_id' in vals:
            patient = self.env['medical.patient'].browse(vals['patient_id'])
            if patient:
                vals.update({
                    'firstname': patient.firstname,
                    'lastname': patient.lastname,
                    'lastname2': patient.lastname2,
                    'vat': patient.vat
                })
        return super(MedicalSurgicalAppointment, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'patient_id' in vals:
            patient = self.env['medical.patient'].browse(vals['patient_id'])
            if patient:
                vals.update({
                    'firstname': patient.firstname,
                    'lastname': patient.lastname,
                    'lastname2': patient.lastname2,
                    'vat': patient.vat
                })
        return super(MedicalSurgicalAppointment, self).write(vals)

    @api.model
    def practitioner_fields(self):
        return ['surgeon_id', 'aux_surgeon_id']

    @api.constrains('start_date', 'end_date', 'state',
                    'surgeon_id', 'aux_surgeon_id')
    def _check_surgeon_intervals(self):
        fields = self.practitioner_fields()
        for record in self.filtered(lambda r: r.state != 'cancelled'):
            partners = [getattr(record, field) for field in fields]
            for partner in partners:
                domain = []
                for field in fields:
                    if domain:
                        domain = ['|'] + domain
                    domain.append((field, '=', partner.id))
                domain += [
                    ('id', '!=', record.id),
                    ('start_date', '<', record.end_date),
                    ('end_date', '>', record.start_date),
                    ('state', '!=', 'cancelled')
                ]
                if self.search(domain, limit=1):
                    raise ValidationError(
                        _('Error! A practitioner cannot have two appointments'
                          ' that overlap in time!'))

    def check_patient(self):
        # https://www.datacamp.com/community/tutorials/fuzzy-string-python
        if not self.patient_id:
            return True
        comparisons = [(self.patient_id.firstname, self.firstname),
                       (self.patient_id.lastname, self.lastname),
                       (self.patient_id.lastname2, self.lastname2),
                       (self.patient_id.vat, self.vat)]
        return all(
            [fuzz.ratio(a or "", b or "") >= 80 for (a, b) in comparisons]
        )