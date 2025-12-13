# -*- coding: utf-8 -*-

# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

"""
Add this method to the GBBrigade model in brigade.py

Place it after the existing action methods like action_open_itinerary_link.
"""

def action_open_roster_import_wizard(self):
    """
    Open the roster import wizard for this brigade.
    """
    self.ensure_one()
    
    return {
        'type': 'ir.actions.act_window',
        'name': 'Import Roster from Excel',
        'res_model': 'lt.roster.import.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'default_brigade_id': self.id,
        },
    }
