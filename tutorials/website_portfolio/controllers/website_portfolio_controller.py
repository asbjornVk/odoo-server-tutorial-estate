# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-
from werkzeug.exceptions import NotFound
from odoo import http, fields
from odoo.http import request


def live_domain():
    now = fields.Datetime.now()
    return [
        ('website_published', '=', True),
        '|', ('publish_from', '=', False), ('publish_from', '<=', now),
        '|', ('publish_to',   '=', False), ('publish_to',   '>=', now),
    ]


class WebsitePortfolioController(http.Controller):

    @http.route(
        ['/repos', '/repos/tag/<string:slug>', '/repos/tagid/<int:tag_id>'],
        type='http', auth='public', website=True, sitemap=True
    )
    def list_projects(self, slug=None, tag_id=None, **kw):
        Project = request.env['website_portfolio'].sudo()
        Tag = request.env['website_portfolio.tag'].sudo()
        domain = list(live_domain())
        active_tag = None

        if tag_id:
            active_tag = Tag.browse(tag_id).exists()
            if active_tag:
                domain.append(('tag_ids', 'in', active_tag.id))
        elif slug:
            active_tag = Tag.search([('slug', '=', slug)], limit=1)
            if active_tag:
                domain.append(('tag_ids', 'in', active_tag.id))

        projects = Project.search(domain, order='publish_from desc, name')
        tags = Tag.search([], order='name')

        fav_tag = Tag.search([('slug', '=', 'favorite')], limit=1) or \
                  Tag.search([('name', 'ilike', 'favorite')], limit=1)
                  
        favorite_repos = Project.search(
            live_domain() + ([('tag_ids', 'in', fav_tag.id)] if fav_tag else []),
            order='name asc', limit=12
        )

        return request.render('website_portfolio.tmpl_projects_list', {
            'projects': projects,
            'tags': tags,
            'active_tag': active_tag,
            'favorite_repos': favorite_repos,
        })

    @http.route(['/repos/<int:project_id>'], type='http', auth='public', website=True, sitemap=True)
    def project_detail(self, project_id, **kw):
        """Detail page is only accessible for 'live' records; otherwise 404."""
        Project = request.env['website_portfolio'].sudo()
        project = Project.search(live_domain() + [('id', '=', project_id)], limit=1)
        if not project:
            raise NotFound()
        return request.render('website_portfolio.tmpl_project_detail', {'project': project})
