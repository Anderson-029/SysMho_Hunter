# Frontend — Reglas React + TypeScript

## Dependencias & Build
- **npm run dev** para desarrollo (Vite en 5173)
- **npm run build** para producción
- **npx tsc --noEmit** verificar TypeScript antes de commit
- Todas las deps en `package.json`, mantener versions compatibles

## Estructura de Carpetas
```
frontend/src/
├── components/      # Componentes React reutilizables
├── stores/         # Zustand stores (estado global)
├── api/           # Cliente axios con interceptores
├── types/         # Tipos TypeScript
├── pages/         # Páginas/vistas principales
└── styles/        # CSS/Tailwind
```

## TypeScript
- **Strict mode siempre:** `strictNullChecks: true`
- Tipear props de componentes: `interface ComponentProps { ... }`
- No usar `any` a menos que sea absolutamente necesario
- Tipos de retorno explícitos en funciones

## Componentes React
- Componentes funcionales con hooks (no class components)
- Props tipadas con interfaces
- UseEffect con array de dependencias correcto
- Cleanup functions en useEffect cuando sea necesario (timers, listeners)

## Estado Global (Zustand)
- Stores en `stores/` con nombres descriptivos (ej: `authStore.ts`)
- Usar `immer` para mutaciones complejas
- Persistencia con localStorage cuando apropiado
- Tipear estado: `interface StoreState { ... }`

## Seguridad Frontend
- **Nunca hardcodear** secrets, tokens o URLs de API
- Usar variables de entorno (`.env.local`)
- CORS headers correctos en cliente
- Validar entrada de usuario en formularios
- Sanitizar outputs cuando sea necesario

## Estilo & UI
- Tailwind CSS para estilos (no inline styles)
- Dark theme por defecto (cyber aesthetic)
- Animations con framer-motion para transiciones suaves
- Responder a cambios en auth store (logout, token refresh)

## Testing Frontend
- Tests unitarios con Vitest o Jest
- Tests E2E con Playwright/Cypress (E2E flow: login → dashboard → logout)
- Coverage mínimo: 70%

## API Client
- Usar axios con interceptores para:
  - Auto-inject JWT token en Authorization header
  - Manejo de 401 → refresh token → retry
  - Error handling centralizado
- No hardcodear URLs, usar `import.meta.env.VITE_API_URL`
