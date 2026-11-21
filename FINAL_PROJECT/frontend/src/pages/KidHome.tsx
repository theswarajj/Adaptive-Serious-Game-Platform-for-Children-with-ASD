import { Link, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '../store/authStore'
import { getGameById, GAME_CATALOGUE } from '../data/games'
import { apiGetStudentAssignments, apiGetStudentProfile } from '../api/client'
import { SkeletonCard, SkeletonCurriculum } from '../components/SkeletonLoader'

// Web Audio sound synthesizer for Duolingo-style rewards and mascot chirps
function playChime(type: 'mascot' | 'star' | 'pop') {
  try {
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()

    if (type === 'mascot') {
      // Pleasant playful chirp
      const notes = [587.33, 880, 1174.66]
      notes.forEach((f, i) => {
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.type = 'sine'
        osc.frequency.setValueAtTime(f, ctx.currentTime + i * 0.08)
        gain.gain.setValueAtTime(0.001, ctx.currentTime + i * 0.08)
        gain.gain.exponentialRampToValueAtTime(0.18, ctx.currentTime + i * 0.08 + 0.02)
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.08 + 0.14)
        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.start(ctx.currentTime + i * 0.08)
        osc.stop(ctx.currentTime + i * 0.08 + 0.15)
      })
    } else if (type === 'star') {
      // Sparkle chime
      const notes = [523.25, 659.25, 783.99, 1046.5]
      notes.forEach((f, i) => {
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.type = 'triangle'
        osc.frequency.setValueAtTime(f, ctx.currentTime + i * 0.09)
        gain.gain.setValueAtTime(0.001, ctx.currentTime + i * 0.09)
        gain.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + i * 0.09 + 0.02)
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.09 + 0.18)
        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.start(ctx.currentTime + i * 0.09)
        osc.stop(ctx.currentTime + i * 0.09 + 0.2)
      })
    }
  } catch {
    // Restricted by gesture policy
  }
}

// Collectible sticker album badges
const STICKER_COLLECTION = [
  { id: 'bubble', title: 'Bubble Popping Ace', emoji: '🎈', desc: 'Popped 15+ bubbles with pinch precision!', unlocked: true, color: 'from-amber-400 to-orange-500' },
  { id: 'star', title: 'Star Gazer Navigator', emoji: '⭐', desc: 'Maintained steady head alignment with the star!', unlocked: true, color: 'from-sky-400 to-blue-500' },
  { id: 'pattern', title: 'Pattern Trail Tracer', emoji: '✏️', desc: 'Traced intricate geometric ribbons smoothly!', unlocked: true, color: 'from-emerald-400 to-teal-500' },
  { id: 'emotion', title: 'Emotion Detective', emoji: '🎭', desc: 'Recognized and mirrored expressive facial clues!', unlocked: true, color: 'from-purple-400 to-indigo-500' },
  { id: 'story', title: 'Nutmeg Storyteller', emoji: '🐿️', desc: 'Described colorful scenes and expanded sentences!', unlocked: true, color: 'from-rose-400 to-pink-500' },
  { id: 'turn', title: 'Turn-Taking Champion', emoji: '🚦', desc: 'Practiced patient reciprocal waiting on green and red!', unlocked: false, color: 'from-slate-400 to-slate-600' },
]

const MASCOT_MESSAGES = [
  "You're doing fantastic today, Alex! Let's conquer the next quest! 🌟",
  "Take your time and breathe! Every little step makes your skills grow! 💖",
  "Ms. Wilson is super proud of your practice this week! 👩‍🏫",
  "Pop! Whiz! Ready to earn some shiny gold stars? 🎈",
  "You have a 3-Day streak going! Keep up the brilliant focus! 🔥",
]

