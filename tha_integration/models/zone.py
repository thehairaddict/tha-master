# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class Zone(models.Model):
    _name = 'zone'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string="Zone", required=True)