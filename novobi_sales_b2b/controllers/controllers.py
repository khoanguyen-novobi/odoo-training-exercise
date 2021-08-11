# -*- coding: utf-8 -*-
import json
import odoo
import re
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    @odoo.http.route("/my/sale-request", type="http", auth="user", website="True")
    def sale_request_portal(self):
        """
        Return portal page with list of sale request
        """
        # values = self._prepare_portal_layout_values()
        SaleRequest = odoo.http.request.env["sale.request"]
        # sale = (
        #     odoo.http.request.env["sale.request"]
        #     .sudo()
        #     .search([("sale_person", "=", odoo.http.request.session.uid)])
        # )
        # response = {"status": "ok", "content": []}
        # price_list = odoo.http.request.env["product.pricelist"].sudo().search([])
        # for line in price_list:
        #     print(line.name)
        # for rec in sale:
        #     response["content"].append({"name": rec.reference})

        # response["user"] = odoo.http.request.session.uid
        return odoo.http.request.render(
            "novobi_sales_b2b.portal_my_sale_request",
            {
                "sr": SaleRequest.sudo().search(
                    [("customer", "=", odoo.http.request.env.user.partner_id.id)]
                )
            },
        )

    @odoo.http.route(
        "/my/sale-request/<int:order_id>", type="http", auth="user", website="True"
    )
    def get_request_detail(self, order_id):
        """
        Return page with sale request detail information
        """
        values = self._prepare_portal_layout_values()
        SaleRequest = odoo.http.request.env["sale.request"]
        sale = (
            odoo.http.request.env["sale.request"].sudo().search([("id", "=", order_id)])
        )

        return odoo.http.request.render(
            "novobi_sales_b2b.sale_request_detail", {"sr": sale}
        )

    @odoo.http.route(
        "/my/sale-request/create-sale-request", type="http", auth="user", website="True"
    )
    def create_request(self):
        """
        Return page to create a new sale request
        """
        return odoo.http.request.render("novobi_sales_b2b.sale_request_create", {})


