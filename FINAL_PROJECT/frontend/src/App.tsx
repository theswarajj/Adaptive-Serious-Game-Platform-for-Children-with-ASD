import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import KidHome from './pages/KidHome'
import GameLibrary from './pages/GameLibrary'
import GameLaunch from './pages/GameLaunch'
import ParentDashboard from './pages/ParentDashboard'
import TeacherDashboard from './pages/TeacherDashboard'
import NotFound from './pages/NotFound'

function ProtectedRoute({ children, allowedRoles }: { children: React.ReactNode, allowedRoles: string[] }) {
  const { isLoggedIn, role } = useAuthStore()
  if (!isLoggedIn || !role) return <Navigate to="/login" replace />
  if (!allowedRoles.includes(role)) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      {/* Kid Routes & Shared Game Launch */}
      <Route path="/kid" element={<ProtectedRoute allowedRoles={['kid']}><KidHome /></ProtectedRoute>} />
      <Route path="/kid/games" element={<ProtectedRoute allowedRoles={['kid', 'teacher', 'parent']}><GameLibrary /></ProtectedRoute>} />
      <Route path="/kid/games/:gameId" element={<ProtectedRoute allowedRoles={['kid', 'teacher', 'parent']}><GameLaunch /></ProtectedRoute>} />

      {/* Parent Routes */}
      <Route path="/parent" element={<ProtectedRoute allowedRoles={['parent']}><ParentDashboard /></ProtectedRoute>} />

      {/* Teacher Routes */}
      <Route path="/teacher" element={<ProtectedRoute allowedRoles={['teacher']}><TeacherDashboard /></ProtectedRoute>} />

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
