---
source: portswigger
category: idor
cwe: CWE-639
severity: high
url: https://portswigger.net/web-security/access-control/idor
---
# Insecure Direct Object References (IDOR)

## Descripción
Ocurre cuando una aplicación expone una referencia directa a un objeto
interno (ID de usuario, archivo, registro de BD) sin verificar que el
usuario autenticado tenga permiso real sobre ese objeto específico.

## Cómo detectar
Buscar parámetros que referencien IDs secuenciales o predecibles
(`?user_id=1042`, `/api/orders/8831`). Cambiar el valor del ID por otro
válido perteneciente a otro usuario y observar si la respuesta retorna
datos que no deberían ser accesibles.

## Payloads de prueba
Incrementar/decrementar IDs numéricos secuenciales.
Sustituir UUIDs por otros capturados en otras sesiones/usuarios.
Probar en parámetros de body, headers y query string, no solo en la URL.

## Impacto
Acceso no autorizado a datos de otros usuarios: información personal,
facturas, mensajes privados. En APIs REST puede escalar a modificación
o eliminación de recursos ajenos (IDOR de escritura).

## Mitigación
Verificar en cada endpoint que el objeto solicitado pertenezca al
usuario autenticado (autorización a nivel de objeto), no solo que el
usuario esté autenticado. Usar identificadores no predecibles (UUID v4)
como defensa en profundidad, nunca como única mitigación.
