##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountDebtReportWizard(models.TransientModel):
    _name = 'account.debt.report.wizard'
    _description = 'Account Debt Report Wizard'

    def _default_result_selection(self):
        return 'all' if self.env.user.has_group('account.group_account_invoice') else 'receivable'

    company_id = fields.Many2one(
        'res.company',
        'Company',
        help="If you don't select a company, debt for all companies will be "
        "exported."
    )
    result_selection = fields.Selection(
        [('receivable', 'Receivable Accounts'),
         ('payable', 'Payable Accounts'),
         ('all', 'Receivable and Payable Accounts')],
        "Account Type's",
        required=True,
        default=_default_result_selection,
    )
    from_date = fields.Date('From')
    to_date = fields.Date('To')
    show_invoice_detail = fields.Boolean('Show Invoice Detail')
    # TODO implementar
    # show_receipt_detail = fields.Boolean('Show Receipt Detail')
    historical_full = fields.Boolean(
        help='If true, then it will show all partner history. If not, only '
        'unreconciled items will be shown.')
    company_currency = fields.Boolean(
        default=True,
        help='Add columns for company currency?'
    )
    secondary_currency = fields.Boolean(
        help='Add columns for secondary currency?')

    def confirm(self):
        active_ids = self._context.get('active_ids', False)
        if not active_ids:
            return True
        partners = self.env['res.partner'].browse(active_ids)
        data = {
            'secondary_currency': self.secondary_currency,
            'result_selection': self.result_selection,
            'company_id': self.company_id.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'historical_full': self.historical_full,
            'show_invoice_detail': self.show_invoice_detail,
        }
        return self.env['ir.actions.report'].search(
            [('report_name', '=', 'account_debt_report')],
            limit=1).with_context(
            company_currency=self.company_currency,
            secondary_currency=self.secondary_currency,
            result_selection=self.result_selection,
            company_id=self.company_id.id,
            from_date=self.from_date,
            to_date=self.to_date,
            historical_full=self.historical_full,
            show_invoice_detail=self.show_invoice_detail,
            # show_receipt_detail=self.show_receipt_detail,
        ).report_action(partners, data=data)

    def send_by_email(self):
        active_ids = self._context.get('active_ids', [])
        active_id = self._context.get('active_id', False)
        context = {
            # report keys
            'company_currency': self.company_currency,
            'secondary_currency': self.secondary_currency,
            'result_selection': self.result_selection,
            'company_id': self.company_id.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'historical_full': self.historical_full,
            'show_invoice_detail': self.show_invoice_detail,
            # email keys
            'active_ids': active_ids,
            'active_id': active_id,
            'active_model': 'res.partner',
            'default_composition_mode': 'mass_mail',
            'default_use_template': True,
            'default_template_id': self.env.ref(
                'account_debt_report.email_template_debt_detail').id,
            'default_partner_to': '{{ object.id or \'\' }}',
        }
        self = self.with_context(context)
        return {
            'name': _('Send by Email'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'src_model': 'res.partner',
            'view_type': 'form',
            'context': context,
            'view_mode': 'form',
            'target': 'new',
            'auto_refresh': 1
        }

    @api.constrains('company_currency', 'secondary_currency')
    def _check_has_one_currency(self):
        for wizard in self:
            if not wizard.company_currency and not wizard.secondary_currency:
                raise ValidationError(_('Debe seleccionar por lo menos una moneda para el informe'))
