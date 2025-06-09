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
            self.env['status.info'].create({
                'partner_id': partner.id,
                'trang_thai_tk_dau_tu': 'cho_duyet',
                'ho_so_goc': 'chua_nhan'
            })
        return partners