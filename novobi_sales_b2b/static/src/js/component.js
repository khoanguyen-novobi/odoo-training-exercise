odoo.define("my.component", function (require) {
	"use strict";

	const { Component, useState, mount } = owl;
	const { xml } = owl.tags;
	var ajax = require("web.ajax");
	var session = require("web.session");
	var product_list = [];

	function getProductPriceList() {
		ajax.jsonRpc("/sale-request/get-product-pricelist", "call", {}).then(function (response) {
			if (response["success"] == "True") {
				product_list = response["data"];
				console.log(product_list);
			}
		});
	}

	function getCurrentUser() {
		ajax.jsonRpc("/sale-request/get-customer", "call", {}).then(function (response) {
			if (response["success"] == "True") {
				$("#customer").html(response["data"]["name"]);
			}
		});
	}

	class CreateButton extends Component {
		constructor() {
			super(...arguments);
		}
		static template = xml`<button id="btn_insert_economic_data" type="button" class="btn btn-success" t-on-click="link">Create</button>`;

		link() {
			location.replace(window.location.href + "/create-sale-request");
		}
	}

	class SubmitButton extends Component {
		static template = xml`<button id="submit_button" type="button" class="btn btn-success" t-on-click="submit">Submit</button>`;

		submit() {
			let data = {
				customer: $("#customer").html(),
				sale_person: $("#sale-person").val(),
				add_product_lines: [],
			};
			$("#product-table tr").each(function () {
				data["add_product_lines"].push({
					id: parseInt($(this).find(".product").val()),
					qty: parseInt($(this).find(".qty").val()),
				});
			});
			ajax.jsonRpc("/sale-request/create", "call", data).then(function (response) {
				if (response["success"] == "True") {
					location.replace("http://localhost:8069/my/sale-request");
				}
			});
		}
	}

	class CreateForm extends Component {
		static template = xml`
			<div>
				<h1>Create Request</h1>
				<form>
					<div class="form-group">
						<label for="salePerson">Sale Person</label>
						<input type="text" class="form-control" id="sale-person"  placeholder="Enter Sale Person"/>
					</div>
					<div class="form-group">
						<label for="Customer">Customer</label>
						<h2 id="customer"></h2>
					</div>
					<div class="form-group">
					<div class="container-lg">
					<div class="table-responsive">
						<div class="table-wrapper">
							<div class="table-title">
								<div class="row">
									<div class="col-sm-4">
										<button t-on-click="addRow" type="button" class="btn btn-info"><i class="fa fa-plus"></i> Add New</button>
									</div>
								</div>
							</div>
							<table  class="table table-bordered">
								<thead>
									<tr>
										<th>Product</th>
										<th>Qty</th>
										<th>Price Unit</th>
										<th>Sub total</th>
										<th>Actions</th>
									</tr>
								</thead>
								<tbody id='product-table'>

								</tbody>
							</table>
						</div>
					</div>
				</div>     
					</div>
				</form>
			</div>
		`;

		addRow() {
			var index = $("table tbody tr:last-child").index();
			var row =
				"<tr>" +
				'<td><select class="form-control product" name="product" id=' +
				'"' +
				(index + 1) +
				'"' +
				"><option value=0 selected>Open this select menu</option></td>" +
				'<td><input value=1 type="text" class="form-control qty" name="qty"></td>' +
				'<td><input disabled="disabled" type="text" class="form-control price_unit" name="price_unit"></td>' +
				'<td><input type="text" class="form-control sub_total" name="sub_total"></td>' +
				"<td>" +
				'<button type="button" class="btn btn-info delete" title="Delete">Delete</button>' +
				"</td>" +
				"</tr>";
			$("table").append(row);
			$("table tbody tr")
				.eq(index + 1)
				.find(".edit")
				.toggle();
			for (let i = 0; i < product_list.length; i++) {
				$("#" + (index + 1)).append("<option value = " + product_list[i][0] + ">" + product_list[i][1] + "</option>");
			}
			let current = $("#" + (index + 1)).closest("tr");
			$("#" + (index + 1)).change(function () {
				if ($(this).val() == 0) {
					current.find(".price_unit").val(0);
					return;
				}
				for (let i = 0; i < product_list.length; i++) {
					if ($(this).val() == product_list[i][0]) {
						current.find(".price_unit").val(product_list[i][2]);
						return;
					}
				}
			});
			current.find(".qty").change(function () {
				let price = current.find(".price_unit").val();
				current.find(".sub_total").val($(this).val() * price);
			});
			current.find(".delete").click(function () {
				current.remove();
			});
		}
	}

	owl.utils.whenReady().then(() => {
		let button = document.getElementById("create_button");
		let form = document.getElementById("create_form");
		let submit = document.getElementById("submit");
		if (button != null) {
			mount(CreateButton, { target: button });
		}
		if (form != null) {
			mount(CreateForm, { target: form });
			getProductPriceList();
			getCurrentUser();
		}
		if (submit != null) {
			mount(SubmitButton, { target: submit });
		}
	});
});
