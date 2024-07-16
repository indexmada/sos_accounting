from odoo import models, fields, api

class SosAccounting(models.Model):
    _name = 'sos.accounting'
    _description = 'Tableau prévisionnel de trésorerie'

    date = fields.Date(string='Date', required=True)
    current_balance = fields.Float(string='Solde actuel')
    client_payable = fields.Float(string='A payer client')
    supplier_payable = fields.Float(string='A payer fournisseur')
    client_order_to_invoice = fields.Float(string='Commande client à facturer')
    supplier_order_to_invoice = fields.Float(string='Commande fournisseur à facturer')
    forecast_balance = fields.Float(string='Solde prévisionnel', compute='_compute_forecast_balance')

    @api.depends('current_balance', 'client_payable', 'supplier_payable', 'client_order_to_invoice', 'supplier_order_to_invoice')
    def _compute_forecast_balance(self):
        for record in self:
            record.forecast_balance = (
                record.current_balance
                + record.client_payable
                - record.supplier_payable
                + record.client_order_to_invoice
                - record.supplier_order_to_invoice
            )

    def name_get(self):
        result = []
        for record in self:
            name = f"Prévision de {record.date.strftime('%Y-%m-%d')}"
            result.append((record.id, name))
        return result
