from odoo import models, fields, api

class KpmVillaExpense(models.Model):
    _name = 'kpm.villa.expense'
    _description = 'Expense Management'

    name = fields.Char(string='Description', required=True)
    expense_date = fields.Date(string='Expense Date', required=True, default=fields.Date.context_today)
    expense_type = fields.Selection([
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('maintenance', 'Maintenance'),
        ('cleaning', 'Cleaning'),
        ('other', 'Other'),
    ], string='Expense Type', default='maintenance', required=True)
    villa_id = fields.Many2one('kpm.villa', string='Villa', required=True)
    amount = fields.Float(string='Amount', required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    notes = fields.Text(string='Notes')
