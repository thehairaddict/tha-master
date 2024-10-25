# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class SaleOrderLoggingError(models.Model):
    _name = 'sale.order.logging.error'
    _rec_name = 'order_code'
    _order = 'create_date desc'

    order_code = fields.Char(string="Order Code", required=True)
    product_sku = fields.Char(string="Product SKU", required=True)