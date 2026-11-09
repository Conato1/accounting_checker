# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    audit_auto_scan = fields.Boolean(
        string="Enable Daily Auto Audit",
        config_parameter='accounting_checker.audit_auto_scan',
        help="If checked, the system will automatically scan accounting data every night and email the manager if errors are found."
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        cron = self.env.ref('accounting_checker.ir_cron_auto_accounting_audit', raise_if_not_found=False)
        if cron:
            res['audit_auto_scan'] = cron.active
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        cron = self.env.ref('accounting_checker.ir_cron_auto_accounting_audit', raise_if_not_found=False)
        if cron:
            cron.active = self.audit_auto_scan