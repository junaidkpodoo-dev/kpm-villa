from odoo import fields, models


class KpmVillaEnquiry(models.Model):
    _name = 'kpm.villa.enquiry'
    _description = 'Villa Enquiry'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Customer Name', required=True)
    phone = fields.Char(string='Phone Number', required=True)
    location = fields.Char(string='Location')
    description = fields.Text(string='Description')
