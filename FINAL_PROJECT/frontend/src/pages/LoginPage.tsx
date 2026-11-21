import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore, type UserRole } from '../store/authStore'
import { apiLogin } from '../api/client'

const ROLES = [
  {
    role: 'kid' as UserRole,
    backendRole: 'student',
    emoji: '👦',
    label: "I'm a Student",
    desc: 'Play fun games, unlock new levels & earn stars!',
    bg: 'bg-ocean',
    shadow: 'shadow-blue-300',
    route: '/kid',
    defaultUsername: 'alex',
    defaultSecret: '1234',
    hint: 'Student PIN: 1234'
  },
  {
    role: 'parent' as UserRole,
    backendRole: 'parent',
    emoji: '👨‍👩‍👧',
    label: "I'm a Parent",
    desc: 'Monitor home progress, submit observations & chat with teachers',
    bg: 'bg-sunny',
    shadow: 'shadow-yellow-300',
    route: '/parent',
    defaultUsername: 'parent',
    defaultSecret: 'parent123',
    hint: 'Demo: parent / parent123'
  },
  {
    role: 'teacher' as UserRole,
    backendRole: 'teacher',
    emoji: '👩‍🏫',
    label: "I'm a Teacher",
    desc: 'Manage classrooms, review AI recommendations & assess skills',
    bg: 'bg-forest',
    shadow: 'shadow-green-300',
    route: '/teacher',
    defaultUsername: 'teacher',
    defaultSecret: 'teacher123',
    hint: 'Demo: teacher / teacher123'
  },
]

