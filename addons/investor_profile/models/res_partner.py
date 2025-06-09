from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    investor_profile_ids = fields.One2many('investor.profile', 'partner_id', string='Investor Profiles')
    bank_account_ids = fields.One2many('investor.bank.account', 'partner_id', string='Bank Accounts')
    address_ids = fields.One2many('investor.address', 'partner_id', string='Addresses')
    status_info_ids = fields.One2many('status.info', 'partner_id', string='Status Information')

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        for partner in partners:
            # Tự động tạo thông tin trạng thái cho partner mới
            # Find the associated investor.profile if it exists
            investor_profile = self.env['investor.profile'].search([('partner_id', '=', partner.id)], limit=1)
            status_vals = {
                'partner_id': partner.id,
                'trang_thai_tk_dau_tu': 'cho_duyet',
                'ho_so_goc': 'chua_nhan'
            }
            if investor_profile:
                status_vals['investor_id'] = investor_profile.id
            self.env['status.info'].create(status_vals)
        return partners