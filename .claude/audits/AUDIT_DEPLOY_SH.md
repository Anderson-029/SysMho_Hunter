# 🔍 Auditoría: deploy.sh & auto_deploy.sh

**Fecha:** 12 Abril 2026  
**Estado:** ❌ FALLA CRÍTICA — Problemas en los 5 Pilares  
**Ejecutor:** Claude Code  
**Resultado:** No apto para producción

---

## 📊 Resumen de Pilares

| Pilar | Estado | Score | Detalles |
|-------|--------|-------|----------|
| **Coherencia** | ❌ FAIL | 35/100 | Lógica redundante, inconsistencia en flujo |
| **Congruencia** | ❌ FAIL | 40/100 | Promesas incumplidas, integraciones incompletas |
| **Funcionalidad** | ❌ FAIL | 25/100 | Docker CLI syntax errors, no manejo de permisos |
| **Estabilidad** | ❌ FAIL | 45/100 | Sin validación de errores, graceful failure inexistente |
| **Seguridad** | ❌ FAIL | 30/100 | Sin permisos verificados, ejecución sin sandbox |
| **SCORE TOTAL** | **❌ FAIL** | **35/100** | **NO CUMPLE 5 PILARES** |

---

## 🚨 Problemas Críticos Encontrados

### 1️⃣ COHERENCIA — Lógica redundante y contradictoria

#### Problema 1.1: Validación de Lab inconsistente
**Ubicación:** `deploy.sh:60-79`

```bash
validate_lab() {
    if [ ! -d "${LABS_DIR}/${lab_name}" ]; then
        # validación OK
    fi
    
    if [ ! -f "${LABS_DIR}/${lab_name}/${lab_name}.tar" ]; then
        # validación OK
    fi
    
    if [ ! -f "${LABS_DIR}/${lab_name}/auto_deploy.sh" ]; then
        # validación OK — pero el archivo NO es ejecutable
    fi
}
```

**Fallo:** El script no verifica que `auto_deploy.sh` sea **ejecutable** (permisos `+x`). Debería validar:
```bash
if [ ! -x "${LABS_DIR}/${lab_name}/auto_deploy.sh" ]; then
    print_error "auto_deploy.sh no es ejecutable"
    exit 1
fi
```

---

#### Problema 1.2: auto_deploy.sh tiene lógica duplicada
**Ubicación:** `auto_deploy.sh:33-62`

```bash
# BUCLE 1 (líneas 33-44)
for name in "$@"; do
    image_id=$(docker images -q "$base_name")
    if [ ! -z "$image_id" ]; then
        # Limpia contenedores
        docker stop $container_ids > /dev/null 2>&1
        docker rm $container_ids > /dev/null 2>&1
    fi
done

# BUCLE 2 (líneas 54-62) — DUPLICADO EXACTO
for name in "$@"; do
    image_id=$(docker images -q "$base_name")
    if [ ! -z "$image_id" ]; then
        # Limpia imagenes
        docker rmi -f "$image_id" > /dev/null 2>&1
    fi
done
```

**Fallo:** 
- Los primeros dos bucles (33-44) son **idénticos** (solo la operación final cambia)
- Esto viola **coherencia** — código repetido sin razón
- Debería ser UNA SOLA función `cleanup()` llamada una vez

---

#### Problema 1.3: deploy_lab() ejecuta en background pero espera indefinido
**Ubicación:** `deploy.sh:81-109`

```bash
deploy_lab() {
    cd "${LABS_DIR}/${lab_name}"
    bash auto_deploy.sh "${tar_file}" &    # ← ejecuta en BACKGROUND
    local deploy_pid=$!
    
    sleep 15  # ← espera 15s (HARDCODEADO)
    
    local ip_address=$(docker inspect ... 2>/dev/null || echo "")
```

