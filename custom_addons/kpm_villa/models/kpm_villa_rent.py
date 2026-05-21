from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class KpmVillaRent(models.Model):
    _name = 'kpm.villa.rent'
    _description = 'Rent Agreement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Tenant', required=True, tracking=True)
    villa_id = fields.Many2one('kpm.villa', string='Villa', required=True, tracking=True)
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string='End Date', required=True)
    monthly_rent = fields.Float(string='Monthly Rent', required=True)
    advance_amount = fields.Float(string='Advance Amount')
    security_deposit = fields.Float(string='Security Deposit')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', tracking=True)

    payment_line_ids = fields.One2many('kpm.villa.payment', 'rent_id', string='Payments')
    water_bill_line_ids = fields.One2many('kpm.villa.water.bill.line', 'rent_id', string='Water Bills')
    expense_ids = fields.One2many('kpm.villa.expense', 'villa_id', string='Expenses', compute='_compute_expenses')

    total_paid = fields.Float(compute='_compute_totals', string='Total Paid')
    pending_amount = fields.Float(compute='_compute_totals', string='Pending Amount')
    water_bill_total = fields.Float(compute='_compute_totals', string='Water Bill Total')
    expense_total = fields.Float(compute='_compute_totals', string='Expense Total')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('kpm.villa.rent') or _('New')
        return super().create(vals_list)

    @api.constrains('villa_id', 'state')
    def _check_active_agreement(self):
        for record in self:
            if record.state == 'running':
                domain = [
                    ('villa_id', '=', record.villa_id.id),
                    ('state', '=', 'running'),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_('This villa already has an active agreement.'))

    @api.onchange('villa_id')
    def _onchange_villa_id(self):
        if self.villa_id:
            self.monthly_rent = self.villa_id.monthly_rent

    def action_confirm(self):
        self.write({'state': 'running'})
        self.villa_id.status = 'occupied'

    def action_close(self):
        self.write({'state': 'closed'})
        self.villa_id.status = 'available'

    def _compute_expenses(self):
        for record in self:
            record.expense_ids = self.env['kpm.villa.expense'].search([('villa_id', '=', record.villa_id.id)])

    def _compute_totals(self):
        for record in self:
            record.total_paid = sum(record.payment_line_ids.mapped('paid_amount'))
            record.pending_amount = sum(record.payment_line_ids.mapped('pending_amount'))
            record.water_bill_total = sum(record.water_bill_line_ids.mapped('amount'))
            record.expense_total = sum(record.expense_ids.mapped('amount'))

    def action_show_payments(self):
        self.ensure_one()
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'kpm.villa.payment',
            'view_mode': 'list,form',
            'domain': [('rent_id', '=', self.id)],
            'context': {'default_rent_id': self.id},
        }

    def action_show_pending(self):
        self.ensure_one()
        return {
            'name': 'Pending Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'kpm.villa.payment',
            'view_mode': 'list,form',
            'domain': [('rent_id', '=', self.id), ('pending_amount', '>', 0)],
            'context': {'default_rent_id': self.id},
        }

    def action_show_water(self):
        self.ensure_one()
        return {
            'name': 'Water Bills',
            'type': 'ir.actions.act_window',
            'res_model': 'kpm.villa.water.bill.line',
            'view_mode': 'list,form',
            'domain': [('rent_id', '=', self.id)],
        }

    def action_show_expenses(self):
        self.ensure_one()
        return {
            'name': 'Villa Expenses',
            'type': 'ir.actions.act_window',
            'res_model': 'kpm.villa.expense',
            'view_mode': 'list,form',
            'domain': [('villa_id', '=', self.villa_id.id)],
            'context': {'default_villa_id': self.villa_id.id},
        }
