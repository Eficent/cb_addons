# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Cb Hr Views',
    'summary': """
        Views for HR modules in Creu Blanca""",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Creu Blanca',
    'website': 'www.creublanca.es',
    'depends': [
        'base_fontawesome',
        'hr_attendance',
        'hr_contract',
        'hr_family',
        'hr_job_category',
        'hr_attendance_report_theoretical_time',
        'hr_employee_calendar_planning',
        'medical_administration_second_lastname',
        'medical_administration_practitioner',
        'cb_departments_chart',
    ],
    'data': [
        'views/resource_calendar_views.xml',
        'views/res_partner.xml',
        'security/hr_attendance_security.xml',
        'security/ir.model.access.csv',
        'security/hr_employee_security.xml',
        'views/hr_attendance_module_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_job_views.xml',
        'views/hr_department_views.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
}