export default function LoginPage() {
  const [step, setStep] = useState<'pick' | 'credentials'>('pick')
  const [selectedRole, setSelectedRole] = useState<(typeof ROLES)[0] | null>(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const setAuthSession = useAuthStore(s => s.setAuthSession)
  const navigate = useNavigate()

  const handleRolePick = (roleObj: (typeof ROLES)[0]) => {
    setSelectedRole(roleObj)
    setUsername(roleObj.defaultUsername)
    setPassword(roleObj.defaultSecret)
    setError(null)
    setStep('credentials')
  }

  const handlePerformLogin = async (userToSubmit?: string, passToSubmit?: string) => {
    if (!selectedRole) return
    const uname = (userToSubmit || username).trim()
    const pass = passToSubmit || password
    if (!uname) {
      setError('Please enter your username')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const res = await apiLogin({
        username: uname,
        password: pass,
        pin: pass,
        role: selectedRole.backendRole,
      })

      if (res && res.success) {
        setAuthSession(res.user, res.token)
        navigate(selectedRole.route)
      } else {
        setError('Login failed. Please check your username and credentials.')
      }
    } catch (err: any) {
      setError(err?.message?.replace('API 401: ', '') || 'Invalid login credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-playground flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-10 left-10 text-5xl animate-float opacity-25">🌟</div>
      <div className="absolute bottom-10 right-10 text-4xl animate-float opacity-20" style={{ animationDelay: '1s' }}>🎈</div>
      <div className="absolute top-1/3 right-20 text-3xl animate-float opacity-15" style={{ animationDelay: '2s' }}>🦋</div>

      <div className="w-full max-w-xl relative z-10">
        <Link to="/" className="inline-flex items-center gap-2 text-[var(--color-text-light)] hover:text-[var(--color-text)] transition-colors mb-6 no-underline font-bold text-sm">
          <span>←</span> Back to Home
        </Link>

        {step === 'pick' ? (
          <div className="animate-fadeInUp">
            <div className="text-center mb-8">
              <div className="text-5xl mb-4 animate-bounceIn">👋</div>
              <h1 className="text-3xl md:text-4xl font-extrabold font-[var(--font-fun)] mb-3">
                Select Your Portal
              </h1>
              <p className="text-[var(--color-text-light)] text-lg">
                Choose your role to access personalized activities & monitoring
              </p>
            </div>

            <div className="grid gap-4">
              {ROLES.map((r, i) => (
                <button
                  key={r.role}
                  onClick={() => handleRolePick(r)}
                  className="clay-card p-6 flex items-center gap-5 text-left animate-fadeInUp cursor-pointer group bg-white/95 rounded-3xl border-2 border-slate-100 hover:border-indigo-300 shadow-md hover:shadow-xl transition-all active:scale-[0.98]"
                  style={{ animationDelay: `${i * 0.1}s` }}
                >
                  <div className={`w-20 h-20 ${r.bg} rounded-3xl flex items-center justify-center text-4xl shadow-lg ${r.shadow} group-hover:scale-110 transition-transform shrink-0`}>
                    {r.emoji}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-[var(--font-fun)] font-bold text-xl mb-1">{r.label}</h3>
                    <p className="text-[var(--color-text-light)] text-sm">{r.desc}</p>
                    <span className="text-xs font-semibold text-emerald-600 mt-1 inline-block">
                      🔑 {r.hint}
                    </span>
                  </div>
                  <div className="text-3xl opacity-50 group-hover:opacity-100 transition-opacity">→</div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="animate-fadeInUp">
            <button
              onClick={() => { setStep('pick'); setError(null) }}
              className="text-[var(--color-text-light)] hover:text-[var(--color-text)] transition-colors mb-6 font-bold text-sm flex items-center gap-1 cursor-pointer"
            >
              ← Choose a different role
            </button>

            <div className="fun-card-flat p-8 md:p-10">
              <div className={`w-20 h-20 ${selectedRole!.bg} rounded-3xl flex items-center justify-center text-4xl mx-auto mb-5 shadow-xl ${selectedRole!.shadow} animate-bounceIn`}>
                {selectedRole!.emoji}
              </div>

              <h2 className="text-2xl font-extrabold font-[var(--font-fun)] text-center mb-1">
                {selectedRole!.label} Login
              </h2>
              <p className="text-[var(--color-text-light)] text-center text-sm mb-6">
                {selectedRole!.role === 'kid' ? 'Sign in to access your assigned game quests!' : 'Sign in to access student records and behavioral profiles.'}
              </p>

              {error && (
                <div className="mb-5 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm font-semibold text-center">
                  ⚠️ {error}
                </div>
              )}

              {selectedRole!.role === 'kid' ? (
                /* Child Quick Student Selector */
                <div className="space-y-4 mb-6">
                  <div className="text-xs font-bold text-slate-500 uppercase tracking-wider text-center">
                    Select Your Name:
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setUsername('alex')
                        setPassword('1234')
                        handlePerformLogin('alex', '1234')
                      }}
                      className="btn-3d btn-3d-slate p-4 rounded-2xl bg-sky-50/80 border-2 border-sky-200 hover:bg-sky-100 transition-all text-center cursor-pointer shadow-xs"
                    >
                      <div className="text-3xl mb-1">👦</div>
                      <div className="font-black text-slate-800 text-sm">Alex Miller</div>
                      <div className="text-xs text-sky-600 font-bold font-mono">STU-1001</div>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setUsername('maya')
                        setPassword('1234')
                        handlePerformLogin('maya', '1234')
                      }}
                      className="btn-3d btn-3d-slate p-4 rounded-2xl bg-purple-50/80 border-2 border-purple-200 hover:bg-purple-100 transition-all text-center cursor-pointer shadow-xs"
                    >
                      <div className="text-3xl mb-1">👧</div>
                      <div className="font-black text-slate-800 text-sm">Maya Lin</div>
                      <div className="text-xs text-purple-600 font-bold font-mono">STU-1002</div>
                    </button>
                  </div>
                  <div className="text-center text-xs text-slate-400 font-medium">Or enter manual username below:</div>
                </div>
              ) : null}

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-[var(--color-text-light)] mb-1 uppercase tracking-wider">
                    Username
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    placeholder="Enter username"
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-indigo-500 focus:outline-none font-semibold text-slate-800 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[var(--color-text-light)] mb-1 uppercase tracking-wider">
                    {selectedRole!.role === 'kid' ? 'Secret PIN' : 'Password'}
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handlePerformLogin()}
                    placeholder={selectedRole!.role === 'kid' ? 'Enter 4-digit PIN' : 'Enter password'}
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-indigo-500 focus:outline-none font-semibold text-slate-800 transition-colors"
                  />
                </div>

                <button
                  onClick={() => handlePerformLogin()}
                  disabled={loading}
                  className="btn-3d btn-3d-blue w-full py-3.5 px-6 rounded-2xl font-black text-white shadow-md transition-all cursor-pointer flex items-center justify-center gap-2 mt-2 disabled:opacity-50 text-sm"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Verifying...</span>
                    </>
                  ) : (
                    <span>Sign In to {selectedRole!.label.replace("I'm a ", "")} Portal →</span>
                  )}
                </button>

                {/* 1-Click Demo Fill */}
                <button
                  type="button"
                  onClick={() => {
                    setUsername(selectedRole!.defaultUsername)
                    setPassword(selectedRole!.defaultSecret)
                    handlePerformLogin(selectedRole!.defaultUsername, selectedRole!.defaultSecret)
                  }}
                  className="btn-3d btn-3d-slate w-full py-2.5 px-4 rounded-xl text-xs font-black text-slate-700 bg-white hover:bg-slate-50 transition-colors cursor-pointer text-center shadow-xs"
                >
                  ⚡ One-Click Instant Demo Login ({selectedRole!.defaultUsername})
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
