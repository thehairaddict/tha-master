# -*- coding: utf-8 -*-

import logging
import psycopg2
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def extra_status_sync(self, limit=50):
        _logger.info('################################################')
        so_ids = self.env['sale.order'].search(
            [('is_synced', '=', False), ('tha_order_code', '!=', False),
             ('extra_state', 'in', ('shipped', 'paid', 'cancel'))], limit=limit)
        _logger.info(so_ids)
        for so_id in so_ids:
            so_id._extra_state_change()
