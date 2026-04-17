# -*- coding: utf-8 -*-
"""
Post-migration 18.0.1.0.6
Verifica conteo de registros migrados correctamente.
"""
import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(date) AS con_fecha,
            COUNT(time_slot) AS con_hora,
            COUNT(*) FILTER (WHERE date_time IS NOT NULL AND date IS NULL) AS sin_migrar
        FROM gb_brigade_transport
        WHERE date_time IS NOT NULL;
    """)
    row = cr.fetchone()
    _logger.info(
        "GB Migration 18.0.1.0.6 POST — transport migrado: "
        "total=%s, con_fecha=%s, con_hora=%s, sin_migrar=%s",
        row[0], row[1], row[2], row[3]
    )

    if row[3] and row[3] > 0:
        _logger.warning(
            "GB Migration 18.0.1.0.6 POST — ADVERTENCIA: %s registros sin migrar!",
            row[3]
        )
    else:
        _logger.info("GB Migration 18.0.1.0.6 POST — Migracion completada sin errores. ✓")
