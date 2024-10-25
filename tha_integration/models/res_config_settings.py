# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_status_sync = fields.Boolean(string='Status Sync', config_parameter="tha.is_status_sync")
    is_extra_status_sync = fields.Boolean(string='Status Sync', config_parameter="tha_integration.is_extra_status_sync")
