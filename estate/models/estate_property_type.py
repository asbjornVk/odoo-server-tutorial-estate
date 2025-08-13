from odoo import models, fields, api, _

class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Real Estate Property Type'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10, help="Used to order property types")
    color = fields.Integer(string='Color Index', default=0, help="Color index for the property type in kanban views")

    offer_ids = fields.One2many(
        'estate.property.offer',
        'property_type_id',
        string='Offers',
    )

    offer_count = fields.Integer(
        compute='_compute_offer_count',
        string='Offer Count',
    )



    property_ids = fields.One2many(
        comodel_name='estate.property',
        inverse_name='property_type_id',
        string='Properties',
        help="Properties of this type"
    )
    property_count = fields.Integer(
        compute='_compute_property_count')

    @api.depends('property_ids')
    def _compute_property_count(self):
        counts = self.env['estate.property'].read_group(
            [('property_type_id', 'in', self.ids)],
            ['property_type_id'],
            ['property_type_id']
        )
        m = {r['property_type_id'][0]: r['property_type_id_count'] for r in counts}
        for rec in self:
            rec.property_count = m.get(rec.id, 0)
    
    def action_open_properties(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Properties'),
            'res_model': 'estate.property',
            'view_mode': 'list,form',
            'domain': [('property_type_id', '=', self.id)],
            'context': {'default_property_type_id': self.id},
        }
    
    def _compute_offer_count(self):
        for rec in self:
            rec.offer_count = len(rec.offer_ids)

    _sql_constraints = [
        ('estate_property_type_name_uniqe', 'UNIQUE(name)', 'Property type name must be unique.')]