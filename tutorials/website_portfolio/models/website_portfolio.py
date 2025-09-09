# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-
from odoo import models, fields


class WebsitePortfolio(models.Model):
    _name = "website_portfolio"
    _description = "Website Portfolio"
    _inherit = ["website.published.mixin", "website.seo.metadata", "mail.thread"]
    _order = "publish_from desc, name"

    name = fields.Char(required=True, tracking=True)
    repo_url = fields.Char(string="Repository URL")
    description_short = fields.Text()
    description_long = fields.Html(sanitize=True)
    image_1920 = fields.Image(max_width=1920, max_height=1920)

    tag_ids = fields.Many2many("website_portfolio.tag", string="Tags")

    publish_from = fields.Datetime("Publish From")
    publish_to   = fields.Datetime("Publish To")

    github_full_name = fields.Char(index=True, help="GitHub owner/repo, e.g. 'odoo/odoo'")

    _sql_constraints = [
        ('uniq_github_full_name', 'unique(github_full_name)', 'This GitHub repository is already imported.')
    ]
