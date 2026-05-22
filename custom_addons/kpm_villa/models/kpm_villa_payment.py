from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class KpmVillaPayment(models.Model):
    _name = 'kpm.villa.payment'
    _description = 'Villa Rent Payment'

    rent_id = fields.Many2one('kpm.villa.rent', string='Agreement', required=True, ondelete='cascade')
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.context_today)
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True)
    rent_amount = fields.Float(string='Rent Amount')
    paid_amount = fields.Float(string='Paid Amount', required=True)
    pending_amount = fields.Float(string='Pending Amount', compute='_compute_pending_amount', store=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online'),
    ], string='Payment Method', default='cash')
    remarks = fields.Char(string='Remarks')

    @api.depends('rent_amount', 'paid_amount')
    def _compute_pending_amount(self):
        for record in self:
            record.pending_amount = record.rent_amount - record.paid_amount

    @api.constrains('paid_amount', 'rent_amount')
    def _check_paid_amount(self):
        for record in self:
            if record.paid_amount > record.rent_amount:
                raise ValidationError(_('Paid amount cannot exceed rent amount.'))
