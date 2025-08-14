from odoo import api, models, _
from odoo import Command
import logging
_logger = logging.getLogger(__name__)

class EstateProperty(models.Model):
    _inherit = "estate.property"

    def action_sold(self):
        """Extend sell action: create a customer invoice for the buyer,
        then continue the normal flow via super().
        """
        for prop in self:
            # Safety net: ensure a buyer is set
            buyer = getattr(prop, "buyer_id", False)
            if not buyer:
                # For stricter behavior, raise an error instead of skipping
                continue

            # Retrieve a sales journal (same company as the property when possible)
            company = prop.salesperson_id.company_id or self.env.company
            sale_journal = self.env["account.journal"].search(
                [("type", "=", "sale"), ("company_id", "=", company.id)],
                limit=1,
            )
            if not sale_journal:
                # As a fallback: use any 'sale' journal
                sale_journal = self.env["account.journal"].search(
                    [("type", "=", "sale")], limit=1
                )

            # Amounts
            selling_price = prop.selling_price or 0.0
            commission = (selling_price * 0.06) if selling_price else 0.0
            admin_fee = 100.0

            _logger.error(
                "estate_account: Selling price: %s, Commission: %s, Admin fee: %s",
                selling_price, commission, admin_fee
            )

            # Create invoice (account.move)
            move_vals = {
                "partner_id": buyer.id,              # The customer (buyer)
                "move_type": "out_invoice",          # Customer invoice
                "journal_id": sale_journal.id if sale_journal else False,
                "invoice_line_ids": [
                    # 6% commission
                    Command.create({
                        "name": _("Commission 6% of selling price"),
                        "quantity": 1.0,
                        "price_unit": commission,
                    }),
                    # Administrative fee 100.00
                    Command.create({
                        "name": _("Administrative fee"),
                        "quantity": 1.0,
                        "price_unit": admin_fee,
                    }),
                ],
            }
            self.env["account.move"].create(move_vals)

        # Continue normal "Sold" flow
        return super().action_sold()
