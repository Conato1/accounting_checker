# -*- coding: utf-8 -*-
{
    'name': "Accounting Data Integrity Checker",
    'summary': """
        Audit Tool to detect Unbalanced Journals, Ghost Invoices, 
        Missing Reconciliations, Sequence Gaps, and Data Consistency Errors.
    """,
    'description': """
Accounting Data Integrity Checker (Community Audit Edition)
===========================================================
Ensure your Odoo Accounting data is healthy, compliant, and audit-ready.
Engineered for Odoo 18.0 (Community & Enterprise).

7-in-1 Forensic Accounting Audit Engine:
----------------------------------------
* **Unbalanced Journal Detector**: Instantly catches corrupted entries where Debit != Credit.
* **Ghost Invoice Hunter**: Detects posted invoices missing underlying Journal Items (lines).
* **Tax Calculation Integrity**: Reconciles invoice header tax calculations with posted tax lines.
* **Sequence Gap Analysis**: Identifies missing sequence numbers to ensure statutory tax compliance.
* **Forensic Audit & Fraud Checks**: Flags suspicious transactions (e.g., weekend postings, unnatural round sums).
* **Automated Daily Monitoring**: Background cron scheduler that sends email alerts upon detecting critical errors.
* **Executive Health Score**: Instant percentage rating of accounting database health with PDF audit exports.

100% Free and Open Source under LGPL-3 by XodetiStudio (https://xodetistudio.id).
    """,
    'author': "XodetiStudio",
    'website': "https://xodetistudio.id",
    'category': 'Accounting/Accounting',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',

    'depends': ['base', 'account'],

    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'reports/audit_report.xml',
        'views/accounting_audit_views.xml',
        'views/res_config_settings_views.xml',
    ],

    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
