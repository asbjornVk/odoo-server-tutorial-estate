from odoo import models, fields, _

class ResUsers(models.Model):
    _inherit = "res.users"

    # Alle ejendomme hvor brugeren er sælger (du har allerede salesperson_id på estate.property)
    ###
    estate_property_ids = fields.One2many("estate.property", "salesperson_id", string="My Properties")
    
    estate_property_count = fields.Integer(
        string="Properties",
        compute="_compute_estate_property_count",
    )

    property_ids = fields.One2many(
        "estate.property",
        "salesperson_id",
        string="Properties",
        domain=[('state', 'in', ['new', 'offer_received', 'offer_accepted'])],  # "available"
        help="Properties assigned to this user (available only).",
    )

    def _compute_estate_property_count(self):
        counts = self.env["estate.property"].read_group(
            [("salesperson_id", "in", self.ids),
             ('state', 'in', ['new', 'offer_received', 'offer_accepted'])], #delete hvis den fejler
            fields=["salesperson_id"],
            groupby=["salesperson_id"],
        )
        by_user = {r["salesperson_id"][0]: r["salesperson_id_count"] for r in counts}
        for user in self:
            user.estate_property_count = by_user.get(user.id, 0)
