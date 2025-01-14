from odoo import models, api, fields
from odoo.http import request
from datetime import datetime
import logging

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _cron_reset_invoice_sequence(self):
        """ Réinitialisation des séquences chaque mois """
        # Obtenir les juornaux
        journals = request.env['account.journal'].search(['|', ('type', '=', 'sale'), ('type', '=', 'purchase')])
        for journal in journals:
            if journal.type == 'sale':
                sequence = self.env['ir.sequence'].search([('code', '=', 'invoice.client')])
            else:
                sequence = self.env['ir.sequence'].search([('code', '=', 'invoice.supplier')])
            if sequence:
                # Vérifiez les factures créées ce mois
                last_invoice = self.search([
                    ('journal_id', '=', journal.id),
                    ('create_date', '>=', datetime.now().replace(day=1)),
                    ('state', 'not in', ('draft', 'cancel'))
                ], limit=1, order='create_date desc')
                # Réinitialiser si c'est un nouveau mois
                if not last_invoice:
                    sequence.number_next = 1
                    
    def post(self, invoice=False):
        res = super(AccountMove, self).post(invoice=invoice)
        for move in self:
            if move.name == '/':
                journal_id = request.env['account.journal'].browse(move.journal_id)
                if journal_id.type in ('sale', 'purchase'):
                    # Utilisez une séquence prédéfinie
                    if journal_id.type == 'sale':
                        sequence = self.env['ir.sequence'].search([('code', '=', 'invoice.client')], limit=1)
                        prefix = journal_id.code
                    else:
                        sequence = self.env['ir.sequence'].search([('code', '=', 'invoice.supplier')], limit=1)
                        prefix = journal_id.code

                    # Vérifiez si invoice_date est initié et si c'était dans le mois précédent
                    if move.invoice_date:
                        # Modification ici pour obtenir les deux derniers chiffres de l'année correctement
                        year_invoice_date = str(move.invoice_date.year)[-2:]
                        month_invoice_date = str(move.invoice_date.month).zfill(2)

                        if datetime.strptime(move.invoice_date, '%Y-%m-%d').date().month < datetime.now().date().month:
                            last_invoice = self.search([
                                ('journal_id', '=', journal_id.id),
                                ('create_date', '>=', datetime.strptime(move.invoice_date, '%Y-%m-%d').replace(day=1)),
                                ('state', 'not in', ('draft', 'cancel'))
                            ], limit=1, order='create_date desc')
                            if last_invoice:
                                n_sequence = int(str(last_invoice.name).split('-')[-1]) + 1
                            else:
                                n_sequence = 1
                            formatted_sequence = f"{prefix}-{year_invoice_date}{month_invoice_date}-{n_sequence:05d}"
                            move.name = formatted_sequence
                        else:
                            if sequence:
                                sequence_number = sequence.next_by_id()
                                sequence_number = int(str(sequence_number).split('-')[-1])
                                formatted_sequence = f"{prefix}-{year_invoice_date}{month_invoice_date}-{sequence_number:05d}"
                                move.name = formatted_sequence
                    else:
                        year_invoice_date = str(datetime.now().year)[-2:]
                        month_invoice_date = datetime.now().month
                        month_invoice_date = str(month_invoice_date).zfill(2)
                        if sequence:
                            sequence_number = sequence.next_by_id()
                            sequence_number = int(str(sequence_number).split('-')[-1])
                            formatted_sequence = f"{prefix}-{year_invoice_date}{month_invoice_date}-{sequence_number:05d}"
                            move.name = formatted_sequence
        return res

