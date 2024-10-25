# -*- coding: utf-8 -*-

import logging
import requests
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    tha_order_code = fields.Char(string="Order Code")
    payment_method = fields.Char(string="Payment Method")
    carrier_id = fields.Many2one(comodel_name="delivery.carrier")

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        for rec in res:
            sale_order = self.env['sale.order'].search([('invoice_ids.id', '=' , res.id)])
            rec.write({
                'tha_order_code': sale_order.tha_order_code,
                'payment_method': sale_order.payment_method,
                'carrier_id': sale_order.carrier_id.id if sale_order.carrier_id else False,
            })
        return res
    
    def action_invoice_paid(self):
        # OVERRIDE
        res = super(AccountMove, self).action_invoice_paid()
        todo = set()
        for invoice in self.filtered(lambda move: move.is_invoice()):
            for line in invoice.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    todo.add((sale_line.order_id, invoice.name))
        for (order, name) in todo:
            order.message_post(body=_("Invoice %s paid") % name)
            if order.tha_order_code:
                order.extra_state = 'paid'
                config = self.env['ir.config_parameter']
                is_extra_status_sync = config.sudo().get_param('tha_integration.is_extra_status_sync')
                order.is_synced = False
                if is_extra_status_sync:
                    order._extra_state_change()
        return res

    # @api.onchange('state')
    # def onchange_state_cancel(self):
    #     if self.tha_order_code and self.payment_state == 'paid':
    #         so = self.env['sale.order'].search([('tha_order_code', '=', self.tha_order_code)])
    #         if so:
    #             so.write({
    #                 'extra_state': 'paid'
    #             })