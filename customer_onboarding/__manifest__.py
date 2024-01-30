# -*- coding: utf-8 -*-

{
    'name': 'Customer On-Boarding',
    'version': '10.0.0',
    "category": "On-Boarding",
    'summary': 'Customer On-Boarding',
    "author": "Planet-odoo",
    'website': 'http://www.planet-odoo.com/',
    'depends': ['sales_meet'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/customer_onboard_view.xml',
        'report/cust_onboard_report.xml'

    ],
    'demo':[],
    'installable': True,
    'application': True,
}
