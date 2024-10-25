# -*- coding: utf-8 -*-
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ResCompany(models.Model):
    _inherit = 'res.company'

    tha_url = fields.Char(string="Tha URL")
    consumer_key = fields.Char(string="Consumer Key", required=True)
    consumer_secret = fields.Char(string="Consumer Secret", required=True, )
    last_order_created = fields.Char()
    # tha_user_name = fields.Char(string="Tha User Name")
    # tha_user_password = fields.Char(string="Tha User Password")
    # tha_token = fields.Char(string="Tha User Password")

    def get_company_tha_url(self):
        if self.tha_url:
            return self.tha_url
        else:
            raise ValidationError(_('Please set tha URL'))

    def get_consumer_info(self):
        if self.consumer_key and self.consumer_secret:
            return self.consumer_key , self.consumer_secret
        else :
            raise ValidationError(_('Please set tha Consumer Data'))