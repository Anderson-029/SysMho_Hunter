# CTF — Capture The Flag

## Metodología por Categoría

### Web
```
1. Ver código fuente (Ctrl+U)
2. Inspect headers (curl -I URL)
3. robots.txt, sitemap.xml, .htaccess
4. Fuzzear directorios (ffuf + SecLists)
5. Probar SQLi en todos los inputs
6. LFI: ?file=../../../../etc/passwd
7. SSTI: {{7*7}}, ${7*7}, <%= 7*7 %>
8. Decode: base64, hex, URL encode, JWT
```

### Forensics / Steganography
```bash
file archivo              # tipo real del archivo
strings archivo           # strings legibles
exiftool archivo          # metadata
binwalk -e archivo        # archivos embebidos
steghide extract -sf img  # esteganografía
stegsolve                 # análisis visual de imágenes
xxd archivo | head        # hex dump
```

### Crypto
- Identificar cipher primero: https://www.dcode.fr/cipher-identifier
- ROT13, Caesar, Vigenere → dcode.fr
- RSA débil → factordb.com, RsaCtfTool
- Hash → hashcat, john, crackstation.net
- Base64 variations: base32, base58, base85

### Reversing / Binary Exploitation
```bash
file binario
checksec --file=binario    # qué protecciones tiene
strings binario
ltrace ./binario           # llamadas a librerías
strace ./binario           # llamadas al sistema
gdb-peda binario           # debugging
ghidra / radare2           # decompilación
```

**pwntools template:**
```python
from pwn import *

elf = ELF('./binario')
p = process('./binario')   # local
# p = remote('host', port)  # remoto

# Buffer overflow básico
payload = b'A' * offset + p64(ret_addr)
p.sendlineafter(b'> ', payload)
p.interactive()
```

### OSINT CTF
- Buscar username en todas las redes: sherlock, maigret
- Reverse image search: Google, TinEye, Yandex
- Metadata de imágenes: exiftool
- Geolocalización: GeoGuessr skills, sombras/edificios
- Wayback Machine: web.archive.org

### Misc / Stego
```bash
# Audio
audacity               # espectrograma visual
sonic-visualiser       # análisis avanzado
# Morse, DTMF, espectrograma escondido

# QR / Barcode dañado
zbarimg imagen.png
# Reparar QR manualmente
```

## Herramientas Esenciales CTF
```
pwntools        # binary exploitation
pwndbg/peda     # gdb mejorado
ghidra          # reversing (NSA)
radare2/r2      # reversing CLI
angr            # symbolic execution
z3              # theorem prover (crypto/reversing)
CyberChef       # transformaciones (online)
RsaCtfTool      # ataques RSA
hashcat + john  # cracking
```

## Workflow al Recibir un Challenge
1. Leer descripción completa — suele haber hints
2. `file` + `strings` + `exiftool` en cualquier archivo recibido
3. Identificar categoría y aplicar checklist correspondiente
4. Buscar el "rabbit hole" — a veces la solución es más simple
5. Si estás atascado 30min → buscar hint o writeup parcial de challenges similares
6. Documentar solución en writeup para reutilizar

## Plataformas Recomendadas
- HackTheBox (máquinas reales)
- TryHackMe (guiado, ideal para aprender)
- CTFtime.org (calendario de CTFs activos)
- PicoCTF (beginner-friendly, buen material)
- pwn.college (binary exploitation específico)
