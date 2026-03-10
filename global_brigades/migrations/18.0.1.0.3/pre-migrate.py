# -*- coding: utf-8 -*-
"""
Migration 18.0.1.0.3

Convert brigade_role_default from a related (virtual) field to a stored Char column.
The column did not exist before because 'related' fields without store=True
are not persisted in the database.
"""


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE gb_brigade_staff
        ADD COLUMN IF NOT EXISTS brigade_role_default VARCHAR;
    """)
