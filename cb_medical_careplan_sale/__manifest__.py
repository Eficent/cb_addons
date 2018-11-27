# Copyright 2017 Creu Blanca
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Medical Careplan to sales',
    'version': '11.0.1.0.2',
    'author': 'Eficent, Creu Blanca, Odoo Community Association (OCA)',
    'category': 'Medical',
    'depends': [
        'medical_clinical_careplan',
        'medical_clinical_procedure',
        'medical_medication_request',
        'medical_clinical_laboratory',
        'medical_administration_encounter_careplan',
        'sale_third_party',
        'mcfix_sale',
        'sale_order_action_invoice_create_hook',
        'cb_medical_authorization',
        'cb_medical_financial_coverage_request',
        'cb_medical_workflow_plandefinition',
        'cb_medical_coverage_magnetic_str',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/medical_invoice_group.xml',
        'data/medical_sub_payor_sequence.xml',
        'security/medical_security.xml',
        'wizard/medical_encounter_add_careplan.xml',
        'views/medical_request_group_view.xml',
        'views/medical_encounter_views.xml',
        'views/medical_request_views.xml',
        'views/medical_laboratory_event_view.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/medical_coverage_agreement_view.xml',
        'views/medical_authorization_method_view.xml',
        'views/sale_order_views.xml',
    ],
    'website': 'https://github.com/eficent/cb-addons',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
