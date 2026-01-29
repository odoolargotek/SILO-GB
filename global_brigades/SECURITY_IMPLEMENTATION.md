# Global Brigades - Implementación de Seguridad y Roles

## Resumen de Cambios

Este documento describe la nueva estructura de roles y permisos implementada para el módulo Global Brigades en Odoo 18.

## Roles Implementados

### 1. Admin
- **Acceso:** Control total sin restricciones
- **Permisos:** CRUD completo en todos los modelos
- **Uso:** Super usuario y administradores del sistema

### 2. Program Advisor (PA)
- **Foco:** Gestión de rosters y coordinación de vuelos
- **Permisos principales:**
  - ✅ Crear y editar fichas de brigadas (datos nivel 1)
  - ✅ Crear contactos (necesario para roster)
  - ✅ Gestión completa de Roster (crear, editar, eliminar)
  - ✅ Gestión completa de Arrivals/Departures (vuelos)
  - ✅ Subir y editar listados de roster
  - ✅ Agregar Add-ons/Extras (activity tags)
  - ✅ Exportar reportes
  - ❌ No puede editar: Programs, Staff, Hotels, Transport, Communities

### 3. Operativo/Programático 1 (OP1)
- **Foco:** Gestión operativa completa
- **Permisos principales:**
  - ✅ Crear y editar fichas de brigadas completas
  - ✅ Crear contactos (necesario para staff)
  - ✅ Gestión completa de Programs
  - ✅ Gestión completa de Staff
  - ✅ Gestión completa de Add-ons/Extras
  - ✅ Gestión completa de Hotels/Rooming
  - ✅ Agregar y editar Hotels (catálogo)
  - ✅ Gestión completa de Transport
  - ✅ Agregar y editar Transport providers/vehicles
  - ✅ Agregar y editar Communities
  - ✅ Exportar reportes
  - ❌ No puede: Editar Roster, Arrivals/Departures (solo lectura)

### 4. Operativo/Programático 2 (OP2)
- **Foco:** Gestión programática limitada
- **Permisos principales:**
  - ✅ Ver fichas de brigadas (solo lectura nivel 1)
  - ✅ Crear contactos (necesario para staff)
  - ✅ Editar Programs
  - ✅ Editar Staff
  - ✅ Editar Add-ons/Extras
  - ✅ Gestión completa de Communities (crear, editar, eliminar)
  - ✅ Exportar reportes
  - ❌ No puede: Crear brigadas, Roster, Arrivals/Departures, Hotels, Transport

## Archivos Modificados

### 1. `security/security.xml`
Define los 4 grupos de seguridad:
- `group_gb_admin`
- `group_gb_program_advisor`
- `group_gb_operative_1`
- `group_gb_operative_2`

### 2. `security/ir.model.access.csv`
Define permisos CRUD (Create, Read, Update, Delete) para cada modelo y cada grupo.

Estructura: `access_[modelo]_[grupo],nombre,model_id,group_id,read,write,create,unlink`

### 3. `security/security_rules.xml` (NUEVO)
Define reglas a nivel de registro (record rules) para controlar qué datos puede ver cada rol.

Actualmente implementa acceso total a todos los registros para todos los roles (domain_force = [(1, '=', 1)]).

Si necesitas restringir por ejemplo que PA solo vea brigadas asignadas a ellos:
```xml
<field name="domain_force">[('program_associate_id', '=', user.partner_id.id)]</field>
```

### 4. `__manifest__.py`
Actualizado para incluir `security/security_rules.xml` en el orden correcto de carga.

## Implementación en Vistas (Pendiente)

Para completar la implementación, necesitas actualizar las vistas XML para mostrar/ocultar campos y pestañas según el rol.

### Ejemplo de Control de Visibilidad

En `views/brigade_views.xml`, agregar atributo `groups` a los elementos:

```xml
<!-- Solo PA, Admin y OP1 ven la pestaña Roster -->
<page name="roster" string="Roster" 
      groups="global_brigades.group_gb_admin,global_brigades.group_gb_program_advisor,global_brigades.group_gb_operative_1">
    ...
</page>

<!-- Solo PA y Admin pueden editar Arrivals/Departures -->
<page name="arrivals" string="Arrivals" 
      groups="global_brigades.group_gb_admin,global_brigades.group_gb_program_advisor">
    ...
</page>

<!-- OP1, OP2 y Admin ven la pestaña Programs -->
<page name="programs" string="Programs" 
      groups="global_brigades.group_gb_admin,global_brigades.group_gb_operative_1,global_brigades.group_gb_operative_2">
    ...
</page>

<!-- Solo OP1 y Admin pueden editar Hotels -->
<page name="hotels" string="Hotels / Rooming" 
      groups="global_brigades.group_gb_admin,global_brigades.group_gb_operative_1">
    ...
</page>

<!-- OP2 puede ver pero es solo lectura (control en modelo) -->
<field name="hotel_booking_ids" 
       groups="global_brigades.group_gb_admin,global_brigades.group_gb_operative_1"
       readonly="context.get('default_group_gb_operative_2', False)">
    ...
</field>
```

### Campos de Nivel 1 vs Nivel 2

**Nivel 1 (Datos básicos - PA y OP2 pueden editar):**
- name (Chapter Name)
- arrival_date
- departure_date
- state
- brigade_type
- brigade_program
- coordinator_id
- program_associate_id
- extra_info

**Nivel 2 (Datos operativos - Solo Admin y OP1 tienen acceso completo):**
- Pestañas completas: Programs, Staff, Hotels, Transport
- Para PA: Solo Roster, Arrivals, Departures
- Para OP2: Solo Programs, Staff, Add-ons (editar), Communities (completo)

## Pasos de Implementación

