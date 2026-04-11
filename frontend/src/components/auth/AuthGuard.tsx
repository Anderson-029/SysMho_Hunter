/**
 * AuthGuard — Protege acceso a componentes autenticados
 * Renderiza LoginPage mientras se inicializa o si no hay token
 */

import { ReactNode, useEffect, useState } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { LoginPage } from './LoginPage'

interface AuthGuardProps {
  children: ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, initialize } = useAuthStore()
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    ;(async () => {
      try {
        await initialize()
      } finally {
        setIsInitializing(false)
      }
    })()
  }, [initialize])

  if (isInitializing) {
    return <LoginPage /> // Mostrar login mientras carga
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return <>{children}</>
}
