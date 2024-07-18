from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from odoo import http, fields
from odoo.http import request

import logging
from datetime import datetime, time

class UpdateSosAccountingWizard(models.TransientModel):
    _name = 'sos.accounting.update.wizard'
    _description = 'Mettre à jour prévisions de trésorerie Wizard'

    date = fields.Date(string='Date', default=fields.Date.context_today)

    def update_sos_accounting_data(self):
        date = fields.Datetime.from_string(self.date)
        date_datetime_date = date.date()
        date = fields.Datetime.to_string(date)

        cash_journal = request.env['account.journal'].search([('type', '=', 'cash')])
        bank_journal = request.env['account.journal'].search([('type', '=', 'bank')])

        all_journal = []

        if cash_journal:
            for cash in cash_journal:
                c_balance = request.env['account.move.line'].search([
                    ('journal_id', '=', cash.id),
                    ('date', '=', date),
                ], order='date desc', limit=1)
                dict_resp = {'name': c_balance.journal_id.name, 'balance': c_balance.balance}
                all_journal.append(dict_resp)

        if bank_journal:
            for bank in bank_journal:
                b_balance = request.env['account.move.line'].search([
                    ('journal_id', '=', bank.id),
                    ('date', '=', date),
                ], order='date desc', limit=1)
                dict_resp = {'name': b_balance.journal_id.name, 'balance': b_balance.balance}
                all_journal.append(dict_resp)

        total_balance = sum(elem['balance'] for elem in all_journal)

        # factures clients non payé today
        unpaid_customer_invoices = request.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('invoice_date', '=', date)
        ])
        total_amount_unpaid_customer_invoices = sum(unpaid_customer_invoices.mapped('amount_total'))

        # factures fournisseurs non payés today
        unpaid_vendor_bills = request.env['account.move'].search([
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('invoice_date', '=', date)
        ])
        total_amount_unpaid_vendor_bills = sum(unpaid_vendor_bills.mapped('amount_total'))

        # commande client à facturer
        unfactured_customer_orders = request.env['sale.order'].search([
            ('state', '=', 'sale'),
            ('invoice_status', '!=', 'invoiced'),
            # ('date_order', '=', date),
            ('date_order', '>=', datetime.combine(date_datetime_date, time.min)),
            ('date_order', '<=', datetime.combine(date_datetime_date, time.max))
        ])
        total_amount_unfactured_customer_orders = sum(unfactured_customer_orders.mapped('amount_total'))

        # commande fournisseur à facturer
        unfactured_vendor_orders = request.env['purchase.order'].search([
            ('state', '=', 'purchase'),
            ('invoice_status', '!=', 'invoiced'),
            # ('date_order', '=', date),
            ('date_order', '>=', datetime.combine(date_datetime_date, time.min)),
            ('date_order', '<=', datetime.combine(date_datetime_date, time.max))
        ])
        total_amount_unfactured_vendor_orders = sum(unfactured_vendor_orders.mapped('amount_total'))

        # update sos.accounting
        all_sos_accounting = request.env['sos.accounting'].search([])
        all_sos_accounting.unlink()

        values = {
            'current_balance': total_balance,
            'client_payable': total_amount_unpaid_customer_invoices,
            'supplier_payable': total_amount_unpaid_vendor_bills,
            'client_order_to_invoice': total_amount_unfactured_customer_orders,
            'supplier_order_to_invoice': total_amount_unfactured_vendor_orders
        }
        new_sos_accounting = request.env['sos.accounting'].create(values)
        
        # Afficher une notification de réussite et recharger la page actuelle
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _('Mise à jour faite.'),
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }