##############################################################################
#
#    Copyright (C) 2020-2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from ast import literal_eval
from datetime import date
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.addons.queue_job.job import job

logger = logging.getLogger(__name__)


class MassMailingContact(models.Model):
    _inherit = "mail.mass_mailing.contact"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    partner_ids = fields.Many2many(
        "res.partner",
        "mass_mailing_contact_partner_rel",
        "partner_id",
        "mass_mailing_contact_id",
        string="Associated partners",
        readonly=False,
    )
    # the principal partner is computed field from the partner ids
    # we then use the principal partner as a stepping stone to compute the other fields
    partner_id = fields.Many2one(
        "res.partner",
        string="Principal partner",
        compute="_compute_partner_id",
        store=True,
        readonly=True,
    )
    name = fields.Char(related="partner_id.name")
    country_id = fields.Many2one(related="partner_id.country_id")
    company_name = fields.Char(related="partner_id.company_name")

    title_id = fields.Many2one(
        "res.partner.title",
        string="Title",
        compute="_compute_title_id",
    )
    salutation = fields.Char(
        compute="_compute_salutation",
    )
    tag_ids = fields.Many2many(
        "res.partner.category",
        string="Tags",
        compute="_compute_tag_ids",
        store=False,
        readonly=True,
    )

    # Add some computed fields to be used in mailchimp merge fields
    sponsored_child_name = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_reference = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_image = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_is = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_was = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_will_be = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_his = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_sein = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_seine = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_seinen = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_seinem = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_seiner = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_ihm = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_ihn = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_son = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_sa = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_ses = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_lui_leur = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_lui_elle = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_le_la = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_your_child = fields.Char(compute="_compute_sponsored_child_fields")
    pending_letter_child_names = fields.Char(compute="_compute_sponsored_child_fields")

    numspons = fields.Char(compute="_compute_sponsored_child_fields")

    _sql_constraints = [(
        "unique_email", "unique(email)", "This mailing contact already exists"
    )]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.depends("partner_ids")
    def _compute_partner_id(self):
        for record in self:
            partners = record.partner_ids.sorted(
                lambda partner: -len(partner.mapped("sponsored_child_ids"))
            )
            if len(partners) > 1:
                record.partner_id = partners[0]
            else:
                record.partner_id = partners

    def _compute_title_id(self):
        def _get_title(name):
            return self.env.ref(f"partner_compassion.res_partner_title_{name}")

        madam = self.env.ref("base.res_partner_title_madam")
        mister = self.env.ref("base.res_partner_title_mister")
        ladies = _get_title("ladies")
        men = _get_title("men")
        family = _get_title("family")
        mister_miss = _get_title("mister_miss")

        for record in self:
            partners = record.partner_ids.with_context(lang=record.partner_id.lang)
            titles = partners.mapped("title")
            if len(partners) == 1:
                record.title_id = record.partner_id.title
            elif len(set(partners.mapped("lastname"))) == 1:
                record.title_id = family
                # is a family, so update the title for the main partner
                if family not in titles:
                    record.partner_id.title = family
            elif set(titles) == {madam}:
                record.title_id = ladies
            elif set(titles) == {mister}:
                record.title_id = men
            else:
                record.title_id = mister_miss

    def _compute_salutation(self):
        for record in self:
            partners = record.partner_ids.with_context(lang=record.partner_id.lang)
            lastnames = partners.mapped("lastname")
            if len(partners) == 1 or len(set(lastnames)) == 1:
                record.salutation = record.partner_id.salutation
            else:
                has_male = len(partners.filtered(lambda p: p.title.gender == "M")) > 0
                advanced_translation = self.env["ir.advanced.translation"].with_context(lang=record.partner_id.lang)
                title_salutation = advanced_translation.get("salutation", female=not has_male, plural=True).title()
                record.salutation = f"{title_salutation} {', '.join(lastnames)}"

    def _compute_tag_ids(self):
        for record in self:
            record.tag_ids = record.partner_ids.mapped("category_id")

    @api.multi
    def _compute_sponsored_child_fields(self):
        country_filter_id = self.env["res.config.settings"].get_param(
            "mass_mailing_country_filter_id")
        for contact in self:
            partners = contact.partner_ids.with_context(lang=contact.partner_id.lang)
            # Allow option to take a child given in context, otherwise take
            sponsored_child_ids = partners.mapped("sponsored_child_ids")
            # the sponsored children.
            child = self.env.context.get("mailchimp_child", sponsored_child_ids)
            contact.numspons = len(list(child))
            if country_filter_id:
                child = child.filtered(
                    lambda c: c.field_office_id.id == country_filter_id)
            contact.sponsored_child_image = child.filtered(
                'image_url')[:1].thumbnail_url or ''
            contact.sponsored_child_name = child.get_list(
                "preferred_name", 3, child.get_number(), translate=False)
            contact.sponsored_child_reference = child.get_list("local_id")
            contact.sponsored_child_is = child.get("is")
            contact.sponsored_child_was = child.get("was")
            contact.sponsored_child_will_be = child.get("will be")
            contact.sponsored_child_he = child.get("he")
            contact.sponsored_child_his = child.get("his")
            contact.sponsored_child_sein = child.get("sein")
            contact.sponsored_child_seine = child.get("seine")
            contact.sponsored_child_seinen = child.get("seinen")
            contact.sponsored_child_seinem = child.get("seinem")
            contact.sponsored_child_seiner = child.get("seiner")
            contact.sponsored_child_ihm = child.get("ihm")
            contact.sponsored_child_ihn = child.get("ihn")
            contact.sponsored_child_son = child.get("son")
            contact.sponsored_child_sa = child.get("sa")
            contact.sponsored_child_ses = child.get("ses")
            contact.sponsored_child_lui_leur = child.get("lui_leur")
            contact.sponsored_child_lui_elle = child.get("lui_elle")
            contact.sponsored_child_le_la = child.get("le_la")
            contact.sponsored_child_your_child = child.get("your sponsored child")
            # Pending B2S letters for more than 1 year
            pending_b2s_child = self.env["compassion.child"].with_context(
                lang=contact.partner_id.lang)
            one_year_ago = date.today() - relativedelta(years=1)
            for one_child in child:
                recent_letters = self.env["correspondence"].search_count([
                    ("child_id", "=", one_child.id),
                    ("direction", "=", "Beneficiary To Supporter"),
                    ("scanned_date", ">=", one_year_ago)
                ])
                if not recent_letters:
                    pending_b2s_child += one_child
            contact.pending_letter_child_names = pending_b2s_child.get_list(
                "preferred_name", translate=False)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        records = self.env[self._name]
        duplicates = []
        for vals in vals_list:
            # Search and avoid duplicates
            contact = self.search([("email", "=", vals["email"])], limit=1)
            if contact:
                partner_id = vals.pop("partner_id", False) or self.env.context.get(
                    "default_partner_id")
                if partner_id:
                    contact.write({"partner_ids": [(4, partner_id)]})
                duplicates.append(vals.pop("email"))
                if vals:
                    contact.write(vals)
                records += contact
            else:
                # Push the primary partner to the Many2many field as well
                partner_id = vals.get("partner_id") or self.env.context.get(
                    "default_partner_id")
                if partner_id and "partner_ids" not in vals:
                    vals["partner_ids"] = [(4, partner_id)]
        records.process_mailchimp_update()
        new_vals = [vals for vals in vals_list if "email" in vals]
        if new_vals:
            new_records = super().create(new_vals)
            new_records.action_export_to_mailchimp()
            records += new_records
        return records

    @api.multi
    def write(self, values):
        """Merge with other potential existing contacts"""
        if "email" in values:
            # Regroup same email contacts
            other = self.search([("email", "=", values["email"]), ("id", "not in", self.ids)], limit=1)
            if other:
                other.write({"partner_ids": [(4, pid) for pid in self.partner_ids.ids]})
                self.with_delay(eta=5).unlink()
                return True
        return super().write(values)

    @api.multi
    def unlink(self):
        try:
            self.action_archive_from_mailchimp()
        except:
            logger.error("Error archiving mailchimp contact", exc_info=True)
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def get_partner(self, _):
        """Override to fetch partner directly from relation if set."""
        return self.partner_id.id

    @api.multi
    def process_mailchimp_update(self):
        """Update contacts to mailchimp in asynchronous job."""
        if not self or self.env.context.get("skip_mailchimp"):
            return True

        mailchimp_channel = self.env.ref("mass_mailing_switzerland.channel_mailchimp")
        queue_job = self.env["queue.job"].sudo().search([
            ("job_function_id.channel_id", "=", mailchimp_channel.id),
            ("state", "!=", "done")
        ])
        to_update = self
        if queue_job:
            args = [
                item for sublist in queue_job.mapped("args") for item in sublist]
            for contact in self:
                if contact.id in args:
                    to_update -= contact
        for contact in to_update:
            contact.with_delay().action_update_to_mailchimp()
        return True

    @api.multi
    def action_export_to_mailchimp(self):
        """
        Filter opt_out partners
        """
        if self.env.context.get("skip_mailchimp"):
            return True
        return super(
            MassMailingContact, self.filtered(lambda c: not c.partner_id.opt_out)
        ).action_export_to_mailchimp()

    @api.multi
    def action_update_to_mailchimp(self):
        out = True

        for contact_to_update in self:
            # If previous write failed reference to mailchimp member will be lost.
            # Error 404
            try:
                out = out and super(
                    MassMailingContact, contact_to_update).action_update_to_mailchimp()
            except Exception as e:
                # if no contact were found, it means an error occurred at last write().
                # Email field in odoo and mailchimp are now different.
                # solution : we remove previous link to mailchimp and export
                # the contact with new mail
                try:
                    if e.args[0] and literal_eval(e.args[0])['status'] == 404:
                        self.env.clear()
                        available_mailchimp_lists = self.env['mailchimp.lists'].search([])
                        lists = available_mailchimp_lists.mapped('odoo_list_id').ids
                        contact_to_update.subscription_list_ids.filtered(
                            lambda x: x.list_id.id in lists).write({"mailchimp_id": False})
                    # raise exception if it's any other type
                    else:
                        raise e

                    # once link is removed member can again be exported to mailchimp
                    out = out and super(MassMailingContact,
                                        contact_to_update).action_export_to_mailchimp()
                except:
                    logger.warning("Mailchimp error is not correctly processed.")
                    raise e
        return out

    @api.multi
    def action_archive_from_mailchimp(self):
        available_mailchimp_lists = self.env['mailchimp.lists'].search([])
        lists = available_mailchimp_lists.mapped('odoo_list_id').ids
        for record in self:
            lists_to_export = record.subscription_list_ids.filtered(
                lambda x: x.list_id.id in lists and x.mailchimp_id)
            for list in lists_to_export:
                mailchimp_list_id = list.list_id.mailchimp_list_id
                val = mailchimp_list_id.account_id._send_request(
                    'search-members?query=%s&field=exact_matches'
                    % list.contact_id.email, {}, method='GET')
                for member in val['exact_matches']['members']:
                    if member['id'] == list.md5_email and \
                            member['status'] != 'archived':
                        mailchimp_list_id.account_id._send_request(
                            'lists/%s/members/%s' % (
                                mailchimp_list_id.list_id, list.md5_email),
                            {}, method='DELETE')
        return True

    def _invalid_contact(self, bounced):
        for invalid_contact in self:
            ref_partner = invalid_contact.partner_id
            if ref_partner:
                vals = {
                    "invalid_mail": invalid_contact.email,
                    "email": False,
                    "bounced": bounced
                }
                # Here we don't want to remove contact from Mailchimp:
                # the info already comes from Mailchimp.
                ref_partner.with_context(recompute=False,
                                         import_from_mailchimp=True,
                                         no_need=True).write(vals)

                # inform partner email is not valid trough a prepared communication
                invalid_comm = self.env.ref(
                    "partner_communication_switzerland.wrong_email")
                if ref_partner.id:
                    self.env["partner.communication.job"].create(
                        {
                            "config_id": invalid_comm.id,
                            "partner_id": ref_partner.id,
                            "object_ids": ref_partner.id,
                        }
                    )
                ref_partner.message_post(
                    body=_("Mailchimp detected an invalid email address"),
                    subject=ref_partner.invalid_mail
                )
            if not ref_partner or bounced:
                invalid_contact.with_delay().unlink()
