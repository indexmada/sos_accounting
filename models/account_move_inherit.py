from odoo import models, api, fields
from odoo.http import request
from datetime import datetime
import logging

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        if 'journal_id' in vals:
            journal_id = request.env['account.journal'].browse(vals.get('journal_id'))
            if journal_id.type in ('sale', 'purchase'):
                # Utilisez une séquence prédéfinie
                if journal_id.type == 'sale':
                    sequence = self.env['ir.sequence'].search([('code', '=', 'invoice.client')], limit=1)
                    # prefix = str(sequence.prefix).split('-')[0]
                    prefix = journal_id.code
                else:
                    sequence = self.env['ir.sequence'].search([('code', '=', 'invoice.supplier')], limit=1)
                    # prefix = str(sequence.prefix).split('-')[0]
                    prefix = journal_id.code
                # Vérifiez si la séquence est trouvée
                if sequence:
                    sequence_number = sequence.next_by_id()
                    sequence_number = int(str(sequence_number).split('-')[-1])

                    formatted_sequence = f"{prefix}-{str(datetime.now().year)[-2:]}{datetime.now().month:02d}-{sequence_number:05d}"
                    vals['name'] = formatted_sequence
        return super(AccountMove, self).create(vals)


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

        # sequences = self.env['ir.sequence'].search(['|', ('code', '=', 'invoice.client'), ('code', '=', 'invoice.supplier')])
        # for sequence in sequences:
        #     last_invoice = self.search([
        #         ('name', 'like', '{}-%'.format(str(sequence.prefix).split('-')[0])),
        #         ('create_date', '>=', datetime.now().replace(day=1)),
        #         ('state', 'not in', ('draft', 'cancel'))
        #     ], order='create_date desc', limit=1)

        #     # Réinitialiser à 1 si aucune facture n'existe pour le mois
        #     if not last_invoice:
        #         sequence.number_next = 1
