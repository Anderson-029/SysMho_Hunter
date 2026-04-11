import { AuthGuard } from './components/auth/AuthGuard'
import { Dashboard } from './components/Dashboard'

function App() {
  return (
    <AuthGuard>
      <Dashboard />
    </AuthGuard>
  )
}

export default App
