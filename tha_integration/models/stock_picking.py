import logging
import requests
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tha_order_code = fields.Char(string="Order Code")
    payment_method = fields.Char(string="Payment Method")
    city_order = fields.Char(string="City")
    state_order = fields.Char(string="State")
    address = fields.Text(string="Address")
    country_order = fields.Char(string="Country")
    customer_name = fields.Char(string="Customer Name")
    customer_phone = fields.Char(string="Customer Phone")

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for rec in self :
            if rec.sale_id and rec.state == 'done':
                rec.sale_id.extra_state = 'shipped'
                config = self.env['ir.config_parameter']
                is_extra_status_sync = config.sudo().get_param('tha_integration.is_extra_status_sync')
                rec.sale_id.is_synced = False
                if is_extra_status_sync:
                    rec.sale_id._extra_state_change()
        return res