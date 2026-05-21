from odoo import models, fields, api

class KpmVilla(models.Model):
    _name = 'kpm.villa'
    _description = 'Villa Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Villa Name / Room No', required=True, tracking=True)
    description = fields.Text(string='Description')
    floor = fields.Selection([
        ('ground', 'Ground Floor'),
        ('first', 'First Floor'),
        ('second', 'Second Floor'),
    ], string='Floor', default='ground')
    villa_type = fields.Selection([
        ('studio', 'Studio'),
        ('1bhk', '1 BHK'),
        ('2bhk', '2 BHK'),
        ('3bhk', '3 BHK'),
        ('villa', 'Full Villa'),
    ], string='Villa Type', default='1bhk')
    monthly_rent = fields.Float(string='Monthly Rent', required=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
    ], string='Status', default='available', tracking=True)
    active = fields.Boolean(default=True)
    image = fields.Binary(string='Image')

    agreement_count = fields.Integer(compute='_compute_agreement_count')
    total_revenue = fields.Float(compute='_compute_total_revenue')

    def _compute_agreement_count(self):
        for villa in self:
            villa.agreement_count = self.env['kpm.villa.rent'].search_count([('villa_id', '=', villa.id)])

    def _compute_total_revenue(self):
        for villa in self:
            payments = self.env['kpm.villa.payment'].search([('rent_id.villa_id', '=', villa.id)])
            villa.total_revenue = sum(payments.mapped('paid_amount'))

    def action_view_agreements(self):
        self.ensure_one()
        print("hii")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agreements',
            'view_mode': 'list,form',
            'res_model': 'kpm.villa.rent',
            'domain': [('villa_id', '=', self.id)],
            'context': {'default_villa_id': self.id},
        }
