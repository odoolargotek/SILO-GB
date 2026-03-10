# -*- coding: utf-8 -*-
# LT Brigade Module - Brigade Program Type Catalog
# Largotek SRL

from odoo import fields, models


class GBBrigadeProgramType(models.Model):
    _name = 'gb.brigade.program.type'
    _description = 'Brigade Program Type'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='Program Name', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Program name must be unique!'),
    ]
