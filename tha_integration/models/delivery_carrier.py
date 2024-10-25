# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    zone_ids = fields.Many2many(comodel_name="zone", string="Zones")
    is_primary_carrier = fields.Boolean(string="Primary Carrire")
    is_international_carrire = fields.Boolean(string="International Carrier")