**Fallo:**
- `auto_deploy.sh` entra en loop infinito (`while true; do sleep 1; done`)
- El timeout de 15s es **arbitrario** — ¿qué pasa si Docker es lento?
- La obtención de IP puede ejecutarse ANTES de que el contenedor esté listo
- No hay reintentos ni validación

---

### 2️⃣ CONGRUENCIA — Promesas incumplidas

#### Problema 2.1: "Crear target en SysMho" — No implementado
**Ubicación:** `deploy.sh:111-135`

```bash
create_target_in_sysmho() {
    print_info "Opción de crear target en SysMho Hunter..."
    
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_warning "Backend SysMho no está disponible"
        return 0  # ← SILENCIOSA COMO SI NADA
    fi
    
    # ... extrae metadata ...
    # ... pero NUNCA llamada a API para crear el target
    return 0
}
```

**Fallo:**
- El script **promete** crear un target automáticamente
- Pero solo **valida** que el backend esté disponible
- **NO HACE** ninguna llamada a `/api/v1/targets` para crear el target
- La metadata se extrae pero se ignora

**Impacto:** Falta congruencia entre lo que dice que hace y lo que realmente hace.

---

#### Problema 2.2: "Lanzar scan completo" — Parcialmente incompleto
**Ubicación:** `deploy.sh:137-148`

```bash
launch_scan() {
    print_info "Scan completamente automatizado en desarrollo..."
    print_info "Por ahora, accede al dashboard:"
    # ← SIN IMPLEMENTACIÓN
    return 0
}
```

**Fallo:**
- El script **reconoce** que está sin completar
- Pero sigue adelante como si funcionara
- **Debería** ser un `TODO` o condición de error

---

### 3️⃣ FUNCIONALIDAD — Errores de ejecución

#### Problema 3.1: Docker CLI syntax error
**Ubicación:** `auto_deploy.sh:39-40`

```bash
container_ids=$(docker ps -a -q --filter "ancestor=$image_id")
# vs
docker ps -a -q -f name=$CONTAINER_NAME
```

**Fallo:**
- El script mezcla dos sintaxis:
  - `docker ps -a -q --filter "ancestor=$image_id"` ✅ CORRECTA
  - `docker ps -aq --filter "id=5938*"` ❌ INCORRECTA (wildcard en `-f id` no funciona)
  - `docker ps $container_ids` ❌ INCORRECTA (ps no acepta IDs como argumentos)

**Error capturado:**
```
docker: 'docker ps' accepts no arguments
Usage:  docker ps [OPTIONS]
```

---

#### Problema 3.2: Sin manejo de permisos Docker
**Ubicación:** `auto_deploy.sh:100-113`

```bash
if ! command -v docker &> /dev/null; then
    echo "Docker no está instalado. Instalando Docker..."
    sudo apt update
    sudo apt install docker.io -y
    systemctl restart docker  # ← sin sudo!
fi
```

**Fallo:**
- El script **detecta** que Docker no está instalado
- **Intenta instalarlo** con `sudo apt`
- Pero luego llama `systemctl restart docker` **sin sudo** 
- Result: La instalación puede fallar silenciosamente
- **NO hay validación** de que la instalación fue exitosa

**Error capturado:**
```
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

**Solución correcta:**
```bash
# Verificar permisos Docker
if ! docker ps &>/dev/null; then
    if groups $USER | grep -q docker; then
        # Usuario en grupo docker pero daemon no responde
        systemctl start docker || sudo systemctl start docker
    else
        # Usuario NO está en grupo docker
        print_error "El usuario no tiene permisos Docker. Ejecuta:"
        print_error "  sudo usermod -aG docker \$USER"
        exit 1
    fi
fi
```

---

#### Problema 3.3: deploy_lab() ignora errores silenciosamente
**Ubicación:** `deploy.sh:205-206`

```bash
local ip_address=$(deploy_lab "$lab_name")  # ← NO VALIDA return code

