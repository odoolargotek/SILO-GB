# -*- coding: utf-8 -*-
"""
Migration 18.0.1.0.4

Convert brigade_role_default and gb_brigade_role from Selection/Char
to Many2one (integer FK) pointing to gb_brigade_role table.
"""


def migrate(cr, version):
    # 1. Create the catalog table if it doesn't exist yet
    #    (Odoo will create it properly, but we need it for FK migration)
    cr.execute("""
        CREATE TABLE IF NOT EXISTS gb_brigade_role (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            create_uid INTEGER,
            write_uid INTEGER,
            create_date TIMESTAMP,
            write_date TIMESTAMP
        );
    """)

    # 2. Drop old columns if they exist with wrong types
    cr.execute("""
        ALTER TABLE gb_brigade_staff
        DROP COLUMN IF EXISTS brigade_role_default;
    """)

    cr.execute("""
        ALTER TABLE res_partner
        DROP COLUMN IF EXISTS gb_brigade_role;
    """)

    # 3. Add new integer FK columns
    cr.execute("""
        ALTER TABLE gb_brigade_staff
        ADD COLUMN IF NOT EXISTS brigade_role_default INTEGER;
    """)

    cr.execute("""
        ALTER TABLE res_partner
        ADD COLUMN IF NOT EXISTS gb_brigade_role INTEGER;
    """)
