# -*- coding: utf-8 -*-
from re import S
from werkzeug.exceptions import NotFound
from odoo.exceptions import ValidationError
from odoo import http
from odoo.http import request

class EstatePortal(http.Controller):
    #HUB: /my/estate
    @http.route(['/my/estate'], type='http', auth='user', website=True)
    def my_estate(self, **kwargs):
        partner = request.env.user.partner_id
        Property = request.env['estate.property']
        Offer = request.env['estate.property.offer']

        prop_domain = [('active', '=', True), ('state', 'not in', ['sold', 'cancelled'])]
        props_count = Property.search_count(prop_domain)
        my_offers_count = Offer.search_count([('partner_id', '=', partner.id)])

        return request.render(
            'vkd_estate_portal_property_offers.portal_estate_hub',
            {
                'props_count': props_count,
                'my_offers_count': my_offers_count,
                'page_name': 'estate_hub',
                'title': 'Estate',
                'breadcrumbs': [
                                ('Home', '/my'),
                                ('Estate', '/my/estate'),
                                ],
            }
        )
    #PROPERTIES LIST: /my/estate/properties
    @http.route(['/my/estate/properties'], type='http', auth='user', website=True)
    def my_estate_properties(self, page=1, **kwargs):
        Property = request.env['estate.property']
        domain = [('active', '=', True), ('state', 'not in', ['sold', 'cancelled'])]
        limit = 20
        offset = (max(int(page), 1) -1) * limit
        props = Property.search(domain, order='id desc', limit=limit, offset=offset)

        return request.render(
            'vkd_estate_portal_property_offers.portal_estate_properties',
            {
                'properties': props,
                'page_name': 'estate_properties',
                'title': 'Estate Properties',
                'breadcrumbs': [
                                ('Home', '/my'),
                                ('Estate', '/my/estate'),
                                ('Properties', False),
                                ],
            }
        )

    # PROPERTY DETAIL: /my/estate/properties/<id>
    @http.route(['/my/estate/properties/<int:property_id>'], type='http', auth='user', website=True)
    def my_estate_property_detail(self, property_id, **kwargs):
        Property = request.env['estate.property']
        estate = Property.search([('id', '=', property_id), ('active', '=', True)], limit=1)
        if not estate:
            raise NotFound()

        err = request.session.pop('estate_bid_error', False)
        return request.render(
            'vkd_estate_portal_property_offers.portal_property_detail_page',
            {
                'error_msg': err,
                'estate': estate,
                'page_name': 'estate_property_detail',
                'title': estate.display_name,
                'breadcrumbs': [
                                ('Home', '/my'),
                                ('Estate', '/my/estate'),
                                ('Properties', '/my/estate/properties'),
                                (estate.display_name, False),
                                ],
            }
        )

    # PLACE BID (POST): /my/estate/properties/<id>/bid
    @http.route(['/my/estate/properties/<int:property_id>/bid'], type='http', auth='user', website=True, methods=['POST'])
    def my_estate_property_bid(self, property_id, **post):
        Property = request.env['estate.property']
        Offer = request.env['estate.property.offer']
        estate = Property.search([('id', '=', property_id), ('active', '=', True)], limit=1)
        if not estate:
            raise NotFound()

        # Parse + validate amount
        raw = (post or {}).get('amount', '').strip()
        try:
            amount = float(raw.replace(',', '.'))
        except Exception:
            return request.redirect(f'/my/estate/properties/{property_id}?error=invalid_amount')

        offer_amount = Offer.price
        if amount <= 0 or amount <= offer_amount:
            return request.redirect(f'/my/estate/properties/{property_id}?error=non_positive')

        partner = request.env.user.partner_id

        try:
            Offer.create({
            'price': amount,
            'partner_id': partner.id,
            'property_id': estate.id,
            # 'status': 'draft', 
        })
        except ValidationError as e:
            msg = e.args[0] if e.args else str(e)
            request.session['estate_bid_error'] = msg
            return request.redirect(f'/my/estate/properties/{property_id}')


        request.session['estate_bid_ok'] = True
        return request.redirect(f'/my/estate/my-offers')

    # MY OFFERS: /my/estate/my-offers 
    @http.route(['/my/estate/my-offers'], type='http', auth='user', website=True)
    def my_estate_my_offers(self, **kwargs):
        partner = request.env.user.partner_id
        Offer = request.env['estate.property.offer']
        offers = Offer.search([('partner_id', '=', partner.id)], order='create_date desc')

        just_submitted = request.session.pop('estate_bid_ok', False)
        return request.render(
            'vkd_estate_portal_property_offers.portal_my_estate_offers',
            {
                'just_submitted': just_submitted,
                'offers': offers,
                'page_name': 'estate_my_offers',
                'title': 'My Offers',
                'breadcrumbs': [
                                ('Home', '/my'),
                                ('Estate', '/my/estate'),
                                ('My Offers', False),
                            ],
            }
        )