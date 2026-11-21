import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/authStore'
import { getGameById } from '../data/games'
import { apiGetStudentAssignments, apiGetStudentProfile } from '../api/client'
import { SkeletonCard } from '../components/SkeletonLoader'

export default function GameLibrary() {
  const [assignments, setAssignments] = useState<any[]>([])
  const [studentProfile, setStudentProfile] = useState<any>(null)
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'completed'>('all')
  const [loading, setLoading] = useState(true)
  const { name, childId, role } = useAuthStore()
  const isTeacher = role === 'teacher'

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

  // Active assignment
  const activeAssignment =
    assignments.find(
      (a) => a.status !== 'completed' && (a.is_unlocked === 1 || a.is_unlocked === true)
    ) ||
    assignments.find((a) => a.status !== 'completed') ||
    assignments[0]

  // Filter ONLY assigned games
  const filteredAssignments = assignments.filter((asg) => {
    if (filterStatus === 'completed') return asg.status === 'completed'
    if (filterStatus === 'active') return asg.id === activeAssignment?.id || asg.is_unlocked === 1
    return true
  })

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#EBF4FF] via-[#F8FAFC] to-[#FFF9E6] relative overflow-hidden">
      {/* Gentle Floating decorations */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-20 right-14 text-5xl animate-float opacity-20">🎮</div>
        <div className="absolute bottom-24 left-10 text-4xl animate-float opacity-15" style={{ animationDelay: '1.5s' }}>
          🌟
        </div>
        <div className="absolute top-1/2 left-8 text-3xl animate-float opacity-15" style={{ animationDelay: '2.5s' }}>
          ✨
        </div>
      </div>

      {/* Nav */}
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/85 border-b-2 border-slate-200/80 shadow-xs">
        <div className="max-w-5xl mx-auto px-6 h-18 flex items-center justify-between">
          {isTeacher ? (
            <Link
              to="/teacher"
              className="flex items-center gap-2 no-underline text-indigo-700 hover:text-indigo-900 transition-colors font-black text-sm"
            >
              <span>←</span>
              <span>Back to Educator Console</span>
            </Link>
          ) : (
            <Link
              to="/kid"
              className="flex items-center gap-2 no-underline text-slate-500 hover:text-slate-800 transition-colors font-black text-sm"
            >
              <span>←</span>
              <span>Back to Dashboard</span>
            </Link>
          )}
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 bg-gradient-to-tr from-amber-400 via-pink-400 to-indigo-500 rounded-2xl flex items-center justify-center text-xl shadow-sm animate-wiggle">
              ✨
            </div>
            <span className="font-[var(--font-fun)] font-black text-xl text-slate-800 tracking-tight">
              SkillSpark
            </span>
          </div>
          {isTeacher ? (
            <span className="text-xs font-black bg-indigo-100 text-indigo-800 px-3.5 py-1.5 rounded-full border border-indigo-200 shadow-xs">
              👨‍🏫 Teacher All-Access
            </span>
          ) : (
            <span className="text-xs font-mono font-black bg-indigo-100 text-indigo-800 px-3.5 py-1.5 rounded-full border border-indigo-200 shadow-xs">
              {studentProfile?.student_id || childId || 'STU-1001'}
            </span>
          )}
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8 relative z-10 space-y-6">
        {/* Header Banner */}
        <div className="clay-card p-7 md:p-8">
          <div className="flex flex-wrap items-center gap-2.5 mb-2">
            <h1 className="text-3xl md:text-4xl font-black font-[var(--font-fun)] text-slate-800 tracking-tight">
              {isTeacher ? '🎮 Serious Games Testing Library' : '🎯 My Teacher-Assigned Missions'}
            </h1>
            <span className="px-3.5 py-1 rounded-full text-xs font-black bg-emerald-100 text-emerald-800 border border-emerald-300">
              {isTeacher
                ? 'Full All-Access (No Order Restrictions)'
                : `Curated by ${studentProfile?.teacher_name || 'Ms. Sarah Wilson'}`}
            </span>
          </div>
          <p className="text-slate-600 text-xs md:text-sm font-medium leading-relaxed max-w-3xl">
            {isTeacher
              ? 'As an educator, you can launch, test, and inspect any serious game at any time with zero sequence or lock restrictions. Restrictions only apply in student logins.'
              : `Hey ${
                  studentProfile?.full_name || name || 'Alex'
                }! These are the specific activities approved for your learning path. All other activities are hidden so you can focus calmly step-by-step!`}
          </p>

          {/* 3D Filter buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-6 mt-6 border-t border-slate-100">
            <button
              onClick={() => setFilterStatus('all')}
              className={`btn-3d text-xs px-4 py-2 ${
                filterStatus === 'all' ? 'btn-3d-blue text-white' : 'btn-3d-slate text-slate-600'
              }`}
            >
              All Assigned ({assignments.length})
            </button>
            <button
              onClick={() => setFilterStatus('active')}
              className={`btn-3d text-xs px-4 py-2 ${
                filterStatus === 'active' ? 'btn-3d-blue text-white' : 'btn-3d-slate text-slate-600'
              }`}
            >
              🎯 Active & Ready (
              {assignments.filter((a) => a.is_unlocked === 1 && a.status !== 'completed').length})
            </button>
            <button
              onClick={() => setFilterStatus('completed')}
              className={`btn-3d text-xs px-4 py-2 ${
                filterStatus === 'completed' ? 'btn-3d-blue text-white' : 'btn-3d-slate text-slate-600'
              }`}
            >
              ⭐ Completed ({assignments.filter((a) => a.status === 'completed').length})
            </button>
          </div>
        </div>

        {/* Game Cards Grid */}
        {loading ? (
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
            <SkeletonCard count={6} />
          </div>
        ) : filteredAssignments.length === 0 ? (
          <div className="clay-card p-12 text-center text-slate-400 space-y-2">
            <div className="text-5xl animate-bounce">🔍</div>
            <p className="font-bold text-slate-600">No missions match the selected filter.</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
            {filteredAssignments.map((asg, idx) => {
              const game = getGameById(asg.game_id)
              const isCompleted = asg.status === 'completed'
              const isCurrent = asg.id === activeAssignment?.id
              const isUnlocked = isTeacher || isCompleted || isCurrent || asg.is_unlocked === 1

              if (!game) return null

              return (
                <motion.div
                  key={asg.id || idx}
                  whileHover={{ y: -4 }}
                  transition={{ duration: 0.2 }}
                  className={`clay-card p-6 flex flex-col justify-between transition-all relative overflow-hidden border-2 ${
                    isTeacher
                      ? 'border-indigo-200/80 hover:border-indigo-400 shadow-sm'
                      : isCompleted
                      ? 'border-emerald-300 bg-emerald-50/40 shadow-xs'
                      : isCurrent
                      ? 'border-blue-400 ring-4 ring-blue-100 shadow-md bg-white'
                      : 'border-slate-200 bg-slate-50/70 opacity-75'
                  }`}
                >
                  <div>
                    {/* Top Step & Status pill */}
                    <div className="flex items-center justify-between mb-4">
                      <span className="px-3 py-1 rounded-full text-xs font-black bg-indigo-100 text-indigo-800 font-mono border border-indigo-200">
                        Step #{asg.sequence_order || idx + 1}
                      </span>
                      {isCompleted ? (
                        <span className="px-3 py-1 rounded-full text-[11px] font-black bg-emerald-100 text-emerald-800 border border-emerald-300">
                          ✓ Completed ⭐
                        </span>
                      ) : isTeacher ? (
                        <span className="px-3 py-1 rounded-full text-[11px] font-black bg-indigo-100 text-indigo-800 border border-indigo-200">
                          ✓ Ready to Test
                        </span>
                      ) : isCurrent ? (
                        <span className="px-3 py-1 rounded-full text-[11px] font-black bg-amber-200 text-amber-950 border border-amber-300 animate-pulse">
                          🎯 Active Mission
                        </span>
                      ) : (
                        <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-slate-200 text-slate-600">
                          🔒 Locked
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-4 mb-3.5">
                      <div className="w-18 h-18 rounded-3xl bg-gradient-to-tr from-slate-50 to-white border-2 border-slate-200/80 flex items-center justify-center text-4xl shadow-sm shrink-0">
                        {game.icon}
                      </div>
                      <div>
                        <h3 className="font-[var(--font-fun)] font-black text-xl text-slate-800 leading-tight">
                          {game.name}
                        </h3>
                        <span className="text-[11px] font-bold text-slate-500 mt-0.5 block">
                          Level {game.level} • {asg.difficulty || 'Easy'} Challenge
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-600 line-clamp-2 mb-4 leading-relaxed font-medium">
                      {game.description}
                    </p>

                    {/* Sensor / Input Mode Pills */}
                    <div className="flex flex-wrap items-center gap-1.5 mb-5">
                      {game.needs?.camera && (
                        <span className="px-2 py-0.5 rounded-lg text-[10px] font-black bg-sky-100 text-sky-800 border border-sky-200">
                          📷 Camera
                        </span>
                      )}
                      {game.needs?.microphone && (
                        <span className="px-2 py-0.5 rounded-lg text-[10px] font-black bg-purple-100 text-purple-800 border border-purple-200">
                          🎙️ Voice
                        </span>
                      )}
                      <span className="px-2 py-0.5 rounded-lg text-[10px] font-black bg-emerald-100 text-emerald-800 border border-emerald-200">
                        👆 Touch/Click
                      </span>
                    </div>
                  </div>

                  <div>
                    {isUnlocked ? (
                      <Link
                        to={`/kid/games/${game.id}`}
                        className={`w-full py-3.5 btn-3d text-sm no-underline ${
                          isTeacher
                            ? 'btn-3d-purple text-white'
                            : isCompleted
                            ? 'btn-3d-green text-white'
                            : 'btn-3d-blue text-white'
                        }`}
                      >
                        <span>
                          {isTeacher
                            ? '▶ Test Game Now'
                            : isCompleted
                            ? '⭐ Replay Mission'
                            : '▶ Play Mission Now'}
                        </span>
                        <span className="ml-1 text-base">🚀</span>
                      </Link>
                    ) : (
                      <div className="w-full py-3.5 rounded-2xl font-black text-xs bg-slate-200 text-slate-500 flex items-center justify-center gap-1.5 cursor-not-allowed">
                        <span>🔒 Complete Step #{asg.sequence_order - 1} First</span>
                      </div>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
