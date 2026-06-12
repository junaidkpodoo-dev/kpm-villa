
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KpmVillaPayment(models.Model):
    _name = 'kpm.villa.payment'
    _description = 'Villa Rent Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'kpm.whatsapp.mixin']
    _order = 'payment_date asc, id asc'

    rent_id = fields.Many2one('kpm.villa.rent', string='Agreement', required=True, ondelete='cascade')
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.context_today)
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True)
    rent_amount = fields.Float(string='Rent Amount')
    paid_amount = fields.Float(string='Paid Amount', required=True)
    balance_amount = fields.Float(string='Balance / Additional Amount', compute='_compute_balance_amount', store=True)
    pending_amount = fields.Float(string='Pending Amount', compute='_compute_pending_amount', store=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online'),
    ], string='Payment Method', default='cash')
    remarks = fields.Char(string='Remarks')

    @api.depends('rent_amount', 'paid_amount')
    def _compute_balance_amount(self):
        for record in self:
            record.balance_amount = (record.paid_amount or 0.0) - (record.rent_amount or 0.0)

    @api.depends('rent_amount', 'paid_amount')
    def _compute_pending_amount(self):
        for record in self:
            record.pending_amount = max((record.rent_amount or 0.0) - (record.paid_amount or 0.0), 0.0)

    def _get_effective_rent_amount(self, rent, advance_amount=None):
        rent.ensure_one()
        monthly_rent = rent.monthly_rent or 0.0
        advance_balance = rent.advance_amount if advance_amount is None else advance_amount
        advance_balance = max(advance_balance or 0.0, 0.0)
        return max(monthly_rent - min(advance_balance, monthly_rent), 0.0)

    def _sync_rent_payment_state(self, rents):
        """Rebuild rent-level carry-forward state from the current payment history.

        Earlier payment lines keep their own pending amount. Positive advance is
        only carried to the next line by reducing that line's rent amount.
        """
        rents = rents.exists()
        if not rents:
            return

        Payment = self.env['kpm.villa.payment']
        for rent in rents:
            payments = Payment.search([('rent_id', '=', rent.id)], order='payment_date asc, id asc')
            carry = 0.0
            monthly_rent = rent.monthly_rent or 0.0

            for payment in payments:
                advance_before_line = max(carry, 0.0)
                effective_rent = max(monthly_rent - min(advance_before_line, monthly_rent), 0.0)

                if payment.rent_amount != effective_rent:
                    payment.with_context(skip_rent_balance_sync=True).write({'rent_amount': effective_rent})

                carry = carry + (payment.paid_amount or 0.0) - monthly_rent

            if rent.advance_amount != carry:
                rent.write({'advance_amount': carry})

    def _get_balance_message(self):
        self.ensure_one()
        balance_amount = self.balance_amount or 0.0
        if balance_amount > 0:
            return _("additional amount is %s") % balance_amount
        if balance_amount < 0:
            return _("pending amount is %s") % abs(balance_amount)
        return _("payment is settled in full")

    def _post_payment_creation_chatter(self):
        for record in self:
            if not record.rent_id or record.paid_amount <= 0:
                continue
            month_label = dict(self._fields['month'].selection).get(record.month, '')
            payment_date_str = fields.Date.to_string(record.payment_date) if record.payment_date else ''
            balance_message = record._get_balance_message()
            message = _(
                "Payment recorded for %(month)s on %(date)s: paid %(paid)s amount out of %(rent)s. %(balance_message)s."
            ) % {
                'month': month_label,
                'date': payment_date_str,
                'paid': record.paid_amount,
                'rent': record.rent_amount,
                'balance_message': balance_message,
            }
            record.rent_id.message_post(body="<p>%s</p>" % message)

    def _post_payment_update_chatter(self, old_paid_amounts):
        for record in self:
            old_paid = old_paid_amounts.get(record.id)
            if old_paid is None or record.paid_amount == old_paid:
                continue
            month_label = dict(self._fields['month'].selection).get(record.month, '')
            payment_date_str = fields.Date.to_string(record.payment_date) if record.payment_date else ''
            balance_message = record._get_balance_message()
            message = _(
                "Payment updated for %(month)s on %(date)s: paid amount changed from %(old)s to %(new)s. %(balance_message)s."
            ) % {
                'month': month_label,
                'date': payment_date_str,
                'old': old_paid,
                'new': record.paid_amount,
                'balance_message': balance_message,
            }
            record.rent_id.message_post(body="<p>%s</p>" % message)

    @api.onchange('rent_id')
    def _onchange_rent_id(self):
        for record in self:
            if record.rent_id:
                record.rent_amount = record._get_effective_rent_amount(record.rent_id)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rent_id = res.get('rent_id') or self.env.context.get('default_rent_id')
        if rent_id:
            rent = self.env['kpm.villa.rent'].browse(rent_id)
            if rent.exists():
                res['rent_amount'] = self._get_effective_rent_amount(rent)
        return res

    def action_open_pending_payment_wizard(self):
        self.ensure_one()
        if self.pending_amount <= 0:
            raise ValidationError(_('This payment has no pending amount.'))
        return {
            'name': _('Pending Amount'),
            'type': 'ir.actions.act_window',
            'res_model': 'kpm.villa.payment.pending.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payment_id': self.id,
                'default_payment_amount': self.pending_amount,
            },
        }

    def _send_payment_receipt_notification(self):
        for record in self:
            if record.paid_amount > 0 and record.rent_id and record.rent_id.partner_id:
                month_label = dict(self._fields['month'].selection).get(record.month, '')
                payment_date_str = fields.Date.to_string(record.payment_date) if record.payment_date else ''
                balance_message = record._get_balance_message()
                message = _(
                    "Dear %s, thank you for your payment of %s on %s for the month of %s. %s."
                ) % (
                    record.rent_id.partner_id.name,
                    record.paid_amount,
                    payment_date_str,
                    month_label,
                    balance_message,
                )
                record._send_whatsapp_message(record.rent_id.partner_id, message)

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals_list = []
        carry_by_rent = {}

        for vals in vals_list:
            new_vals = dict(vals)
            rent = self.env['kpm.villa.rent'].browse(new_vals.get('rent_id'))
            if rent.exists():
                monthly_rent = rent.monthly_rent or 0.0
                carry = carry_by_rent.get(rent.id, rent.advance_amount or 0.0)
                advance_before_line = max(carry, 0.0)
                new_vals['rent_amount'] = max(monthly_rent - min(advance_before_line, monthly_rent), 0.0)
                carry_by_rent[rent.id] = carry + (new_vals.get('paid_amount') or 0.0) - monthly_rent
            prepared_vals_list.append(new_vals)

        records = super(KpmVillaPayment, self).create(prepared_vals_list)
        self._sync_rent_payment_state(records.mapped('rent_id'))
        records._post_payment_creation_chatter()
        return records

    def write(self, vals):
        if self.env.context.get('skip_rent_balance_sync'):
            return super(KpmVillaPayment, self).write(vals)

        old_paid_amounts = {record.id: record.paid_amount for record in self}
        updated_vals = dict(vals)
        if 'rent_id' in updated_vals:
            rent = self.env['kpm.villa.rent'].browse(updated_vals['rent_id'])
            if rent.exists():
                updated_vals['rent_amount'] = self._get_effective_rent_amount(rent)

        old_rents = self.mapped('rent_id')
        res = super(KpmVillaPayment, self).write(updated_vals)

        self._sync_rent_payment_state(old_rents | self.mapped('rent_id'))

        if 'paid_amount' in updated_vals:
            self._post_payment_update_chatter(old_paid_amounts)
            for record in self:
                old_paid = old_paid_amounts.get(record.id, 0.0)
                if record.paid_amount > old_paid:
                    record._send_payment_receipt_notification()
        return res

    def unlink(self):
        rents = self.mapped('rent_id')
        res = super().unlink()
        self.env['kpm.villa.payment']._sync_rent_payment_state(rents)
        return res


class KpmVillaPaymentPendingWizard(models.TransientModel):
    _name = 'kpm.villa.payment.pending.wizard'
    _description = 'Payment Pending Amount Wizard'

    payment_id = fields.Many2one('kpm.villa.payment', string='Payment', required=True, readonly=True)
    payment_amount = fields.Float(string='Payment Amount', required=True)

    def action_confirm_payment(self):
        self.ensure_one()
        if self.payment_amount <= 0:
            raise ValidationError(_('Payment amount must be greater than zero.'))
        if self.payment_amount > self.payment_id.pending_amount:
            raise ValidationError(_('Payment amount cannot exceed the pending amount.'))
        self.payment_id.write({
            'paid_amount': self.payment_id.paid_amount + self.payment_amount,
        })
        return {'type': 'ir.actions.act_window_close'}
