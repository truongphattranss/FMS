{
    'name': 'Investor Profile',
    'version': '1.0',
    'category': 'Investor',
    'summary': 'Manage investor profiles and related information',
    'description': """
        This module provides functionality to manage investor profiles including:
        - Personal information
        - Bank accounts
        - Addresses
        - ID documents
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/status_info_views.xml',
        'views/personal_info_view.xml',
        'views/res_partner_profiles_views.xml',
        'views/res_partner_bank_views.xml',
        'views/res_partner_address_views.xml',
        'views/menu_views.xml',
        'views/res_partner_hide_view.xml',
        'views/res_partner_status_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
