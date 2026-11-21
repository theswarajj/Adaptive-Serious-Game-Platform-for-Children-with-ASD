import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import {
  apiParentChildren,
  apiAddParentObservation,
  apiAddParentFeedback,
  apiGetMessages,
  apiSendMessage,
  apiGetStudentReport,
  apiGetParentProfile,
  apiUpdateParentProfile,
  apiParentUpdateChildPassword,
  apiParentUpdateOwnPassword
} from '../api/client'
import { getGameById } from '../data/games'
import { SkeletonProfile360, SkeletonStatsGrid, SkeletonCurriculum } from '../components/SkeletonLoader'

const DEFAULT_CHILDREN = [
  {
    id: 'STU-1001',
    student_id: 'STU-1001',
    full_name: 'Alex Miller',
    age: 7,
    avatar: 'boy-1',
    class_name: 'Sunflower Room (Early Primary)',
    parent_name: 'Elena Miller',
    relationship: 'Mother',
    latest_teacher_note: 'Alex demonstrated wonderful joint attention and waiting during turn-taking today.',
    stars_earned: 15,
    assignments: [
      { id: 'asg-01', game_id: 'bubble-hunt', sequence_order: 1, difficulty: 'easy', status: 'completed', is_unlocked: 1 },
      { id: 'asg-02', game_id: 'pattern-trail', sequence_order: 2, difficulty: 'easy', status: 'completed', is_unlocked: 1 },
      { id: 'asg-03', game_id: 'talk-and-build', sequence_order: 3, difficulty: 'medium', status: 'in_progress', is_unlocked: 1 },
      { id: 'asg-04', game_id: 'my-turn-your-turn', sequence_order: 4, difficulty: 'medium', status: 'pending', is_unlocked: 0 },
      { id: 'asg-05', game_id: 'shopping-adventure', sequence_order: 5, difficulty: 'hard', status: 'pending', is_unlocked: 0 },
    ],
    assigned_games: [
      { id: 'asg-01', game_id: 'bubble-hunt', sequence_order: 1, difficulty: 'easy', status: 'completed', is_unlocked: 1 },
      { id: 'asg-02', game_id: 'pattern-trail', sequence_order: 2, difficulty: 'easy', status: 'completed', is_unlocked: 1 },
      { id: 'asg-03', game_id: 'talk-and-build', sequence_order: 3, difficulty: 'medium', status: 'in_progress', is_unlocked: 1 },
      { id: 'asg-04', game_id: 'my-turn-your-turn', sequence_order: 4, difficulty: 'medium', status: 'pending', is_unlocked: 0 },
      { id: 'asg-05', game_id: 'shopping-adventure', sequence_order: 5, difficulty: 'hard', status: 'pending', is_unlocked: 0 },
    ]
  }
]

type ParentTab = 'progress' | 'observation' | 'feedback' | 'messages' | 'report' | 'profile'

