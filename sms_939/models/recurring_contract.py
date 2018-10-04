# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models
from odoo.addons.queue_job.job import job


class Contract(models.Model):
    _inherit = 'recurring.contract'

    @api.multi
    def contract_waiting_mandate(self):
        """
        In case the sponsor paid the first month online, we want to force
        activation of contract and later put it in waiting mandate state.
        """
        for contract in self.filtered('invoice_line_ids'):
            invoices = contract.invoice_line_ids.mapped('invoice_id')
            payment = self.env['account.payment'].search([
                ('invoice_ids', 'in', invoices.ids),
                ('state', '=', 'draft')
            ])
            if payment:
                # Activate contract
                contract._post_payment_first_month()
                contract.contract_active()
        return super(Contract, self).contract_waiting_mandate()

    def associate_group(self, payment_mode_id):
        res = super(Contract, self).associate_group(payment_mode_id)
        self.group_id.on_change_payment_mode()
        return res

    @api.model
    @job
    def create_sms_sponsorship(self, vals, partner, sms_child_request):
        """ Creates sponsorship from REACT webapp data.
        - Mark the partner in pending state if it is a new partner.

        :param vals: form values
        :param partner: res.partner record
        :param sms_child_request: sms.child.request record
        :return: True
        """
        res = super(Contract, self).create_sms_sponsorship(
            vals, partner, sms_child_request)
        if sms_child_request.new_partner:
            sms_child_request.partner_id.state = 'pending'
        return res