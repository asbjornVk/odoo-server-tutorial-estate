# __manifest__.py

{
    'name': 'Real Estate',
    'version': '1.0',
    'depends': ['base'],
    'author': 'Asbjørn Jacobsen',
    'category': 'Real Estate',
    'description': 'A module for managing real estate properties',
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/estate_property_offer_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_search_views.xml',
        'views/estate_menus.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}