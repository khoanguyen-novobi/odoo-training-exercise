from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime as dt


class SaleRequest(models.Model):
    _name = "sale.request"
    _description = "Sale Request"
    _rec_name = "reference"

    reference = fields.Char(
        string="Order Request", readonly=True, copy=False, default=lambda self: _("New")
    )
    date = fields.Date(string="Date", default=dt.today())
    confirmed_date = fields.Date(string="Confirm Date")
    cancelled_date = fields.Date(string="Cancel Date")
    sale_person = fields.Many2one(
        "res.users", string="Sale Person", default=lambda self: self.env.user
    )
    customer = fields.Many2one("res.partner", string="Customer")
    total = fields.Float(string="Total", compute="_compute_total_price", default=0)
    sale_state = fields.Selection(
        string="Sales",
        selection=[
            ("pending", "Pending"),
            ("approve", "Approve"),
            ("rejected", "Rejected"),
        ],
        readonly=True,
        default="pending",
    )
    fulfill_state = fields.Selection(
        string="Fulfillment",
        selection=[("waiting", "Waiting"), ("ready", "Ready"), ("done", "Done")],
    )
    items = fields.Integer(string="Items", compute="_compute_items_count")
    sale_id = fields.Integer(string="Sale Id")
    add_product_lines = fields.One2many(
        "sale.request.line", "connect_sale_request", string="Products"
    )

    def _compute_items_count(self):
        for rec in self:
            rec.items = len(rec.add_product_lines)

    def get_quotation_date(self):
        quotation = self.env["sale.order"].search([("id", "=", self.sale_id)])
        return quotation.create_date

    def get_sale_date(self):
        order = self.env["sale.order"].search([("id", "=", self.sale_id)])
        return order.date_order

    def get_sale_state(self):
        order = self.env["sale.order"].search([("id", "=", self.sale_id)])
        return order.state

    def get_all_delivery_order(self):
        delivery = self.env["stock.picking"].search([("sale_id", "=", self.sale_id)])
        return delivery.create_date

    def get_delivery_done_date(self):
        delivery = self.env["stock.picking"].search([("sale_id", "=", self.sale_id)])
        return delivery.date_done

    @api.depends("add_product_lines")
    def _compute_total_price(self):
        for rec in self:
            total = 0.0
            for line in rec.add_product_lines:
                total += line.sub_total
            rec.total = total

    def get_order_lines_from_request(self):
        order_lines = []
        for line in self.add_product_lines:
            order_lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": line.product_id.id,
                        "product_uom_qty": line.pro_qty,
                        "price_unit": line.unit_price,
                    },
                )
            )
        return order_lines

    def action_approve(self):
        self.sale_state = "approve"
        self.confirmed_date = dt.today()
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "date_order": self.date,
                "order_line": self.get_order_lines_from_request(),
            }
        )
        self.sale_id = sale_order.id

    def action_rejected(self):
        self.sale_state = "rejected"
        self.cancelled_date = dt.today()

    def get_portal_url(self):
        return "/my/sale-request/" + str(self.id)

    def find_all_done_delivery(self):
        """
        Function to send email to all done delivery order for cron job
        """
        dev = self.env["stock.picking"].search([("state", "=", "done")])
        mail = self.env["mail.mail"]
        for rec in dev:
            if rec.partner_id.email is not False:
                values = {
                    "subject": "Receive order",
                    "email_to": rec.partner_id.email,
                    "body_html": "You will receive your order soon",
                }
                msg_id = mail.create(values)
                if msg_id:
                    mail.send([msg_id])

    @api.model
    def create(self, vals):
        """
        Override create sale order add reference sequence
        """
        if vals.get("reference", _("New")) == _("New"):
            vals["reference"] = self.env["ir.sequence"].next_by_code(
                "sale.request"
            ) or _("New")
        res = super(SaleRequest, self).create(vals)
        return res


class SaleRequestLine(models.Model):
    _name = "sale.request.line"

    connect_sale_request = fields.Many2one("sale.request", string="Connect")
    product_id = fields.Many2one("product.product", string="Product")
    description = fields.Text(string="Description")
    pro_qty = fields.Integer(string="Quantity", default=1)
    unit_price = fields.Float(string="Unit Price", default=0)
    tax = fields.Many2one("account.tax", string="Tax")
    sub_total = fields.Float(string="Sub Total", compute="_compute_sub_total")

    @api.depends("pro_qty", "unit_price")
    def _compute_sub_total(self):
        for line in self:
            line.sub_total = line.pro_qty * line.unit_price

    @api.model
    def write(self, vals):
        """
        Override update sale request line cannot update larger quantity
        """
        if vals.get("pro_qty") is not None:
            current_qty = vals["pro_qty"]
        for rec in self:
            if rec.pro_qty < current_qty:
                raise ValidationError("Cannot update larger current quantity")
        res = super(SaleRequestLine, self).write(vals)
        return res
