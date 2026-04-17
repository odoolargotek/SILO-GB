# -*- coding: utf-8 -*-
"""
Pre-migration 18.0.1.0.6
Agrega columnas date, time_slot y date_time_display a gb_brigade_transport
y popula desde date_time existente (UTC -> America/Panama, slot 15 min).
"""
import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info("GB Migration 18.0.1.0.6 PRE: Agregando columnas date, time_slot, date_time_display...")

    # 1. Agregar columna date si no existe
    cr.execute("""
        ALTER TABLE gb_brigade_transport
        ADD COLUMN IF NOT EXISTS date date;
    """)

    # 2. Agregar columna time_slot si no existe
    cr.execute("""
        ALTER TABLE gb_brigade_transport
        ADD COLUMN IF NOT EXISTS time_slot varchar;
    """)

    # 3. Agregar columna date_time_display si no existe
    cr.execute("""
        ALTER TABLE gb_brigade_transport
        ADD COLUMN IF NOT EXISTS date_time_display varchar;
    """)

    # 4. Poblar desde date_time existente (UTC -> Panama, redondear a 15 min)
    cr.execute("""
        UPDATE gb_brigade_transport
        SET
            date = (date_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Panama')::date,

            time_slot = to_char(
                date_trunc('hour',
                    (date_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Panama')
                ) + INTERVAL '15 min' * ROUND(
                    EXTRACT(MINUTE FROM
                        (date_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Panama')
                    ) / 15.0
                ),
                'HH24:MI'
            ),

            date_time_display = concat(
                (date_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Panama')::date,
                ' ',
                to_char(
                    date_trunc('hour',
                        (date_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Panama')
                    ) + INTERVAL '15 min' * ROUND(
                        EXTRACT(MINUTE FROM
                            (date_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Panama')
                        ) / 15.0
                    ),
                    'HH24:MI'
                )
            )
        WHERE date_time IS NOT NULL;
    """)

    _logger.info("GB Migration 18.0.1.0.6 PRE: Columnas creadas y pobladas correctamente.")
