# -*- coding: utf-8 -*-

import datetime
import xlwt
from io import BytesIO
from odoo import http, fields
from odoo.http import request, content_disposition
from odoo.addons.web.controllers.dataset import DataSet

NOM_COLONNE = [
   'Journal',
   'Solde actuel',
   'A payer client',
   'A payer fournisseur',
   'Commande client à facturer',
   'Commande fournisseur à facturer',
   'Solde prévisionnel',
]

COLONNE_EXPORT = {
    'journal': 0,
    'solde_actuel': 1,
    'a_payer_client': 2,
    'a_payer_fournisseur': 3,
    'commande_client_a_facturer': 4,
    'commande_fournisseur_a_facturer': 5,
    'solde_previsionnel': 6
}

class DataSetController(DataSet):
    @http.route('/web/dataset/call_button', type='json', auth="user")
    def call_button(self, model, method, args, kwargs):
        if method == 'export_sos_accounting_to_xls':
            # Get the wizard record
            wizard = request.env['sos.accounting.wizard'].browse(args[0])
            # Call the export_sos_accounting_to_xls method with the wizard record
            return wizard.export_sos_accounting_to_xls()
        else:
            return super(DataSetController, self).call_button(model, method, args, kwargs)
        

class ExportSosAccountingController(http.Controller):
    """Function to export sos accounting """

    @http.route('/web/binary/export_sos_accounting_xls', type='http', auth="public")
    def download_sos_accounting_xls(self, id_export, **kw):
        ## 
        """ 
        - solde des journaux type = liquidité et banque
        - factures clients non payé today
        - factures fournisseurs non payé today
        - commande client à facturer
        - commande fournisseur à facturer
        """
        sos_accounting_wiz = request.env['sos.accounting.wizard'].browse(int(id_export))
        date = sos_accounting_wiz.date
        
        date = fields.Datetime.from_string(date)
        date = fields.Datetime.to_string(date)

        cash_journal = request.env['account.journal'].search([('type', '=', 'cash')])
        bank_journal = request.env['account.journal'].search([('type', '=', 'bank')])

        all_journal = []

        if cash_journal:
            for cash in cash_journal:
                c_balance = request.env['account.move.line'].search([
                    ('journal_id', '=', cash.id),
                    # ('date', '=', date),
                ], order='date desc', limit=1)
                dict_resp = {'name': c_balance.journal_id.name, 'balance': c_balance.balance}
                all_journal.append(dict_resp)

        if bank_journal:
            for bank in bank_journal:
                b_balance = request.env['account.move.line'].search([
                    ('journal_id', '=', bank.id),
                    # ('date', '=', date),
                ], order='date desc', limit=1)
                dict_resp = {'name': b_balance.journal_id.name, 'balance': b_balance.balance}
                all_journal.append(dict_resp)

        total_balance = sum(elem['balance'] for elem in all_journal)

        # factures clients non payé today
        unpaid_customer_invoices = request.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            # ('invoice_date', '=', date)
        ])
        total_amount_unpaid_customer_invoices = sum(unpaid_customer_invoices.mapped('amount_total'))

        # factures fournisseurs non payés today
        unpaid_vendor_bills = request.env['account.move'].search([
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            # ('invoice_date', '=', date)
        ])
        total_amount_unpaid_vendor_bills = sum(unpaid_vendor_bills.mapped('amount_total'))

        # commande client à facturer
        unfactured_customer_orders = request.env['sale.order'].search([
            ('state', '=', 'sale'),
            ('invoice_status', '!=', 'invoiced'),
            # ('date_order', '=', date)
        ])
        total_amount_unfactured_customer_orders = sum(unfactured_customer_orders.mapped('amount_total'))

        # commande fournisseur à facturer
        unfactured_vendor_orders = request.env['purchase.order'].search([
            ('state', '=', 'purchase'),
            ('invoice_status', '!=', 'invoiced'),
            # ('date_order', '=', date)
        ])
        total_amount_unfactured_vendor_orders = sum(unfactured_vendor_orders.mapped('amount_total'))
        
        # get current date
        today = datetime.datetime.now()
        date_str = today.date().strftime("%d/%m/%Y")
        # date_str = fields.Date.from_string(date).strftime("%d/%m/%Y")
        # domain_history = [('date', '=', date)]
        title = "Prévision"
        filename = "Rapport prévision du " + str(date_str)

        workbook = xlwt.Workbook(encoding='utf-8')
        sheet_etat = workbook.add_sheet("Prévision comptable")
        filename = filename + ".xls"
        style_row = xlwt.easyxf('align: wrap yes, horiz right;')

         ### IN HEADER ###
        col = 0
        sheet_etat.write_merge(0,0,0,6,title,xlwt.easyxf("align: horiz center; font: bold 1; "))

        for nom_col in NOM_COLONNE :
            sheet_etat.write(1,col , nom_col,xlwt.easyxf("font : bold 1; align: wrap yes, horiz center; "))
            col += 1
            row = 2
                    
        # sos_accounting_history_entry = request.env['sos.accounting'].search(domain_history)
        
        i = 0
        while i < 7:
            sheet_etat.col(i).width = 256 * 20
            i += 1
            
        # for sos in sorted(sos_accounting_history_entry, key=lambda p: p.date):
        #     date = fields.Datetime.from_string(sos.date)
        #     date = fields.Datetime.to_string(date)
        #     date_str = fields.Date.from_string(date).strftime("%d/%m/%Y")
        #     sheet_etat.write(row, COLONNE_EXPORT['date'], date_str, style_row)
        #     sheet_etat.write(row, COLONNE_EXPORT['solde_actuel'], sos.current_balance, style_row)
        #     sheet_etat.write(row, COLONNE_EXPORT['a_payer_client'], sos.client_payable, style_row)
        #     sheet_etat.write(row, COLONNE_EXPORT['a_payer_fournisseur'], sos.supplier_payable, style_row)
        #     sheet_etat.write(row, COLONNE_EXPORT['commande_client_a_facturer'], sos.client_order_to_invoice, style_row)
        #     sheet_etat.write(row, COLONNE_EXPORT['commande_fournisseur_a_facturer'], sos.supplier_order_to_invoice, style_row)
        #     sheet_etat.write(row, COLONNE_EXPORT['solde_previsionnel'], sos.forecast_balance, style_row)
        #     row += 1

        forecast_balance = (
            total_balance
            + total_amount_unpaid_customer_invoices
            - total_amount_unpaid_vendor_bills
            + total_amount_unfactured_customer_orders
            - total_amount_unfactured_vendor_orders
        )

        formatted_total_balance = '{:,.2f}'.format(total_balance).replace(',', ' ')
        formatted_total_amount_unpaid_customer_invoices = '{:,.2f}'.format(total_amount_unpaid_customer_invoices).replace(',', ' ')
        formatted_total_amount_unpaid_vendor_bills = '{:,.2f}'.format(total_amount_unpaid_vendor_bills).replace(',', ' ')
        formatted_total_amount_unfactured_customer_orders = '{:,.2f}'.format(total_amount_unfactured_customer_orders).replace(',', ' ')
        formatted_total_amount_unfactured_vendor_orders = '{:,.2f}'.format(total_amount_unfactured_vendor_orders).replace(',', ' ')
        formatted_forecast_balance = '{:,.2f}'.format(forecast_balance).replace(',', ' ')
        for journal in all_journal:
            if str(journal['name']) == 'False' and journal['balance'] == 0.0:
                continue
            formatted_journal_balance = '{:,.2f}'.format(journal['balance']).replace(',', ' ')
            sheet_etat.write(row, COLONNE_EXPORT['journal'], journal['name'], xlwt.easyxf('align: wrap yes;'))
            sheet_etat.write(row, COLONNE_EXPORT['solde_actuel'], formatted_journal_balance, style_row)
            # sheet_etat.write(row, COLONNE_EXPORT['a_payer_client'], total_amount_unpaid_customer_invoices, style_row)
            # sheet_etat.write(row, COLONNE_EXPORT['a_payer_fournisseur'], total_amount_unpaid_vendor_bills, style_row)
            # sheet_etat.write(row, COLONNE_EXPORT['commande_client_a_facturer'], total_amount_unfactured_customer_orders, style_row)
            # sheet_etat.write(row, COLONNE_EXPORT['commande_fournisseur_a_facturer'], total_amount_unfactured_vendor_orders, style_row)
            # sheet_etat.write(row, COLONNE_EXPORT['solde_previsionnel'], forecast_balance, style_row)
            row += 1
        # Merge cells in column X from start_row to end_row
        if any(str(elem['name']) != 'False' for elem in all_journal):
            # Determine the range of rows to merge in column X
            start_row = 2
            sheet_etat.write_merge(start_row, row-1, COLONNE_EXPORT['a_payer_client'], COLONNE_EXPORT['a_payer_client'], formatted_total_amount_unpaid_customer_invoices, xlwt.easyxf("align: vert center, horiz right; font: bold 1;"))
            sheet_etat.write_merge(start_row, row-1, COLONNE_EXPORT['a_payer_fournisseur'], COLONNE_EXPORT['a_payer_fournisseur'], formatted_total_amount_unpaid_vendor_bills, xlwt.easyxf("align: vert center, horiz right; font: bold 1;"))
            sheet_etat.write_merge(start_row, row-1, COLONNE_EXPORT['commande_client_a_facturer'], COLONNE_EXPORT['commande_client_a_facturer'], formatted_total_amount_unfactured_customer_orders, xlwt.easyxf("align: vert center, horiz right; font: bold 1;"))
            sheet_etat.write_merge(start_row, row-1, COLONNE_EXPORT['commande_fournisseur_a_facturer'], COLONNE_EXPORT['commande_fournisseur_a_facturer'], formatted_total_amount_unfactured_vendor_orders, xlwt.easyxf("align: vert center, horiz right; font: bold 1;"))
            sheet_etat.write_merge(start_row, row, COLONNE_EXPORT['solde_previsionnel'], COLONNE_EXPORT['solde_previsionnel'], formatted_forecast_balance, xlwt.easyxf("align: vert center, horiz right; font: bold 1;"))

        sheet_etat.write(row, COLONNE_EXPORT['journal'], 'TOTAL', xlwt.easyxf("font : bold 1; align: wrap yes, horiz center; "))
        sheet_etat.write(row, COLONNE_EXPORT['solde_actuel'], formatted_total_balance, xlwt.easyxf("font : bold 1; align: wrap yes, horiz right; "))
        sheet_etat.write(row, COLONNE_EXPORT['a_payer_client'], formatted_total_amount_unpaid_customer_invoices, style_row)
        sheet_etat.write(row, COLONNE_EXPORT['a_payer_fournisseur'], formatted_total_amount_unpaid_vendor_bills, style_row)
        sheet_etat.write(row, COLONNE_EXPORT['commande_client_a_facturer'], formatted_total_amount_unfactured_customer_orders, style_row)
        sheet_etat.write(row, COLONNE_EXPORT['commande_fournisseur_a_facturer'], formatted_total_amount_unfactured_vendor_orders, style_row)
        # sheet_etat.write(row, COLONNE_EXPORT['solde_previsionnel'], formatted_forecast_balance, xlwt.easyxf("font : bold 1; align: wrap yes; "))

        f = BytesIO()
        workbook.save(f)
        f.seek(0)
        file_out = f.read()
        f.close()
        xlsheader = [
            ('Content-Type', 'application/octet-stream'),
            ('Content-Disposition', content_disposition(filename))
        ]
        return request.make_response(file_out,xlsheader)
