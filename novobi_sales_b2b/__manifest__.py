# -*- coding: utf-8 -*-
{
    "name": "novobi_sales_b2b",
    "summary": """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    "description": """
        Long description of module's purpose
    """,
    "author": "Khoa",
    "website": "http://www.yourcompany.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Sale",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["base", "sale", "portal"],
    # always loaded
    "data": [
        "security/sale_security.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
        "wizard/batch_approve.xml",
        "views/sale_request.xml",
        "views/sale_request_portal_templates.xml",
    ]
    # only loaded in demonstration mode
    # "demo": [
    #     "demo/demo.xml",
    # ],
}
