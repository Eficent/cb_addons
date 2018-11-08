# Copyright 2017 Creu Blanca
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'CB Medical sequence configuration',
    'version': '11.0.1.0.0',
    'author': 'Eficent, Creu Blanca, Odoo Community Association (OCA)',
    'depends': [
        'cb_medical_careplan_sale',
        'mrp',
    ],
    'data': [
        'wizard/medical_careplan_medication_views.xml',
        'views/product_category_views.xml',
        'views/medical_careplan_views.xml',
        'report/medical_encounter_medication_report.xml',
    ],
    'website': 'https://github.com/OCA/vertical-medical',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
