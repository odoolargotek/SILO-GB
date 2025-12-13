# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import base64
import pandas as pd
import io
from datetime import datetime

class PartnerExcelImport(models.TransientModel):
    _name = 'lt.partner.excel.import'
    _description = 'LT Importar Participantes desde Excel'

    brigade_id = fields.Many2one('brigade', string='Brigada', required=True)
    import_file = fields.Binary(string='Archivo Excel', required=True)
    filename = fields.Char(string='Nombre Archivo')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('ready', 'Listo para Importar'),
        ('done', 'Importado'),
    ], default='draft', readonly=True)

    preview_lines = fields.Text(string='Vista Previa', readonly=True)
    total_lines = fields.Integer(string='Total Líneas', readonly=True)
    imported_count = fields.Integer(string='Importados', readonly=True)
    error_count = fields.Integer(string='Errores', readonly=True)

    @api.onchange('import_file')
    def _onchange_import_file(self):
        if self.import_file:
            try:
                # Leer Excel con pandas
                df = pd.read_excel(io.BytesIO(base64.b64decode(self.import_file)))
                self.total_lines = len(df)
                
                # Columnas esperadas mínimas
                required_cols = ['nombre', 'apellido', 'identificacion']
                missing_cols = [col for col in required_cols if col.lower() not in [c.lower() for c in df.columns]]
                
                if missing_cols:
                    raise ValidationError(_('Faltan columnas obligatorias: %s. Verifique que el Excel tenga: nombre, apellido, identificacion') % ', '.join(missing_cols))
                
                # Vista previa de primeras 5 líneas
                preview = df.head(5).to_dict('records')
                self.preview_lines = str(preview)[:1000]
                self.state = 'ready'
                
            except Exception as e:
                raise ValidationError(_('Error leyendo Excel: %s') % str(e))

    def action_import_excel(self):
        """Importa los datos del Excel"""
        if not self.import_file:
            raise UserError(_('Debe seleccionar un archivo Excel'))

        # Leer Excel
        df = pd.read_excel(io.BytesIO(base64.b64decode(self.import_file)))
        
        imported = 0
        errors = 0
        error_details = []

        for index, row in df.iterrows():
            try:
                # Limpiar y mapear datos
                partner_data = {
                    'name': f"{row.get('nombre', '').strip()} {row.get('apellido', '').strip()}".strip(),
                    'brigade_ids': [(4, self.brigade_id.id)],
                    'is_company': False,
                    'customer_rank': 1,
                }
                
                # Campos opcionales con prefijo LT para evitar conflictos
                if pd.notna(row.get('identificacion')):
                    partner_data['LT_identificacion'] = str(row.get('identificacion')).strip()
                if pd.notna(row.get('email')):
                    partner_data['email'] = str(row.get('email')).strip()
                if pd.notna(row.get('telefono')):
                    partner_data['phone'] = str(row.get('telefono')).strip()
                if pd.notna(row.get('celular')):
                    partner_data['mobile'] = str(row.get('celular')).strip()
                if pd.notna(row.get('direccion')):
                    partner_data['street'] = str(row.get('direccion')).strip()
                if pd.notna(row.get('ciudad')):
                    partner_data['city'] = str(row.get('ciudad')).strip()
                if pd.notna(row.get('provincia')):
                    partner_data['state_id'] = self._get_state_id(str(row.get('provincia')).strip())
                
                # Crear partner
                partner = self.env['res.partner'].create(partner_data)
                imported += 1
                
            except Exception as e:
                errors += 1
                error_details.append(f"Línea {index+1}: {str(e)}")

        # Actualizar wizard
        self.write({
            'state': 'done',
            'imported_count': imported,
            'error_count': errors,
        })

        # Mensaje resumen
        message = f"Importación completada: {imported} participantes creados"
        if errors:
            message += f", {errors} errores"
            if error_details:
                message += f"\nErrores:\n" + "\n".join(error_details[:5])
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importación Excel'),
                'message': message,
                'type': 'success' if errors == 0 else 'warning',
                'sticky': True,
            }
        }

    def _get_state_id(self, state_name):
        """Busca estado por nombre"""
        state = self.env['res.country.state'].search([('name', 'ilike', state_name)], limit=1)
        return state.id if state else False
