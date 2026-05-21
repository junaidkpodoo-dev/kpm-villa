from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class KpmVillaWaterBill(models.Model):
    _name = 'kpm.villa.water.bill'
    _description = 'Water Bill Split'

    name = fields.Char(string='Bill Reference', required=True)
    bill_date = fields.Date(string='Bill Date', required=True, default=fields.Date.context_today)
    total_amount = fields.Float(string='Total Amount', required=True)
    split_method = fields.Selection([
        ('equal', 'Equal Split'),
        ('manual', 'Manual Split'),
    ], string='Split Method', default='equal', required=True)
    line_ids = fields.One2many('kpm.villa.water.bill.line', 'water_bill_id', string='Split Lines')

    def _prepare_equal_split_lines(self, raise_if_empty=False):
        self.ensure_one()
        occupied_rents = self.env['kpm.villa.rent'].search([('state', '=', 'running')])
        if not occupied_rents:
            if raise_if_empty:
                raise ValidationError(_('No running rent agreements found to split this bill.'))
            return []

        split_amount = self.total_amount / len(occupied_rents)
        return [(0, 0, {
            'villa_id': rent.villa_id.id,
            'rent_id': rent.id,
            'amount': split_amount,
        }) for rent in occupied_rents]

    @api.onchange('total_amount', 'split_method')
    def _onchange_split_method(self):
        for record in self:
            if record.split_method == 'equal' and record.total_amount > 0:
                record.line_ids = [(5, 0, 0)] + record._prepare_equal_split_lines()

    def action_split_bill(self):
        for record in self:
            if record.split_method != 'equal':
                raise ValidationError(_('Automatic split is only available for Equal Split.'))
            if record.total_amount <= 0:
                raise ValidationError(_('Please enter a total amount before splitting.'))
            record.line_ids = [(5, 0, 0)] + record._prepare_equal_split_lines(raise_if_empty=True)

    @api.constrains('line_ids', 'total_amount')
    def _check_total_amount(self):
        for record in self:
            if round(sum(record.line_ids.mapped('amount')) - record.total_amount, 2) != 0:
                raise ValidationError(_('Total split amount must equal total bill amount.'))

class KpmVillaWaterBillLine(models.Model):
    _name = 'kpm.villa.water.bill.line'
    _description = 'Water Bill Line'

    water_bill_id = fields.Many2one('kpm.villa.water.bill', string='Water Bill', ondelete='cascade')
    villa_id = fields.Many2one('kpm.villa', string='Villa', required=True)
    rent_id = fields.Many2one('kpm.villa.rent', string='Agreement', required=True)
    amount = fields.Float(string='Total Amount', required=True)
    paid_amount = fields.Float(string='Paid Amount')
    due_amount = fields.Float(string='Due Amount', compute='_compute_due_amount', store=True)

    @api.depends('amount', 'paid_amount')
    def _compute_due_amount(self):
        for record in self:
            record.due_amount = max(record.amount - record.paid_amount, 0.0)

    @api.constrains('amount', 'paid_amount')
    def _check_paid_amount(self):
        for record in self:
            if record.paid_amount > record.amount:
                raise ValidationError(_('Paid amount cannot exceed the water bill amount.'))

    def action_open_payment_wizard(self):
        self.ensure_one()
        if self.due_amount <= 0:
            raise ValidationError(_('This water bill is already paid.'))
        return {
            'name': _('Pay Water Bill'),
            'type': 'ir.actions.act_window',
            'res_model': 'kpm.villa.water.bill.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_payment_amount': self.due_amount,
            },
        }


class KpmVillaWaterBillPaymentWizard(models.TransientModel):
    _name = 'kpm.villa.water.bill.payment.wizard'
    _description = 'Water Bill Payment Wizard'

    line_id = fields.Many2one('kpm.villa.water.bill.line', string='Water Bill Line', required=True, readonly=True)
    payment_amount = fields.Float(string='Payment Amount', required=True)

    def action_confirm_payment(self):
        self.ensure_one()
        if self.payment_amount <= 0:
            raise ValidationError(_('Payment amount must be greater than zero.'))
        if self.payment_amount > self.line_id.due_amount:
            raise ValidationError(_('Payment amount cannot exceed the due amount.'))
        self.line_id.paid_amount += self.payment_amount
        return {'type': 'ir.actions.act_window_close'}
