# -*- coding: utf-8 -*-

import logging
import requests
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tha_order_code = fields.Char(string="Order Code")
    payment_method = fields.Char(string="Payment Method")
    note = fields.Text(string="Order Note")
    city_order = fields.Char(string="City")
    state_order = fields.Char(string="State")
    country_order = fields.Char(string="Country")
    customer_name = fields.Char(string="Customer Name")
    customer_phone = fields.Char(string="Customer Phone")
    address = fields.Text(string="Address")
    extra_state = fields.Selection(selection=[('new', 'New'), ('shipped', 'Shipped'), ('paid', 'Done'),
                                              ('draft', 'Quotation'), ('sent', 'Quotation Sent'),
                                              ('sale', 'Sale Order'), ('done', 'Locked'), ('cancel', 'Cancelled')],
                                   compute="_compute_extra_state", copy=False, search="_search_extra_state", store=True)

    is_synced = fields.Boolean(string='Is synced')

    def _extra_state_change(self):
        map_dict = {
            # 'draft': 'processing',
            'shipped': 'is-shipped',
            'paid': 'completed',
            'cancel': 'cancelled',
        }
        company_id = self.env.user.company_id
        url = company_id.get_company_tha_url() and str(
            company_id.get_company_tha_url()) + '/wp-json/wc/v3/orders/%s' % self.tha_order_code or False
        consumer_key, consumer_secret = company_id.get_consumer_info()
        if url and map_dict.get(self.extra_state, False) and self.tha_order_code:
            params = {'consumer_key': consumer_key, 'consumer_secret': consumer_secret}
            data = {
                "status": map_dict[self.extra_state]
            }
            r = requests.put(url=url, params=params, json=data)
            print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
            print(r.status_code)
            if r.status_code == 200:
                self.is_synced = True
                self.message_post(body="Status change successfully to %s" % map_dict[self.extra_state])
            elif r.status_code == 400:
                self.message_post(body="Invalid Order %s" % self.tha_order_code)
            elif r.status_code == 522:
                raise ValidationError('Connection timed out from external system when change order status')
            else:
                raise ValidationError(_('Error :: {}').format(r.status_code))

    @api.depends('state')
    def _compute_extra_state(self):
        for rec in self:
            # old_state = rec.extra_state
            # invoices = rec.invoice_ids.filtered(lambda i: i.state != 'cancel')
            # if invoices and all(invoice.payment_state == 'paid' for invoice in invoices) and rec.state == 'sale':
            #     rec.extra_state = 'paid'
            # elif rec.picking_ids.filtered(lambda p: p.state == 'done') and rec.state == 'sale':
            #     rec.extra_state = 'shipped'
            # else:
            config = self.env['ir.config_parameter']
            is_extra_status_sync = config.sudo().get_param('tha_integration.is_extra_status_sync')
            rec.is_synced = False
            rec.extra_state = rec.state
            if rec.state == 'cancel' and is_extra_status_sync:
                rec._extra_state_change()

    # @api.model
    # def fields_view_get(self, view_id=None, view_type="form", toolbar=False, submenu=False):
    #     result = super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     self._extra_state_change()
    #     return result

    def _search_extra_state(self, operator, value):
        recs = self.search([]).filtered(lambda x: x.extra_state == value)
        return [('id', operator, [x.id for x in recs] if recs else False)]

    def action_confirm(self):
        for rec in self:
            res = super(SaleOrder, rec).action_confirm()
            for picking in rec.picking_ids:
                picking.write({
                    'city_order': rec.city_order,
                    'state_order': rec.state_order,
                    'tha_order_code': rec.tha_order_code,
                    'payment_method': rec.payment_method,
                    'address': rec.address,
                    'country_order': rec.country_order,
                    'customer_name': rec.customer_name,
                    'customer_phone': rec.customer_phone,
                })

    def server_action_cancel(self):
        for rec in self:
            res = super(SaleOrder, rec).action_cancel()
            if res != True:
                raise UserError(_("Please cancel %s from the FORM !!") % rec.name)

    def _cron_take_orders(self, per_page=1):
        company_id = self.env.user.company_id
        url = company_id.get_company_tha_url() and str(
            company_id.get_company_tha_url()) + '/wp-json/wc/v3/orders' or False
        consumer_key, consumer_secret = company_id.get_consumer_info()
        if url:
            params = {'consumer_key': consumer_key, 'consumer_secret': consumer_secret, 'per_page': per_page,
                      'order': 'asc'}
            last_order_created = company_id.last_order_created or False
            params.update({'after': last_order_created}) if last_order_created else False
            request_result = requests.get(url=url, params=params)
            status_code = request_result.status_code
            if status_code == 200:
                data = request_result.json()
                for rec in data:
                    lines = []
                    for line in rec['line_items']:
                        product_id = self.env['product.product'].search([('default_code', '=', line['sku'])])
                        if product_id:
                            l = {
                                'product_id': product_id.id,
                                'price_unit': float(line.get('subtotal', '0.0')) / float(line.get('quantity', 1.0)),
                                'product_uom_qty': line.get('quantity', 0.0),
                            }
                            lines.append((0, 0, l))
                        else:
                            # order ==> 12100
                            sale_order_logging_error = self.env['sale.order.logging.error'].search(
                                [('order_code', '=', str(rec['id'])), ('product_sku', '=', line['sku'])])
                            if not sale_order_logging_error:
                                self.env['sale.order.logging.error'].create({
                                    'order_code': str(rec['id']),
                                    'product_sku': line['sku'] or line['id'],
                                })
                            return
                    if float(rec['discount_total']) != 0.0:
                        product_id = self.env['product.product'].search([('name', '=', 'Discount Product')])
                        if product_id:
                            l = {
                                'product_id': product_id.id,
                                'price_unit': -1.0 * float(rec['discount_total']),
                                'product_uom_qty': 1.0,
                            }
                            lines.append((0, 0, l))
                    if float(rec['shipping_total']) != 0.0:
                        product_id = self.env['product.product'].search([('name', '=', 'Delivery Product')])
                        if product_id:
                            l = {
                                'product_id': product_id.id,
                                'price_unit': float(rec['shipping_total']),
                                'product_uom_qty': 1.0,
                            }
                            lines.append((0, 0, l))
                    if float(rec['total_tax']) != 0.0:
                        product_id = self.env['product.product'].search([('name', '=', 'Tax Product')])
                        if product_id:
                            l = {
                                'product_id': product_id.id,
                                'price_unit': float(rec['total_tax']),
                                'product_uom_qty': 1.0,
                            }
                            lines.append((0, 0, l))
                    billing = rec['billing']
                    customer_id = self.env['res.partner'].search(
                        [('parent_id', '=', False), ('email', '=', billing['email'])])
                    country_id = self.env['res.country'].search([('code', '=', billing['country'])])
                    state_id = self.env['res.country.state'].search([('name', '=', billing['state'])])
                    if not state_id and country_id:
                        state_id = self.env['res.country.state'].create({
                            'name': billing['state'],
                            'code': billing['state'],
                            'country_id': country_id.id
                        })
                    if billing['country'] != 'EG':
                        carrier_id = self.env['delivery.carrier'].search([('is_international_carrire', '=', True)],
                                                                         limit=1)
                    elif billing['state'] not in ('cairo'):
                        carrier_id = self.env['delivery.carrier'].search([('is_primary_carrier', '=', True)],
                                                                         limit=1)
                    else:
                        zone = self.env['zone'].search([('name', '=', billing['city'])])
                        delivery_carriers = self.env['delivery.carrier'].search([])
                        carrier_id = delivery_carriers.filtered(
                            lambda x: x.zone_ids.filtered(lambda y: y.id == zone.id if zone else False))

                    if customer_id:
                        customer_id.write({
                            'name': billing['first_name'] + ' ' + billing['last_name'],
                            'street': billing['address_1'],
                            'street2': billing['address_2'],
                            'city': billing['city'],
                            'email': billing['email'],
                            'mobile': billing['phone'],
                            'country_id': country_id.id if country_id else False,
                            'state_id': state_id.id if state_id else False,
                        })
                    else:
                        customer_id = self.env['res.partner'].create({
                            'name': billing['first_name'] + ' ' + billing['last_name'],
                            'street': billing['address_1'],
                            'street2': billing['address_2'],
                            'city': billing['city'],
                            'email': billing['email'],
                            'mobile': billing['phone'],
                            'country_id': country_id.id if country_id else False,
                            'state_id': state_id.id if state_id else False,
                            'tha_customer': str(rec['customer_id'])
                        })
                    if rec['status'] == 'processing':
                        order_status = 'draft'
                    elif rec['status'] == 'cancelled':
                        order_status = 'cancel'
                    else:
                        return
                    sale_order_id = self.env['sale.order'].search([('tha_order_code', '=', str(rec['id']))])
                    if not sale_order_id:
                        sale_order = {
                            'company_id': self.env.user.company_id.id,
                            'tha_order_code': str(rec['id']),
                            'state': order_status,
                            'partner_id': customer_id.id,
                            'order_line': lines,
                            'payment_method': rec['payment_method_title'],
                            'note': rec['customer_note'],
                            'carrier_id': carrier_id.id if carrier_id else False,
                            'city_order': billing['city'],
                            'state_order': billing['state'],
                            'address': billing['address_1'],
                            'country_order': billing['country'],
                            'customer_phone': billing['phone'],
                            'customer_name': billing['first_name'] + ' ' + billing['last_name'],
                        }
                        self.env['sale.order'].sudo().create(sale_order)
                        company_id.last_order_created = rec['date_created']
            elif status_code == 522:
                raise ValidationError('Connection timed out from external system')
            else:
                raise ValidationError(_('Error :: {}').format(status_code))
