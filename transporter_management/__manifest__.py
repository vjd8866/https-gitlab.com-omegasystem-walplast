# -*- coding: utf-8 -*-

{
    'name': 'TPR',
    'version': '10.0.0',
    "category": "Transporter Management",
    'summary': 'Transporter Management',
    "author": "Planet-odoo",
    'website': 'http://www.planet-odoo.com/',
    'depends': ['base','stock','product','sales_meet', 'contacts','wp_contract'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/schedulers.xml',
        'wizard/update_planning_details.xml',
        'views/transporter_management_system.xml',
        'views/transporter_masters.xml',
        # 'views/partner_view_inherit.xml',
        'wizard/map_trans_to_depot.xml',
        'views/users_view_inherit.xml',
        'report/export_tpr_plan.xml'
    ],
    'demo':[],
    'installable': True,
    'application': True,
}