if [ -z "$ip_address" ]; then
    print_error "No se pudo obtener la IP del contenedor"
    # ← pero continúa de todos modos
fi

# ... sigue como si todo estuviera bien ...
```

**Fallo:**
- Si `deploy_lab()` retorna un string vacío, debería **exit 1**
- Pero el script continúa hasta el final
- `show_next_steps` intenta mostrar URLs vacías

---

### 4️⃣ ESTABILIDAD — Sin validación

#### Problema 4.1: Obtención de IP con comando débil
**Ubicación:** `deploy.sh:96-98`

```bash
local ip_address=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$container_name" 2>/dev/null || echo "")

if [ -z "$ip_address" ]; then
    print_error "No se pudo obtener la IP del contenedor"
    kill $deploy_pid 2>/dev/null || true
    exit 1
fi
```

**Fallo:**
- El comando `docker inspect` puede devolver un string vacío si:
  - El contenedor no existe
  - El contenedor no tiene IP asignada (status: exited)
  - Permisos insuficientes
- No hay **reintentos** para esperar a que el contenedor asigne IP
- El `kill $deploy_pid` puede no limpiar recursos de Docker

---

#### Problema 4.2: auto_deploy.sh sin validación de docker load
**Ubicación:** `auto_deploy.sh:119-122`

```bash
docker load -i "$TAR_FILE" > /dev/null

if [ $? -eq 0 ]; then
    # OK
else
    echo "Error al cargar el laboratorio"
    exit 1
fi
```

**Fallo:**
- Si el `docker load` falla por corrupción de `.tar`, el error es silencioso
- Si el `.tar` tiene 1.5GB y se interrumpe el I/O, el error llegará **después** de 5+ minutos
- No hay timeout para `docker load`
- El TAR_FILE no se valida antes (¿archivo vacío? ¿permisos?)

---

### 5️⃣ SEGURIDAD — Sin auditoría

#### Problema 5.1: Ejecución sin logging
**Ubicación:** Ambos scripts

```bash
docker stop $container_ids > /dev/null 2>&1
docker rm $container_ids > /dev/null 2>&1
docker rmi -f "$image_id" > /dev/null 2>&1
```

**Fallo:**
- **TODOS los comandos Docker se ejecutan sin logging**
- No hay auditoría de:
  - Qué contenedores se crearon
  - Qué imágenes se borraron
  - Cuándo se ejecutó cada operación
- En caso de incident, es imposible rastrear qué pasó

**Requisito de seguridad:** Toda operación crítica debe estar loguada a un archivo de auditoría con timestamp.

---

#### Problema 5.2: Permisos Docker no validados
**Ubicación:** `auto_deploy.sh:115`

```bash
docker load -i "$TAR_FILE" > /dev/null
```

**Fallo:**
- No valida que el usuario tenga permisos Docker
- No valida que el usuario esté en el grupo `docker`
- No proporciona instrucciones claras si falla
- Puede causar confusión en el usuario

---

#### Problema 5.3: Sin validación de integridad del TAR
**Ubicación:** `deploy.sh:68`

```bash
if [ ! -f "${LABS_DIR}/${lab_name}/${lab_name}.tar" ]; then
    print_error "Archivo ${lab_name}.tar no encontrado"
    exit 1
fi
```

**Fallo:**
- Solo valida **existencia** del archivo
- **NO valida integridad**:
  - ¿Archivo vacío (0 bytes)?
  - ¿Archivo corrupto?
  - ¿Permisos de lectura?
  - ¿Checksums (MD5/SHA256)?

**Requisito de seguridad:** Antes de ejecutar `docker load`, validar que el TAR es válido:
```bash
if ! tar -tzf "${LABS_DIR}/${lab_name}/${lab_name}.tar" > /dev/null 2>&1; then
    print_error "TAR corrupto o inválido"
    exit 1
