# -*- coding: utf-8 -*-
# LT Brigade Module - Brigade Role Catalog
# Largotek SRL

from odoo import fields, models


class GBBrigadeRole(models.Model):
    _name = 'gb.brigade.role'
    _description = 'Brigade Role'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='Role Name', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Role name must be unique!'),
    ]
