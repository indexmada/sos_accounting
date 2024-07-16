from odoo import models, fields, api
from odoo.exceptions import ValidationError

from odoo import http, fields

class TreasuryForecastWizard(models.TransientModel):
    _name = 'sos.accounting.wizard'
    _description = 'Tableau prévisionnel de trésorerie Wizard'

    date = fields.Date(string='Date', default=fields.Date.context_today)

    @api.model
    def export_sos_accounting_to_xls(self):
        if not self.date:
            raise ValidationError('Veuillez ajouter une date !')
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/export_sos_accounting_xls?id_export={}'.format(self.id),
            'target': 'self',
        }