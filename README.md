# Accounting Data Integrity Checker for Odoo 18.0

[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-714B67.svg?style=flat-square&logo=odoo&logoColor=white)](https://www.odoo.com)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg?style=flat-square)](https://www.gnu.org/licenses/lgpl-3.0)
[![Author: XodetiStudio](https://img.shields.io/badge/Author-XodetiStudio-06b6d4.svg?style=flat-square)](https://xodetistudio.id)
[![Category](https://img.shields.io/badge/Category-Accounting%20%2F%20Integrity-orange.svg?style=flat-square)](https://xodetistudio.id)

A comprehensive 7-in-1 automated forensic accounting audit tool for **Odoo 18.0 (Community & Enterprise)**. Detect unbalanced journal entries, discover ghost invoices, uncover sequence gaps, verify tax calculations, and compute real-time Database Health Scores. Distributed **100% Free and Open Source** under the LGPL-3 license by **[XodetiStudio](https://xodetistudio.id)**.

---

## 🌟 Key Features

1. **Unbalanced Journal Detector**
   - Scans posted journal entries to immediately identify corrupted entries where Total Debit &ne; Total Credit.

2. **Ghost Invoice Hunter**
   - Finds posted customer invoices or vendor bills that have missing or detached Journal Items (lines).

3. **Tax Calculation Integrity Check**
   - Compares invoice document tax headers against underlying tax journal lines to spot rounding or manual override errors.

4. **Statutory Sequence Gap Analysis**
   - Catches missing invoice numbers to avoid tax auditor penalties and maintain statutory audit compliance.

5. **Forensic Fraud & Anomaly Flags**
   - Flags suspicious transactions, such as weekend or off-hour entries and unnatural round-number amounts.

6. **"Who Did It" Creator Attribution**
   - Pinpoints the exact user account and timestamp associated with problematic entries for swift accountability.

7. **Automated Daily Monitoring & PDF Reports**
   - Configurable automated cron job that sends email notifications when critical data issues are detected.
   - One-click export of executive audit summaries and PDF health certificates.

---

## 📋 Technical Requirements & Dependencies

- **Odoo Version**: 18.0 (Community or Enterprise)
- **Dependencies**:
  - `base`
  - `account`

---

## 🚀 Installation

1. Clone or download this repository.
2. Copy the `accounting_checker` folder to your Odoo `custom_addons` directory.
3. Restart your Odoo server.
4. Enable **Developer Mode** in Settings.
5. Navigate to **Apps** &rarr; **Update Apps List**.
6. Search for `Accounting Data Integrity Checker` and click **Activate**.

---

## ⚙️ How to Use

1. Navigate to **Accounting** &rarr; **Audit** &rarr; **Data Integrity Checker**.
2. Click **Run Health Scan** to inspect your financial ledgers.
3. Review your **Health Score (%)** and drill down into critical error lines.
4. Export the findings report or configure scheduled cron alerts under Settings.

---

## 💼 Explore Flagship Enterprise Suites by XodetiStudio

| Suite | Description | Pricing |
| :--- | :--- | :--- |
| **[Docu eSign Suite](https://xodetistudio.id/?deck=esign)** | PAdES-B-LT Cryptographic PDF Signing, Statutory PERURI e-Materai (UU No. 10/2020), Drag-and-Drop Coordinate Designer, Smart PIN 2FA. Zero SaaS tolls. | €600 (One-Time) |
| **[PathSFA Suite](https://xodetistudio.id)** | Enterprise Offline-First Sales Force Automation Flutter Mobile App + Odoo 18 Backend: GPS visit tracking, order booking, stock check, anti-fraud telemetry. | €2,999 (One-Time) |
| **[PathTMS Suite](https://xodetistudio.id)** | Enterprise Fleet, Dispatch & Transport Management System: delivery optimization, driver companion mobile app, fuel accounting, digital POD. | €2,999 (One-Time) |

---

## 📞 Support, Customization & Consulting

Need ledger repair services, custom tax reporting, or automated banking reconciliation?

- **Website**: [https://xodetistudio.id](https://xodetistudio.id)
- **WhatsApp**: [+62 878-9516-4590](https://wa.me/6287895164590?text=Halo%20XodetiStudio%2C%20saya%20tertarik%20konsultasi%20modul%20Accounting%20Checker.)
- **Email**: [info@xodetistudio.id](mailto:info@xodetistudio.id)

---

## 📄 License

This module is licensed under the **GNU Lesser General Public License v3.0 (LGPL-3)**.  
Copyright &copy; 2026 [XodetiStudio](https://xodetistudio.id). Engineered by Muhammad Thoriq.

