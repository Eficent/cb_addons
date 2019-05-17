# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestNextYearWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env['hr.holidays.public.line'].search([]).unlink()
        self.env['hr.holidays.public'].search([]).unlink()

    def test_error_no_template(self):
        with self.assertRaises(UserError):
            self.env['hr.holidays.next.year.public.holidays'].create({})

    def test_next_year_wizard(self):
        self.env['hr.holidays.public'].create({
            'year': 2019,
            'line_ids': [
                (0, 0, {'name': 'Day1', 'date': '2019-06-06'}),
                (0, 0, {'name': 'Day2', 'date': '2019-06-07',
                        'variable_date': False}),
            ]
        })
        wizard = self.env['hr.holidays.next.year.public.holidays'].create({})
        pending = self.env['hr.holidays.public.line.transient'].search([])
        self.assertTrue(pending)
        self.assertEqual(wizard.year, 2020)

        pending.write({'date': '2020-06-08'})
        wizard.create_public_holidays()
        holidays = self.env['hr.holidays.public'].search([('year', '=', 2020)])
        self.assertEqual(len(holidays.line_ids), 2)