class SaleRequestAPI(odoo.http.Controller):
    def _montary_2_float(self, price):
        """
        Convert Monetary type to Float
        """
        trim = re.compile(r"[^\d.,]+")
        result = trim.sub("", price)
        return float(result)

    @odoo.http.route("/sale-request/create", type="json", auth="public")
    def create_sale_request_api(self, **params):
        """
        External API to create a sale request
        """
        vals = {}
        order_lines = []
        required_field = ["sale_person", "customer", "add_product_lines"]

        for key in required_field:
            if key not in params.keys():
                return {"success": "False", "message": f"{key} is required"}
        if odoo.http.request.jsonrequest:
            for k, v in params.items():
                if k == "customer":
                    customer = (
                        odoo.http.request.env["res.partner"]
                        .sudo()
                        .search([("name", "=", v)], limit=1)
                    )
                    prod_accept = []
                    for prod in customer.property_product_pricelist.item_ids:
                        prod_accept.append(
                            {
                                "id": prod.id,
                                "product_id": prod.product_id.id,
                                "price": prod.price,
                            }
                        )
                    print(prod_accept)
                    if len(customer) != 0:
                        vals.update({"customer": customer.id})
                    else:
                        return {"success": "False", "message": "Customer not found"}
                    if len(prod_accept) == 0:
                        return {"success": "False", "message": "User not in price list"}
                elif k == "sale_person":
                    sale_person = (
                        odoo.http.request.env["res.users"]
                        .sudo()
                        .search([("name", "=", v)], limit=1)
                    )
                    if len(sale_person) != 0:
                        vals.update({"sale_person": sale_person.id})
                    else:
                        return {"success": "False", "message": "Sale person not found"}
                elif k == "add_product_lines":
                    for order in v:
                        new = list(
                            filter(lambda x: x["id"] == order["id"], prod_accept)
                        )
                        order_lines.append(
                            (
                                0,
                                0,
                                {
                                    "product_id": new[0]["product_id"],
                                    "pro_qty": order["qty"],
                                    "unit_price": self._montary_2_float(
                                        new[0]["price"]
                                    ),
                                },
                            )
                        )
            new_sale_request = odoo.http.request.env["sale.request"].sudo().create(vals)
            if len(order_lines) != 0:
                new_sale_request.write({"add_product_lines": order_lines})
        return {"success": "True", "id": 1, "message": "Success call"}

    @odoo.http.route("/sale-request/update", type="json", auth="public")
    def update_sale_request_api(self, **params):
        """
        External API to update an exist sale request only in pending state
        """
        vals = {}
        order_lines = []
        required_field = ["reference"]
        prod_accept = []
        for key in required_field:
            if key not in params.keys():
                return {"success": "False", "message": f"{key} is required"}

        if odoo.http.request.jsonrequest:
            for k, v in params.items():
                if k == "reference":
                    request = (
                        odoo.http.request.env["sale.request"]
                        .sudo()
                        .search([("reference", "=", v)])
                    )
                    if request.sale_state != "pending":
                        return {
                            "success": "False",
                            "message": f"Cannot update sale request with {request.sale_state} state",
                        }
                elif k == "sale_person":
                    sale_person = (
                        odoo.http.request.env["res.users"]
                        .sudo()
                        .search([("name", "=", v)], limit=1)
                    )
                    if len(sale_person) != 0:
                        vals.update({"sale_person": sale_person.id})
                    else:
                        return {"success": "False", "message": "Sale person not found"}
                elif k == "add_product_lines":
                    for order in v:
                        new = list(
                            filter(lambda x: x["id"] == order["id"], prod_accept)
                        )
                        order_lines.append(
                            (
                                0,
                                0,
                                {
                                    "product_id": new[0]["product_id"],
                                    "pro_qty": order["qty"],
                                    "unit_price": self._montary_2_float(
                                        new[0]["price"]
                                    ),
                                },
                            )
                        )
            customer = (
                odoo.http.request.env["res.partner"]
                .sudo()
                .search([("name", "=", v)], limit=1)
            )
            for prod in customer.property_product_pricelist.item_ids:
                prod_accept.append(
                    {
                        "id": prod.id,
                        "product_id": prod.product_id.id,
                        "price": prod.price,
                    }
                )
            request.write(vals)
            for product_line in request.add_product_lines:
                product_line.unlink()
            if len(order_lines) != 0:
                request.write({"add_product_lines": order_lines})
        return {"success": "True", "id": 1, "message": "Success call"}

    @odoo.http.route("/sale-request/cancel-request", type="json", auth="public")
    def cancel_sale_request_api(self, **params):
        """
        External API to cancel an exist sale request in pending state only
        """
        required_field = ["reference"]
        for key in required_field:
            if key not in params.keys():
                return {"success": "False", "message": f"{key} is required"}
        if odoo.http.request.jsonrequest:
            for k, v in params.items():
                if k == "reference":
                    request = (
                        odoo.http.request.env["sale.request"]
                        .sudo()
                        .search([("reference", "=", v)])
                    )
                    if request.sale_state != "pending":
                        return {
                            "success": "False",
                            "message": f"Cannot update sale request with {request.sale_state} state",
                        }
                    else:
                        request.action_rejected()
                        return {
                            "success": "True",
                            "message": f"The sale request {request.reference} is cancelled",
                        }

    @odoo.http.route("/sale-request/get-product-pricelist", type="json", auth="public")
    def get_product_pricelist_api(self, **params):
        """
        External API to get all product detail in pricelist according to current user
        """
        if odoo.http.request.jsonrequest:
            customer = odoo.http.request.env.user.partner_id
            product_list = []
            for product in customer.property_product_pricelist.item_ids:
                product_list.append(
                    (product.id, product.name, self._montary_2_float(product.price))
                )

            return {"success": "True", "message": "Success call", "data": product_list}

    @odoo.http.route("/sale-request/get-customer", type="json", auth="public")
    def get_current_user_api(self):
        """
        External API to get customer name with current login user
        """
        if odoo.http.request.jsonrequest:
            customer = odoo.http.request.env.user.partner_id
            print(customer.name)
            return {
                "success": "True",
                "message": "Success call",
                "data": {"name": customer.name},
            }
