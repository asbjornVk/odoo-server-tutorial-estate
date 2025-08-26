import datetime
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Estate Property Offer'
    _order = 'price desc'

    _sql_constraints = [
        ('check_price_positive', 'CHECK(price >= 0)', 'Offer price must be positive.'),]

    property_type_id = fields.Many2one(
        'estate.property.type',
        string='Property Type',
        related='property_id.property_type_id',
        store=True,
        index=True
        )
    
    property_id = fields.Many2one('estate.property', string='Property', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    price = fields.Float(string='Price', required=True)
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('accepted', 'Accepted'),
            ('refused', 'Refused')
        ],
        string='Status',
        default='draft',
        required=True,
    )
    validity = fields.Integer(
        string='Validity (days)',
        default=7,
        help='Number of days the offer is valid before it expires.'
    )
    date_deadline = fields.Date(
        string='Deadline',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
        store=True,
        help='Deadline for the offer based on the validity period.',
        compute_sudo=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        Property = self.env['estate.property']
        for vals in vals_list:
            prop_id = vals.get('property_id')
            if prop_id:
                # find the highest existing price for this property
                existing_max = self.search_read(
                    [('property_id', '=', prop_id)],
                    ['price'],
                    limit=1,
                    order='price desc',
                )
                if existing_max and vals.get('price', 0.0) <= existing_max[0]['price']:
                    raise ValidationError(_("Offer price must be strictly higher than existing offers."))

        records = super().create(vals_list)

        # set the state on all affected properties
        props = Property.browse(list({v.get('property_id') for v in vals_list if v.get('property_id')}))
        if props:
            props.with_user(SUPERUSER_ID).write({'state': 'offer_received'})

        return records

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for rec in self:
            base = rec.create_date.date() if rec.create_date else fields.Date.context_today(self)
            rec.date_deadline = base + datetime.timedelta(days=rec.validity or 0)

    def _inverse_date_deadline(self):
        for rec in self:
            if rec.date_deadline:
                base = rec.create_date.date() if rec.create_date else fields.Date.context_today(self)
                rec.validity = (rec.date_deadline - base).days
            else:
                rec.validity = 0

    # Action methods
    def action_accept(self):
        self.ensure_one()
        for rec in self:
            if rec.property_id.offer_ids.filtered(lambda o: o.status == 'accepted'):
                raise UserError(_("This property already has an accepted offer."))
            rec.status = 'accepted'
            rec.property_id.write({
                'state': 'offer_accepted',
                'selling_price': rec.price,
                'buyer_id': rec.partner_id.id
            })
            (rec.property_id.offer_ids - rec).write({'status': 'refused'})
    
    def action_refuse(self):
        self.ensure_one()

        for rec in self:
            if rec.status != 'accepted':
                rec.status = 'refused'


    