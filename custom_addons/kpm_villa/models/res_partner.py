from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # New Many2many field for partner attachments
    partner_document_ids = fields.Many2many(
        'ir.attachment',
        'res_partner_attachment_rel',  # Custom relation table name
        'partner_id',
        'attachment_id',
        string='Partner Documents'
    )
    aadhaar_number = fields.Char(
        string="Aadhaar Number",
        required=True
    )