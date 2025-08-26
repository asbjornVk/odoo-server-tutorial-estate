from odoo import models, fields, api, _

class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Estate Property Tag'
    _order = 'name'

    _sql_constraints = [
        ('estate_property_tag_name_unique', 'UNIQUE(name)', 'Tag name must be unique.')]

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string="Color")
    
    property_count = fields.Integer(
        string='Properties',
        compute='_compute_property_count',
        help="Number of properties associated with this tag",
        compute_sudo=True
    )

    def _compute_property_count(self):
        Property = self.env['estate.property']
        for rec in self:
            rec.property_count = Property.search_count([('tag_ids', 'in', rec.id)])

    def action_open_properties(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Properties'),
            'res_model': 'estate.property',
            'view_mode': 'list,form',
            'domain': [('tag_ids', 'in', self.id)],
            'context': {'default_tag_ids': [self.id]},
        }


