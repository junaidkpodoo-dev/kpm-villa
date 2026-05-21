from odoo import http
from odoo.http import request
import datetime

class VillaWebsite(http.Controller):

    def _get_dashboard_stats(self):
        villas = request.env['kpm.villa'].search([])
        payments = request.env['kpm.villa.payment'].search([])
        expenses = request.env['kpm.villa.expense'].search([])
        agreements = request.env['kpm.villa.rent'].search([('state', '=', 'running')])
        
        total_revenue = sum(payments.mapped('paid_amount'))
        # Total pending = Rent pending + Water bill pending
        pending_rent = sum(payments.mapped('pending_amount'))
        pending_water = sum(request.env['kpm.villa.water.bill.line'].search([]).mapped('due_amount'))
        pending_amount = pending_rent + pending_water
        
        total_expenses = sum(expenses.mapped('amount'))
        
        return {
            'total_revenue': total_revenue,
            'pending_amount': pending_amount,
            'pending_rent': pending_rent,
            'pending_water': pending_water,
            'total_expenses': total_expenses,
            'net_profit': total_revenue - total_expenses,
            'occupied_villas': len(villas.filtered(lambda v: v.status == 'occupied')),
            'available_villas': len(villas.filtered(lambda v: v.status == 'available')),
            'active_agreements_count': len(agreements),
        }

    @http.route('/villa/mobile/dashboard', type='http', auth='user', website=True)
    def mobile_dashboard(self, **kwargs):
        stats = self._get_dashboard_stats()
        agreements = request.env['kpm.villa.rent'].search([], limit=5, order='create_date desc')
        return request.render("kpm_villa.villa_mobile_dashboard", {
            'stats': stats,
            'agreements': agreements,
        })

    # --- Rooms ---

    @http.route('/villa/mobile/rooms', type='http', auth='user', website=True)
    def mobile_rooms(self, **kwargs):
        selected_status = kwargs.get('status') if kwargs.get('status') in ['occupied', 'available'] else 'all'
        all_rooms = request.env['kpm.villa'].search([], order='name')
        rooms = all_rooms if selected_status == 'all' else all_rooms.filtered(lambda room: room.status == selected_status)
        summary = {
            'total': len(all_rooms),
            'occupied': len(all_rooms.filtered(lambda room: room.status == 'occupied')),
            'available': len(all_rooms.filtered(lambda room: room.status == 'available')),
        }
        return request.render("kpm_villa.villa_mobile_rooms", {
            'rooms': rooms,
            'summary': summary,
            'selected_status': selected_status,
        })

    @http.route('/villa/mobile/room/<int:room_id>', type='http', auth='user', website=True)
    def mobile_room_detail(self, room_id, **kwargs):
        room = request.env['kpm.villa'].browse(room_id)
        if not room.exists():
            return request.redirect('/villa/mobile/rooms')
        active_agreement = request.env['kpm.villa.rent'].search([
            ('villa_id', '=', room.id),
            ('state', '=', 'running'),
        ], limit=1)
        return request.render("kpm_villa.villa_mobile_room_detail", {
            'room': room,
            'active_agreement': active_agreement,
        })

    # --- Customers ---

    @http.route('/villa/mobile/customers', type='http', auth='user', website=True)
    def mobile_customers(self, **kwargs):
        search_term = (kwargs.get('q') or '').strip()
        domain = []
        if search_term:
            domain = [
                '|', '|', '|', '|',
                ('name', 'ilike', search_term),
                ('mobile', 'ilike', search_term),
                ('phone', 'ilike', search_term),
                ('city', 'ilike', search_term),
                ('email', 'ilike', search_term),
            ]
        customers = request.env['res.partner'].search(domain, order='name')
        return request.render("kpm_villa.villa_mobile_customers", {
            'customers': customers,
            'search_term': search_term,
        })

    @http.route('/villa/mobile/customer/new', type='http', auth='user', website=True)
    def mobile_customer_new(self, **kwargs):
        return request.render("kpm_villa.villa_mobile_customer_form", {})

    @http.route('/villa/mobile/customer/save', type='http', auth='user', methods=['POST'], website=True)
    def mobile_customer_save(self, **post):
        customer = request.env['res.partner'].create({
            'name': post.get('name'),
            'mobile': post.get('mobile'),
            'phone': post.get('phone'),
            'email': post.get('email'),
            'street': post.get('street'),
            'street2': post.get('street2'),
            'city': post.get('city'),
        })
        return request.redirect('/villa/mobile/customer/%s' % customer.id)

    @http.route('/villa/mobile/customer/<int:partner_id>', type='http', auth='user', website=True)
    def mobile_customer_detail(self, partner_id, **kwargs):
        customer = request.env['res.partner'].browse(partner_id)
        if not customer.exists():
            return request.redirect('/villa/mobile/customers')
        agreements = request.env['kpm.villa.rent'].search([('partner_id', '=', customer.id)], order='create_date desc')
        return request.render("kpm_villa.villa_mobile_customer_detail", {
            'customer': customer,
            'agreements': agreements,
        })

    # --- Agreements ---

    @http.route('/villa/mobile/agreements', type='http', auth='user', website=True)
    def mobile_agreements(self, **kwargs):
        agreements = request.env['kpm.villa.rent'].search([], order='create_date desc')
        return request.render("kpm_villa.villa_mobile_agreements", {
            'agreements': agreements
        })

    @http.route('/villa/mobile/agreement/<int:agreement_id>', type='http', auth='user', website=True)
    def mobile_agreement_detail(self, agreement_id, **kwargs):
        agreement = request.env['kpm.villa.rent'].browse(agreement_id)
        if not agreement.exists():
            return request.redirect('/villa/mobile/dashboard')
        today = datetime.date.today()
        return request.render("kpm_villa.villa_mobile_agreement_detail", {
            'agreement': agreement,
            'today': today,
            'current_month': today.strftime('%m'),
        })

    @http.route('/villa/mobile/agreement/new', type='http', auth='user', website=True)
    def mobile_agreement_new(self, **kwargs):
        villas = request.env['kpm.villa'].search([('status', '=', 'available')])
        partners = request.env['res.partner'].search([])
        return request.render("kpm_villa.villa_mobile_agreement_edit", {
            'villas': villas,
            'partners': partners,
            'agreement': None,
            'datetime': datetime
        })

    @http.route('/villa/mobile/agreement/<int:agreement_id>/edit', type='http', auth='user', website=True)
    def mobile_agreement_edit(self, agreement_id, **kwargs):
        agreement = request.env['kpm.villa.rent'].browse(agreement_id)
        villas = request.env['kpm.villa'].search([])
        partners = request.env['res.partner'].search([])
        return request.render("kpm_villa.villa_mobile_agreement_edit", {
            'agreement': agreement,
            'villas': villas,
            'partners': partners,
            'datetime': datetime
        })

    @http.route('/villa/mobile/agreement/save', type='http', auth='user', methods=['POST'], website=True)
    def mobile_agreement_save(self, **post):
        vals = {
            'villa_id': int(post.get('villa_id')),
            'partner_id': int(post.get('partner_id')),
            'start_date': post.get('start_date'),
            'end_date': post.get('end_date'),
            'monthly_rent': float(post.get('monthly_rent', 0)),
            'notes': post.get('notes'),
        }
        agreement_id = post.get('agreement_id')
        if agreement_id:
            agreement = request.env['kpm.villa.rent'].browse(int(agreement_id))
            agreement.write(vals)
        else:
            agreement = request.env['kpm.villa.rent'].create(vals)
            agreement.action_confirm() # Automatically confirm for demo/mobile simplicity
            
        return request.redirect('/villa/mobile/agreement/%s' % agreement.id)

    @http.route('/villa/mobile/agreement/<int:agreement_id>/payment/save', type='http', auth='user', methods=['POST'], website=True)
    def mobile_agreement_payment_save(self, agreement_id, **post):
        agreement = request.env['kpm.villa.rent'].browse(agreement_id)
        if not agreement.exists():
            return request.redirect('/villa/mobile/dashboard')

        paid_amount = float(post.get('paid_amount') or 0)
        payment_id = post.get('payment_id')
        if payment_id:
            payment = request.env['kpm.villa.payment'].search([
                ('id', '=', int(payment_id)),
                ('rent_id', '=', agreement.id),
            ], limit=1)
            if payment.exists() and paid_amount > 0:
                amount_to_add = min(paid_amount, payment.pending_amount)
                payment.write({
                    'payment_date': post.get('payment_date') or datetime.date.today(),
                    'paid_amount': payment.paid_amount + amount_to_add,
                    'payment_method': post.get('payment_method') or payment.payment_method,
                    'remarks': post.get('remarks') or payment.remarks,
                })
            return request.redirect('/villa/mobile/agreement/%s' % agreement.id)

        request.env['kpm.villa.payment'].create({
            'rent_id': agreement.id,
            'payment_date': post.get('payment_date') or datetime.date.today(),
            'month': post.get('month'),
            'rent_amount': float(post.get('rent_amount') or agreement.monthly_rent or 0),
            'paid_amount': paid_amount,
            'payment_method': post.get('payment_method') or 'cash',
            'remarks': post.get('remarks'),
        })
        return request.redirect('/villa/mobile/agreement/%s' % agreement.id)

    @http.route('/villa/mobile/agreement/<int:agreement_id>/water/payment/save', type='http', auth='user', methods=['POST'], website=True)
    def mobile_water_payment_save(self, agreement_id, **post):
        agreement = request.env['kpm.villa.rent'].browse(agreement_id)
        if not agreement.exists():
            return request.redirect('/villa/mobile/dashboard')

        line_id = post.get('water_line_id')
        payment_amount = float(post.get('water_payment_amount') or 0)
        if not line_id:
            return request.redirect('/villa/mobile/agreement/%s' % agreement.id)

        water_line = request.env['kpm.villa.water.bill.line'].search([
            ('id', '=', int(line_id)),
            ('rent_id', '=', agreement.id),
        ], limit=1)
        if water_line.exists() and payment_amount > 0 and water_line.due_amount > 0:
            amount_to_add = min(payment_amount, water_line.due_amount)
            water_line.paid_amount += amount_to_add

        return request.redirect('/villa/mobile/agreement/%s' % agreement.id)

    @http.route('/villa/mobile/agreement/delete/<int:agreement_id>', type='http', auth='user', website=True)
    def mobile_agreement_delete(self, agreement_id, **kwargs):
        agreement = request.env['kpm.villa.rent'].browse(agreement_id)
        if agreement.exists():
            agreement.unlink()
        return request.redirect('/villa/mobile/agreements')

    # --- Expenses ---

    @http.route('/villa/mobile/expenses', type='http', auth='user', website=True)
    def mobile_expenses(self, **kwargs):
        search_term = (kwargs.get('q') or '').strip()
        domain = []
        if search_term:
            domain = [
                '|', '|',
                ('name', 'ilike', search_term),
                ('villa_id.name', 'ilike', search_term),
                ('expense_type', 'ilike', search_term),
            ]
        expenses = request.env['kpm.villa.expense'].search(domain, order='expense_date desc')
        return request.render("kpm_villa.villa_mobile_expenses", {
            'expenses': expenses,
            'search_term': search_term,
        })

    @http.route('/villa/mobile/expense/new', type='http', auth='user', website=True)
    def mobile_expense_new(self, **kwargs):
        villas = request.env['kpm.villa'].search([])
        return request.render("kpm_villa.villa_mobile_expense_form", {
            'villas': villas,
            'datetime': datetime
        })

    @http.route('/villa/mobile/expense/save', type='http', auth='user', methods=['POST'], website=True)
    def mobile_expense_save(self, **post):
        request.env['kpm.villa.expense'].create({
            'name': post.get('name'),
            'villa_id': int(post.get('villa_id')),
            'expense_type': post.get('expense_type'),
            'amount': float(post.get('amount', 0)),
            'expense_date': post.get('expense_date'),
        })
        return request.redirect('/villa/mobile/expenses')

    # --- Water Bills ---

    @http.route('/villa/mobile/water_bills', type='http', auth='user', website=True)
    def mobile_water_bills(self, **kwargs):
        search_term = (kwargs.get('q') or '').strip()
        domain = []
        if search_term:
            domain = [
                '|',
                ('name', 'ilike', search_term),
                ('line_ids.villa_id.name', 'ilike', search_term),
            ]
        bills = request.env['kpm.villa.water.bill'].search(domain, order='bill_date desc, create_date desc')
        return request.render("kpm_villa.villa_mobile_water_bills", {
            'bills': bills,
            'search_term': search_term,
        })

    @http.route('/villa/mobile/water_bill/new', type='http', auth='user', website=True)
    def mobile_water_bill_new(self, **kwargs):
        running_rents = request.env['kpm.villa.rent'].search([('state', '=', 'running')])
        return request.render("kpm_villa.villa_mobile_water_bill_form", {
            'datetime': datetime,
            'running_rents': running_rents,
        })

    @http.route('/villa/mobile/water_bill/save', type='http', auth='user', methods=['POST'], website=True)
    def mobile_water_bill_save(self, **post):
        total_amount = float(post.get('total_amount') or 0)
        split_method = post.get('split_method', 'equal')
        
        line_vals = []
        if split_method == 'equal':
            running_rents = request.env['kpm.villa.rent'].search([('state', '=', 'running')])
            if not running_rents or total_amount <= 0:
                return request.redirect('/villa/mobile/water_bills')
            split_amount = total_amount / len(running_rents)
            line_vals = [(0, 0, {
                'villa_id': rent.villa_id.id,
                'rent_id': rent.id,
                'amount': split_amount,
            }) for rent in running_rents]
        else:
            # Manual split
            # Expecting keys like rent_amount_1, rent_amount_2...
            for key, value in post.items():
                if key.startswith('rent_amount_') and value:
                    rent_id = int(key.replace('rent_amount_', ''))
                    rent = request.env['kpm.villa.rent'].browse(rent_id)
                    if rent.exists():
                        line_vals.append((0, 0, {
                            'villa_id': rent.villa_id.id,
                            'rent_id': rent.id,
                            'amount': float(value),
                        }))
        
        if not line_vals:
            return request.redirect('/villa/mobile/water_bills')

        bill = request.env['kpm.villa.water.bill'].create({
            'name': post.get('name'),
            'bill_date': post.get('bill_date'),
            'total_amount': total_amount,
            'split_method': split_method,
            'line_ids': line_vals,
        })
        return request.redirect('/villa/mobile/water_bill/%s' % bill.id)

    @http.route('/villa/mobile/water_bill/<int:bill_id>', type='http', auth='user', website=True)
    def mobile_water_bill_detail(self, bill_id, **kwargs):
        bill = request.env['kpm.villa.water.bill'].browse(bill_id)
        if not bill.exists():
            return request.redirect('/villa/mobile/water_bills')
        return request.render("kpm_villa.villa_mobile_water_bill_detail", {
            'bill': bill,
            'datetime': datetime,
        })

    @http.route('/villa/mobile/water_bill/line/<int:line_id>/payment', type='http', auth='user', methods=['POST'], website=True)
    def mobile_water_bill_line_payment_save(self, line_id, **post):
        line = request.env['kpm.villa.water.bill.line'].browse(line_id)
        if not line.exists():
            return request.redirect('/villa/mobile/water_bills')
        
        payment_amount = float(post.get('payment_amount') or 0)
        if payment_amount > 0:
            line.paid_amount += min(payment_amount, line.due_amount)
            
        return request.redirect('/villa/mobile/water_bill/%s' % line.water_bill_id.id)

