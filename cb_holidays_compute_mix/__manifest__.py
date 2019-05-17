# Copyright 2015 iDT LABS (http://www.@idtlabs.sl)
# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': ' CB Holidays',
    'version': '11.0.1.0.0',
    'category': 'Human Resources',
    'license': 'AGPL-3',
    'summary': 'Módulo Holidays adaptado a Creu Blanca. '
               'Añade principalmente cambios en vistas, '
               'allocations, conteo del tiempo de vacaciones, '
               'cambio del wizard de public holidays y security.',
    'author': 'iDT LABS, '
              'Tecnativa, '
              'Creu Blanca, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/hr',
    'depends': [
        'hr_holidays_public',
    ],
    'data': [
        'wizards/hr_holidays_allocation_wizard.xml',
        'wizards/hr_holidays_next_year_wizard.xml',
        'wizards/hr_holidays_pending_employees_wizard.xml',
        'wizards/hr_holidays_summary_department.xml',
        'security/holidays_security.xml',
        'views/hr_holidays_public_views.xml',
        'views/hr_holidays_status_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_holidays_views.xml',
        'views/hr_module_views.xml',
    ],
    'installable': True,
    'post_init_hook': 'post_init_hook',
}
