# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _


class GBBrigadeGeneralReportWizard(models.TransientModel):
    """Wizard to generate Brigade General Report"""
    _name = "gb.brigade.general.report.wizard"
    _description = "Brigade General Report Wizard"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
        help="Select the brigade to generate the report.",
    )

    def action_generate_report(self):
        """Generate the Excel report and return download action"""
        self.ensure_one()

        # Create the report record
        report = self.env["gb.brigade.general.report"].create({
            "brigade_id": self.brigade_id.id,
        })

        # Generate the Excel file
        report.generate_excel_report()

        # Return download action
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/gb.brigade.general.report/{report.id}/excel_file?download=true&filename={report.excel_filename}",
            "target": "new",
        }
