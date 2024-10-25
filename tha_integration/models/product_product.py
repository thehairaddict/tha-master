# -*- coding: utf-8 -*-

import logging
import requests
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    tha_product_id = fields.Integer(string='Website Product ID')

    def _get_product_id(self, sku='False'):
        company_id = self.env.user.company_id
        url = company_id.get_company_tha_url() and str(
            company_id.get_company_tha_url()) + "/wp-json/wc/v3/products"
        consumer_key, consumer_secret = company_id.get_consumer_info()
        if url:
            params = {'consumer_key': consumer_key, 'consumer_secret': consumer_secret, 'sku': sku}
            request_result = requests.get(url=url, params=params)
            status_code = request_result.status_code
            if status_code == 200:
                data = request_result.json()
                if data and data[0]['manage_stock']:
                    return data[0]['id']

    def _update_stock(self, tha_product_id='', forecasted_with_pending=0):
        company_id = self.env.user.company_id
        url = company_id.get_company_tha_url() and str(
            company_id.get_company_tha_url()) + '/wp-json/wc/v3/products/%s' % tha_product_id
        consumer_key, consumer_secret = company_id.get_consumer_info()
        if url:
            params = {'consumer_key': consumer_key, 'consumer_secret': consumer_secret}

            data = {
                "stock_quantity": forecasted_with_pending
            }

            r = requests.put(url=url, params=params, json=data)
            if r.status_code == 200:
                self.message_post(body="Stock updated successfully")
            elif r.status_code == 400:
                self.message_post(body="Invalid request with status code 400")
            elif r.status_code == 522:
                raise ValidationError('Connection timed out from external system when change order status')
            else:
                raise ValidationError(_('Error :: {} for url :: {} and data :: {}').format(r.status_code, url, str(data)))

    def _cron_update_products(self):
        product_ids = self.env['product.product'].search([('detailed_type', '!=', 'service')])
        for product_id in product_ids:
            report = self.env['report.stock.report_product_product_replenishment']
            list_id = [product_id.id]
            report_values = report._get_report_values(docids=list_id)
            docs = report_values['docs']
            forecasted_with_pending = docs['virtual_available'] + docs['qty']['in'] - docs['qty']['out']

            tha_product_id = self._get_product_id(sku=product_id.default_code)
            if tha_product_id:
                product_id._update_stock(tha_product_id=str(tha_product_id), forecasted_with_pending=int(forecasted_with_pending))
