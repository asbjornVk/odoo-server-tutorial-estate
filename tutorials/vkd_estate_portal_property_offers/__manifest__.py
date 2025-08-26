{
    "name": "Portal Offers",
    "summary": "Create customer invoices when an estate property is sold.",
    "version": "18.0.1.0.0",
    "author": "You",
    "license": "LGPL-3",
    "depends": ["estate", "portal", "website"],
    "data": [
        "security/ir.model.access.csv",
        "security/estate_portal_security.xml",
        'views/estate_website_templates.xml',
        'views/estate_portal_templates.xml',
        'data/website_menu_estate_data.xml',
        'views/portal_breadcrumbs_templates.xml'

    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}