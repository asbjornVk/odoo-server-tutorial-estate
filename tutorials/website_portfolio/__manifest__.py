# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Website Portfolio",
    "version": "18.0.1.2",
    "author": "Asbjørn Jacobsen",
    "summary": "Portfolio of code projects (list + detail on website)",
    "category": "Website",
    "application": False,
    "installable": True,
    "license": "LGPL-3",
    "depends": ["base", "website", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/website_portfolio_menu_views.xml",
        "views/website_portfolio_templates_views.xml",
        "views/website_portfolio_views.xml",
        "views/website_portfolio_github_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "website_portfolio/static/src/scss/website_portfolio_backend.scss",
        ],
        "web.assets_frontend": [
            "website_portfolio/static/src/scss/website_portfolio_tags_assets.scss",

        ],
    },
}