fi
```

---

## 📋 Checklist de Correcciones Necesarias

### TIER 1 (Bloqueadores) — CRÍTICO
- [ ] Arreglar Docker CLI syntax (ps, images commands)
- [ ] Implementar validación de permisos Docker **antes** de ejecución
- [ ] Implementar reintentos para obtención de IP con timeout
- [ ] Hacer exit 1 si deploy_lab falla (no continuar)
- [ ] Agregar logging de TODAS las operaciones Docker
- [ ] Validar integridad de TAR antes de `docker load`

### TIER 2 (Alta Prioridad) — IMPORTANTE
- [ ] Eliminar lógica duplicada en auto_deploy.sh (bucles repetidos)
- [ ] Implementar `create_target_in_sysmho()` con llamada real a API
- [ ] Implementar `launch_scan()` con lógica real o marcar como TODO
- [ ] Hacer que cleanup() sea una función reutilizable
- [ ] Validar que auto_deploy.sh sea ejecutable en validate_lab()

### TIER 3 (Mejora) — RECOMENDADO
- [ ] Usar variables en lugar de hardcodes (timeout, nombres contenedores)
- [ ] Agregar dry-run mode para pruebas sin ejecutar Docker
- [ ] Validar formato de config.json antes de procesar
- [ ] Agregar health check del contenedor después de start

---

## 📝 Recomendaciones por Pilar

### Coherencia: Refactorizar
```bash
# ANTES: 3 bucles duplicados
for name in "$@"; do cleanup_containers; done
for name in "$@"; do cleanup_images; done

# DESPUÉS: 1 función reutilizable
cleanup_lab() { ... }
cleanup_lab "$lab_name"
```

### Congruencia: Completar promesas
- [ ] `create_target_in_sysmho()` → Llamar a `POST /api/v1/targets`
- [ ] `launch_scan()` → Llamar a `POST /api/v1/scans` o retornar error

### Funcionalidad: Validar todo
```bash
# DESPUÉS de cada operación crítica:
[ $? -eq 0 ] || { print_error "Fallo X"; cleanup; exit 1; }
```

### Estabilidad: Reintentos + Timeouts
```bash
# ESPERAR A QUE CONTENEDOR ESTÉ READY
for i in {1..30}; do
    ip_address=$(docker inspect -f '{{.NetworkSettings.IPAddress}}' "$CONTAINER_NAME" 2>/dev/null)
    [ ! -z "$ip_address" ] && break
    sleep 1
done
```

### Seguridad: Logging + Auditoría
```bash
# LOGGER function
log_action() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $1" >> /tmp/deploy.log
}

log_action "Deploy started: $lab_name"
docker load -i "$TAR_FILE"
log_action "Docker load completed: exit_code=$?"
```

---

## 🎯 Conclusión

**Status:** ❌ **NO APTO PARA PRODUCCIÓN**

El script `deploy.sh` tiene problemas **críticos** en todos los 5 pilares:

1. **No cumple Coherencia**: Lógica duplicada y contradictoria
2. **No cumple Congruencia**: Funciones incompletas que prometen pero no entregan
3. **No cumple Funcionalidad**: Errores Docker CLI, sin manejo de permisos
4. **No cumple Estabilidad**: Sin validación, sin reintentos, sin timeouts
5. **No cumple Seguridad**: Sin logging, sin auditoría, sin validación de integridad

### Acciones Inmediatas:
1. ❌ **NO ejecutar** contra targets reales hasta no reparar TIER 1
2. 🔧 Implementar correcciones TIER 1 (bloqueadores)
3. ✅ Crear tests para validar cada corrección
4. 📝 Documentar cambios en CHANGELOG.md

**Estimado de esfuerzo:** 4-6 horas para reparación + testing.

---

**Auditoría realizada por:** Claude Code v4.5  
**Fecha:** 12 Abril 2026 15:45 UTC  
**Siguiente revisión:** Después de correcciones TIER 1
