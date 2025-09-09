# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

PALETTE = {
  0: "#6c757d",  
  1: "#1abc9c",
  2: "#3498db",
  3: "#9b59b6",
  4: "#e67e22",
  5: "#e74c3c",
  6: "#2ecc71",
  7: "#95a5a6",
  8: "#16a085",
  9: "#2980b9",
}


def _slugify(s: str) -> str:
    """Basic, stable slug (lowercase, hyphen, ASCII-ish)"""
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-]+", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


class WebsitePortfolioTag(models.Model):
    _name = "website_portfolio.tag"
    _description = "Project Tag"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    slug = fields.Char(index=True, translate=False, help="Stable URL slug (non-translated).", copy=False)
    color = fields.Integer(default=0)
    color_display = fields.Html(string='Color Preview', compute='_compute_color_display', store=False)
    usage_count = fields.Integer(string="Used By", compute="_compute_usage_count", readonly=True)
    
    @api.depends("color")
    def _compute_color_display(self):
        for rec in self:
            hex_ = PALETTE.get(rec.color, "#BBBBBB")
            rec.color_display = (
                f'<div title="Color {rec.color}" '
                f'style="width:16px;height:16px;border-radius:4px;'
                f'border:1px solid #ccc;background:{hex_};"></div>'
            )

    _sql_constraints = [
        ('uniq_tag_slug', 'unique(slug)', 'A tag with this slug already exists.')
    ]

    @api.constrains('color')
    def _check_color_range(self):
        for rec in self:
            if rec.color is not None and (rec.color < 0 or rec.color > 9):
                raise ValidationError(_("Color index must be between 0 and 9."))

    @api.onchange('name')
    def _onchange_name_set_slug(self):
        for rec in self:
            if rec.name and not rec.slug:
                rec.slug = _slugify(rec.name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('slug') and vals.get('name'):
                vals['slug'] = _slugify(vals['name'])
        return super().create(vals_list)

    def write(self, vals):
        if 'name' in vals and not vals.get('slug'):
            vals = dict(vals)
            vals['slug'] = _slugify(vals['name'])
        return super().write(vals)
    
    def _compute_usage_count(self):
        Project = self.env['website_portfolio'].sudo()
        for tag in self:
            tag.usage_count = Project.search_count([('tag_ids', 'in', tag.id)])
    
    def action_open_projects(self):
        self.ensure_one()
        return {
        "type": "ir.actions.act_window",
        "name": "Projects",
        "res_model": "website_portfolio",
        "view_mode": "list,form",
        "domain": [("tag_ids", "in", self.id)],
        "target": "current",
    }
