# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    carrier_ids = fields.Many2many(comodel_name="delivery.carrier", string="Carrier", compute='_compute_carrier_ids')

    @api.depends('picking_ids')
    def _compute_carrier_ids(self):
        for rec in self:
            origin = [picking_id.origin for picking_id in rec.picking_ids]
            rec.carrier_ids = rec.env['sale.order'].search([('name', 'in', origin)]).mapped('carrier_id')

    def do_print_product(self):
        # self.write({'printed': True})
        return self.env.ref('tha_integration.action_report_product_batch').report_action(self)
