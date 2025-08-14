from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import datetime

class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Real Estate Property'
    _order = 'id desc'
    _sql_constraints = [
        ('check_expected_price_positive', 'CHECK(expected_price > 0)', 'Expected price must be positive.'),
        ('check_selling_price_positive', 'CHECK(selling_price >= 0)', 'Selling price must be positive.'),]
    
    property_type_id = fields.Many2one('estate.property.type', string='Property Type', required=True)
    color = fields.Integer(string="Color")

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    postcode = fields.Char(string='Postcode', default='1000')
    date_availability = fields.Date(string='Date of Availability', default= datetime.date.today() + datetime.timedelta(days=90), copy=False)
    expected_price = fields.Float(string='Expected Price')
    selling_price = fields.Float(string='Selling Price', readonly=True, copy=False)
    bedrooms = fields.Integer(string='Bedrooms', required=True, default=2)
    living_area = fields.Float(string='Living Area (sqm)')
    facades = fields.Integer(string='Facades', required=True, default=1)
    garage = fields.Boolean(string='Garage')
    garden = fields.Boolean(string='Garden', default=False)
    garden_area = fields.Float(string='Garden Area (sqm)')
    active = fields.Boolean(string='Active', default=True)
    property_count = fields.Integer(
        compute='_compute_property_count',
        string='Property Count')
    garden_orientation = fields.Selection(
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West')
        ],
    string= 'Garden Orientation')
    state= fields.Selection(
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('cancelled', 'Cancelled')
        ],
        string='State',
        default='new',
        required=True,
        copy=False)
    
    salesperson_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        default=lambda self: self.env.user,)
    
    buyer_id = fields.Many2one(
        "res.partner",
        string="Buyer",
        copy=False)
    
    tag_ids = fields.Many2many(
        "estate.property.tag",
        string="Tags",
        help="Tags for the property, e.g. 'new', 'renovated', 'garden', etc.",
        )
    
    offer_ids = fields.One2many(
        "estate.property.offer",
        "property_id",
        string="Offers",
        help="Offers made on the property"
        )
    
    best_price = fields.Float(
        compute='_compute_best_price', 
        store=True)
    
    total_area = fields.Float(
        string="Total Area (sqm)",
        compute="_compute_total_area",
        store=True,
        readonly=True,
        help="Total area of the property including living area and garden area"
    )

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for rec in self:
            rec.total_area = (rec.living_area or 0.0) + (rec.garden_area or 0.0)
    
    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0.0
            self.garden_orientation = False
        
    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for rec in self:
            prices = rec.offer_ids.mapped('price')
            rec.best_price = max(prices) if prices else 0.0
    
    def action_cancel(self):
        for rec in self:
            if rec.state == 'sold':
                raise UserError(_("You cannot cancel a property that has been sold."))
            rec.state = 'cancelled'
    
    def action_sold(self):
        for rec in self:
            if rec.state == 'sold':
                raise UserError(_("This property is already sold."))
            rec.state = 'sold'
    
    @api.constrains('expected_price', 'selling_price')
    def _check_prices(self):
        for rec in self:
            if ( rec.selling_price and rec.selling_price < rec.expected_price * 0.9):
                raise ValidationError(_("Selling price must be at least 90% of the expected price."))
    
    @api.constrains('expected_price', 'selling_price')
    def _check_positive_prices(self):
        for rec in self:
            if rec.expected_price <= 0:
                raise ValidationError(_("Expected price must be positive."))
            if rec.selling_price < 0:
                raise ValidationError(_("Selling price must be positive."))

    @api.ondelete(at_uninstall=False)
    def _check_can_delete(self):
        for rec in self:
            if rec.state not in ['new', 'cancelled']:
                raise UserError(_("You cannot delete a property that is not new or cancelled."))




   
