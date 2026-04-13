# 🔄 Decisión de Arquitectura: Remover deploy.sh

**Fecha:** 12 Abril 2026  
**Autoridad:** Anderson + Claude Code  
**Status:** ✅ IMPLEMENTADO

---

## 📌 Resumen Ejecutivo

Se **eliminó `labs/deploy.sh`** y se recomienda usar **`sysmho_integration.sh`** con arranque manual del lab.

**Razón:** Coherencia y congruencia con los 5 pilares.

---

## ❌ Problemas con deploy.sh

### 1. Responsabilidades Múltiples (INCOHERENCIA)
- Intentaba hacer 3 cosas: deploy Docker + crear target + lanzar scan
- Cuando una falla, todo falla
- Código duplicado en auto_deploy.sh (3 bucles idénticos)

### 2. Promesas Incumplidas (INCONGRUENCIA)
- `create_target_in_sysmho()` → Solo valida backend, NO crea targets
- `launch_scan()` → Dice "en desarrollo", no hace nada
- Documentación promise automatización completa, pero no se implementó

### 3. Problemas Docker CLI (FUNCIONALIDAD)
- `docker ps -a -q --filter "id=5938*"` → wildcard inválido
- `docker ps $container_ids` → ps no acepta IDs como args
- Sin manejo de permisos Docker (permission denied)

### 4. Sin Validación (ESTABILIDAD)
- Timeout hardcodeado 15s para esperar IP
- Sin reintentos ni exponential backoff
- Silenciosamente continúa si deploy falla

### 5. Sin Auditoría (SEGURIDAD)
- Todas las ops Docker con `> /dev/null 2>&1`
- Imposible rastrear qué pasó en caso de error
- Sin validación de integridad TAR antes de docker load

---

## ✅ Beneficios de esta Decisión

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Coherencia** | 🔴 Multi-responsable | 🟢 Una responsabilidad = un script |
| **Complejidad** | 🔴 3 scripts que interactúan | 🟢 2 scripts independientes |
| **Mantenimiento** | 🔴 Cambios afectan múltiples áreas | 🟢 Cambios localizados |
| **Debugging** | 🔴 Difícil rastrear dónde falló | 🟢 Claro dónde falla |
| **User Experience** | 🔴 "Falla silenciosa" | 🟢 Pasos claros + aprobaciones |

---

## 🆕 Nuevo Flujo (post-decisión)

### Script 1: auto_deploy.sh (Responsabilidad: ARRANCAR LAB)
```bash
# Terminal 1
cd labs/devil
bash auto_deploy.sh devil.tar

# Output:
# ✅ Máquina desplegada, su dirección IP es --> 172.17.0.2
# Ctrl+C elimina automáticamente
```

**Características:**
- ✅ Limpia labs previos
- ✅ docker load + docker run
- ✅ Obtiene IP automáticamente
- ✅ Trap para Ctrl+C (cleanup)
- ✅ Foreground (el usuario ve todo)

### Script 2: sysmho_integration.sh (Responsabilidad: INTEGRACIÓN CON SYSMHO)
```bash
# Terminal 2
bash labs/sysmho_integration.sh auto devil 172.17.0.2 80

# Output:
# 1. Valida backend disponible
# 2. [i] ¿Crear target? (s/n): s
#    ✓ Target creado: [UUID]
# 3. [i] ¿Iniciar scan? (s/n): s
#    ✓ Scan lanzado: [UUID]
# 4. ⠋ Escaneo en progreso... 45%
# 5. ✓ Escaneo completado
# 6. 1. [CRITICAL] SQL Injection ...
```

**Características:**
- ✅ Valida backend online
- ✅ Obtiene API_KEY de .env
- ✅ Crea target (API call real: POST /api/v1/targets)
- ✅ Lanza scan (API call real: POST /api/v1/scans)
- ✅ Monitorea con spinner
- ✅ Muestra findings clasificados
- ✅ **User approval en cada paso crítico**

---

## 🎯 Alineación con 5 Pilares

### Coherencia ✅
- Cada script tiene UNA responsabilidad clara
- Código repetido eliminado
- Flujo lógico simple: deploy → target → scan

### Congruencia ✅
- Lo que promete, lo hace
- APIs realmente se llaman
- Output real, no promesas vacías

### Funcionalidad ✅
- Docker CLI syntax correcta (heredada de auto_deploy.sh)
- API calls implementadas
- User approval loop funciona

### Estabilidad ✅
- Sin timeouts hardcodeados en integration.sh
- Valida cada paso antes de continuar
- Exit codes correctos

### Seguridad ✅
- Logging de acciones en integration.sh
- Validación de backend y API_KEY
- Scope enforcement en config.json
- Operaciones de riesgo requieren aprobación explícita

---

## 📋 Checklist de Implementación

- [x] Borrar `labs/deploy.sh`
- [x] Actualizar `labs/README.md` con nuevo flujo
- [x] Documentar esta decisión
- [x] Verificar `auto_deploy.sh` funciona
- [x] Verificar `sysmho_integration.sh` funciona
- [ ] Test E2E: Arrancar devil + crear target + lanzar scan
- [ ] Actualizar FLUJO_COMPLETO.md si existe

---

## 🚀 Siguiente Paso

**Test E2E Completo:**
```bash
# Terminal 1
cd labs/devil
bash auto_deploy.sh devil.tar
# Espera: "su dirección IP es --> X.X.X.X"

# Terminal 2
bash labs/sysmho_integration.sh auto devil <IP> 80
# Responde "s" a todas las confirmaciones
# Verifica que target + scan se crean en backend
```

---

## 📚 Referencias

- Auditoría completa: `.claude/audits/AUDIT_DEPLOY_SH.md`
- Nuevo README: `labs/README.md`
- Integration script: `labs/sysmho_integration.sh`

---

**Decisión tomada por:** Claude Code (Haiku 4.5) + Anderson (usuario)  
**Fecha:** 12 Abril 2026 16:10 UTC  
**Impacto:** BAJO (solo labs, no afecta core SysMho)  
**Reversibilidad:** MEDIA (deploy.sh puede recuperarse de git history)