export default function KidHome() {
  const { name, logout, childId } = useAuthStore()
  const navigate = useNavigate()

  const [studentProfile, setStudentProfile] = useState<any>(null)
  const [assignments, setAssignments] = useState<any[]>([])
  const [softTheme, setSoftTheme] = useState(false)
  const [largeText, setLargeText] = useState(false)
  const [loading, setLoading] = useState(true)

  // Duolingo UI Features
  const [viewMode, setViewMode] = useState<'winding' | 'grid'>('winding')
  const [showStickers, setShowStickers] = useState(false)
  const [mascotMsgIdx, setMascotMsgIdx] = useState(0)
  const [mascotWiggle, setMascotWiggle] = useState(false)

  useEffect(() => {
    const studentTarget = childId || 'STU-1001'
    setLoading(true)
    Promise.allSettled([
      apiGetStudentAssignments(studentTarget),
      apiGetStudentProfile(studentTarget),
    ]).then(([asgRes, profRes]) => {
      if (asgRes.status === 'fulfilled' && Array.isArray(asgRes.value)) {
        setAssignments(asgRes.value)
      }
      if (profRes.status === 'fulfilled') {
        setStudentProfile(profRes.value)
      }
      setLoading(false)
    })
  }, [childId])

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const handleMascotClick = () => {
    playChime('mascot')
    setMascotWiggle(true)
    setTimeout(() => setMascotWiggle(false), 600)
    setMascotMsgIdx((prev) => (prev + 1) % MASCOT_MESSAGES.length)
  }

  // Active teacher assignment is first unlocked incomplete assignment, or first pending
  const activeAssignment =
    assignments.find(
      (a) => a.status !== 'completed' && (a.is_unlocked === 1 || a.is_unlocked === true)
    ) ||
    assignments.find((a) => a.status !== 'completed') ||
    assignments[0]

  const activeGame = activeAssignment ? getGameById(activeAssignment.game_id) : undefined
  const completedCount = assignments.filter((a) => a.status === 'completed').length
  const progressPercent = assignments.length > 0 ? Math.round((completedCount / assignments.length) * 100) : 0

  return (
    <div
      className={`min-h-screen relative overflow-hidden transition-colors duration-300 ${
        softTheme
          ? 'calm-theme bg-[#F7F9F6] text-slate-800'
          : 'bg-gradient-to-b from-[#EBF4FF] via-[#F5F8FF] to-[#FFF9E6] text-slate-800'
      } ${largeText ? 'text-lg' : 'text-base'}`}
    >
      {/* Gentle Floating Magical Background Elements */}
      {!softTheme && (
        <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
          <div className="absolute top-20 right-12 text-5xl animate-float opacity-25">⭐</div>
          <div className="absolute bottom-28 left-8 text-4xl animate-float opacity-20" style={{ animationDelay: '1.2s' }}>🎈</div>
          <div className="absolute top-1/3 left-1/4 text-3xl animate-float opacity-15" style={{ animationDelay: '2.4s' }}>🌟</div>
          <div className="absolute bottom-1/3 right-1/4 text-4xl animate-float opacity-20" style={{ animationDelay: '0.8s' }}>🚀</div>
          <div className="absolute -top-32 -left-32 w-96 h-96 bg-blue-300/20 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute top-1/2 -right-32 w-96 h-96 bg-amber-300/20 rounded-full blur-3xl pointer-events-none" />
        </div>
      )}

      {/* ── Duolingo-style Top HUD & Tactile Navbar ─────────────────────── */}
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/90 border-b-2 border-slate-200/80 shadow-xs">
        <div className="max-w-5xl mx-auto px-6 h-18 flex items-center justify-between">
          <Link to="/kid" className="flex items-center gap-3 no-underline group">
            <div className="w-11 h-11 bg-gradient-to-tr from-amber-400 via-pink-400 to-indigo-500 rounded-2xl flex items-center justify-center text-2xl shadow-md group-hover:scale-105 transition-transform animate-wiggle">
              ✨
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-[var(--font-fun)] font-black text-2xl tracking-tight text-slate-800">
                  SkillSpark
                </span>
                <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 hidden sm:inline">
                  Guided Path
                </span>
              </div>
              <span className="text-[11px] font-semibold text-slate-400 hidden sm:block">
                Interactive Learning Kingdom
              </span>
            </div>
          </Link>

          {/* Gamified Duolingo Top HUD Counters */}
          <div className="flex items-center gap-3">
            {/* Streak Counter */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-amber-50 border-2 border-amber-200 shadow-xs" title="3 Days Streak!">
              <span className="text-lg animate-bounce">🔥</span>
              <span className="font-[var(--font-fun)] font-black text-sm text-amber-700">3 Days</span>
            </div>

            {/* Stars Counter */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-sky-50 border-2 border-sky-200 shadow-xs" title="Stars Earned">
              <span className="text-lg">⭐</span>
              <span className="font-[var(--font-fun)] font-black text-sm text-sky-700">{studentProfile?.stars_earned ?? 15}</span>
            </div>

            {/* Gems / Energy */}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-indigo-50 border-2 border-indigo-200 shadow-xs" title="Energy Gems">
              <span className="text-base">💎</span>
              <span className="font-[var(--font-fun)] font-black text-sm text-indigo-700">120</span>
            </div>

            {/* Sensory Calm Mode Toggle */}
            <button
              onClick={() => setSoftTheme(!softTheme)}
              title={softTheme ? "Calm Mode Active" : "Enable Sensory Calm Mode"}
              className={`btn-3d text-xs px-3 py-1.5 font-bold cursor-pointer flex items-center gap-1 ${
                softTheme ? 'btn-3d-teal text-white' : 'btn-3d-slate text-slate-700'
              }`}
            >
              <span>{softTheme ? '🌙 Calm Mode: ON' : '☀️ Sensory Mode'}</span>
            </button>

            {/* Big Font Toggle */}
            <button
              onClick={() => setLargeText(!largeText)}
              title="Large Friendly Text"
              className={`btn-3d text-xs px-2.5 py-1.5 font-bold cursor-pointer ${
                largeText ? 'btn-3d-amber text-amber-950' : 'btn-3d-slate text-slate-700'
              }`}
            >
              🔤
            </button>

            {/* Sign Out */}
            <button
              onClick={handleLogout}
              className="text-xs font-black text-slate-500 bg-slate-100 hover:bg-slate-200 px-3 py-2 rounded-2xl transition-all cursor-pointer border border-slate-200 hover:text-slate-800"
            >
              👋 Bye!
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8 relative z-10 space-y-8">
        {/* ── Student Hero Card with Claymorphism & 3D Badges ────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="clay-card p-7 md:p-8 relative overflow-hidden"
          style={{
            background: softTheme
              ? 'linear-gradient(135deg, #F4F7F4 0%, #EBF0EA 100%)'
              : 'linear-gradient(135deg, #E0F2FE 0%, #EDE9FE 50%, #FEF3C7 100%)',
          }}
        >
          <div className="flex flex-col md:flex-row items-center gap-6 relative z-10">
            {/* Animated Avatar Circle with 3D Border */}
            <div className="relative">
              <div className="w-24 h-24 md:w-28 md:h-28 bg-white rounded-3xl flex items-center justify-center text-5xl md:text-6xl shadow-xl border-4 border-amber-300 animate-bounceIn shrink-0">
                {studentProfile?.avatar === 'girl-1' ? '👧' : '👦'}
              </div>
              <div className="absolute -bottom-2 -right-2 bg-emerald-500 text-white rounded-full p-1 text-sm shadow-md border-2 border-white">
                ✨
              </div>
            </div>

            {/* Student Info & Learning Focus */}
            <div className="text-center md:text-left space-y-2 flex-1">
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-2.5">
                <h1 className="text-3xl md:text-4xl font-black font-[var(--font-fun)] text-slate-800 tracking-tight">
                  Hi, {studentProfile?.full_name || name || 'Alex'}!
                </h1>
                <span className="px-3.5 py-1 rounded-full text-xs font-black bg-indigo-600 text-white shadow-sm font-mono tracking-wider border border-indigo-400">
                  ID: {studentProfile?.student_id || childId || 'STU-1001'}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-black bg-amber-400 text-amber-950 shadow-xs border border-amber-500">
                  Level 3 Adventurer 🌟
                </span>
              </div>
              <p className="text-slate-600 text-sm font-medium">
                Room: <span className="font-bold text-slate-800">{studentProfile?.class_name || 'Sunflower Room'}</span> • Lead Educator:{' '}
                <span className="font-bold text-emerald-700">{studentProfile?.teacher_name || 'Ms. Sarah Wilson'}</span>
              </p>

              {/* Today's Learning Objective Focus Card */}
              <div className="mt-3 p-4 bg-white/85 backdrop-blur-md rounded-2xl border-2 border-amber-200/90 text-xs text-slate-700 shadow-xs flex items-start gap-3">
                <span className="text-2xl shrink-0 animate-bounce">🎯</span>
                <div>
                  <span className="font-black text-amber-900 uppercase tracking-wider text-[11px] block">
                    Your Tailored Skill Focus for Today:
                  </span>
                  <p className="font-semibold text-slate-800 mt-0.5 leading-relaxed">
                    {studentProfile?.learning_objectives ||
                      'Develop joint attention, practice reciprocal waiting, and build expressive speech communication.'}
                  </p>
                </div>
              </div>
            </div>

            {/* Trophy Cabinet & Sticker Album Action Button */}
            <div className="flex flex-col items-center gap-3 shrink-0">
              <button
                onClick={() => {
                  playChime('star')
                  setShowStickers(true)
                }}
                className="btn-3d btn-3d-amber px-5 py-3 rounded-2xl font-black text-sm text-amber-950 flex items-center gap-2 shadow-md cursor-pointer"
              >
                <span>🏆</span>
                <span>Sticker Album</span>
                <span className="px-2 py-0.5 rounded-full bg-white text-amber-900 text-xs font-black">5/6</span>
              </button>
              <div className="text-center text-xs font-bold text-slate-500">
                <span>{completedCount} of {assignments.length} Quests Mastered</span>
              </div>
            </div>
          </div>

          {/* Interactive Quest Progress Bar with Glossy Highlight */}
          <div className="mt-6 pt-5 border-t border-slate-200/60">
            <div className="flex items-center justify-between text-xs font-black text-slate-700 mb-2">
              <span className="flex items-center gap-1.5">
                <span>🚀 Quest Path Progress</span>
                <span className="text-indigo-600">({progressPercent}%)</span>
              </span>
              <span>{completedCount} of {assignments.length} Adventures Mastered</span>
            </div>
            <div className="w-full h-4 bg-white/90 rounded-full p-0.5 border border-slate-200 overflow-hidden shadow-inner">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-500 transition-all duration-700 relative"
                style={{ width: `${Math.max(6, progressPercent)}%` }}
              >
                <div className="absolute inset-0 bg-white/25 rounded-full animate-pulse" />
              </div>
            </div>
          </div>
        </motion.div>

        {/* ── Active Mission Banner ────────────────────────────────────────── */}
        {loading ? (
          <SkeletonCard count={1} />
        ) : activeAssignment && activeGame ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="p-7 md:p-8 bg-gradient-to-r from-emerald-500 via-teal-600 to-cyan-600 text-white rounded-3xl shadow-xl relative overflow-hidden border-3 border-emerald-300/40"
          >
            <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-5">
                <div className="w-20 h-20 rounded-3xl bg-white text-5xl flex items-center justify-center shadow-xl border-4 border-amber-300 animate-bounce shrink-0">
                  {activeGame.icon}
                </div>
                <div>
                  <div className="inline-flex items-center gap-2 bg-black/20 px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider mb-2">
                    <span className="text-amber-300">⭐</span>
                    <span>Next Up • Step #{activeAssignment.sequence_order || 1}</span>
                  </div>
                  <h2 className="text-2xl md:text-3xl font-black font-[var(--font-fun)] tracking-tight">
                    {activeGame.name}
                  </h2>
                  <p className="text-emerald-100 text-xs sm:text-sm mt-1 max-w-xl leading-relaxed font-medium">
                    {activeGame.description}
                  </p>
                </div>
              </div>

              <Link
                to={`/kid/games/${activeGame.id}`}
                className="btn-3d btn-3d-amber text-lg px-8 py-4 text-amber-950 no-underline shrink-0 flex items-center gap-3 shadow-lg"
              >
                <span>▶ Start Adventure!</span>
                <span className="text-2xl animate-float">🚀</span>
              </Link>
            </div>
          </motion.div>
        ) : null}

        {/* ── Duolingo-style Winding Stepping Stone Learning Path ────────── */}
        <div className="clay-card p-6 md:p-10 relative">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8 pb-4 border-b border-slate-100">
            <div>
              <h3 className="font-[var(--font-fun)] font-black text-2xl flex items-center gap-2 text-slate-800">
                <span>🗺️ My Learning Adventure Path</span>
                <span className="text-xs font-black px-3 py-1 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
                  {completedCount} of {assignments.length} Done
                </span>
              </h3>
              <p className="text-xs font-bold text-slate-400 mt-1">
                Step-by-step sequential quest map curated by your educator
              </p>
            </div>

            {/* View Mode Toggle: Duolingo Path vs Grid */}
            <div className="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-2xl border border-slate-200">
              <button
                onClick={() => setViewMode('winding')}
                className={`btn-3d text-xs px-3 py-1.5 font-black cursor-pointer ${
                  viewMode === 'winding' ? 'btn-3d-blue text-white' : 'btn-3d-slate text-slate-600'
                }`}
              >
                <span>🗺️ Winding Path</span>
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`btn-3d text-xs px-3 py-1.5 font-black cursor-pointer ${
                  viewMode === 'grid' ? 'btn-3d-blue text-white' : 'btn-3d-slate text-slate-600'
                }`}
              >
                <span>📋 Cards</span>
              </button>
            </div>
          </div>

          {loading ? (
            <SkeletonCurriculum count={4} />
          ) : assignments.length === 0 ? (
            <div className="p-10 text-center text-slate-400 text-sm font-semibold bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200">
              No assignments loaded. Please check with your teacher.
            </div>
          ) : viewMode === 'winding' ? (
            /* Duolingo Winding Stepping Stones View */
            <div className="relative py-6 max-w-md mx-auto flex flex-col items-center">
              {assignments.map((asg, idx) => {
                const g = getGameById(asg.game_id)
                const isCompleted = asg.status === 'completed'
                const isCurrent = asg.id === activeAssignment?.id
                const isPlayable = isCompleted || isCurrent || asg.is_unlocked === 1

                // S-curve lateral offsets: 0 = center, 1 = left, 2 = center, 3 = right
                const offsetPattern = [0, -50, 0, 50]
                const xOffset = offsetPattern[idx % 4]

                return (
                  <div
                    key={asg.id || idx}
                    className="relative flex flex-col items-center my-4"
                    style={{ transform: `translateX(${xOffset}px)` }}
                  >
                    {/* Path connector line to previous node */}
                    {idx > 0 && (
                      <div
                        className="w-1.5 h-10 border-l-4 border-dashed mb-1"
                        style={{
                          borderColor: isCompleted || isCurrent ? '#10B981' : '#CBD5E1',
                        }}
                      />
                    )}

                    {/* Active Mission Mascot Crown & Tooltip */}
                    {isCurrent && (
                      <div className="absolute -top-11 z-20 animate-bounce flex flex-col items-center pointer-events-none">
                        <span className="text-2xl drop-shadow-md">👑</span>
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-400 text-amber-950 shadow-md border border-amber-300">
                          START!
                        </span>
                      </div>
                    )}

                    {/* Stepping Stone Node Button */}
                    <div className="relative flex items-center justify-center">
                      {/* Pulsing Ring for current quest */}
                      {isCurrent && (
                        <div className="absolute -inset-2 rounded-full border-4 border-sky-400 duo-pulse-ring pointer-events-none" />
                      )}

                      {isPlayable && g ? (
                        <Link
                          to={`/kid/games/${g.id}`}
                          className={`w-20 h-20 rounded-full flex flex-col items-center justify-center text-3xl shadow-lg transition-transform duo-step-node no-underline ${
                            isCompleted
                              ? 'btn-3d btn-3d-green text-white'
                              : isCurrent
                              ? 'btn-3d btn-3d-blue text-white shadow-blue-400/50'
                              : 'btn-3d btn-3d-slate text-slate-700'
                          }`}
                        >
                          <span>{isCompleted ? '⭐' : g.icon}</span>
                          <span className="text-[10px] font-black mt-0.5">#{asg.sequence_order || idx + 1}</span>
                        </Link>
                      ) : (
                        <div className="w-18 h-18 rounded-full bg-slate-200 border-4 border-slate-300 flex flex-col items-center justify-center text-slate-400 shadow-inner">
                          <span className="text-xl">🔒</span>
                          <span className="text-[9px] font-black">#{asg.sequence_order || idx + 1}</span>
                        </div>
                      )}
                    </div>

                    {/* Node Title & Status */}
                    <div className="mt-2 text-center max-w-[140px]">
                      <div className="font-[var(--font-fun)] font-black text-xs text-slate-800 leading-tight">
                        {g?.name || asg.game_id}
                      </div>
                      <div className="text-[10px] font-bold mt-0.5">
                        {isCompleted ? (
                          <span className="text-emerald-700">✓ Mastered</span>
                        ) : isCurrent ? (
                          <span className="text-blue-700 font-extrabold animate-pulse">Current Quest</span>
                        ) : (
                          <span className="text-slate-400">Locked</span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            /* Cards View */
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
              {assignments.map((asg, idx) => {
                const g = getGameById(asg.game_id)
                const isCompleted = asg.status === 'completed'
                const isCurrent = asg.id === activeAssignment?.id
                const isPlayable = isCompleted || isCurrent || asg.is_unlocked === 1

                return (
                  <motion.div
                    key={asg.id || idx}
                    whileHover={{ scale: isPlayable ? 1.02 : 1 }}
                    className={`flex items-center gap-3.5 p-4 rounded-3xl border-2 transition-all shadow-xs ${
                      isCompleted
                        ? 'bg-emerald-50/90 border-emerald-300 text-emerald-950'
                        : isCurrent
                        ? 'bg-blue-50/95 border-blue-400 ring-4 ring-blue-200/60 shadow-md'
                        : 'bg-slate-50/80 border-slate-200 text-slate-400 opacity-80'
                    }`}
                  >
                    <div className="w-13 h-13 rounded-2xl bg-white flex items-center justify-center text-3xl shadow-sm border border-slate-200 shrink-0">
                      {isCompleted ? '✅' : g?.icon || '🎮'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                        Step #{asg.sequence_order || idx + 1}
                      </div>
                      <div className="font-[var(--font-fun)] font-black text-base truncate text-slate-800">
                        {g?.name || asg.game_id}
                      </div>
                      <div className="text-[11px] font-bold capitalize mt-0.5">
                        {isCompleted ? (
                          <span className="text-emerald-700">Completed ⭐</span>
                        ) : isCurrent ? (
                          <span className="text-blue-700 font-extrabold animate-pulse">Active Mission 🎯</span>
                        ) : (
                          <span className="text-slate-400">Locked 🔒</span>
                        )}
                      </div>
                    </div>

                    {isCompleted ? (
                      <Link
                        to={`/kid/games/${g?.id || asg.game_id}`}
                        className="btn-3d btn-3d-slate text-xs px-3 py-1.5 text-emerald-700 no-underline shrink-0"
                        title="Replay for fun and extra stars"
                      >
                        ⭐ Replay
                      </Link>
                    ) : isPlayable && g ? (
                      <Link
                        to={`/kid/games/${g.id}`}
                        className="btn-3d btn-3d-blue text-xs px-3.5 py-1.5 text-white no-underline shrink-0"
                      >
                        ▶ Play
                      </Link>
                    ) : (
                      <span className="text-xs font-black text-slate-400 px-3 py-1.5 rounded-xl bg-slate-200/80 shrink-0">
                        🔒 Locked
                      </span>
                    )}
                  </motion.div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* ── Mascot Nutmeg Floating Companion Widget (Bottom Right) ──────── */}
      <div className="fixed bottom-6 right-6 z-40 flex items-end gap-3 select-none">
        {/* Animated Speech Bubble */}
        <AnimatePresence mode="wait">
          <motion.div
            key={mascotMsgIdx}
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: -10 }}
            className="p-3.5 bg-white/95 backdrop-blur-md rounded-2xl border-2 border-amber-300 shadow-xl max-w-xs text-xs font-bold text-slate-800 relative hidden sm:block"
          >
            <div className="flex items-center justify-between gap-1 mb-1 text-[10px] font-black uppercase text-amber-700">
              <span>🐿️ Nutmeg Says:</span>
              <span className="text-slate-400 cursor-pointer" onClick={handleMascotClick}>Next ❯</span>
            </div>
            <p className="leading-snug">{MASCOT_MESSAGES[mascotMsgIdx]}</p>
            {/* Speech bubble beak */}
            <div className="absolute -right-2 bottom-4 w-0 h-0 border-t-8 border-t-transparent border-b-8 border-b-transparent border-l-8 border-l-amber-300" />
          </motion.div>
        </AnimatePresence>

        {/* Mascot Avatar Button */}
        <button
          onClick={handleMascotClick}
          title="Click to talk with Nutmeg!"
          className={`w-16 h-16 rounded-full bg-gradient-to-tr from-amber-400 to-orange-500 p-0.5 shadow-2xl border-3 border-white cursor-pointer transition-transform ${
            mascotWiggle ? 'animate-wiggle scale-110' : 'hover:scale-105 active:scale-95'
          }`}
        >
          <div className="w-full h-full bg-white rounded-full flex items-center justify-center text-3xl shadow-inner">
            🐿️
          </div>
        </button>
      </div>

      {/* ── Sticker Album & Trophy Cabinet Modal ─────────────────────────── */}
      <AnimatePresence>
        {showStickers && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="clay-card p-6 sm:p-8 max-w-2xl w-full bg-white rounded-3xl shadow-2xl border-4 border-amber-300 space-y-6 relative"
            >
              <div className="flex items-center justify-between border-b pb-4">
                <div className="flex items-center gap-3">
                  <span className="text-4xl">🏆</span>
                  <div>
                    <h2 className="text-2xl font-black font-[var(--font-fun)] text-slate-900">
                      Alex's Sticker Album & Badges
                    </h2>
                    <p className="text-xs text-slate-500 font-bold">
                      Earned by completing teacher-assigned practice milestones
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowStickers(false)}
                  className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 font-black flex items-center justify-center cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {/* Grid of 6 Badges */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {STICKER_COLLECTION.map((badge) => (
                  <div
                    key={badge.id}
                    className={`p-4 rounded-2xl border-2 text-center transition-all flex flex-col items-center justify-between gap-2 ${
                      badge.unlocked
                        ? 'bg-gradient-to-br from-amber-50 to-orange-50 border-amber-300 shadow-sm'
                        : 'bg-slate-50 border-slate-200 opacity-60'
                    }`}
                  >
                    <div
                      className={`w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shadow-md border-2 border-white bg-gradient-to-tr ${badge.color}`}
                    >
                      {badge.unlocked ? badge.emoji : '🔒'}
                    </div>
                    <div>
                      <h4 className="font-[var(--font-fun)] font-black text-xs text-slate-800">
                        {badge.title}
                      </h4>
                      <p className="text-[10px] text-slate-500 font-medium leading-tight mt-1">
                        {badge.desc}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${
                        badge.unlocked
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : 'bg-slate-200 text-slate-500'
                      }`}
                    >
                      {badge.unlocked ? '✓ Unlocked' : 'Locked'}
                    </span>
                  </div>
                ))}
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => {
                    playChime('star')
                    setShowStickers(false)
                  }}
                  className="btn-3d btn-3d-blue px-6 py-2.5 rounded-xl font-black text-xs text-white cursor-pointer"
                >
                  Awesome! Back to Quests →
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
