# -*- coding: utf-8 -*-

{
    'name': 'Contract',
    'version': '10.0.0',
    "category": "Contract",
    'summary': 'IT & Non-IT Contracts',
    "author": "Planet-odoo",
    'website': 'http://www.planet-odoo.com/',
    'depends': ['base','hr','employee_creation_from_user'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_groups.xml',
        'wizard/views/contract_remarks_view.xml',
        'views/contract_view.xml',
        'views/wp_locations_view.xml',
        'views/contract_categories_view.xml',
        'views/document_type_view.xml',
        'views/contract_supplier_view.xml',
        'views/contract_scheduler.xml',
        'views/users_view.xml'
         ],
    'demo':[],
    'installable': True,
    'application': True,
}
