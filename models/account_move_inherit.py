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
                    
                    # Vérifiez si invoice_date est défini et si c'était dans le mois précédent
                    if move.invoice_date:
                        invoice_date = datetime.strptime(str(move.invoice_date), '%Y-%m-%d').date()
                        year_invoice_date = str(invoice_date.year)[-2:]  # Utilisation de l'année complète
                        month_invoice_date = str(invoice_date.month).zfill(2)  # Mois formaté avec 2 chiffres

                        # Si la facture est dans le mois précédent (par exemple, décembre 2023 pour une facture de janvier 2024)
                        if invoice_date.month < datetime.now().month:
                            # Recherche des dernières factures créées dans ce mois pour calculer la séquence
                            last_invoice = self.search([
                                ('journal_id', '=', journal_id.id),
                                ('create_date', '>=', datetime(invoice_date.year, invoice_date.month, 1)),
                                ('state', 'not in', ('draft', 'cancel'))
                            ], limit=1, order='create_date desc')

                            if last_invoice:
                                # Incrémente la séquence de facture
                                n_sequence = int(str(last_invoice.name).split('-')[-1]) + 1
                            else:
                                # Si aucune facture existante, commence à 1
                                n_sequence = 1

                            # Formate le numéro de facture
                            formatted_sequence = f"{prefix}-{year_invoice_date}{month_invoice_date}-{n_sequence:05d}"
                            move.name = formatted_sequence
                        else:
                            # Si la facture est pour le mois courant
                            if sequence:
                                sequence_number = sequence.next_by_id()
                                sequence_number = int(str(sequence_number).split('-')[-1])
                                formatted_sequence = f"{prefix}-{year_invoice_date}{month_invoice_date}-{sequence_number:05d}"
                                move.name = formatted_sequence
                    else:
                        # Si invoice_date n'est pas défini, utiliser la date actuelle
                        year_invoice_date = str(datetime.now().year)[-2:]
                        month_invoice_date = str(datetime.now().month).zfill(2)

                        if sequence:
                            sequence_number = sequence.next_by_id()
                            sequence_number = int(str(sequence_number).split('-')[-1])
                            formatted_sequence = f"{prefix}-{year_invoice_date}{month_invoice_date}-{sequence_number:05d}"
                            move.name = formatted_sequence
        return res

