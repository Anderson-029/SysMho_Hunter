#!/bin/bash

##############################################################################
# SysMho Hunter — Test E2E de Integration (sin interacción)
#
# Uso: bash scripts/test_integration_e2e.sh <lab> <ip> [port]
# Ejemplo: bash scripts/test_integration_e2e.sh devil 172.17.0.2 80
##############################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

log_ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
log_err()  { echo -e "${RED}[✗]${NC} $1"; }
log_info() { echo -e "${CYAN}[i]${NC} $1"; }

BACKEND_URL="http://localhost:8000"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
env_file="${BACKEND_DIR}/.env"

# Validar argumentos
if [ $# -lt 2 ]; then
    log_err "Uso: $0 <lab> <ip> [port]"
    log_info "Ejemplo: $0 devil 172.17.0.2 80"
    exit 1
fi

LAB_NAME=$1
TARGET_IP=$2
TARGET_PORT=${3:-80}

echo -e "\n${BOLD}${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║   SysMho Hunter — Test E2E Integration             ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════╝${NC}\n"

# 1. Obtener API_KEY
log_info "Obteniendo API_KEY..."
if [ ! -f "$env_file" ]; then
    log_err "No se encontró ${env_file}"
    exit 1
fi

API_KEY=$(grep "^API_KEY=" "$env_file" | cut -d'=' -f2 | tr -d '\n')
if [ -z "$API_KEY" ]; then
    log_err "API_KEY no configurada en .env"
    exit 1
fi
log_ok "API Key obtenida"

# 2. Verificar backend
log_info "Verificando backend en ${BACKEND_URL}..."
if ! curl -s "${BACKEND_URL}/health" > /dev/null 2>&1; then
    log_err "Backend no disponible"
    exit 1
fi
log_ok "Backend disponible"

# 3. Crear target
echo -e "\n${BOLD}${BLUE}[PASO 1] Crear Target${NC}"
TARGET_NAME="${LAB_NAME^} (Local Lab)"
TARGET_URL="http://${TARGET_IP}:${TARGET_PORT}"

log_info "Creando target: ${TARGET_NAME}"
log_info "URL: ${TARGET_URL}"

TARGETS_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/v1/targets/" \
    -H "X-API-Key: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"${TARGET_NAME}\",
      \"scopes\": [
        {\"scope_type\": \"domain\", \"value\": \"localhost\"},
        {\"scope_type\": \"domain\", \"value\": \"127.0.0.1\"},
        {\"scope_type\": \"ip\", \"value\": \"${TARGET_IP}\"}
      ]
    }" 2>/dev/null || echo "{}")

TARGET_ID=$(echo "$TARGETS_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id', ''))" 2>/dev/null || echo "")

if [ -z "$TARGET_ID" ]; then
    log_err "Fallo al crear target"
    echo "$TARGETS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TARGETS_RESPONSE"
    exit 1
fi
log_ok "Target creado: ${TARGET_ID}"

# 4. Lanzar scan
echo -e "\n${BOLD}${BLUE}[PASO 2] Lanzar Scan${NC}"
log_info "Lanzando scan reconnaissance..."

SCANS_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/v1/scans/" \
    -H "X-API-Key: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
      \"target_id\": \"${TARGET_ID}\",
      \"scan_type\": \"reconnaissance\"
    }" 2>/dev/null || echo "{}")

SCAN_ID=$(echo "$SCANS_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id', ''))" 2>/dev/null || echo "")

if [ -z "$SCAN_ID" ]; then
    log_err "Fallo al lanzar scan"
    echo "$SCANS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SCANS_RESPONSE"
    exit 1
fi
log_ok "Scan lanzado: ${SCAN_ID}"

# 5. Monitorear progreso
echo -e "\n${BOLD}${BLUE}[PASO 3] Monitoreo del Scan${NC}"
SPINNER=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
SPINNER_IDX=0
ATTEMPTS=0
MAX_ATTEMPTS=120  # 2 minutos máximo

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    SCAN_STATUS=$(curl -s -X GET "${BACKEND_URL}/api/v1/scans/${SCAN_ID}" \
        -H "X-API-Key: ${API_KEY}" 2>/dev/null || echo "{}")

    STATUS=$(echo "$SCAN_STATUS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    PHASE=$(echo "$SCAN_STATUS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('phase', 'N/A'))" 2>/dev/null || echo "N/A")
    PROGRESS=$(echo "$SCAN_STATUS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('progress', 0))" 2>/dev/null || echo "0")

    case "$STATUS" in
        "running")
            printf "\r${SPINNER[$SPINNER_IDX]} Escaneo en progreso... Fase: ${PHASE} | ${PROGRESS}%%   "
            SPINNER_IDX=$(( (SPINNER_IDX + 1) % 10 ))
            ;;
        "completed")
            printf "\r${GREEN}[✓]${NC} Escaneo completado                                     \n"
            log_ok "Estado final: COMPLETADO"
            break
            ;;
        "failed")
            printf "\r${RED}[✗]${NC} Escaneo falló\n"
            log_err "Estado final: FALLO"
            exit 1
            ;;
        *)
            printf "\r[?] Estado: ${STATUS}"
            ;;
    esac

    ATTEMPTS=$((ATTEMPTS + 1))
    sleep 2
done

if [ $ATTEMPTS -eq $MAX_ATTEMPTS ]; then
    log_err "Timeout: escaneo tardó demasiado"
    exit 1
fi

# 6. Obtener findings
echo -e "\n${BOLD}${BLUE}[PASO 4] Resultados${NC}"
FINDINGS=$(curl -s -X GET "${BACKEND_URL}/api/v1/findings/?scan_id=${SCAN_ID}" \
    -H "X-API-Key: ${API_KEY}" 2>/dev/null || echo "[]")

FINDINGS_COUNT=$(echo "$FINDINGS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d) if isinstance(d, list) else 0)" 2>/dev/null || echo "0")

if [ "$FINDINGS_COUNT" -eq 0 ]; then
    log_info "No se encontraron vulnerabilidades"
else
    log_ok "Total de vulnerabilidades encontradas: ${FINDINGS_COUNT}"
    echo -e "\n${BOLD}Hallazgos:${NC}"
    echo "$FINDINGS" | python3 -c "
import json, sys
findings = json.load(sys.stdin)
if isinstance(findings, list):
    for i, f in enumerate(findings, 1):
        severity = f.get('severity', 'info').upper()
        title = f.get('title', 'Unknown')
        cwe = f.get('cwe_id', 'N/A')
        print(f'{i}. [{severity}] {title}')
        if cwe != 'N/A':
            print(f'   CWE: {cwe}')
" 2>/dev/null || echo "$FINDINGS" | python3 -m json.tool
fi

# 7. Resumen final
echo -e "\n${BOLD}${BLUE}════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}✓ Test E2E Completado Exitosamente${NC}"
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}Información útil:${NC}"
echo -e "  Dashboard:    ${BOLD}http://localhost:5173${NC}"
echo -e "  Target ID:    ${BOLD}${TARGET_ID}${NC}"
echo -e "  Scan ID:      ${BOLD}${SCAN_ID}${NC}"
echo -e "  Status:       ${BOLD}${STATUS}${NC}"
echo -e "  Findings:     ${BOLD}${FINDINGS_COUNT}${NC}\n"
