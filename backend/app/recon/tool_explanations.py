"""
Explicaciones en lenguaje natural para cada herramienta de pentesting.
Combinación de lenguaje técnico y no técnico para que Anderson entienda
exactamente qué va a ejecutar SysMho Hunter y por qué.
"""

TOOL_EXPLANATIONS: dict[str, dict[str, str]] = {
    # ─── SUBDOMAIN ENUMERATION ────────────────────────────────────────────────
    "subfinder": {
        "human_explanation": (
            "Voy a buscar subdominios ocultos de tu target. "
            "Es como explorar el árbol genealógico del sitio web para "
            "descubrir servicios secundarios, APIs privadas y paneles de "
            "administración que no son visibles en la página principal."
        ),
        "why_needed": (
            "Los subdominios suelen tener menor protección que el dominio "
            "principal. Un api.target.com o admin.target.com puede ser la "
            "puerta de entrada para encontrar vulnerabilidades críticas."
        ),
        "risk_explanation": (
            "Riesgo MUY BAJO — Solo consulta registros DNS públicos. "
            "No envía payloads, no modifica nada, no genera tráfico "
            "hacia el servidor. Es completamente pasivo."
        ),
        "command_template": "subfinder -d {target} -silent -o /dev/stdout",
    },
    "amass": {
        "human_explanation": (
            "Voy a hacer un reconocimiento profundo de subdominios usando "
            "múltiples fuentes: certificados SSL, DNS, motores de búsqueda "
            "y bases de datos públicas. Es más exhaustivo que subfinder."
        ),
        "why_needed": (
            "Amass puede encontrar subdominios que subfinder no detecta "
            "porque consulta más fuentes. Un subdominio olvidado puede "
            "tener versiones antiguas de software con vulnerabilidades conocidas."
        ),
        "risk_explanation": (
            "Riesgo BAJO — Consulta fuentes externas (OSINT). "
            "No envía tráfico directo al servidor. "
            "Puede tomar más tiempo porque consulta muchas fuentes públicas."
        ),
        "command_template": "amass enum -passive -d {target} -timeout 10",
    },
    # ─── PORT SCANNING ────────────────────────────────────────────────────────
    "nmap": {
        "human_explanation": (
            "Voy a escanear qué puertas de entrada (puertos) están abiertas "
            "en el servidor y qué servicios están corriendo detrás de cada "
            "una. Es como ir puerta por puerta en un edificio para saber "
            "cuáles están abiertas y quién está adentro."
        ),
        "why_needed": (
            "Cada puerto abierto es una superficie de ataque potencial. "
            "Si hay un servicio SSH viejo, una base de datos expuesta, o "
            "un panel de admin en un puerto inusual, nmap lo va a detectar."
        ),
        "risk_explanation": (
            "Riesgo MEDIO — Envía paquetes de red al servidor para ver "
            "cuáles responden. No es intrusivo pero sí genera tráfico. "
            "Puede disparar alertas en sistemas de detección de intrusos (IDS). "
            "El servidor puede notar el escaneo en sus logs."
        ),
        "command_template": (
            "nmap -sV -sC --min-rate 2000 -p 80,443,8080,8443,22,21,25,"
            "3306,5432,6379,27017 {target}"
        ),
    },
    "masscan": {
        "human_explanation": (
            "Voy a escanear TODOS los 65,535 puertos del servidor a alta "
            "velocidad. Es como tocar cada puerta del edificio en segundos "
            "en lugar de minutos. Más rápido que nmap pero menos detallado."
        ),
        "why_needed": (
            "Los servicios en puertos no estándar (ej: 31337, 8888, 9200) "
            "suelen ser los más vulnerables porque los administradores no "
            "los monitorean tanto. Masscan los encuentra rápidamente."
        ),
        "risk_explanation": (
            "Riesgo MEDIO-ALTO — Genera mucho tráfico de red en poco tiempo. "
            "Es muy probable que el servidor registre este escaneo en sus logs "
            "y puede disparar alertas de seguridad. Se usa a velocidad moderada "
            "para reducir el impacto."
        ),
        "command_template": "masscan {target} -p 1-65535 --rate 1000",
    },
    # ─── WEB FINGERPRINTING ───────────────────────────────────────────────────
    "httpx": {
        "human_explanation": (
            "Voy a verificar qué URLs y subdominios están activos y "
            "recolectar información básica: código de respuesta HTTP, "
            "título de la página, tecnologías detectadas y estado del servidor."
        ),
        "why_needed": (
            "No todos los subdominios encontrados están activos. httpx "
            "filtra los muertos y me da metadata útil como qué tecnología "
            "usa el servidor (Nginx, Apache, IIS) que guiará el siguiente paso."
        ),
        "risk_explanation": (
            "Riesgo BAJO — Hace peticiones HTTP GET normales, como las que "
            "haría un navegador visitando la página. "
            "El servidor verá visitas normales en sus logs."
        ),
        "command_template": "httpx -u {target} -silent -status-code -title -tech-detect",
    },
    "wafw00f": {
        "human_explanation": (
            "Voy a detectar si el sitio tiene un Web Application Firewall "
            "(WAF) protegiendo el servidor. Un WAF es como el guardia de "
            "seguridad en la entrada que puede bloquear mis pruebas. "
            "Necesito saber si hay uno y de qué tipo es."
        ),
        "why_needed": (
            "Si hay un WAF (Cloudflare, AWS WAF, ModSecurity), tengo que "
            "adaptar mis técnicas para evitar ser bloqueado. Sin esta info "
            "podría activar reglas de bloqueo a mitad del análisis."
        ),
        "risk_explanation": (
            "Riesgo BAJO — Envía peticiones HTTP con patrones reconocibles "
            "para identificar el WAF. No intenta bypassearlo, solo detectarlo."
        ),
        "command_template": "wafw00f {target} -a",
    },
    "whatweb": {
        "human_explanation": (
            "Voy a identificar qué tecnologías usa el sitio web: "
            "CMS (WordPress, Drupal), lenguaje de programación (PHP, Python, "
            "Node.js), framework, versiones de librerías y plugins instalados. "
            "Es como leer la etiqueta de los ingredientes de un producto."
        ),
        "why_needed": (
            "Saber que usa WordPress 5.8 o jQuery 1.9 me permite buscar "
            "vulnerabilidades conocidas (CVEs) para esas versiones específicas "
            "en lugar de hacer pruebas genéricas."
        ),
        "risk_explanation": (
            "Riesgo BAJO — Analiza las respuestas HTTP y HTML del sitio. "
            "Solo hace peticiones GET normales. No envía payloads."
        ),
        "command_template": "whatweb {target} --color=never",
    },
    "nikto": {
        "human_explanation": (
            "Voy a hacer un escaneo de vulnerabilidades web conocidas: "
            "archivos sensibles expuestos (backup.zip, .env, config.php), "
            "cabeceras HTTP inseguras, configuraciones incorrectas y "
            "versiones de software con CVEs conocidos."
        ),
        "why_needed": (
            "Nikto busca más de 6,700 problemas conocidos. Un archivo .env "
            "expuesto puede revelar credenciales de la base de datos. "
            "Una cabecera X-Powered-By revela la versión exacta del servidor."
        ),
        "risk_explanation": (
            "Riesgo MEDIO — Hace muchas peticiones HTTP al servidor incluyendo "
            "rutas sospechosas como /admin, /backup.sql, /.git. "
            "El servidor puede notar el patrón de exploración en sus logs."
        ),
        "command_template": "nikto -h {target} -nointeractive -maxtime 120",
    },
    # ─── DIRECTORY/PATH FUZZING ───────────────────────────────────────────────
    "ffuf": {
        "human_explanation": (
            "Voy a buscar directorios y rutas ocultas en el servidor que "
            "no aparecen en la página principal: /admin, /api, /backup, "
            "/panel, /dashboard, etc. Es como probar si hay habitaciones "
            "secretas en el edificio que no están en el mapa."
        ),
        "why_needed": (
            "Los paneles de administración olvidados, APIs sin documentar "
            "y carpetas de backup son fuentes frecuentes de vulnerabilidades "
            "críticas en programas de bug bounty."
        ),
        "risk_explanation": (
            "Riesgo MEDIO — Genera muchas peticiones HTTP consecutivas al "
            "servidor. Puede disparar alertas de rate-limiting o ser "
            "bloqueado por WAF. Se usa a velocidad moderada para evitar esto."
        ),
        "command_template": (
            "ffuf -u {target}/FUZZ -w /usr/share/wordlists/dirb/common.txt "
            "-mc 200,301,302,403 -t 50 -timeout 10"
        ),
    },
    "gobuster": {
        "human_explanation": (
            "Voy a enumerar directorios, archivos y subdominios usando "
            "fuerza bruta de diccionario. Similar a ffuf pero con un "
            "enfoque diferente. Uso una lista de palabras comunes para "
            "encontrar rutas que no están enlazadas públicamente."
        ),
        "why_needed": (
            "Rutas como /api/v1/users, /admin/login, /phpmyadmin o "
            "/wp-admin son candidatos clásicos de bug bounty que ffuf "
            "puede haberse saltado con otra lista de palabras."
        ),
        "risk_explanation": (
            "Riesgo MEDIO — Similar a ffuf. Genera tráfico notable hacia "
            "el servidor. Los logs mostrarán muchos 404 seguidos."
        ),
        "command_template": (
            "gobuster dir -u {target} "
            "-w /usr/share/wordlists/dirb/common.txt -q"
        ),
    },
    "feroxbuster": {
        "human_explanation": (
            "Voy a hacer un fuzzing recursivo de directorios: cuando "
            "encuentro una carpeta, busco subcarpetas dentro de ella "
            "automáticamente. Es la versión más exhaustiva de la búsqueda "
            "de rutas ocultas."
        ),
        "why_needed": (
            "Si hay /api/v1, feroxbuster automáticamente buscará "
            "/api/v1/admin, /api/v1/users, /api/v1/config, etc. "
            "Esto encuentra APIs mal configuradas que los otros no ven."
        ),
        "risk_explanation": (
            "Riesgo MEDIO-ALTO — Es el más agresivo de los tres fuzzers. "
            "Genera el mayor volumen de tráfico porque explora recursivamente. "
            "Alta probabilidad de ser detectado por WAF o IDS."
        ),
        "command_template": (
            "feroxbuster -u {target} -q --no-recursion "
            "-w /usr/share/wordlists/dirb/common.txt"
        ),
    },
    # ─── VULNERABILITY SCANNING ───────────────────────────────────────────────
    "nuclei": {
        "human_explanation": (
            "Voy a ejecutar más de 9,000 plantillas de vulnerabilidades "
            "conocidas contra el target: CVEs específicos, misconfigs, "
            "exposed panels, credenciales por defecto, etc. "
            "Es como correr un antivirus pero para servidores web."
        ),
        "why_needed": (
            "Nuclei tiene plantillas para Log4Shell, Spring4Shell, "
            "Confluence RCE, paneles de Kibana expuestos, y cientos de "
            "CVEs de alta severidad. Un solo template puede encontrar "
            "una vulnerabilidad crítica de millones de dólares."
        ),
        "risk_explanation": (
            "Riesgo MEDIO — Envía payloads de detección (no explotación). "
            "Los templates 'safe' no causan daño pero sí generan tráfico. "
            "Ejecuto solo templates de severidad medium-critical."
        ),
        "command_template": (
            "nuclei -u {target} -severity medium,high,critical "
            "-silent -no-color"
        ),
    },
    "wapiti": {
        "human_explanation": (
            "Voy a hacer un análisis de vulnerabilidades web más profundo: "
            "inyección SQL básica, XSS, SSRF, inclusión de archivos y "
            "otros problemas en formularios y parámetros de la URL. "
            "Es un escáner activo que prueba las entradas del sitio."
        ),
        "why_needed": (
            "Wapiti interactúa con el sitio web real, prueba formularios "
            "y parámetros, lo que permite detectar vulnerabilidades que "
            "solo aparecen cuando alguien interactúa con la aplicación."
        ),
        "risk_explanation": (
            "Riesgo MEDIO — Envía payloads de prueba a formularios y URLs. "
            "No es destructivo pero sí activo. Puede generar registros de "
            "error en el servidor y ser detectado por WAF."
        ),
        "command_template": (
            "wapiti -u {target} --scope page -f txt -o /dev/stdout "
            "--max-scan-time 120"
        ),
    },
    # ─── EXPLOITATION TESTING ─────────────────────────────────────────────────
    "sqlmap": {
        "human_explanation": (
            "Voy a probar si los parámetros de la URL o formularios son "
            "vulnerables a inyección SQL. Enviaré payloads especiales para "
            "ver si la base de datos responde de forma inusual, lo que "
            "indicaría que se puede manipular."
        ),
        "why_needed": (
            "SQL injection sigue siendo una de las vulnerabilidades más "
            "reportadas en HackerOne. Si existe, podría dar acceso a "
            "toda la base de datos del target: usuarios, contraseñas, "
            "tokens, datos privados."
        ),
        "risk_explanation": (
            "Riesgo ALTO — Envía payloads SQL activos al servidor. "
            "Aunque uso nivel 1 (no destructivo), los logs del servidor "
            "registrarán claramente el intento. Alto riesgo de detección. "
            "SOLO ejecutar con autorización confirmada del scope."
        ),
        "command_template": (
            "sqlmap -u {target} --level=1 --risk=1 --batch "
            "--random-agent --timeout=10 --retries=1"
        ),
    },
    "dalfox": {
        "human_explanation": (
            "Voy a buscar vulnerabilidades de Cross-Site Scripting (XSS): "
            "puntos donde puedo inyectar código JavaScript en la página. "
            "XSS permite robar cookies de sesión, redirigir usuarios, "
            "o ejecutar código en el navegador de las víctimas."
        ),
        "why_needed": (
            "XSS es una de las vulnerabilidades más comunes en bug bounty. "
            "Dalfox es más preciso que herramientas genéricas y puede "
            "encontrar XSS en parámetros, headers y body de la respuesta."
        ),
        "risk_explanation": (
            "Riesgo ALTO — Inyecta payloads JavaScript especiales en la "
            "aplicación. Payloads de detección únicamente (no destructivos), "
            "pero el servidor registrará las peticiones claramente."
        ),
        "command_template": (
            "dalfox url {target} --silence --no-color --skip-bav --timeout 10"
        ),
    },
    # ─── CRAWLING & DISCOVERY ─────────────────────────────────────────────────
    "gau": {
        "human_explanation": (
            "Voy a obtener todas las URLs históricas que han sido indexadas "
            "para este dominio en servicios como Wayback Machine, Common Crawl "
            "y URLScan. Es como revisar fotos antiguas del sitio para encontrar "
            "páginas que ya no aparecen pero siguen activas."
        ),
        "why_needed": (
            "Las URLs antiguas pueden revelar APIs obsoletas, endpoints "
            "de administración viejos, archivos de backup o versiones "
            "anteriores con vulnerabilidades que no fueron parcheadas."
        ),
        "risk_explanation": (
            "Riesgo MUY BAJO — Solo consulta servicios externos como "
            "Wayback Machine. No envía ningún tráfico al servidor target. "
            "Completamente pasivo."
        ),
        "command_template": "gau {target} --threads 5 --timeout 10",
    },
    "hakrawler": {
        "human_explanation": (
            "Voy a rastrear el sitio web siguiendo enlaces internos para "
            "descubrir todas las páginas y endpoints. Como un robot de "
            "Google que indexa el sitio, pero buscando rutas interesantes "
            "para análisis de seguridad."
        ),
        "why_needed": (
            "Un crawler activo puede encontrar páginas que no están "
            "indexadas públicamente pero sí accesibles: /internal/report, "
            "/api/debug/status, /admin/users/list, etc."
        ),
        "risk_explanation": (
            "Riesgo BAJO — Hace peticiones HTTP GET normales siguiendo "
            "enlaces del sitio. Genera tráfico similar al de un usuario "
            "explorando la página."
        ),
        "command_template": (
            "echo {target} | hakrawler -depth 2 -plain -timeout 10"
        ),
    },
    "waybackurls": {
        "human_explanation": (
            "Voy a extraer URLs históricas del Wayback Machine de Internet Archive. "
            "Similar a gau pero específicamente del archivo histórico de internet. "
            "Permite ver qué páginas tuvo el sitio en el pasado."
        ),
        "why_needed": (
            "Endpoints como /api/v1/users/export que existieron hace 2 años "
            "pueden seguir activos aunque ya no estén enlazados. "
            "El historial de URLs es oro para el bug bounty."
        ),
        "risk_explanation": (
            "Riesgo MUY BAJO — Solo consulta archive.org. "
            "No hace ninguna petición al servidor target."
        ),
        "command_template": "waybackurls {target}",
    },
    "httprobe": {
        "human_explanation": (
            "Voy a verificar qué hosts de una lista están activos y "
            "respondiendo HTTP/HTTPS. Toma la lista de subdominios "
            "encontrados y filtra los que están vivos."
        ),
        "why_needed": (
            "De 100 subdominios encontrados, quizás 30 están activos. "
            "httprobe filtra los muertos para que el análisis posterior "
            "no pierda tiempo en hosts que no responden."
        ),
        "risk_explanation": (
            "Riesgo BAJO — Hace una petición HTTP GET simple a cada host. "
            "Solo para verificar si responde. No envía payloads."
        ),
        "command_template": "httprobe -prefer-https -timeout 10",
    },
    "eyewitness": {
        "human_explanation": (
            "Voy a tomar capturas de pantalla de cada sitio web encontrado. "
            "Esto me permite revisar visualmente qué hay en cada URL sin "
            "abrirlas manualmente una por una. Como un fotógrafo que documenta "
            "cada puerta del edificio."
        ),
        "why_needed": (
            "Una captura de pantalla puede revelar inmediatamente un panel de "
            "login de admin, una aplicación interna expuesta, o una página de "
            "error con información sensible, sin tener que visitar cada URL."
        ),
        "risk_explanation": (
            "Riesgo BAJO — Abre un navegador headless que visita cada URL. "
            "Genera tráfico HTTP normal. Puede ser lento si hay muchas URLs."
        ),
        "command_template": (
            "eyewitness --single {target} --no-prompt --timeout 10"
        ),
    },
    "wfuzz": {
        "human_explanation": (
            "Voy a hacer fuzzing de parámetros web: probar diferentes valores "
            "en los parámetros de la URL y formularios para detectar "
            "comportamientos inesperados. Es más flexible que ffuf para "
            "pruebas específicas de parámetros."
        ),
        "why_needed": (
            "Permite detectar IDOR (acceso a recursos de otros usuarios), "
            "path traversal, y parámetros ocultos que no aparecen en la UI "
            "pero el backend sí procesa."
        ),
        "risk_explanation": (
            "Riesgo MEDIO — Envía muchas peticiones con valores variados "
            "a parámetros del servidor. Puede generar errores en la app "
            "y ser detectado por WAF o IDS."
        ),
        "command_template": (
            "wfuzz -c -z file,/usr/share/wordlists/dirb/common.txt "
            "--hc 404 {target}/FUZZ"
        ),
    },
}

# Explicación genérica para tools no documentadas
DEFAULT_EXPLANATION: dict[str, str] = {
    "human_explanation": (
        "Voy a ejecutar esta herramienta de análisis de seguridad "
        "contra el target. Esta herramienta aún no tiene una explicación "
        "detallada configurada."
    ),
    "why_needed": (
        "Forma parte del pipeline de reconocimiento y análisis "
        "de SysMho Hunter."
    ),
    "risk_explanation": (
        "Riesgo desconocido — Revisar la documentación de la herramienta."
    ),
    "command_template": "{binary} {target}",
}


def get_tool_explanation(tool_name: str) -> dict[str, str]:
    """Retorna la explicación de una herramienta, o el default si no existe."""
    return TOOL_EXPLANATIONS.get(tool_name, DEFAULT_EXPLANATION)
