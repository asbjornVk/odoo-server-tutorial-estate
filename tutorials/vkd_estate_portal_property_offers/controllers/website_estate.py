# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class WebsiteEstate(http.Controller):

    # Redirect - '/' -> '/estate'
    @http.route('/', type='http', auth='public', website=True)
    def website_home(self, **kw):
        return request.redirect('/estate', code=302)


    # PUBLIC LIST: /estate (website)
    @http.route(['/estate'], type='http', auth='public', website=True)
    def estate_public_list(self, page=1, **kw):
        Property = request.env['estate.property'].sudo()
        # Public visibility Rules
        domain = [('active', '=', True), ('state', 'not in', ['sold', 'cancelled'])]
        limit = 20
        page = max(int(page or 1), 1)
        offset = (page - 1) * limit

        props = Property.search(domain, order='id desc', limit=limit, offset=offset)
        total = Property.search_count(domain)
        has_next = (offset + len(props)) < total
        has_prev = page > 1

        return request.render(
            'vkd_estate_portal_property_offers.website_estate_list',
            {
                'properties': props,
                'page': page,
                'has_next': has_next,
                'has_prev': has_prev,
                'next_page': page + 1,
                'prev_page': page - 1,
                'title': 'Estate',
            }
        )

    # PUBLIC DETAIL: /estate/<id> (website)
    @http.route(['/estate/<int:property_id>'], type='http', auth='public', website=True)
    def estate_public_detail(self, property_id, **kw):
        Property = request.env['estate.property'].sudo()
        estate = Property.search(
            [('id', '=', property_id), ('active', '=', True), ('state', 'not in', ['sold', 'cancelled'])],
            limit=1
        )
        if not estate:
            return request.not_found()

        return request.render(
            'vkd_estate_portal_property_offers.website_estate_detail',
            {
                'estate': estate,
                'title': estate.display_name,
            }
        )