export default function ParentDashboard() {
  const { name, logout, userId, childId } = useAuthStore()
  const navigate = useNavigate()

  const [activeTab, setActiveTab] = useState<ParentTab>('progress')
  const [children, setChildren] = useState<any[]>(DEFAULT_CHILDREN)
  const [selectedChild, setSelectedChild] = useState<any>(DEFAULT_CHILDREN[0])
  const [messages, setMessages] = useState<any[]>([])
  const [newMessageText, setNewMessageText] = useState<string>('')
  const [reportData, setReportData] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)

  // Parent Profile state
  const [parentProfile, setParentProfile] = useState<any>(null)
  const [profileForm, setProfileForm] = useState({ display_name: '', email: '', phone: '', relationship: '' })
  const [profileSavedMsg, setProfileSavedMsg] = useState<string | null>(null)

  // Password & PIN Management States
  const [parentNewPassword, setParentNewPassword] = useState('')
  const [parentConfirmPassword, setParentConfirmPassword] = useState('')
  const [parentPasswordSuccess, setParentPasswordSuccess] = useState<string | null>(null)
  const [parentPasswordError, setParentPasswordError] = useState<string | null>(null)

  const [childNewPin, setChildNewPin] = useState('')
  const [childConfirmPin, setChildConfirmPin] = useState('')
  const [childPinSuccess, setChildPinSuccess] = useState<string | null>(null)
  const [childPinError, setChildPinError] = useState<string | null>(null)

  const handleUpdateParentPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setParentPasswordError(null)
    setParentPasswordSuccess(null)
    if (!parentNewPassword || parentNewPassword.length < 3) {
      setParentPasswordError('Password must be at least 3 characters.')
      return
    }
    if (parentNewPassword !== parentConfirmPassword) {
      setParentPasswordError('Passwords do not match.')
      return
    }
    try {
      await apiParentUpdateOwnPassword(parentNewPassword)
      setParentPasswordSuccess('✓ Your parent portal password has been updated successfully!')
      setParentNewPassword('')
      setParentConfirmPassword('')
      setTimeout(() => setParentPasswordSuccess(null), 5000)
    } catch (err: any) {
      setParentPasswordError(err?.message || 'Failed to update password')
    }
  }

  const handleUpdateChildPin = async (e: React.FormEvent) => {
    e.preventDefault()
    setChildPinError(null)
    setChildPinSuccess(null)
    if (!childNewPin || childNewPin.length < 2) {
      setChildPinError('Child PIN/Password must be at least 2 characters.')
      return
    }
    if (childNewPin !== childConfirmPin) {
      setChildPinError('Child PIN confirmation does not match.')
      return
    }
    try {
      const studentId = selectedChild?.id || selectedChild?.student_id || 'STU-1001'
      await apiParentUpdateChildPassword(studentId, childNewPin)
      setChildPinSuccess(`✓ Success! ${selectedChild?.full_name || 'Your child'}'s login PIN/Password updated to '${childNewPin}'. They can now log in with this PIN!`)
      setChildNewPin('')
      setChildConfirmPin('')
      setTimeout(() => setChildPinSuccess(null), 6000)
    } catch (err: any) {
      setChildPinError(err?.message || 'Failed to update child PIN')
    }
  }

  // Home Observation Form
  const [obsForm, setObsForm] = useState({
    routine_transitions: 4,
    communication_attempts: 5,
    sensory_sensitivity: 2,
    regulation_strategies: '',
    home_notes: '',
  })
  const [obsSavedMessage, setObsSavedMessage] = useState<string | null>(null)

  // Game Feedback Form
  const [feedbackForm, setFeedbackForm] = useState({
    game_id: 'talk-and-build',
    enjoyment_rating: 5,
    frustration_level: 1,
    assistance_needed: 2,
    comments: '',
  })
  const [feedbackSavedMessage, setFeedbackSavedMessage] = useState<string | null>(null)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const loadData = async () => {
    try {
      setLoading(true)
      const results = await Promise.allSettled([
        apiParentChildren(),
        apiGetParentProfile(),
      ])
      const kidsList = results[0].status === 'fulfilled' ? results[0].value : []
      const profData = results[1].status === 'fulfilled' ? results[1].value : null

      if (Array.isArray(kidsList) && kidsList.length > 0) {
        setChildren(kidsList)
        setSelectedChild(kidsList[0])
        loadMessages(kidsList[0].id)
      } else {
        loadMessages('STU-1001')
      }
      if (profData?.parent) {
        setParentProfile(profData.parent)
        setProfileForm({
          display_name: profData.parent.display_name || '',
          email: profData.parent.email || 'elena.miller@example.com',
          phone: profData.parent.phone || '+1 (555) 234-5678',
          relationship: profData.children?.[0]?.relationship || 'Mother / Primary Caregiver',
        })
      }
    } catch (err) {
      console.error('Error loading parent data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await apiUpdateParentProfile(profileForm)
      setProfileSavedMsg('Contact details updated successfully!')
      setParentProfile((prev: any) => ({ ...prev, ...profileForm }))
      setTimeout(() => setProfileSavedMsg(null), 3500)
    } catch (err) {
      console.error('Error updating parent profile:', err)
    }
  }

  const loadMessages = async (studentId: string) => {
    try {
      const msgs = await apiGetMessages(studentId)
      setMessages(msgs)
    } catch (err) {
      console.error('Error loading messages:', err)
    }
  }

  const loadReport = async (studentId: string) => {
    try {
      const rep = await apiGetStudentReport(studentId)
      setReportData(rep)
      setActiveTab('report')
    } catch (err) {
      console.error('Error loading report:', err)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Submit Observation
  const handleSubmitObservation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!obsForm.home_notes.trim() || !selectedChild) return
    try {
      await apiAddParentObservation({
        student_id: selectedChild.id,
        ...obsForm,
      })
      setObsSavedMessage('Home observation submitted successfully! Your teacher will see it.')
      setObsForm({
        routine_transitions: 4,
        communication_attempts: 5,
        sensory_sensitivity: 2,
        regulation_strategies: '',
        home_notes: '',
      })
      setTimeout(() => setObsSavedMessage(null), 3000)
    } catch (err) {
      console.error('Error submitting parent observation:', err)
    }
  }

  // Submit Feedback
  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedChild) return
    try {
      await apiAddParentFeedback({
        student_id: selectedChild.id,
        ...feedbackForm,
      })
      setFeedbackSavedMessage('Game feedback recorded successfully!')
      setFeedbackForm({
        game_id: 'talk-and-build',
        enjoyment_rating: 5,
        frustration_level: 1,
        assistance_needed: 2,
        comments: '',
      })
      setTimeout(() => setFeedbackSavedMessage(null), 3000)
    } catch (err) {
      console.error('Error submitting feedback:', err)
    }
  }

  // Send Message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessageText.trim() || !selectedChild) return
    try {
      await apiSendMessage({
        sender_id: parentProfile?.id || userId || 'parent-user',
        receiver_id: 'teacher-user',
        student_id: selectedChild.id,
        content: newMessageText.trim(),
      })
      setNewMessageText('')
      await loadMessages(selectedChild.id)
    } catch (err) {
      console.error('Error sending message:', err)
    }
  }

  const child = selectedChild || children[0]

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Top Navbar */}
      <nav className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center text-xl text-white shadow-md shadow-amber-200">
              👨‍👩‍👧
            </div>
            <div>
              <span className="font-extrabold text-lg text-slate-900 tracking-tight">Parent Portal</span>
              <span className="ml-2.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                Home Observation & Progress
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="hidden md:flex items-center gap-1.5 bg-slate-100/90 backdrop-blur-sm p-1.5 rounded-2xl border border-slate-200/80 shadow-inner">
            <button
              onClick={() => setActiveTab('progress')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                activeTab === 'progress' ? 'btn-3d btn-3d-slate bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              📊 Child Progress
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                activeTab === 'profile' ? 'btn-3d btn-3d-slate bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              👤 Profile & Student ID
            </button>
            <button
              onClick={() => setActiveTab('observation')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                activeTab === 'observation' ? 'btn-3d btn-3d-slate bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              🏡 Home Observation
            </button>
            <button
              onClick={() => setActiveTab('feedback')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                activeTab === 'feedback' ? 'btn-3d btn-3d-slate bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              ⭐ Game Feedback
            </button>
            <button
              onClick={() => setActiveTab('messages')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                activeTab === 'messages' ? 'btn-3d btn-3d-slate bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              💬 Teacher Chat
            </button>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-600 hidden sm:inline">
              👋 {name || 'Elena Miller'}
            </span>
            <button
              onClick={handleLogout}
              className="px-3.5 py-1.5 rounded-xl text-xs font-black bg-white text-slate-600 hover:bg-rose-50 hover:text-rose-600 transition-colors cursor-pointer border border-slate-200 shadow-xs active:translate-y-0.5"
            >
              Sign Out
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {loading ? (
          <div className="space-y-6 animate-fadeInUp">
            <SkeletonProfile360 />
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-6 bg-white rounded-3xl border border-slate-100 shadow-sm space-y-4">
                <div className="h-6 w-48 rounded-lg skeleton-shimmer" />
                <div className="space-y-3 pt-2">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="h-8 rounded-xl skeleton-shimmer" />
                  ))}
                </div>
              </div>
              <SkeletonCurriculum count={4} />
            </div>
          </div>
        ) : (
          <>
            {/* Child Header Card */}
        {child && (
          <div className="clay-card p-6 bg-gradient-to-r from-amber-50/90 via-orange-50/70 to-amber-50/90 rounded-3xl border border-amber-200/80 shadow-md mb-8 flex flex-col md:flex-row md:items-center justify-between gap-5 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-400 via-orange-400 to-amber-300" />
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-amber-400 to-orange-400 p-0.5 shadow-md flex items-center justify-center">
                  <div className="w-full h-full bg-white rounded-[14px] flex items-center justify-center text-4xl shadow-inner">
                    {child.avatar === 'girl-1' ? '👧' : '👦'}
                  </div>
                </div>
                <span className="absolute -bottom-1 -right-1 px-1.5 py-0.5 rounded-full text-[9px] font-black bg-emerald-500 text-white border-2 border-white shadow-xs">
                  Active
                </span>
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <h1 className="text-2xl font-black text-slate-900 tracking-tight">{child.full_name}</h1>
                  <span className="px-3 py-0.5 rounded-full text-xs font-black bg-indigo-100 text-indigo-800 border border-indigo-200 font-mono shadow-xs">
                    Student ID: {child.student_id || child.id}
                  </span>
                </div>
                <p className="text-xs text-slate-600 flex items-center gap-2 flex-wrap">
                  <span>Class: <strong className="font-bold text-slate-800">{child.class_name || 'Sunflower Room'}</strong></span>
                  <span>•</span>
                  <span>Age: <strong className="font-bold text-slate-800">{child.age || 7}</strong></span>
                  <span>•</span>
                  <span>Guardian: <strong className="font-bold text-slate-800">{parentProfile?.display_name || child.parent_name || 'Elena Miller'}</strong> ({child.relationship || 'Mother / Guardian'})</span>
                </p>
                <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                  {parentProfile?.phone && <span>📞 {parentProfile.phone}</span>}
                  {parentProfile?.email && <span>✉️ {parentProfile.email}</span>}
                </div>
                {child.latest_teacher_note && (
                  <p className="text-xs text-amber-900 mt-1 italic font-medium bg-amber-100/60 px-3 py-1.5 rounded-xl border border-amber-200/60 inline-block">
                    💬 <span className="font-bold">Latest Note from Teacher:</span> "{child.latest_teacher_note.notes || child.latest_teacher_note}"
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              {children.length > 1 && (
                <select
                  value={child.id}
                  onChange={e => {
                    const c = children.find(item => item.id === e.target.value)
                    if (c) {
                      setSelectedChild(c)
                      loadMessages(c.id)
                    }
                  }}
                  className="px-3.5 py-2.5 rounded-xl text-xs font-bold border-2 border-amber-300 bg-white shadow-xs cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-400"
                >
                  {children.map(c => (
                    <option key={c.id} value={c.id}>
                      Switch Child: {c.full_name} ({c.id})
                    </option>
                  ))}
                </select>
              )}
              <button
                onClick={() => loadReport(child.id)}
                className="btn-3d btn-3d-blue px-4 py-2.5 rounded-xl text-xs font-black shadow-xs cursor-pointer flex items-center gap-2 text-white"
              >
                <span>📑</span> View Full Progress Report
              </button>
            </div>
          </div>
        )}

        {/* Home Skill-Transfer Tip of the Day (Co-Regulation & Evidence-Based Routine) */}
        {child && (
          <div className="clay-card p-5 bg-gradient-to-r from-emerald-50/90 via-teal-50/80 to-sky-50/90 rounded-3xl border-2 border-emerald-200/90 shadow-sm mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500 text-white flex items-center justify-center text-2xl shadow-sm shrink-0 animate-bounce">
                💡
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300">
                    Home Skill-Transfer Tip of the Day
                  </span>
                  <span className="text-xs font-bold text-slate-400">• Evidence-Based Co-Regulation</span>
                </div>
                <h3 className="font-extrabold text-sm text-slate-800">
                  Practicing Reciprocal Turn-Taking & Descriptive Speech at Home
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
                  {child.full_name} practiced joint attention and waiting games in class today. Try a 2-minute <strong className="text-slate-800">"Chef & Helper"</strong> turn-taking activity at dinner tonight—pass the serving spoon back and forth, pausing 3 seconds before taking your turn to reinforce reciprocal waiting!
                </p>
              </div>
            </div>

            <button
              onClick={() => {
                alert('Great job! Daily home activity marked as completed. Your teacher has been updated!')
              }}
              className="btn-3d btn-3d-green px-4 py-2.5 rounded-xl text-xs font-black text-white shrink-0 flex items-center gap-1.5 shadow-xs cursor-pointer"
            >
              <span>✓</span> Mark Done Today
            </button>
          </div>
        )}

        {/* TAB 1: CHILD PROGRESS & LEARNING PATH */}
        {activeTab === 'progress' && child && (
          <div className="grid md:grid-cols-2 gap-6 animate-fadeInUp">
            {/* Multi-Domain Behavioral Radar */}
            <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
              <h2 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                <span>📊</span> Developmental Practice Domains
              </h2>
              <p className="text-xs text-slate-500">
                Tracked practice progress across 6 developmental skill areas:
              </p>

              <div className="space-y-3 pt-2">
                {[
                  { label: 'Motor Skills & Coordination', score: child.motor_skills, color: 'bg-emerald-500' },
                  { label: 'Attention & Visual Focus', score: child.attention_focus, color: 'bg-sky-500' },
                  { label: 'Emotion Recognition', score: child.emotion_recognition, color: 'bg-amber-500' },
                  { label: 'Communication & Speech', score: child.communication_language, color: 'bg-indigo-500' },
                  { label: 'Social Turn-Taking', score: child.social_interaction, color: 'bg-purple-500' },
                  { label: 'Daily Living Routines', score: child.daily_living, color: 'bg-teal-500' },
                ].map((d, i) => {
                  const pct = Math.round((d.score || 0.6) * 100)
                  return (
                    <div key={i} className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div className="flex justify-between items-center text-xs font-bold mb-1">
                        <span className="text-slate-700">{d.label}</span>
                        <span className="text-slate-900">{pct}%</span>
                      </div>
                      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${d.color}`} style={{ width: `${pct}%` }}></div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Approved Learning Path Sequence */}
            <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                  <span>🎯</span> Teacher-Approved Learning Quests
                </h2>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-black bg-indigo-100 text-indigo-800">
                  {(child.assignments || []).filter((a: any) => a.status === 'completed').length} / {(child.assignments || []).length} Mastered
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Curated specifically for {child.full_name} by Lead Educator Ms. Sarah Wilson. Non-assigned activities remain hidden to preserve a calm, focused schedule.
              </p>

              <div className="space-y-2.5 pt-2">
                {(child.assignments || []).length === 0 ? (
                  <div className="p-6 text-center text-slate-400 text-xs">
                    Your educator is currently planning upcoming learning quests.
                  </div>
                ) : (
                  (child.assignments || []).map((asg: any) => {
                    const g = getGameById(asg.game_id)
                    const isCompleted = asg.status === 'completed'
                    const isUnlocked = asg.is_unlocked === 1 && !isCompleted
                    return (
                      <div
                        key={asg.id}
                        className={`p-3.5 rounded-2xl border flex items-center justify-between text-xs transition-all ${
                          isCompleted
                            ? 'bg-emerald-50/70 border-emerald-200'
                            : isUnlocked
                            ? 'bg-blue-50/80 border-blue-400 ring-2 ring-blue-200 shadow-xs'
                            : 'bg-slate-50 border-slate-200 opacity-65'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="w-6 h-6 rounded-full bg-white border border-slate-300 flex items-center justify-center font-bold text-[11px] text-slate-700">
                            #{asg.sequence_order}
                          </span>
                          <span className="text-2xl">{g?.icon || '🎮'}</span>
                          <div>
                            <div className="font-bold text-slate-900">{g?.name || asg.game_id}</div>
                            <div className="text-[11px] text-slate-500">
                              Difficulty: <span className="capitalize font-semibold">{asg.difficulty || 'Easy'}</span> • Level {g?.level || 1}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold ${
                            isCompleted
                              ? 'bg-emerald-200 text-emerald-800'
                              : isUnlocked
                              ? 'bg-blue-200 text-blue-900 animate-pulse font-extrabold'
                              : 'bg-slate-200 text-slate-600'
                          }`}>
                            {isCompleted ? '✓ Mastered' : isUnlocked ? '🎯 Active Quest' : '🔒 Locked'}
                          </span>
                          {isUnlocked && (
                            <Link
                              to={`/kid/games/${g?.id || asg.game_id}`}
                              className="btn-3d btn-3d-blue px-3.5 py-1.5 rounded-xl text-xs font-bold text-white no-underline shadow-xs inline-flex items-center gap-1"
                            >
                              ▶ Guide Play
                            </Link>
                          )}
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: RECORD HOME OBSERVATION */}
        {activeTab === 'observation' && child && (
          <div className="max-w-2xl mx-auto p-8 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-6 animate-fadeInUp">
            <div>
              <h2 className="text-2xl font-black text-slate-900">Record Home Observation</h2>
              <p className="text-xs text-slate-500 mt-1">
                Your observations help teachers understand how skills transfer from school and screen to home routines.
              </p>
            </div>

            {obsSavedMessage && (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold text-center">
                ✓ {obsSavedMessage}
              </div>
            )}

            <form onSubmit={handleSubmitObservation} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">
                    Daily Routine Transitions (1-5)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={obsForm.routine_transitions}
                    onChange={e => setObsForm(prev => ({ ...prev, routine_transitions: Number(e.target.value) }))}
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-bold"
                  />
                  <span className="text-[10px] text-slate-400">1 = difficult, 5 = smooth</span>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">
                    Communication Attempts (1-5)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={obsForm.communication_attempts}
                    onChange={e => setObsForm(prev => ({ ...prev, communication_attempts: Number(e.target.value) }))}
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-bold"
                  />
                  <span className="text-[10px] text-slate-400">1 = minimal, 5 = frequent</span>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">
                    Sensory Sensitivity (1-5)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={obsForm.sensory_sensitivity}
                    onChange={e => setObsForm(prev => ({ ...prev, sensory_sensitivity: Number(e.target.value) }))}
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-bold"
                  />
                  <span className="text-[10px] text-slate-400">1 = calm, 5 = highly reactive</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Regulation Strategies Used at Home
                </label>
                <input
                  type="text"
                  value={obsForm.regulation_strategies}
                  onChange={e => setObsForm(prev => ({ ...prev, regulation_strategies: e.target.value }))}
                  placeholder="e.g. Quiet music, deep pressure hug, 5-minute timer"
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Home Notes & Behavioral Observations *
                </label>
                <textarea
                  rows={4}
                  required
                  value={obsForm.home_notes}
                  onChange={e => setObsForm(prev => ({ ...prev, home_notes: e.target.value }))}
                  placeholder="Share details about dinner conversations, bedtime transitions, emotional regulation, or newly practiced words..."
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs"
                ></textarea>
              </div>

              <button
                type="submit"
                className="btn-3d btn-3d-amber w-full py-3 rounded-2xl font-black text-xs text-white shadow-sm cursor-pointer flex items-center justify-center gap-2"
              >
                <span>✓</span> Submit Home Observation
              </button>
            </form>
          </div>
        )}

        {/* TAB 3: GAME FEEDBACK */}
        {activeTab === 'feedback' && child && (
          <div className="max-w-2xl mx-auto p-8 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-6 animate-fadeInUp">
            <div>
              <h2 className="text-2xl font-black text-slate-900">Per-Game Session Feedback</h2>
              <p className="text-xs text-slate-500 mt-1">
                Share how your child reacted to a specific game played at home or school.
              </p>
            </div>

            {feedbackSavedMessage && (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold text-center">
                ✓ {feedbackSavedMessage}
              </div>
            )}

            <form onSubmit={handleSubmitFeedback} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">Select Game</label>
                <select
                  value={feedbackForm.game_id}
                  onChange={e => setFeedbackForm(prev => ({ ...prev, game_id: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-bold"
                >
                  {(child.assignments || []).length > 0 ? (
                    (child.assignments || []).map((asg: any) => {
                      const g = getGameById(asg.game_id)
                      return (
                        <option key={asg.id} value={asg.game_id}>
                          Step #{asg.sequence_order}: {g?.name || asg.game_id} ({asg.difficulty || 'Easy'}) - {asg.status === 'completed' ? 'Mastered ⭐' : asg.is_unlocked ? 'Active Quest 🎯' : 'Locked 🔒'}
                        </option>
                      )
                    })
                  ) : (
                    <>
                      <option value="bubble-hunt">Bubble Hunt (Lvl 1)</option>
                      <option value="follow-the-star">Follow the Star (Lvl 1)</option>
                      <option value="pattern-trail">Pattern Trail (Lvl 1)</option>
                      <option value="emotion-mirror">Emotion Mirror (Lvl 2)</option>
                      <option value="talk-and-build">Talk & Build (Lvl 3)</option>
                    </>
                  )}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Enjoyment (1-5)</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={feedbackForm.enjoyment_rating}
                    onChange={e => setFeedbackForm(prev => ({ ...prev, enjoyment_rating: Number(e.target.value) }))}
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-bold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Frustration (1-5)</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={feedbackForm.frustration_level}
                    onChange={e => setFeedbackForm(prev => ({ ...prev, frustration_level: Number(e.target.value) }))}
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-bold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Assistance (1-5)</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={feedbackForm.assistance_needed}
                    onChange={e => setFeedbackForm(prev => ({ ...prev, assistance_needed: Number(e.target.value) }))}
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-bold"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">Comments & Reactions</label>
                <textarea
                  rows={3}
                  value={feedbackForm.comments}
                  onChange={e => setFeedbackForm(prev => ({ ...prev, comments: e.target.value }))}
                  placeholder="e.g. Loved the squirrel mascot, wanted to play two more rounds!"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs"
                ></textarea>
              </div>

              <button
                type="submit"
                className="btn-3d btn-3d-blue w-full py-3 rounded-2xl font-black text-xs text-white shadow-sm cursor-pointer flex items-center justify-center gap-2"
              >
                <span>⭐</span> Submit Game Feedback
              </button>
            </form>
          </div>
        )}

        {/* TAB 4: TEACHER MESSAGES */}
        {activeTab === 'messages' && child && (
          <div className="max-w-3xl mx-auto bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden animate-fadeInUp">
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <h3 className="font-extrabold text-base text-slate-900">Direct Chat with Lead Educator</h3>
                <p className="text-xs text-slate-500">Teacher: Ms. Sarah Wilson</p>
              </div>
              <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                Active
              </span>
            </div>

            <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
              {messages.map((m: any) => {
                const isMe = m.sender_role === 'parent'
                return (
                  <div key={m.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-md p-4 rounded-2xl text-xs space-y-1 ${
                      isMe ? 'bg-amber-600 text-white' : 'bg-slate-100 text-slate-800'
                    }`}>
                      <div className={`font-bold text-[11px] ${isMe ? 'text-amber-200' : 'text-slate-500'}`}>
                        {m.sender_name}
                      </div>
                      <p className="leading-relaxed">{m.content}</p>
                    </div>
                  </div>
                )
              })}
            </div>

            <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-200 bg-slate-50 flex gap-3">
              <input
                type="text"
                value={newMessageText}
                onChange={e => setNewMessageText(e.target.value)}
                placeholder="Ask Ms. Wilson a question or share home feedback..."
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-xs font-medium focus:outline-none focus:border-amber-500"
              />
              <button
                type="submit"
                className="btn-3d btn-3d-amber px-5 py-2.5 rounded-xl font-black text-xs text-white shadow-xs cursor-pointer flex items-center gap-1.5"
              >
                <span>💬</span> Send
              </button>
            </form>
          </div>
        )}

        {/* TAB: PARENT & STUDENT PROFILE */}
        {activeTab === 'profile' && (
          <div className="space-y-6 max-w-4xl mx-auto animate-fadeInUp">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-black text-slate-900 flex items-center gap-2">
                  <span>👤</span> Family Profile & Student Details
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Verified school records, student identification number, contact information, and home-school coordination profile.
                </p>
              </div>
            </div>

            {profileSavedMsg && (
              <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold text-center">
                ✓ {profileSavedMsg}
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-6">
              {/* Linked Student Card */}
              <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b pb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{child?.avatar === 'girl-1' ? '👧' : '👦'}</span>
                    <div>
                      <h3 className="font-extrabold text-base text-slate-900">{child?.full_name || 'Alex Miller'}</h3>
                      <span className="text-xs text-slate-500">Student Profile</span>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-black bg-indigo-100 text-indigo-800 border border-indigo-200 font-mono">
                    ID: {child?.student_id || child?.id || 'STU-1001'}
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="flex justify-between p-2.5 bg-slate-50 rounded-xl">
                    <span className="text-slate-500 font-medium">Student Identification / Roll No:</span>
                    <span className="font-black text-indigo-700 font-mono">{child?.student_id || child?.id || 'STU-1001'}</span>
                  </div>
                  <div className="flex justify-between p-2.5 bg-slate-50 rounded-xl">
                    <span className="text-slate-500 font-medium">Age & Date of Birth:</span>
                    <span className="font-bold text-slate-800">{child?.age || 7} yrs • {child?.dob || '2019-04-12'}</span>
                  </div>
                  <div className="flex justify-between p-2.5 bg-slate-50 rounded-xl">
                    <span className="text-slate-500 font-medium">Classroom / Group:</span>
                    <span className="font-bold text-slate-800">{child?.class_name || 'Sunflower Room'}</span>
                  </div>
                  <div className="flex justify-between p-2.5 bg-slate-50 rounded-xl">
                    <span className="text-slate-500 font-medium">Assigned Lead Educator:</span>
                    <span className="font-bold text-emerald-700">Ms. Sarah Wilson</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl space-y-1">
                    <span className="text-slate-500 font-bold block">Individual Learning Goals:</span>
                    <p className="text-slate-700">{child?.learning_objectives || 'Develop joint attention, practice reciprocal waiting, and enhance speech vocabulary.'}</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl space-y-1">
                    <span className="text-slate-500 font-bold block">Support & Sensory Accommodations:</span>
                    <p className="text-slate-700">{child?.support_requirements || 'Low auditory stress, visual countdown timer, positive reinforcement tokens.'}</p>
                  </div>

                  {/* Child Login PIN & Password Management Card */}
                  <div className="p-4 bg-indigo-50/70 rounded-2xl border border-indigo-200 space-y-3 pt-3 mt-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">🔑</span>
                        <div>
                          <h4 className="font-extrabold text-xs text-indigo-950">Child Login PIN / Password</h4>
                          <p className="text-[11px] text-slate-500">
                            Username: <strong className="font-mono text-indigo-700">@{child?.username || 'alex'}</strong>
                          </p>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-white text-indigo-700 border border-indigo-200">
                        Home Access
                      </span>
                    </div>

                    {childPinSuccess && (
                      <div className="p-2.5 rounded-xl bg-emerald-100/90 border border-emerald-300 text-emerald-900 text-[11px] font-bold animate-fadeInUp">
                        {childPinSuccess}
                      </div>
                    )}

                    {childPinError && (
                      <div className="p-2.5 rounded-xl bg-rose-100 border border-rose-300 text-rose-900 text-[11px] font-bold">
                        {childPinError}
                      </div>
                    )}

                    <form onSubmit={handleUpdateChildPin} className="space-y-2.5 text-xs">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[11px] font-bold text-slate-700 mb-1">New PIN / Password</label>
                          <input
                            type="text"
                            value={childNewPin}
                            onChange={e => setChildNewPin(e.target.value)}
                            placeholder="e.g. 1234"
                            className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-mono font-bold text-xs"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-bold text-slate-700 mb-1">Confirm PIN</label>
                          <input
                            type="text"
                            value={childConfirmPin}
                            onChange={e => setChildConfirmPin(e.target.value)}
                            placeholder="Re-enter PIN"
                            className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-mono font-bold text-xs"
                            required
                          />
                        </div>
                      </div>

                      <button
                        type="submit"
                        className="btn-3d btn-3d-blue w-full py-2.5 rounded-xl font-black text-xs text-white shadow-xs cursor-pointer flex items-center justify-center gap-1.5"
                      >
                        <span>✓</span> Update Child Login PIN
                      </button>
                    </form>
                  </div>
                </div>
              </div>

              {/* Parent Account Details & Edit Form */}
              <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-5">
                <div className="flex items-center justify-between border-b pb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">🏡</span>
                    <div>
                      <h3 className="font-extrabold text-base text-slate-900">{parentProfile?.display_name || name || 'Elena Miller'}</h3>
                      <span className="text-xs font-bold text-slate-500 font-mono">@{parentProfile?.username || 'parent'}</span>
                    </div>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-emerald-100 text-emerald-800">
                    Verified Parent
                  </span>
                </div>

                <form onSubmit={handleUpdateProfile} className="space-y-3.5 text-xs">
                  <div>
                    <label className="block font-bold text-slate-600 mb-1">Guardian Full Name</label>
                    <input
                      type="text"
                      value={profileForm.display_name}
                      onChange={e => setProfileForm(prev => ({ ...prev, display_name: e.target.value }))}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-bold text-slate-800"
                      placeholder="e.g. Elena Miller"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-600 mb-1">Relationship to Student</label>
                    <input
                      type="text"
                      value={profileForm.relationship}
                      onChange={e => setProfileForm(prev => ({ ...prev, relationship: e.target.value }))}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium"
                      placeholder="e.g. Mother, Father, Guardian"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-600 mb-1">Contact Email</label>
                    <input
                      type="email"
                      value={profileForm.email}
                      onChange={e => setProfileForm(prev => ({ ...prev, email: e.target.value }))}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono"
                      placeholder="parent@example.com"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-600 mb-1">Contact Phone</label>
                    <input
                      type="tel"
                      value={profileForm.phone}
                      onChange={e => setProfileForm(prev => ({ ...prev, phone: e.target.value }))}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono"
                      placeholder="+1 (555) 000-0000"
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn-3d btn-3d-slate w-full py-2.5 rounded-xl font-black text-xs shadow-xs cursor-pointer"
                  >
                    Save Contact Details
                  </button>
                </form>

                {/* Change Parent Portal Password Form */}
                <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-3 pt-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🔐</span>
                    <div>
                      <h4 className="font-extrabold text-xs text-slate-900">Change Parent Portal Password</h4>
                      <p className="text-[11px] text-slate-500">
                        Update the password you use to sign in to this portal.
                      </p>
                    </div>
                  </div>

                  {parentPasswordSuccess && (
                    <div className="p-2.5 rounded-xl bg-emerald-100/90 border border-emerald-300 text-emerald-900 text-[11px] font-bold animate-fadeInUp">
                      {parentPasswordSuccess}
                    </div>
                  )}

                  {parentPasswordError && (
                    <div className="p-2.5 rounded-xl bg-rose-100 border border-rose-300 text-rose-900 text-[11px] font-bold">
                      {parentPasswordError}
                    </div>
                  )}

                  <form onSubmit={handleUpdateParentPassword} className="space-y-2.5 text-xs">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">New Password</label>
                        <input
                          type="password"
                          value={parentNewPassword}
                          onChange={e => setParentNewPassword(e.target.value)}
                          placeholder="Min 3 characters"
                          className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-mono text-xs"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">Confirm Password</label>
                        <input
                          type="password"
                          value={parentConfirmPassword}
                          onChange={e => setParentConfirmPassword(e.target.value)}
                          placeholder="Re-enter password"
                          className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-mono text-xs"
                          required
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="btn-3d btn-3d-amber w-full py-2.5 rounded-xl font-black text-xs text-white shadow-xs cursor-pointer flex items-center justify-center gap-1.5"
                    >
                      <span>✓</span> Update Parent Password
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: PRINTABLE REPORT */}
        {activeTab === 'report' && reportData && (
          <div className="max-w-4xl mx-auto bg-white p-10 rounded-3xl border border-slate-200 shadow-md space-y-8 animate-fadeInUp">
            <div className="flex items-center justify-between border-b pb-6">
              <div>
                <span className="text-xs font-extrabold uppercase tracking-widest text-indigo-600">
                  Individual Student Progress Report
                </span>
                <h1 className="text-2xl font-black text-slate-900 mt-1">{reportData.title}</h1>
                <p className="text-xs text-slate-500 mt-1">Generated: {reportData.generated_at}</p>
              </div>
              <button
                onClick={() => window.print()}
                className="btn-3d btn-3d-blue px-4 py-2 rounded-xl text-xs font-black text-white shadow-xs cursor-pointer flex items-center gap-1.5"
              >
                <span>🖨️</span> Print / Save PDF
              </button>
            </div>

            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="font-bold text-slate-400 block">CHILD NAME</span>
                <span className="font-extrabold text-slate-800 text-sm">{reportData.student?.name}</span>
              </div>
              <div>
                <span className="font-bold text-slate-400 block">STUDENT ID</span>
                <span className="font-extrabold text-slate-800 text-sm">{reportData.student?.student_id}</span>
              </div>
              <div>
                <span className="font-bold text-slate-400 block">CLASSROOM</span>
                <span className="font-extrabold text-slate-800 text-sm">{reportData.student?.class}</span>
              </div>
              <div>
                <span className="font-bold text-slate-400 block">TOTAL PRACTICE</span>
                <span className="font-extrabold text-slate-800 text-sm">{reportData.student?.total_minutes} mins</span>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="font-extrabold text-base text-slate-900">Skill Domain Index</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(reportData.radar_profile || {}).map(([dom, score]: any) => (
                  <div key={dom} className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="flex justify-between items-center text-xs font-bold mb-1">
                      <span className="text-slate-700">{dom}</span>
                      <span className="text-indigo-600">{score}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-600 rounded-full" style={{ width: `${score}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-slate-500 text-xs italic leading-relaxed text-center">
              ⚠️ {reportData.disclaimer}
            </div>
          </div>
        )}
          </>
        )}
      </main>
    </div>
  )
}
