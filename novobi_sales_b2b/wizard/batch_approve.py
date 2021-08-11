from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BatchApproveWizard(models.TransientModel):
    _name = "sale.request.batchapprove.wizard"
    _description = "Batch approve for sale.request model"

    def multi_approve(self):
        ids = self.env.context["active_ids"]
        sale_requests = self.env["sale.request"].browse(ids)
        for sale_rq in sale_requests:
            sale_rq.action_approve()