### 1. Actualizar Módulo en Odoo

```bash
# Opción 1: Desde línea de comandos
cd /path/to/odoo
./odoo-bin -u global_brigades -d tu_database --stop-after-init

# Opción 2: Desde interfaz web
# Apps > Global Brigades > Upgrade
```

### 2. Verificar Grupos Creados

- Ir a: **Settings > Users & Companies > Groups**
- Buscar: "Global Brigades"
- Deberían aparecer los 4 grupos nuevos

### 3. Asignar Usuarios a Grupos

- Ir a: **Settings > Users & Companies > Users**
- Editar cada usuario
- En la pestaña "Access Rights", buscar "Global Brigades"
- Seleccionar el rol apropiado:
  - GB / Admin
  - GB / Program Advisor
  - GB / Operativo Programático 1
  - GB / Operativo Programático 2

### 4. Probar Permisos

Con diferentes usuarios asignados a cada rol:

#### Pruebas para Program Advisor:
- ✅ Puede crear nueva brigada
- ✅ Puede editar nombre, fechas básicas
- ✅ Puede agregar/editar roster
- ✅ Puede agregar/editar arrivals/departures
- ✅ Puede exportar reportes
- ❌ No puede editar programs
- ❌ No puede editar staff
- ❌ No puede editar hotels
- ❌ No puede eliminar brigada

#### Pruebas para Operativo 1:
- ✅ Puede crear nueva brigada
- ✅ Puede editar todos los campos
- ✅ Puede agregar/editar programs
- ✅ Puede agregar/editar staff
- ✅ Puede agregar/editar hotels
- ✅ Puede agregar/editar transport
- ✅ Puede agregar/editar communities
- ✅ Puede eliminar brigada
- ❌ Solo lectura en roster
- ❌ Solo lectura en arrivals/departures

#### Pruebas para Operativo 2:
- ❌ No puede crear brigada
- ✅ Puede ver brigadas existentes
- ✅ Puede editar programs
- ✅ Puede editar staff
- ✅ Puede editar add-ons
- ✅ Puede crear/editar/eliminar communities
- ✅ Puede exportar reportes
- ❌ Solo lectura en todo lo demás

### 5. Actualizar Vistas (Recomendado)

Para mejorar la experiencia de usuario, actualiza las vistas XML para ocultar pestañas y campos que el usuario no puede editar.

Archivos a revisar:
- `views/brigade_views.xml` (principal)
- `views/brigade_hotel_booking_views.xml`
- `views/brigade_transport_views.xml`
- `views/add_participants_wizard_views.xml`

## Troubleshooting

### Problema: Usuario no ve el menú de Global Brigades
**Solución:** Asegúrate de que el usuario tiene asignado al menos uno de los grupos GB. Todos los grupos tienen acceso a los menús principales.

### Problema: Error "Access Denied" al intentar guardar
**Solución:** 
1. Verifica que el usuario tiene el grupo correcto asignado
2. Revisa el archivo `ir.model.access.csv` para el modelo específico
3. Verifica que `security_rules.xml` no está bloqueando el acceso con un domain restrictivo

### Problema: Usuario puede editar campos que no debería
**Solución:** 
1. Los permisos de modelo permiten la edición pero las vistas deben controlar qué campos mostrar
2. Actualiza las vistas con atributos `groups` o `readonly` según corresponda
3. Considera agregar validaciones en los métodos `write()` del modelo si necesitas control estricto

### Problema: No se cargaron los cambios después de actualizar
**Solución:**
```bash
# Fuerza recarga de datos de seguridad
./odoo-bin -u global_brigades -d tu_database --stop-after-init --load-language=es_BO

# O desde Python
python3 odoo-bin -u global_brigades -d tu_database --stop-after-init
```

## Migración de Usuarios Existentes

Si ya tenías usuarios con los grupos antiguos:

### Mapeo de grupos antiguos a nuevos:
- `group_gb_admin` → Sin cambios (sigue siendo Admin)
- `group_gb_coordinator` → **group_gb_operative_1** (Operativo 1)
- `group_gb_pa` → **group_gb_program_advisor** (Program Advisor)

### Script de migración (ejecutar en shell de Odoo):

```python
# Conectar a la base de datos y ejecutar:
old_coord_group = env.ref('global_brigades.group_gb_coordinator', raise_if_not_found=False)
old_pa_group = env.ref('global_brigades.group_gb_pa', raise_if_not_found=False)

new_op1_group = env.ref('global_brigades.group_gb_operative_1')
new_pa_group = env.ref('global_brigades.group_gb_program_advisor')

if old_coord_group:
    users_coord = old_coord_group.users
    new_op1_group.users = [(4, u.id) for u in users_coord]
    print(f"Migrados {len(users_coord)} usuarios de Coordinator a Operative 1")

if old_pa_group:
    users_pa = old_pa_group.users
    new_pa_group.users = [(4, u.id) for u in users_pa]
    print(f"Migrados {len(users_pa)} usuarios de PA antiguo a Program Advisor nuevo")
```

## Próximos Pasos

1. ✅ Estructura de grupos definida
2. ✅ Permisos de modelo configurados
3. ✅ Record rules implementadas
4. ✅ Manifest actualizado
5. ⏳ **Pendiente:** Actualizar vistas XML con atributos `groups`
6. ⏳ **Pendiente:** Probar exhaustivamente con usuarios reales
7. ⏳ **Pendiente:** Documentar casos especiales y excepciones

## Contacto y Soporte

Para dudas o problemas con la implementación:
- **Desarrollador:** Largotek SRL
- **Email:** contacto@largotek.com
- **Web:** https://largotek.com

---

**Última actualización:** 2026-01-29  
**Versión del módulo:** 18.0.1.0.0
