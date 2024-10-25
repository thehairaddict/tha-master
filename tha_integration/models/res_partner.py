# -*- coding: utf-8 -*-

import logging
import requests
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'res.partner'

    tha_customer = fields.Char()