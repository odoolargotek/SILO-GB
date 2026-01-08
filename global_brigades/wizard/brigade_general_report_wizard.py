# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api


class GBBrigadeGeneralReportWizard(models.TransientModel):
    _name = 'gb.brigade.general.report.wizard'
    _description = 'Brigade General Report Wizard'
    
    brigade_id = fields.Many2one(
        'gb.brigade',
        string='Brigade',
        required=True,
        help='Select the brigade to generate the general report.'
    )
    
    def action_generate_report(self):
        """Generate the report and open the form view."""
        self.ensure_one()
        
        # Create the report record
        report = self.env['gb.brigade.general.report'].create({
            'brigade_id': self.brigade_id.id,
        })
        
        # Generate the Excel file
        report.generate_excel_report()
        
        # Return action to open the report
        return {
            'type': 'ir.actions.act_window',
            'name': 'Brigade General Report',
            'res_model': 'gb.brigade.general.report',
            'res_id': report.id,
            'view_mode': 'form',
            'target': 'current',
        }
