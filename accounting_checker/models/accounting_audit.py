# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import io
import base64
import xlsxwriter
from datetime import datetime

class AccountingAudit(models.Model):
    _name = 'accounting.audit'
    _description = 'Accounting Data Integrity Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_audit desc, id desc'
    _check_company_auto = True  # Odoo Automatic Multi-Company Security

    name = fields.Char(string='Audit Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    date_audit = fields.Datetime(string='Audit Date', default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one('res.users', string='Auditor', default=lambda self: self.env.user, readonly=True)
    
    # Menambahkan default agar otomatis mengambil company user saat ini
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scanning', 'Scanning...'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    target_start_date = fields.Date(string="Start Date (Optional)")
    target_end_date = fields.Date(string="End Date (Optional)")
    
    line_ids = fields.One2many('accounting.audit.line', 'audit_id', string='Audit Lines')
    error_count = fields.Integer(string='Issues Found', compute='_compute_statistics', store=True)
    integrity_score = fields.Float(string='Health Score (%)', compute='_compute_statistics', store=True)

    excel_file = fields.Binary('Report File', readonly=True)
    excel_filename = fields.Char('Report Filename', readonly=True)

    @api.depends('line_ids', 'line_ids.severity', 'line_ids.error_type')
    def _compute_statistics(self):
        for record in self:
            total_issues = len(record.line_ids)
            critical_lines = record.line_ids.filtered(lambda l: l.severity == 'critical')
            
            fatal_errors = critical_lines.filtered(lambda l: l.error_type in ['ghost_invoice', 'unbalanced_journal'])
            
            if len(fatal_errors) > 0:
                record.integrity_score = 0.0
            elif len(critical_lines) > 0:
                record.integrity_score = max(0.0, 80.0 - (len(critical_lines) * 5))
            elif total_issues > 0:
                record.integrity_score = max(0.0, 100.0 - total_issues)
            else:
                record.integrity_score = 100.0
            
            record.error_count = total_issues

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('accounting.audit') or _('New')
        return super(AccountingAudit, self).create(vals_list)

    @api.model
    def _cron_scheduled_scan(self):
        # Loop semua company yang aktif di database
        # Agar scheduler berjalan untuk setiap perusahaan secara terpisah
        for company in self.env['res.company'].search([]):
            audit_name = f"Auto Audit: {datetime.today().strftime('%Y-%m-%d')}"
            # Environment switch ke company tersebut
            audit = self.with_company(company).create({
                'name': audit_name,
                'user_id': self.env.ref('base.user_admin').id,
                'company_id': company.id
            })
            audit.action_start_scan()
            
            if audit.error_count > 0:
                template = self.env.ref('accounting_checker.mail_template_audit_alert', raise_if_not_found=False)
                if template:
                    group_manager = self.env.ref('account.group_account_manager')
                    # Hanya ambil user manager di company terkait
                    recipient_emails = [e for e in group_manager.users.filtered(lambda u: u.email and company.id in u.company_ids.ids).mapped('email') if e]
                    if recipient_emails:
                        email_values = {'email_to': ','.join(recipient_emails)}
                        template.send_mail(audit.id, force_send=True, email_values=email_values)

    def action_start_scan(self):
        self.ensure_one()
        self.write({'state': 'scanning'})
        self.line_ids.unlink()
        
        self._scan_unbalanced_journals()
        self._scan_ghost_invoices()
        self._scan_currency_mismatch()
        self._scan_unreconciled_payments()
        self._scan_tax_integrity()
        self._scan_sequence_gaps()
        self._scan_suspicious_entries()
        
        self.action_complete_scan()

    def action_complete_scan(self):
        self.write({'state': 'done'})

    def action_export_excel(self):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Audit Findings')

        style_header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        style_critical = workbook.add_format({'font_color': 'red', 'bold': True})
        style_warning = workbook.add_format({'font_color': 'orange'})
        style_date = workbook.add_format({'num_format': 'yyyy-mm-dd'})

        headers = ['Severity', 'Error Type', 'Description', 'Trans. Date', 'Created By', 'Partner', 'Related Model', 'Related ID', 'Technical Info']
        for col, title in enumerate(headers):
            sheet.write(0, col, title, style_header)

        row = 1
        for line in self.line_ids:
            style = style_critical if line.severity == 'critical' else style_warning if line.severity == 'warning' else None
            sheet.write(row, 0, line.severity.upper(), style)
            sheet.write(row, 1, line.error_type)
            sheet.write(row, 2, line.name)
            sheet.write(row, 3, line.record_date or '', style_date)
            sheet.write(row, 4, line.move_creator_id.name if line.move_creator_id else 'System/Unknown')
            sheet.write(row, 5, line.partner_id.name if line.partner_id else '')
            sheet.write(row, 6, line.res_model or '')
            sheet.write(row, 7, line.res_id or '')
            sheet.write(row, 8, line.technical_info or '')
            row += 1

        workbook.close()
        output.seek(0)
        filename = f"Audit_Report_{self.name}.xlsx"
        self.write({'excel_file': base64.b64encode(output.read()), 'excel_filename': filename})
        output.close()
        return {'type': 'ir.actions.act_url', 'url': f'/web/content/?model=accounting.audit&id={self.id}&field=excel_file&download=true&filename={filename}', 'target': 'self'}

    # =========================================================
    # SCANNERS (UPDATED FOR MULTI-COMPANY)
    # =========================================================
    
    def _scan_unbalanced_journals(self):
        # Filter: am.company_id = self.company_id.id
        params = [self.company_id.id]
        sql = """
            SELECT am.id, am.name, am.date, am.partner_id, am.create_uid,
                   SUM(aml.debit) as d, SUM(aml.credit) as c
            FROM account_move_line aml JOIN account_move am ON am.id=aml.move_id
            WHERE am.state='posted' AND am.company_id = %s
            """ + self._get_date_filter() + """
            GROUP BY am.id, am.name, am.date, am.partner_id, am.create_uid
            HAVING ABS(SUM(aml.debit)-SUM(aml.credit)) > %s
        """
        
        # Urutan parameter harus sama dengan urutan %s di SQL
        # 1. company_id (di atas)
        # 2. start_date & end_date (di-generate oleh _get_date_params)
        # 3. tolerance (0.001) di HAVING clause
        final_params = self._get_date_params(params)
        final_params.append(0.001)
        
        self.env.cr.execute(sql, final_params)
        for res in self.env.cr.dictfetchall():
            self._create_line(f"Unbalanced: Dr {res['d']} != Cr {res['c']}", 'unbalanced_journal', 'critical', 'account.move', res['id'], res['date'], res['partner_id'], res['create_uid'])

    def _scan_ghost_invoices(self):
        # Filter: am.company_id = self.company_id.id
        params = [self.company_id.id]
        sql = """
            SELECT id, name, date, partner_id, create_uid
            FROM account_move am 
            WHERE state='posted' AND move_type IN ('out_invoice','in_invoice') 
            AND am.company_id = %s
            AND NOT EXISTS (SELECT 1 FROM account_move_line WHERE move_id=am.id)
        """ + self._get_date_filter(date_field='date')
        self.env.cr.execute(sql, self._get_date_params(params))
        for res in self.env.cr.dictfetchall():
            self._create_line(f"Ghost Invoice: {res['name']}", 'ghost_invoice', 'critical', 'account.move', res['id'], res['date'], res['partner_id'], res['create_uid'])

    def _scan_currency_mismatch(self):
        # Filter: am.company_id = self.company_id.id
        params = [self.company_id.id]
        sql = """
            SELECT aml.id, aml.move_id, am.date, am.partner_id, am.create_uid 
            FROM account_move_line aml JOIN account_move am ON am.id=aml.move_id 
            WHERE aml.amount_currency != 0 AND aml.currency_id IS NULL AND am.state='posted'
            AND am.company_id = %s
        """ + self._get_date_filter(alias='aml')
        self.env.cr.execute(sql, self._get_date_params(params))
        for res in self.env.cr.dictfetchall():
            self._create_line("Currency Mismatch", 'currency_mismatch', 'critical', 'account.move', res['move_id'], res['date'], res['partner_id'], res['create_uid'])

    def _scan_unreconciled_payments(self):
        # Filter: company_id = self.company_id.id
        params = [self.company_id.id]
        sql = """
            SELECT id, name, amount, date, partner_id, create_uid
            FROM account_payment 
            WHERE state='posted' AND is_reconciled=false
            AND company_id = %s
        """ + self._get_date_filter(alias='account_payment', date_field='date')
        self.env.cr.execute(sql, self._get_date_params(params))
        for res in self.env.cr.dictfetchall():
            self._create_line(f"Unreconciled: {res['name']}", 'broken_reconciliation', 'warning', 'account.payment', res['id'], res['date'], res['partner_id'], res['create_uid'])

    def _scan_tax_integrity(self):
        """
        UPDATED: Multi-Currency Support.
        - If Foreign Currency: Compare Header Tax vs Sum of Lines 'amount_currency'.
        - If Local Currency: Compare Header Tax vs Sum of Lines 'balance'.
        """
        # Filter: am.company_id = self.company_id.id
        params = [self.company_id.id]
        
        # Penjelasan Logic SQL Baru:
        # Kita Join ke res_company (rc) untuk tahu mata uang perusahaan.
        # CASE WHEN: Jika mata uang invoice beda dengan mata uang company -> Pakai amount_currency.
        # ELSE: Pakai balance (konvensional).
        
        sql = """
            SELECT am.id, am.name, am.amount_tax, am.date, am.partner_id, am.create_uid,
                   COALESCE(SUM(
                       CASE 
                           WHEN am.currency_id != rc.currency_id THEN ABS(aml.amount_currency) 
                           ELSE ABS(aml.balance) 
                       END
                   ), 0) as tax_lines
            FROM account_move am
            JOIN res_company rc ON rc.id = am.company_id
            LEFT JOIN account_move_line aml ON aml.move_id = am.id AND aml.tax_line_id IS NOT NULL
            WHERE am.state = 'posted' 
            AND am.move_type IN ('out_invoice','in_invoice')
            AND am.company_id = %s
            """ + self._get_date_filter() + """
            GROUP BY am.id, am.name, am.amount_tax, am.date, am.partner_id, am.create_uid, am.currency_id, rc.currency_id
            HAVING ABS(am.amount_tax - COALESCE(SUM(
                CASE 
                   WHEN am.currency_id != rc.currency_id THEN ABS(aml.amount_currency) 
                   ELSE ABS(aml.balance) 
                END
            ), 0)) > 0.1 -- Toleransi 0.1 untuk pembulatan kurs
        """
        
        self.env.cr.execute(sql, self._get_date_params(params))
        for res in self.env.cr.dictfetchall():
            self._create_line(
                name=f"Tax Mismatch: Header {res['amount_tax']} != Lines {res['tax_lines']}", 
                etype='tax_error', 
                sev='warning', 
                model='account.move', 
                rid=res['id'], 
                date=res['date'], 
                partner=res['partner_id'], 
                creator=res['create_uid']
            )
            
    def _scan_sequence_gaps(self):
        # Filter: am.company_id = self.company_id.id (Requires string interpolation in CTE for safety or specific handling)
        # Using format here safely because we pass integer ID
        company_sql_filter = f"AND company_id = {self.company_id.id}"
        
        sql = f"""
            WITH sequences AS (
                SELECT id, name, date, partner_id, create_uid,
                    substring(name from '^(.*?)(\\d+)$') as prefix,
                    cast(substring(name from '(\\d+)$') as integer) as seq_num
                FROM account_move
                WHERE state = 'posted' AND move_type = 'out_invoice' AND name IS NOT NULL AND name ~ '(\\d+)$'
                {company_sql_filter}
            ),
            gaps AS (
                SELECT id, name, date, partner_id, create_uid, prefix, seq_num,
                    LAG(seq_num) OVER (PARTITION BY prefix ORDER BY seq_num) as prev_seq_num
                FROM sequences
            )
            SELECT id, name, date, partner_id, create_uid, prefix, seq_num, prev_seq_num,
                (seq_num - prev_seq_num - 1) as missing_count
            FROM gaps
            WHERE prev_seq_num IS NOT NULL AND (seq_num - prev_seq_num) > 1
        """
        self.env.cr.execute(sql)
        for res in self.env.cr.dictfetchall():
            start, end = res['prev_seq_num'] + 1, res['seq_num'] - 1
            msg = f"Missing {res['missing_count']} between {start}-{end}" if start != end else f"Missing: {res['prefix']}{start}"
            self._create_line(f"Gap in {res['prefix']}...", 'sequence_gap', 'warning', 'account.move', res['id'], res['date'], res['partner_id'], res['create_uid'])

    def _scan_suspicious_entries(self):
        # Filter: am.company_id = self.company_id.id
        params = [self.company_id.id]
        sql = """
            SELECT am.id, am.name, am.date, am.partner_id, am.create_uid,
                CASE WHEN EXTRACT(ISODOW FROM am.date) IN (6, 7) THEN 'Weekend Entry'
                     WHEN (am.ref IS NULL OR am.ref = '') THEN 'Missing Reference'
                     ELSE 'Suspicious Round Number'
                END as reason
            FROM account_move am LEFT JOIN account_move_line aml ON aml.move_id = am.id
            WHERE am.state = 'posted' AND am.move_type = 'entry'
            AND am.company_id = %s
            AND (EXTRACT(ISODOW FROM am.date) IN (6, 7) OR (am.ref IS NULL OR am.ref = '') OR (ABS(aml.balance) > 1000000 AND MOD(ABS(aml.balance)::numeric, 100000.0) = 0))
            """ + self._get_date_filter() + """
            GROUP BY am.id, am.name, am.date, am.partner_id, am.ref, am.create_uid
        """
        self.env.cr.execute(sql, self._get_date_params(params))
        for res in self.env.cr.dictfetchall():
            self._create_line(f"Suspicious: {res['reason']}", 'suspicious_entry', 'warning', 'account.move', res['id'], res['date'], res['partner_id'], res['create_uid'])

    # --- Helpers ---
    def _get_date_filter(self, alias='am', date_field='date'):
        f = ""
        if self.target_start_date: f += f" AND {alias}.{date_field} >= %s"
        if self.target_end_date: f += f" AND {alias}.{date_field} <= %s"
        return f

    def _get_date_params(self, params):
        # Helper to push date params to the END of the list
        if self.target_start_date: params.append(self.target_start_date)
        if self.target_end_date: params.append(self.target_end_date)
        return params

    def _create_line(self, name, etype, sev, model, rid, date=False, partner=False, creator=False):
        self.env['accounting.audit.line'].create({
            'audit_id': self.id, 
            'name': name, 
            'error_type': etype, 
            'severity': sev, 
            'res_model': model, 
            'res_id': rid, 
            'record_date': date, 
            'partner_id': partner,
            'move_creator_id': creator
        })

class AccountingAuditLine(models.Model):
    _name = 'accounting.audit.line'
    _description = 'Accounting Audit Detail'
    _order = 'severity, id desc'
    _check_company_auto = True

    audit_id = fields.Many2one('accounting.audit', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='audit_id.company_id', store=True) # Auto-company check
    name = fields.Char(required=True)
    error_type = fields.Selection([('unbalanced_journal','Unbalanced'),('ghost_invoice','Ghost'),('broken_reconciliation','Reconcile'),('currency_mismatch','Currency'),('tax_error','Tax'),('sequence_gap', 'Sequence Gap'),('suspicious_entry', 'Suspicious Entry'),('other','Other')], required=True)
    severity = fields.Selection([('critical','Critical'),('warning','Warning'),('info','Info')], default='warning')
    
    # Details
    record_date = fields.Date(string='Trans. Date')
    partner_id = fields.Many2one('res.partner', string='Partner')
    move_creator_id = fields.Many2one('res.users', string='Created By (User)')
    
    res_model = fields.Char()
    res_id = fields.Integer()
    technical_info = fields.Text()
    is_ignored = fields.Boolean(default=False)

    def action_view_record(self):
        self.ensure_one()
        if not self.res_model or not self.res_id: return
        return {'type': 'ir.actions.act_window', 'res_model': self.res_model, 'res_id': self.res_id, 'view_mode': 'form', 'target': 'current'}