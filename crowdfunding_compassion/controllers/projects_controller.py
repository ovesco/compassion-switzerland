##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import werkzeug
from odoo.http import request, route, Controller


class ProjectsController(Controller):

    @route('/together/projects',
           auth="public",
           type="http",
           website=True)
    def get_projects_list(self, **kwargs):
        values = {}
        project_obj = request.env['crowdfunding.project']
        projects = project_obj._get_active_projects_rows()
        first_row = []
        second_row = []
        third_row = []
        for project in projects:
            if len(first_row) < 3:
                first_row.append(project)
            elif len(second_row) < 3:
                second_row.append(project)
            else:
                third_row.append(project)

        values.update({
            "project_list": [first_row, second_row, third_row],
        })
        return request.render(
            "crowdfunding_compassion.project_list_view_template", values)

    @route('/projects/create',
           auth="user",
           type="http",
           method='POST',
           website=True)
    def project_creation_step1(self,  **kwargs):
        values = kwargs.copy()

        reg_obj = request.env["crowdfunding.project"].sudo()
        # project = reg_obj.browse(reg_id).exists().filtered("is_published")
        # if not registration:
        #     # This may be an old link. We can fetch the registration
        #     registration = reg_obj.search(
        #         [("backup_id", "=", reg_id), ("is_published", "=", True)]
        #     )
        #     if not registration:
        #         return werkzeug.utils.redirect("/event/" + str(event.id), 301)

        values["form_model_key"] = "cms.form.crowdfunding.project"
        # This allows the translation to still work on the page
        project_creation_form = self.get_form("crowdfunding.project", **values)
        project_creation_form.form_process()
        values.update(
            {
                "form": project_creation_form,
                # "main_object": registration,
                "website_template": "crowdfunding_compassion.project_creation_view_template",
            }
        )
        project_creation_form = values["form"]
        if project_creation_form.form_success:
            # The user submitted a donation, redirect to confirmation
            result = werkzeug.utils.redirect(project_creation_form.form_next_url(), code=303)
        else:
            result = request.render(values["website_template"], values)
        return self._form_redirect(result)
        # if partner_id != "":
        #     existing_participant = request.env['crowdfunding.participant'].search([
        #         ('partner_id', '=', partner_id)
        #     ])
        #     if not existing_participant:
        #         # create participant if not existing already
        #         request.env['crowdfunding.participant'].create({
        #             'partner_id': partner_id
        #         })
        #     if post:
        #         # create project
        #         request.env['crowdfunding.project'].create({
        #             "name": post.get("project_name"),
        #             "type": post.get("project_type"),
        #             "deadline": post.get("fundraising_duration"),
        #             "project_owner_id": request.env['crowdfunding.participant'].search([
        #                 ('partner_id', '=', partner_id)
        #             ]).id
        #         })
        #         # return confirmation page
        #         return request.render(
        #             "crowdfunding_compassion.project_creation_confirmation_view_template", {})
        #
        # return request.render(
        #     "crowdfunding_compassion.project_creation_view_template", {"user": request.env.user})
