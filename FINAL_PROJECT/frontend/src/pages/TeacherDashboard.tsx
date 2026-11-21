import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { SkeletonStatsGrid, SkeletonCurriculum, SkeletonProfile360 } from '../components/SkeletonLoader'
import {
  apiTeacherDashboard,
  apiTeacherStudents,
  apiStudentDetail,
  apiCreateStudent,
  apiTeacherClasses,
  apiCreateClass,
  apiGetParents,
  apiCreateParent,
  apiAddTeacherObservation,
  apiGetRecommendations,
  apiTriggerRecommendation,
  apiApproveRecommendation,
  apiRejectRecommendation,
  apiGetMessages,
  apiSendMessage,
  apiCreateAssignment,
  apiDeleteAssignment,
  apiUnassignGame,
  apiUpdateAssignmentDifficulty,
  apiReorderAssignments,
  apiBulkAssignStudent,
  apiBulkAssignClass,
  apiClearPendingAssignments,
  apiGetStudentAssignments,
  apiGetStudentReport,
  apiGetCredentials,
  apiUpdateTeacherPassword,
  apiUpdateStudentPassword,
  apiUpdateParentPasswordByTeacher,
  apiUpdateStudent,
  apiUpdateParentByTeacher
} from '../api/client'
import { GAME_CATALOGUE, getGameById, LEVEL_INFO } from '../data/games'

const DEFAULT_STUDENTS = [
  {
    id: 'STU-1001',
    user_id: 'usr-student-01',
    full_name: 'Alex Miller',
    dob: '2019-04-12',
    age: 7,
    class_id: 'cls-sunflower',
    class_name: 'Sunflower Room (Early Primary)',
    learning_objectives: 'Develop joint attention, practice reciprocal waiting during turn-taking, expand expressive vocabulary in school settings.',
    interests: 'Trains, Space, Dinosaurs, Bubbles',
    preferred_activities: 'Bubble Hunt, Talk & Build, Shopping Adventure',
    support_requirements: 'Responds best to visual timers and gentle auditory chimes; avoid sudden loud buzzer sounds.',
    avatar: 'boy-1',
    status: 'active',
    attention_focus: 0.74,
    motor_skills: 0.81,
    communication_language: 0.70,
    emotion_recognition: 0.73,
    social_interaction: 0.68,
    daily_living: 0.93,
    confidence_score: 0.95,
    sessions_count: 15,
    parent_id: 'parent-user',
    parent_name: 'Elena Miller (Parent)',
    parent_username: 'parent',
    parent_email: 'elena.miller@example.com',
    parent_phone: '+1 (555) 234-5678',
    parent_relationship: 'Mother',
  },
  {
    id: 'STU-1002',
    user_id: 'usr-student-02',
    full_name: 'Maya Lin',
    dob: '2018-09-20',
    age: 8,
    class_id: 'cls-sunflower',
    class_name: 'Sunflower Room (Early Primary)',
    learning_objectives: 'Enhance fine-motor precision, practice facial expression recognition, and school routine transition steps.',
    interests: 'Animals, Drawing, Music, Supermarket',
    preferred_activities: 'Emotion Mirror, Pattern Trail, Community Travel',
    support_requirements: 'Prefers larger buttons and clear high-contrast visual cues.',
    avatar: 'girl-1',
    status: 'active',
    attention_focus: 0.68,
    motor_skills: 0.72,
    communication_language: 0.65,
    emotion_recognition: 0.78,
    social_interaction: 0.70,
    daily_living: 0.82,
    confidence_score: 0.88,
    sessions_count: 12,
    parent_id: 'usr-parent-1ae3d9',
    parent_name: 'David Lin',
    parent_username: 'david_parent',
    parent_email: 'david.lin@example.com',
    parent_phone: '+1 (555) 876-5432',
    parent_relationship: 'Father',
  }
]

const DEFAULT_PARENTS = [
  {
    id: 'parent-user',
    username: 'parent',
    full_name: 'Elena Miller (Parent)',
    role: 'parent',
    email: 'elena.miller@example.com',
    phone: '+1 (555) 234-5678',
    student_id: 'STU-1001',
    student_name: 'Alex Miller',
    relationship: 'Mother',
  },
  {
    id: 'usr-parent-1ae3d9',
    username: 'david_parent',
    full_name: 'David Lin',
    role: 'parent',
    email: 'david.lin@example.com',
    phone: '+1 (555) 876-5432',
    student_id: 'STU-1002',
    student_name: 'Maya Lin',
    relationship: 'Father',
  }
]

export const GAME_ENHANCED_META: Record<string, { domain: string; domainIcon: string; shortDesc: string; skillTarget: string }> = {
  'bubble-hunt': {
    domain: 'Motor Skills & Coordination',
    domainIcon: '🎯',
    shortDesc: 'Pop bubbles using hand-pinch gestures to develop fine motor control and visual focus.',
    skillTarget: 'Finger pinch accuracy, hand-eye coordination & visual tracking',
  },
  'follow-the-star': {
    domain: 'Attention & Focus',
    domainIcon: '🧠',
    shortDesc: 'Move your head to track moving star targets and sustain visual focus in smooth pursuit.',
    skillTarget: 'Vestibular control, smooth visual pursuit & head-pose tracking',
  },
  'pattern-trail': {
    domain: 'Motor Skills & Coordination',
    domainIcon: '✏️',
    shortDesc: 'Trace letter, number, and shape outlines with your fingertip to build motor planning.',
    skillTarget: 'Fingertip tracking, fine motor path planning & dexterity',
  },
  'emotion-mirror': {
    domain: 'Emotion Recognition',
    domainIcon: '🎭',
    shortDesc: 'Recognize and mimic facial expressions (happy, surprised, calm) in real-time camera feedback.',
    skillTarget: 'Facial affect recognition, imitation & emotion labeling',
  },
  'body-says-it': {
    domain: 'Emotion & Social Awareness',
    domainIcon: '🧍',
    shortDesc: 'Interpret non-verbal emotions and intent from body language postures and animated gestures.',
    skillTarget: 'Body language reading, postural cues & non-verbal inference',
  },
  'object-quest': {
    domain: 'Attention & Visual Naming',
    domainIcon: '🔍',
    shortDesc: 'Hold real everyday objects up to the camera for AI detection, matching, and categorization.',
    skillTarget: 'Real-world object recognition, functional categorization & visual scanning',
  },
  'talk-and-build': {
    domain: 'Communication & Speech',
    domainIcon: '🗣️',
    shortDesc: 'Answer scene comprehension questions using spoken voice or candy choice buttons.',
    skillTarget: 'Expressive sentence building, verbal responses & auditory comprehension',
  },
  'describe-the-scene': {
    domain: 'Expressive Communication',
    domainIcon: '🎬',
    shortDesc: 'Watch lively video events and narrate what is happening in full descriptive sentences.',
    skillTarget: 'Narrative storytelling, spoken vocabulary & syntactic complexity',
  },
  'object-quest-see-say': {
    domain: 'Speech & Rapid Naming',
    domainIcon: '🗣️',
    shortDesc: 'Inspect high-definition objects on screen and speak their names aloud into the microphone.',
    skillTarget: 'Rapid confrontation naming, phonological retrieval & speech clarity',
  },
  'look-point-share': {
    domain: 'Social Interaction',
    domainIcon: '🤝',
    shortDesc: 'Follow gaze cues and point to target animals to practice joint attention and gaze sharing.',
    skillTarget: 'Joint attention, referential pointing & shared visual engagement',
  },
  'my-turn-your-turn': {
    domain: 'Reciprocal Interaction',
    domainIcon: '🔄',
    shortDesc: 'Practice patience and impulse control by waiting on red cues and raising hand on green cues.',
    skillTarget: 'Turn-taking, impulse regulation & reciprocal waiting',
  },
  'copy-my-move': {
    domain: 'Motor & Social Imitation',
    domainIcon: '🤹',
    shortDesc: 'Mirror full-body postures and arm movements demonstrated by animated instructor avatars.',
    skillTarget: 'Gross motor mimicry, bilateral coordination & body spatial awareness',
  },
  'school-day-simulator': {
    domain: 'Daily Living & School Routines',
    domainIcon: '🏫',
    shortDesc: 'Navigate a 3D school campus, attend classrooms, and practice peer greetings and transitions.',
    skillTarget: 'Classroom routine adaptation, school transitions & social rules',
  },
  'community-travel-simulator': {
    domain: 'Daily Living & Community Navigation',
    domainIcon: '🚌',
    shortDesc: 'Explore a 3D community, wait at the bus stop, board transit, and pay bus fare safely.',
    skillTarget: 'Public transit independence, route navigation & community safety',
  },
  'shopping-adventure': {
    domain: 'Daily Living & Functional Skills',
    domainIcon: '🛒',
    shortDesc: 'Explore a 3D supermarket, find grocery items from a list, and interact with the cashier.',
    skillTarget: 'Task sequencing, checklist following & monetary exchange',
  },
}

type TabType = 'overview' | 'ranking' | 'curriculum' | 'students' | 'parents' | 'security' | 'observations' | 'messages' | 'report'

export default function TeacherDashboard() {
  const { name, logout } = useAuthStore()
  const navigate = useNavigate()

  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [students, setStudents] = useState<any[]>(DEFAULT_STUDENTS)
  const [classes, setClasses] = useState<any[]>([])
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [selectedStudentId, setSelectedStudentId] = useState<string>('STU-1001')
  const [selectedStudentDetail, setSelectedStudentDetail] = useState<any>(null)
  const [reportData, setReportData] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)

  // Dedicated Curriculum & Assignment Management State
  const [curriculumStudentId, setCurriculumStudentId] = useState<string>('STU-1001')
  const [curriculumAssignments, setCurriculumAssignments] = useState<any[]>([])
  const [applyToAllClass, setApplyToAllClass] = useState<boolean>(false)
  const [curriculumSuccessMsg, setCurriculumSuccessMsg] = useState<string | null>(null)
  const [selectedLevelFilter, setSelectedLevelFilter] = useState<number | 'all'>('all')
  const [assigningGameId, setAssigningGameId] = useState<string | null>(null)

  // RL Recommendation Interactive State
  const [rlLoadingStudentId, setRlLoadingStudentId] = useState<string | null>(null)
  const [latestRlRecommendation, setLatestRlRecommendation] = useState<any>(null)
  const [rlBannerDismissed, setRlBannerDismissed] = useState<boolean>(false)
  const [rlActionToast, setRlActionToast] = useState<string | null>(null)

  // Credentials & Security State
  const [credentialsData, setCredentialsData] = useState<any>(null)
  const [editingStudentPinId, setEditingStudentPinId] = useState<string | null>(null)
  const [newStudentPinValue, setNewStudentPinValue] = useState<string>('')
  const [editingParentPwId, setEditingParentPwId] = useState<string | null>(null)
  const [newParentPwValue, setNewParentPwValue] = useState<string>('')
  const [teacherCurrentPw, setTeacherCurrentPw] = useState<string>('')
  const [teacherNewPw, setTeacherNewPw] = useState<string>('')
  const [teacherConfirmPw, setTeacherConfirmPw] = useState<string>('')
  const [securityToast, setSecurityToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Modals & Form states
  const [showAddStudentModal, setShowAddStudentModal] = useState<boolean>(false)
  const [showAddClassModal, setShowAddClassModal] = useState<boolean>(false)
  const [showAddParentModal, setShowAddParentModal] = useState<boolean>(false)
  const [parents, setParents] = useState<any[]>(DEFAULT_PARENTS)
  const [newClassName, setNewClassName] = useState('')
  const [newClassDesc, setNewClassDesc] = useState('')
  const [newParentForm, setNewParentForm] = useState({
    full_name: '',
    username: '',
    password: 'parent123',
    student_id: 'STU-1001',
    relationship: 'Mother / Primary Caregiver',
    email: '',
    phone: '',
  })
  const [newStudentForm, setNewStudentForm] = useState({
    full_name: '',
    username: '',
    password: '1234',
    age: 7,
    class_id: 'cls-sunflower',
    learning_objectives: '',
    interests: '',
    preferred_activities: '',
    support_requirements: '',
    avatar: 'boy-1',
  })

  // Edit Student Profile Modal State
  const [showEditStudentModal, setShowEditStudentModal] = useState<boolean>(false)
  const [editStudentForm, setEditStudentForm] = useState<{
    id: string
    full_name: string
    username: string
    dob: string
    age: number
    class_id: string
    avatar: string
    status: string
    learning_objectives: string
    interests: string
    preferred_activities: string
    support_requirements: string
  }>({
    id: '',
    full_name: '',
    username: '',
    dob: '',
    age: 7,
    class_id: 'cls-sunflower',
    avatar: 'boy-1',
    status: 'active',
    learning_objectives: '',
    interests: '',
    preferred_activities: '',
    support_requirements: '',
  })
  const [editStudentSaving, setEditStudentSaving] = useState<boolean>(false)
  const [editStudentError, setEditStudentError] = useState<string | null>(null)
  const [editStudentSuccess, setEditStudentSuccess] = useState<string | null>(null)

  // Edit Parent Details Modal State
  const [showEditParentModal, setShowEditParentModal] = useState<boolean>(false)
  const [showIepModal, setShowIepModal] = useState<boolean>(false)
  const [editParentForm, setEditParentForm] = useState<{
    id: string
    display_name: string
    username: string
    email: string
    phone: string
    relationship: string
    student_id: string
  }>({
    id: '',
    display_name: '',
    username: '',
    email: '',
    phone: '',
    relationship: '',
    student_id: '',
  })
  const [editParentSaving, setEditParentSaving] = useState<boolean>(false)
  const [editParentError, setEditParentError] = useState<string | null>(null)
  const [editParentSuccess, setEditParentSuccess] = useState<string | null>(null)

  // Observation form
  const [obsForm, setObsForm] = useState({
    student_id: 'STU-1001',
    attention_rating: 4,
    emotional_regulation: 4,
    peer_interaction: 3,
    motor_skills: 4,
    triggers_observed: '',
    strategies_used: '',
    notes: '',
  })
  const [obsSavedMessage, setObsSavedMessage] = useState<string | null>(null)

  // Messaging state
  const [messages, setMessages] = useState<any[]>([])
  const [newMessageText, setNewMessageText] = useState<string>('')

  // Assign Game form
  const [assignGameId, setAssignGameId] = useState<string>('bubble-hunt')
  const [assignDifficulty, setAssignDifficulty] = useState<string>('easy')

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  // Load Initial Dashboard Data
  const loadDashboard = async () => {
    try {
      setLoading(true)
      const results = await Promise.allSettled([
        apiTeacherDashboard(),
        apiTeacherStudents(),
        apiTeacherClasses(),
        apiGetRecommendations(undefined, 'pending_approval'),
        apiGetParents(),
      ])

      const dash = results[0].status === 'fulfilled' ? results[0].value : null
      const stuList = results[1].status === 'fulfilled' && Array.isArray(results[1].value) && results[1].value.length > 0 ? results[1].value : null
      const clsList = results[2].status === 'fulfilled' && Array.isArray(results[2].value) && results[2].value.length > 0 ? results[2].value : null
      const recList = results[3].status === 'fulfilled' && Array.isArray(results[3].value) ? results[3].value : []
      const parList = results[4].status === 'fulfilled' && Array.isArray(results[4].value) && results[4].value.length > 0 ? results[4].value : null

      if (dash) setDashboardData(dash)
      if (stuList) {
        setStudents(stuList)
        loadStudentDetail(stuList[0].id)
      } else {
        loadStudentDetail('STU-1001')
      }
      if (clsList) setClasses(clsList)
      if (recList) setRecommendations(recList)
      if (parList) setParents(parList)

      await loadCurriculumAssignments(curriculumStudentId)
      await loadCredentials()
    } catch (err) {
      console.error('Error loading teacher dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadCredentials = async () => {
    try {
      const data = await apiGetCredentials()
      setCredentialsData(data)
    } catch (err) {
      console.error('Error loading credentials:', err)
    }
  }

  const handleUpdateTeacherPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!teacherNewPw || teacherNewPw.length < 3) {
      setSecurityToast({ type: 'error', message: 'New password must be at least 3 characters long.' })
      return
    }
    if (teacherNewPw !== teacherConfirmPw) {
      setSecurityToast({ type: 'error', message: 'Passwords do not match.' })
      return
    }
    try {
      await apiUpdateTeacherPassword(teacherNewPw, teacherCurrentPw || undefined)
      setSecurityToast({ type: 'success', message: '✓ Teacher master password updated successfully!' })
      setTeacherCurrentPw('')
      setTeacherNewPw('')
      setTeacherConfirmPw('')
      await loadCredentials()
      setTimeout(() => setSecurityToast(null), 5000)
    } catch (err: any) {
      setSecurityToast({ type: 'error', message: err?.message || 'Failed to update teacher password' })
    }
  }

  const handleSaveStudentPin = async (studentId: string) => {
    if (!newStudentPinValue || newStudentPinValue.length < 2) {
      setSecurityToast({ type: 'error', message: 'PIN/Password must be at least 2 characters long.' })
      return
    }
    try {
      const res = await apiUpdateStudentPassword(studentId, newStudentPinValue)
      setSecurityToast({ type: 'success', message: `✓ ${res.message}` })
      setEditingStudentPinId(null)
      setNewStudentPinValue('')
      await loadCredentials()
      await loadDashboard()
      setTimeout(() => setSecurityToast(null), 5000)
    } catch (err: any) {
      setSecurityToast({ type: 'error', message: err?.message || 'Failed to update student PIN' })
    }
  }

  const handleSaveParentPassword = async (parentId: string) => {
    if (!newParentPwValue || newParentPwValue.length < 3) {
      setSecurityToast({ type: 'error', message: 'Password must be at least 3 characters long.' })
      return
    }
    try {
      const res = await apiUpdateParentPasswordByTeacher(parentId, newParentPwValue)
      setSecurityToast({ type: 'success', message: `✓ ${res.message}` })
      setEditingParentPwId(null)
      setNewParentPwValue('')
      await loadCredentials()
      await loadDashboard()
      setTimeout(() => setSecurityToast(null), 5000)
    } catch (err: any) {
      setSecurityToast({ type: 'error', message: err?.message || 'Failed to update parent password' })
    }
  }

  const loadCurriculumAssignments = async (studentId: string = curriculumStudentId) => {
    try {
      const asgs = await apiGetStudentAssignments(studentId)
      if (Array.isArray(asgs)) {
        setCurriculumAssignments(asgs)
      }
    } catch (err) {
      console.error('Error loading curriculum assignments:', err)
    }
  }

  const handleAssignGameToCurriculum = async (gameId: string, difficulty: string = 'easy') => {
    try {
      setAssigningGameId(gameId)
      const game = getGameById(gameId)
      if (applyToAllClass) {
        await apiCreateAssignment({
          student_id: 'STU-1001',
          game_id: gameId,
          difficulty,
          sequence_order: 0,
        })
        await apiCreateAssignment({
          student_id: 'STU-1002',
          game_id: gameId,
          difficulty,
          sequence_order: 0,
        })
        setCurriculumSuccessMsg(`✓ Assigned "${game?.name || gameId}" (${difficulty.toUpperCase()}) to ALL students in Sunflower Room!`)
      } else {
        await apiCreateAssignment({
          student_id: curriculumStudentId,
          game_id: gameId,
          difficulty,
          sequence_order: 0,
        })
        const stu = students.find(s => s.id === curriculumStudentId)
        setCurriculumSuccessMsg(`✓ Assigned "${game?.name || gameId}" (${difficulty.toUpperCase()}) to ${stu?.full_name || curriculumStudentId}!`)
      }
      await loadCurriculumAssignments(curriculumStudentId)
      await loadDashboard()
      setTimeout(() => setCurriculumSuccessMsg(null), 4000)
    } catch (err) {
      console.error('Error assigning game:', err)
    } finally {
      setAssigningGameId(null)
    }
  }

  const handleUnassignGameFromCurriculum = async (gameId: string, assignmentId?: string) => {
    try {
      const game = getGameById(gameId)
      if (applyToAllClass) {
        await apiUnassignGame('STU-1001', gameId)
        await apiUnassignGame('STU-1002', gameId)
        setCurriculumSuccessMsg(`✕ Removed "${game?.name || gameId}" from all students in Sunflower Room!`)
      } else {
        if (assignmentId) {
          await apiDeleteAssignment(assignmentId)
        } else {
          await apiUnassignGame(curriculumStudentId, gameId)
        }
        const stu = students.find(s => s.id === curriculumStudentId)
        setCurriculumSuccessMsg(`✕ Removed "${game?.name || gameId}" from ${stu?.full_name || curriculumStudentId}!`)
      }
      await loadCurriculumAssignments(curriculumStudentId)
      await loadDashboard()
      setTimeout(() => setCurriculumSuccessMsg(null), 4000)
    } catch (err) {
      console.error('Error unassigning game:', err)
    }
  }

  const handleUpdateDifficulty = async (assignmentId: string, difficulty: string) => {
    try {
      await apiUpdateAssignmentDifficulty(assignmentId, difficulty)
      await loadCurriculumAssignments(curriculumStudentId)
      setCurriculumSuccessMsg(`✓ Difficulty updated to ${difficulty.toUpperCase()}`)
      setTimeout(() => setCurriculumSuccessMsg(null), 3000)
    } catch (err) {
      console.error('Error updating difficulty:', err)
    }
  }

  const handleMoveAssignment = async (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1
    if (targetIndex < 0 || targetIndex >= curriculumAssignments.length) return
    const reordered = [...curriculumAssignments]
    const temp = reordered[index]
    reordered[index] = reordered[targetIndex]
    reordered[targetIndex] = temp
    setCurriculumAssignments(reordered)
    try {
      const assignmentIds = reordered.map(a => a.id)
      await apiReorderAssignments(curriculumStudentId, assignmentIds)
      await loadCurriculumAssignments(curriculumStudentId)
    } catch (err) {
      console.error('Error reordering assignments:', err)
    }
  }

  const handleLoadRecommendedSequence = async () => {
    const recommended = [
      { game_id: 'bubble-hunt', difficulty: 'easy' },
      { game_id: 'emotion-mirror', difficulty: 'easy' },
      { game_id: 'talk-and-build', difficulty: 'medium' },
      { game_id: 'look-point-share', difficulty: 'medium' },
      { game_id: 'school-day-simulator', difficulty: 'medium' },
    ]
    try {
      if (applyToAllClass) {
        await apiBulkAssignClass('cls-sunflower', recommended)
        setCurriculumSuccessMsg('⭐ Loaded 5-Level Adaptive Sequence for ALL students in Sunflower Room!')
      } else {
        await apiBulkAssignStudent(curriculumStudentId, recommended)
        const stu = students.find(s => s.id === curriculumStudentId)
        setCurriculumSuccessMsg(`⭐ Loaded 5-Level Adaptive Sequence for ${stu?.full_name || curriculumStudentId}!`)
      }
      await loadCurriculumAssignments(curriculumStudentId)
      await loadDashboard()
      setTimeout(() => setCurriculumSuccessMsg(null), 4000)
    } catch (err) {
      console.error('Error loading recommended sequence:', err)
    }
  }

  const handleClearPending = async () => {
    try {
      if (applyToAllClass) {
        await apiClearPendingAssignments('STU-1001')
        await apiClearPendingAssignments('STU-1002')
        setCurriculumSuccessMsg('✕ Cleared pending uncompleted assignments for all students in class!')
      } else {
        await apiClearPendingAssignments(curriculumStudentId)
        const stu = students.find(s => s.id === curriculumStudentId)
        setCurriculumSuccessMsg(`✕ Cleared pending assignments for ${stu?.full_name || curriculumStudentId}!`)
      }
      await loadCurriculumAssignments(curriculumStudentId)
      await loadDashboard()
      setTimeout(() => setCurriculumSuccessMsg(null), 4000)
    } catch (err) {
      console.error('Error clearing pending assignments:', err)
    }
  }

  const handleSyncClassroom = async () => {
    try {
      const toSync = curriculumAssignments.map(a => ({ game_id: a.game_id, difficulty: a.difficulty }))
      await apiBulkAssignClass('cls-sunflower', toSync)
      setCurriculumSuccessMsg('👥 Synced active curriculum sequence across all students in Sunflower Room!')
      setTimeout(() => setCurriculumSuccessMsg(null), 4000)
    } catch (err) {
      console.error('Error syncing class assignments:', err)
    }
  }

  const handleToggleGame = async (gameId: string, currentAssigned: boolean, assignmentId?: string) => {
    if (currentAssigned) {
      await handleUnassignGameFromCurriculum(gameId, assignmentId)
    } else {
      const selectEl = document.getElementById(`diff-select-${gameId}`) as HTMLSelectElement
      const diff = selectEl ? selectEl.value : 'easy'
      await handleAssignGameToCurriculum(gameId, diff)
    }
  }

  const handleSelectAllInLevel = async (lvl: number) => {
    const levelGames = GAME_CATALOGUE.filter(g => g.level === lvl)
    const unassigned = levelGames.filter(g => !curriculumAssignments.some(a => a.game_id === g.id))
    if (unassigned.length === 0) return
    try {
      for (const g of unassigned) {
        if (applyToAllClass) {
          await apiCreateAssignment({ student_id: 'STU-1001', game_id: g.id, difficulty: 'easy', sequence_order: 0 })
          await apiCreateAssignment({ student_id: 'STU-1002', game_id: g.id, difficulty: 'easy', sequence_order: 0 })
        } else {
          await apiCreateAssignment({ student_id: curriculumStudentId, game_id: g.id, difficulty: 'easy', sequence_order: 0 })
        }
      }
      setCurriculumSuccessMsg(`✓ Selected and assigned all Level ${lvl} games!`)
      await loadCurriculumAssignments(curriculumStudentId)
      await loadDashboard()
      setTimeout(() => setCurriculumSuccessMsg(null), 3000)
    } catch (err) {
      console.error('Error selecting all games in level:', err)
    }
  }

  const handleUnselectAllInLevel = async (lvl: number) => {
    const levelGames = GAME_CATALOGUE.filter(g => g.level === lvl)
    const assigned = curriculumAssignments.filter(a => levelGames.some(g => g.id === a.game_id))
    if (assigned.length === 0) return
    try {
      for (const a of assigned) {
        if (applyToAllClass) {
          await apiUnassignGame('STU-1001', a.game_id)
          await apiUnassignGame('STU-1002', a.game_id)
        } else {
          await apiDeleteAssignment(a.id)
        }
      }
      setCurriculumSuccessMsg(`✕ Unselected all Level ${lvl} games!`)
      await loadCurriculumAssignments(curriculumStudentId)
      await loadDashboard()
      setTimeout(() => setCurriculumSuccessMsg(null), 3000)
    } catch (err) {
      console.error('Error unselecting games in level:', err)
    }
  }

  const handleTriggerRecommendation = async (studentId: string) => {
    try {
      setRlLoadingStudentId(studentId)
      setRlBannerDismissed(false)
      const res = await apiTriggerRecommendation(studentId)
      if (res?.recommendation) {
        setLatestRlRecommendation(res.recommendation)
      }
      setRlActionToast('⚡ Contextual Bandit generated fresh recommendation based on 6-domain profile, IEP goals, and parent reviews!')
      setTimeout(() => setRlActionToast(null), 5000)
      await loadDashboard()
      await loadStudentDetail(studentId)
      await loadCurriculumAssignments(studentId)
    } catch (err) {
      console.error('Error triggering recommendation:', err)
    } finally {
      setRlLoadingStudentId(null)
    }
  }

  const loadStudentDetail = async (studentId: string) => {
    setSelectedStudentId(studentId)
    try {
      const detail = await apiStudentDetail(studentId)
      setSelectedStudentDetail(detail)
      setObsForm(prev => ({ ...prev, student_id: studentId }))
      loadMessages(studentId)
    } catch (err) {
      console.error('Error loading student detail:', err)
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
      console.error('Error generating report:', err)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  // Approve AI Recommendation (with optional modification)
  const handleApproveRecommendation = async (recId: string, modifiedGameId?: string, modifiedDifficulty?: string) => {
    try {
      const payload: any = {
        teacher_notes: modifiedGameId
          ? `Educator approved alternative activity: ${modifiedGameId}`
          : 'Approved by educator for next quest step.',
      }
      if (modifiedGameId) payload.modified_game_id = modifiedGameId
      if (modifiedDifficulty) payload.modified_difficulty = modifiedDifficulty

      await apiApproveRecommendation(recId, payload)
      setLatestRlRecommendation(null)
      setRlActionToast('✓ Successfully approved! Added activity to student learning path.')
      setTimeout(() => setRlActionToast(null), 5000)
      await loadDashboard()
      if (selectedStudentId) {
        await loadStudentDetail(selectedStudentId)
        await loadCurriculumAssignments(selectedStudentId)
      }
    } catch (err) {
      console.error('Error approving recommendation:', err)
    }
  }

  // Reject AI Recommendation
  const handleRejectRecommendation = async (recId: string) => {
    try {
      await apiRejectRecommendation(recId, 'Declined for current curriculum focus.')
      setLatestRlRecommendation(null)
      setRlBannerDismissed(true)
      setRlActionToast('✕ Recommendation dismissed.')
      setTimeout(() => setRlActionToast(null), 4000)
      await loadDashboard()
      if (selectedStudentId) {
        await loadStudentDetail(selectedStudentId)
      }
    } catch (err) {
      console.error('Error rejecting recommendation:', err)
    }
  }

  // Submit Observation
  const handleSubmitObservation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!obsForm.notes.trim()) return
    try {
      await apiAddTeacherObservation(obsForm)
      setObsSavedMessage('Classroom observation recorded successfully!')
      setObsForm({
        student_id: selectedStudentId,
        attention_rating: 4,
        emotional_regulation: 4,
        peer_interaction: 3,
        motor_skills: 4,
        triggers_observed: '',
        strategies_used: '',
        notes: '',
      })
      await loadStudentDetail(selectedStudentId)
      await loadDashboard()
      setTimeout(() => setObsSavedMessage(null), 3000)
    } catch (err) {
      console.error('Error submitting observation:', err)
    }
  }

  // Send Message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessageText.trim()) return
    try {
      await apiSendMessage({
        sender_id: 'teacher-user',
        receiver_id: 'parent-user',
        student_id: selectedStudentId,
        content: newMessageText.trim(),
      })
      setNewMessageText('')
      await loadMessages(selectedStudentId)
    } catch (err) {
      console.error('Error sending message:', err)
    }
  }

  // Create Student
  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await apiCreateStudent(newStudentForm)
      setShowAddStudentModal(false)
      setNewStudentForm({
        full_name: '',
        username: '',
        password: '1234',
        age: 7,
        class_id: 'cls-sunflower',
        learning_objectives: '',
        interests: '',
        preferred_activities: '',
        support_requirements: '',
        avatar: 'boy-1',
      })
      await loadDashboard()
    } catch (err) {
      console.error('Error creating student:', err)
    }
  }

  // Create Class
  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newClassName.trim()) return
    try {
      await apiCreateClass({ name: newClassName, description: newClassDesc })
      setShowAddClassModal(false)
      setNewClassName('')
      setNewClassDesc('')
      await loadDashboard()
    } catch (err) {
      console.error('Error creating class:', err)
    }
  }

  // Create Parent Account
  const handleCreateParent = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newParentForm.username.trim() || !newParentForm.full_name.trim()) return
    try {
      await apiCreateParent(newParentForm)
      setShowAddParentModal(false)
      setNewParentForm({
        full_name: '',
        username: '',
        password: 'parent123',
        student_id: selectedStudentId || 'STU-1001',
        relationship: 'Mother / Primary Caregiver',
        email: '',
        phone: '',
      })
      await loadDashboard()
    } catch (err) {
      console.error('Error creating parent:', err)
    }
  }

  // Edit Student Handlers
  const handleOpenEditStudent = (stu: any) => {
    setEditStudentForm({
      id: stu.id,
      full_name: stu.full_name || '',
      username: stu.username || (stu.id === 'STU-1001' ? 'alex' : stu.id === 'STU-1002' ? 'maya' : ''),
      dob: stu.dob || '2019-04-12',
      age: stu.age || 7,
      class_id: stu.class_id || 'cls-sunflower',
      avatar: stu.avatar || 'boy-1',
      status: stu.status || 'active',
      learning_objectives: stu.learning_objectives || '',
      interests: stu.interests || '',
      preferred_activities: stu.preferred_activities || '',
      support_requirements: stu.support_requirements || '',
    })
    setEditStudentError(null)
    setEditStudentSuccess(null)
    setShowEditStudentModal(true)
  }

  const handleSaveStudentEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    setEditStudentSaving(true)
    setEditStudentError(null)
    try {
      await apiUpdateStudent(editStudentForm.id, {
        full_name: editStudentForm.full_name.trim(),
        username: editStudentForm.username.trim().toLowerCase(),
        dob: editStudentForm.dob,
        age: Number(editStudentForm.age),
        class_id: editStudentForm.class_id,
        avatar: editStudentForm.avatar,
        status: editStudentForm.status,
        learning_objectives: editStudentForm.learning_objectives,
        interests: editStudentForm.interests,
        preferred_activities: editStudentForm.preferred_activities,
        support_requirements: editStudentForm.support_requirements,
      })
      setEditStudentSuccess('✓ Student details and credentials saved successfully!')
      await loadDashboard()
      await loadStudentDetail(editStudentForm.id)
      setTimeout(() => {
        setShowEditStudentModal(false)
        setEditStudentSuccess(null)
      }, 1000)
    } catch (err: any) {
      setEditStudentError(err?.message || 'Failed to update student details')
    } finally {
      setEditStudentSaving(false)
    }
  }

  // Edit Parent Handlers
  const handleOpenEditParent = (p: any) => {
    setEditParentForm({
      id: p.id,
      display_name: p.full_name || p.display_name || '',
      username: p.username || '',
      email: p.email || '',
      phone: p.phone || '',
      relationship: p.relationship || 'Parent / Guardian',
      student_id: p.student_id || selectedStudentId || 'STU-1001',
    })
    setEditParentError(null)
    setEditParentSuccess(null)
    setShowEditParentModal(true)
  }

  const handleSaveParentEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    setEditParentSaving(true)
    setEditParentError(null)
    try {
      await apiUpdateParentByTeacher(editParentForm.id, {
        display_name: editParentForm.display_name.trim(),
        username: editParentForm.username.trim().toLowerCase(),
        email: editParentForm.email.trim(),
        phone: editParentForm.phone.trim(),
        relationship: editParentForm.relationship.trim(),
        student_id: editParentForm.student_id,
      })
      setEditParentSuccess('✓ Parent details updated successfully!')
      await loadDashboard()
      if (selectedStudentId) {
        await loadStudentDetail(selectedStudentId)
      }
      setTimeout(() => {
        setShowEditParentModal(false)
        setEditParentSuccess(null)
      }, 1000)
    } catch (err: any) {
      setEditParentError(err?.message || 'Failed to update parent details')
    } finally {
      setEditParentSaving(false)
    }
  }

  // Assign Game
  const handleAssignGame = async () => {
    try {
      await apiCreateAssignment({
        student_id: selectedStudentId,
        game_id: assignGameId,
        sequence_order: (selectedStudentDetail?.assignments?.length || 0) + 1,
        difficulty: assignDifficulty,
        is_unlocked: 1,
      })
      await loadStudentDetail(selectedStudentId)
    } catch (err) {
      console.error('Error assigning game:', err)
    }
  }

  const stats = dashboardData?.stats || {
    total_students: 2,
    total_parents: 1,
    total_classes: 1,
    total_assignments: 5,
    pending_recommendations_count: 1,
    unread_messages_count: 1,
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Top Professional Navigation Bar */}
      <nav className="sticky top-0 z-40 bg-white/90 backdrop-blur-xl border-b border-slate-200/80 shadow-xs">
        <div className="max-w-7xl mx-auto px-6 h-18 flex items-center justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 bg-gradient-to-tr from-emerald-600 to-teal-500 rounded-2xl flex items-center justify-center text-2xl text-white shadow-md shadow-emerald-200">
              👩‍🏫
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-xl text-slate-900 tracking-tight">Educator Console</span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300">
                  Primary Administrator
                </span>
              </div>
              <span className="text-xs text-slate-400 font-semibold hidden sm:block">Clinical & Curricular Orchestration</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="hidden lg:flex items-center gap-1.5 bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200/80 shadow-inner">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                activeTab === 'overview'
                  ? 'btn-3d btn-3d-slate text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              📊 Overview & AI Queue
            </button>
            <button
              onClick={() => setActiveTab('ranking')}
              className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'ranking'
                  ? 'btn-3d btn-3d-slate text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              🏆 Class Ranking & Care
            </button>
            <button
              onClick={() => {
                setActiveTab('curriculum')
                loadCurriculumAssignments(curriculumStudentId)
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'curriculum'
                  ? 'btn-3d btn-3d-slate text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              🎮 Manage & Assign Games
            </button>
            <button
              onClick={() => setActiveTab('students')}
              className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                activeTab === 'students'
                  ? 'btn-3d btn-3d-slate text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              👨‍🎓 Student 360° ({students.length})
            </button>
            <button
              onClick={() => setActiveTab('parents')}
              className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                activeTab === 'parents'
                  ? 'btn-3d btn-3d-slate text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              👪 Parents ({parents.length})
            </button>
            <button
              onClick={() => {
                setActiveTab('security')
                loadCredentials()
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'security'
                  ? 'btn-3d btn-3d-slate text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              🔐 Passwords
            </button>
            <button
              onClick={() => setActiveTab('observations')}
              className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                activeTab === 'observations'
                  ? 'btn-3d btn-3d-slate text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              📝 Observation
            </button>
            <button
              onClick={() => setActiveTab('messages')}
              className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'messages'
                  ? 'btn-3d btn-3d-slate text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              💬 Messages
              {stats.unread_messages_count > 0 && (
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
              )}
            </button>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => loadDashboard()}
              title="Refresh all data"
              className="px-2.5 py-1.5 rounded-lg text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <span>🔄</span> Refresh
            </button>
            <span className="text-xs font-bold text-slate-600 hidden sm:inline">
              👋 {name || 'Ms. Sarah Wilson'}
            </span>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 text-slate-600 hover:bg-rose-50 hover:text-rose-600 transition-colors cursor-pointer border border-slate-200"
            >
              Sign Out
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="space-y-6">
            <SkeletonStatsGrid count={6} />
            <SkeletonCurriculum count={5} />
          </div>
        ) : (
          <>
            {/* TAB 1: OVERVIEW & AI RECOMMENDATIONS QUEUE */}
        {activeTab === 'overview' && (
          <div className="space-y-8 animate-fadeInUp">
            {/* Top Stat Summary Grid */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm">
                <div className="text-xs font-bold text-slate-400 uppercase">Active Students</div>
                <div className="text-2xl font-black text-slate-900 mt-1">{stats.total_students}</div>
                <div className="text-xs font-semibold text-emerald-600 mt-1">100% active</div>
              </div>
              <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm">
                <div className="text-xs font-bold text-slate-400 uppercase">Parents Linked</div>
                <div className="text-2xl font-black text-slate-900 mt-1">{stats.total_parents}</div>
                <div className="text-xs font-semibold text-sky-600 mt-1">Connected</div>
              </div>
              <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm">
                <div className="text-xs font-bold text-slate-400 uppercase">Classrooms</div>
                <div className="text-2xl font-black text-slate-900 mt-1">{stats.total_classes}</div>
                <div className="text-xs font-semibold text-indigo-600 mt-1">Sunflower Room</div>
              </div>
              <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm">
                <div className="text-xs font-bold text-slate-400 uppercase">Quests Completed</div>
                <div className="text-2xl font-black text-slate-900 mt-1">{stats.completed_assignments}</div>
                <div className="text-xs font-semibold text-emerald-600 mt-1">Verified games</div>
              </div>
              <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm border-l-4 border-l-amber-500">
                <div className="text-xs font-bold text-amber-600 uppercase">AI Review Queue</div>
                <div className="text-2xl font-black text-slate-900 mt-1">{recommendations.length}</div>
                <div className="text-xs font-semibold text-amber-600 mt-1">Awaiting approval</div>
              </div>
              <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm">
                <div className="text-xs font-bold text-slate-400 uppercase">Parent Chats</div>
                <div className="text-2xl font-black text-slate-900 mt-1">{messages.length}</div>
                <div className="text-xs font-semibold text-sky-600 mt-1">Direct feedback</div>
              </div>
            </div>

            {/* SECTION: INTERACTIVE STUDENT SELECTION & PROGRESS PRESENTATION */}
            <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-6">
              {/* Header with Title and Student Switcher */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase bg-indigo-100 text-indigo-700 tracking-wide">
                      Student Progress & Performance Dashboard
                    </span>
                    <span className="text-xs font-semibold text-slate-400">
                      Executive Presentation View
                    </span>
                  </div>
                  <h2 className="text-xl font-black text-slate-900 mt-1 flex items-center gap-2">
                    <span>📈</span> Individual Growth Trajectory & Developmental Graphs
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Select a student below to inspect real-time progress graphs, radar competency benchmarks, and quest journey milestones.
                  </p>
                </div>

                {/* Student Switcher Pills */}
                <div className="flex items-center gap-2 bg-slate-100 p-1.5 rounded-2xl">
                  {students.map(stu => {
                    const isSelected = selectedStudentId === stu.id
                    return (
                      <button
                        key={stu.id}
                        onClick={() => {
                          loadStudentDetail(stu.id)
                        }}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
                          isSelected
                            ? 'bg-white text-indigo-700 shadow-sm border border-slate-200/80 scale-102'
                            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                        }`}
                      >
                        <span className="text-base">{stu.avatar === 'girl-1' ? '👧' : '👦'}</span>
                        <div className="text-left">
                          <div className="font-extrabold leading-tight">{stu.full_name}</div>
                          <div className="text-[10px] text-slate-400 font-mono">{stu.id}</div>
                        </div>
                        {isSelected && (
                          <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse ml-1"></span>
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Active Selected Student Details & Graphical Progression */}
              {selectedStudentDetail ? (
                <div className="space-y-6">
                  {/* Student Executive Summary Bar */}
                  <div className="p-4 bg-gradient-to-r from-indigo-50/70 via-sky-50/40 to-slate-50 rounded-2xl border border-indigo-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center gap-3.5">
                      <div className="w-14 h-14 rounded-2xl bg-indigo-600 text-white flex items-center justify-center text-3xl shadow-sm">
                        {selectedStudentDetail.avatar === 'girl-1' ? '👧' : '👦'}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-black text-lg text-slate-900">{selectedStudentDetail.full_name}</h3>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-white text-indigo-700 border border-indigo-200">
                            {selectedStudentDetail.class_name || 'Sunflower Room'}
                          </span>
                          <span className="text-xs text-slate-400 font-medium">Age {selectedStudentDetail.age || 7}</span>
                        </div>
                        <div className="text-xs text-slate-600 flex items-center gap-3 mt-1 flex-wrap">
                          <span>👨‍👩‍👧 Parent: <strong>{selectedStudentDetail.parents?.[0]?.display_name || (selectedStudentDetail.id === 'STU-1002' ? 'David Lin' : 'Elena Miller')}</strong></span>
                          <span>📞 <span className="font-mono">{selectedStudentDetail.parents?.[0]?.phone || (selectedStudentDetail.id === 'STU-1002' ? '+1 (555) 876-5432' : '+1 (555) 234-5678')}</span></span>
                          <span>🎯 IEP: <span className="italic text-slate-500 max-w-xs truncate inline-block align-bottom">{selectedStudentDetail.learning_objectives || 'Joint attention & reciprocity'}</span></span>
                        </div>
                      </div>
                    </div>

                    {/* Quick Action Badges */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          loadReport(selectedStudentDetail.id)
                        }}
                        className="px-3.5 py-2 rounded-xl text-xs font-bold bg-white border border-slate-200 hover:bg-slate-50 text-indigo-700 shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer"
                      >
                        <span>📑</span> Progress Report
                      </button>
                      <button
                        onClick={() => {
                          setActiveTab('curriculum')
                          setCurriculumStudentId(selectedStudentDetail.id)
                          loadCurriculumAssignments(selectedStudentDetail.id)
                        }}
                        className="px-3.5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all flex items-center gap-1.5 cursor-pointer"
                      >
                        <span>🎮</span> Curriculum Path
                      </button>
                    </div>
                  </div>

                  {/* Graphical Presentation Grid */}
                  <div className="grid md:grid-cols-12 gap-6">
                    {/* GRAPH 1: 6-Domain Multi-Source Competency Progress Chart (7 Cols) */}
                    <div className="md:col-span-7 p-5 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-extrabold text-sm text-slate-900 flex items-center gap-2">
                            <span>📊</span> 6-Domain Competency Mastery Graph
                          </h4>
                          <p className="text-[11px] text-slate-500">
                            Continuous synthesis of in-game telemetry, educator rubrics, and home routine logs.
                          </p>
                        </div>
                        <span className="px-2.5 py-1 rounded-full text-[10px] font-black bg-indigo-100 text-indigo-800">
                          Readiness: {Math.round((selectedStudentDetail.behavioral_profile?.confidence_score || (selectedStudentDetail.id === 'STU-1002' ? 0.80 : 0.95)) * 100)}%
                        </span>
                      </div>

                      {/* 6 Visual Progress Bars with Benchmark Lines */}
                      <div className="space-y-3 pt-1">
                        {[
                          {
                            label: 'Motor Skills & Coordination',
                            score: selectedStudentDetail.behavioral_profile?.motor_skills ?? (selectedStudentDetail.id === 'STU-1002' ? 0.78 : 0.81),
                            color: 'bg-emerald-500',
                            tag: 'Fine & gross motor tracking'
                          },
                          {
                            label: 'Attention & Focus Stability',
                            score: selectedStudentDetail.behavioral_profile?.attention_focus ?? (selectedStudentDetail.id === 'STU-1002' ? 0.82 : 0.74),
                            color: 'bg-sky-500',
                            tag: 'Gaze hold & sustained focus'
                          },
                          {
                            label: 'Emotion Recognition & Expression',
                            score: selectedStudentDetail.behavioral_profile?.emotion_recognition ?? (selectedStudentDetail.id === 'STU-1002' ? 0.65 : 0.73),
                            color: 'bg-amber-500',
                            tag: 'Affect mirroring & regulation'
                          },
                          {
                            label: 'Communication & Language',
                            score: selectedStudentDetail.behavioral_profile?.communication_language ?? (selectedStudentDetail.id === 'STU-1002' ? 0.72 : 0.70),
                            color: 'bg-indigo-500',
                            tag: 'Speech & auditory comprehension'
                          },
                          {
                            label: 'Social Interaction & Reciprocity',
                            score: selectedStudentDetail.behavioral_profile?.social_interaction ?? (selectedStudentDetail.id === 'STU-1002' ? 0.61 : 0.68),
                            color: 'bg-purple-500',
                            tag: 'Turn-taking & joint attention'
                          },
                          {
                            label: 'Daily Living & Functional Routines',
                            score: selectedStudentDetail.behavioral_profile?.daily_living ?? (selectedStudentDetail.id === 'STU-1002' ? 0.55 : 0.93),
                            color: 'bg-teal-500',
                            tag: 'Schedule transitions & routines'
                          },
                        ].map((domain, i) => {
                          const pct = Math.round(domain.score * 100)
                          const statusLabel = pct >= 75 ? 'Proficient' : pct >= 65 ? 'Developing' : 'Emerging'
                          return (
                            <div key={i} className="space-y-1">
                              <div className="flex items-center justify-between text-xs">
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-slate-800">{domain.label}</span>
                                  <span className="text-[10px] text-slate-400 hidden sm:inline">({domain.tag})</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-md ${
                                    pct >= 75 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                                    pct >= 65 ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                                    'bg-rose-50 text-rose-700 border border-rose-200'
                                  }`}>
                                    {statusLabel}
                                  </span>
                                  <span className="font-extrabold text-slate-900 w-9 text-right font-mono">{pct}%</span>
                                </div>
                              </div>
                              {/* Progress Bar with Benchmark Line */}
                              <div className="w-full h-3 bg-slate-200/80 rounded-full overflow-hidden relative shadow-inner">
                                <div className="absolute top-0 bottom-0 left-[70%] w-0.5 bg-slate-400/40 z-10" title="70% Proficient Benchmark"></div>
                                <div
                                  className={`h-full rounded-full ${domain.color} transition-all duration-700 ease-out`}
                                  style={{ width: `${pct}%` }}
                                ></div>
                              </div>
                            </div>
                          )
                        })}
                      </div>

                      {/* Benchmark Legend */}
                      <div className="flex items-center justify-between pt-2 border-t border-slate-200/60 text-[10px] text-slate-500 flex-wrap gap-2">
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Proficient (≥75%)</span>
                          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Developing (65-74%)</span>
                          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Priority Focus (&lt;65%)</span>
                        </div>
                        <span className="font-medium text-slate-400">Target Standard: 70%</span>
                      </div>
                    </div>

                    {/* GRAPH 2 & 3: Performance Trajectory & Quest Milestone Roadmap (5 Cols) */}
                    <div className="md:col-span-5 space-y-4 flex flex-col justify-between">
                      {/* Performance Accuracy & Stability Trend Graph */}
                      <div className="p-5 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-extrabold text-sm text-slate-900 flex items-center gap-1.5">
                            <span>📈</span> Session Accuracy Trend
                          </h4>
                          <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100">
                            {selectedStudentDetail.id === 'STU-1002' ? '+18% Steady Gain' : '+14% Growth'}
                          </span>
                        </div>

                        {/* SVG Visual Line/Area Trend Chart */}
                        <div className="p-3 bg-white rounded-xl border border-slate-100 shadow-2xs">
                          <svg viewBox="0 0 280 85" className="w-full h-20 overflow-visible">
                            <defs>
                              <linearGradient id={`gradAcc-${selectedStudentDetail.id}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#6366f1" stopOpacity="0.35" />
                                <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
                              </linearGradient>
                            </defs>
                            <line x1="0" y1="20" x2="280" y2="20" stroke="#f1f5f9" strokeWidth="1" strokeDasharray="3 3" />
                            <line x1="0" y1="50" x2="280" y2="50" stroke="#f1f5f9" strokeWidth="1" strokeDasharray="3 3" />
                            <line x1="0" y1="80" x2="280" y2="80" stroke="#f1f5f9" strokeWidth="1" />
                            {selectedStudentDetail.id === 'STU-1002' ? (
                              <>
                                <polygon
                                  points="15,68 60,60 110,50 160,42 210,32 265,22 265,80 15,80"
                                  fill={`url(#gradAcc-${selectedStudentDetail.id})`}
                                />
                                <polyline
                                  points="15,68 60,60 110,50 160,42 210,32 265,22"
                                  fill="none"
                                  stroke="#4f46e5"
                                  strokeWidth="3"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                />
                                {[
                                  { x: 15, y: 68, val: '62%' },
                                  { x: 60, y: 60, val: '68%' },
                                  { x: 110, y: 50, val: '75%' },
                                  { x: 160, y: 42, val: '80%' },
                                  { x: 210, y: 32, val: '86%' },
                                  { x: 265, y: 22, val: '92%' },
                                ].map((pt, idx) => (
                                  <g key={idx}>
                                    <circle cx={pt.x} cy={pt.y} r="3.5" fill="#ffffff" stroke="#4f46e5" strokeWidth="2.5" />
                                    <text x={pt.x} y={pt.y - 7} fontSize="8.5" fontWeight="bold" fill="#334155" textAnchor="middle">
                                      {pt.val}
                                    </text>
                                  </g>
                                ))}
                              </>
                            ) : (
                              <>
                                <polygon
                                  points="15,62 60,52 110,45 160,35 210,24 265,15 265,80 15,80"
                                  fill={`url(#gradAcc-${selectedStudentDetail.id})`}
                                />
                                <polyline
                                  points="15,62 60,52 110,45 160,35 210,24 265,15"
                                  fill="none"
                                  stroke="#4f46e5"
                                  strokeWidth="3"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                />
                                {[
                                  { x: 15, y: 62, val: '68%' },
                                  { x: 60, y: 52, val: '74%' },
                                  { x: 110, y: 45, val: '78%' },
                                  { x: 160, y: 35, val: '84%' },
                                  { x: 210, y: 24, val: '90%' },
                                  { x: 265, y: 15, val: '95%' },
                                ].map((pt, idx) => (
                                  <g key={idx}>
                                    <circle cx={pt.x} cy={pt.y} r="3.5" fill="#ffffff" stroke="#4f46e5" strokeWidth="2.5" />
                                    <text x={pt.x} y={pt.y - 7} fontSize="8.5" fontWeight="bold" fill="#334155" textAnchor="middle">
                                      {pt.val}
                                    </text>
                                  </g>
                                ))}
                              </>
                            )}
                          </svg>
                          <div className="flex justify-between text-[10px] text-slate-400 font-semibold px-1 mt-1">
                            <span>Sess 1</span>
                            <span>Sess 4</span>
                            <span>Sess 8</span>
                            <span>Sess 12</span>
                            <span>Latest</span>
                          </div>
                        </div>
                      </div>

                      {/* Quest Journey & Level 1..5 Milestone Stepper */}
                      <div className="p-5 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-extrabold text-sm text-slate-900 flex items-center gap-1.5">
                            <span>🗺️</span> 5-Level Quest Journey
                          </h4>
                          <span className="text-[11px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">
                            {(selectedStudentDetail.assignments || []).filter((a: any) => a.status === 'completed').length} / {(selectedStudentDetail.assignments || []).length || 5} Complete
                          </span>
                        </div>

                        {/* Stepper Roadmap */}
                        <div className="grid grid-cols-5 gap-1.5 pt-1">
                          {[
                            { lvl: 1, name: 'L1: Motor', icon: '🫧', status: 'completed' },
                            { lvl: 2, name: 'L2: Affect', icon: '🪞', status: 'completed' },
                            { lvl: 3, name: 'L3: Language', icon: '🐿️', status: 'completed' },
                            { lvl: 4, name: 'L4: Social', icon: '👆', status: selectedStudentDetail.id === 'STU-1002' ? 'locked' : 'in-progress' },
                            { lvl: 5, name: 'L5: Autonomy', icon: '🏫', status: selectedStudentDetail.id === 'STU-1002' ? 'in-progress' : 'locked' },
                          ].map((step, idx) => {
                            const isComplete = step.status === 'completed'
                            const isCurrent = step.status === 'in-progress'
                            return (
                              <div
                                key={idx}
                                className={`p-2 rounded-xl text-center border transition-all ${
                                  isComplete
                                    ? 'bg-emerald-50/80 border-emerald-200 text-emerald-800'
                                    : isCurrent
                                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 shadow-2xs ring-2 ring-indigo-200'
                                    : 'bg-white border-slate-200 text-slate-400 opacity-70'
                                }`}
                              >
                                <div className="text-base">{step.icon}</div>
                                <div className="font-extrabold text-[10px] mt-0.5 leading-tight">{step.name}</div>
                                <div className="text-[9px] mt-1 font-bold">
                                  {isComplete ? '✓ Done' : isCurrent ? '⚡ Active' : '🔒 Locked'}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Presentable Insights: Strengths, Target Growth Areas & Parent Feedback Summary */}
                  <div className="grid md:grid-cols-3 gap-4 pt-1">
                    {/* Identified Strengths */}
                    <div className="p-4 bg-emerald-50/60 rounded-2xl border border-emerald-100 space-y-1.5 text-xs">
                      <div className="font-black text-emerald-900 flex items-center gap-1.5">
                        <span>🌟</span> Identified Core Strengths
                      </div>
                      <ul className="space-y-1 text-emerald-800 font-semibold">
                        {(selectedStudentDetail.behavioral_profile?.strengths || (selectedStudentDetail.id === 'STU-1002' ? ['Attention & Focus (82%)', 'Motor Skills (78%)'] : ['Daily Living (93%)', 'Motor Coordination (81%)'])).map((s: string, idx: number) => (
                          <li key={idx} className="flex items-center gap-1.5">
                            <span className="text-emerald-500 font-bold">•</span>
                            <span>{s}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Priority Growth Need */}
                    <div className="p-4 bg-amber-50/60 rounded-2xl border border-amber-100 space-y-1.5 text-xs">
                      <div className="font-black text-amber-900 flex items-center gap-1.5">
                        <span>🌱</span> Priority Growth Targets
                      </div>
                      <ul className="space-y-1 text-amber-800 font-semibold">
                        {(selectedStudentDetail.behavioral_profile?.growth_areas || (selectedStudentDetail.id === 'STU-1002' ? ['Daily Living & Routines (55%)', 'Social Interaction (61%)'] : ['Social Interaction & Reciprocity (68%)'])).map((g: string, idx: number) => (
                          <li key={idx} className="flex items-center gap-1.5">
                            <span className="text-amber-500 font-bold">•</span>
                            <span>{g}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Home & Parent Collaboration Status */}
                    <div className="p-4 bg-indigo-50/50 rounded-2xl border border-indigo-100 space-y-1.5 text-xs">
                      <div className="font-black text-indigo-900 flex items-center gap-1.5">
                        <span>🏡</span> Home Collaboration & Engagement
                      </div>
                      <div className="space-y-1 text-indigo-900">
                        <div className="flex justify-between font-semibold">
                          <span>Home Adaptation:</span>
                          <span className="font-black">{selectedStudentDetail.id === 'STU-1002' ? '⭐ 4.2 / 5.0' : '⭐ 4.5 / 5.0'}</span>
                        </div>
                        <div className="flex justify-between font-semibold">
                          <span>Parent Reviews:</span>
                          <span className="font-black">{(selectedStudentDetail.parent_feedback || []).length || 1} Submitted</span>
                        </div>
                        <div className="text-[11px] text-slate-500 italic pt-0.5">
                          "{selectedStudentDetail.id === 'STU-1002' ? 'Practicing morning routines at home with visual checklist.' : 'Transitions well with gentle visual cues and auditory timers.'}"
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-slate-400 font-semibold text-xs">
                  Loading student progress presentation...
                </div>
              )}
            </div>

            {/* AI-POWERED ADAPTIVE RECOMMENDATION REVIEW BANNER */}
            <div className="p-6 bg-gradient-to-r from-amber-50 via-orange-50 to-indigo-50 rounded-3xl border border-amber-200 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <span className="w-8 h-8 rounded-xl bg-amber-500 text-white flex items-center justify-center font-bold text-sm shadow-sm">
                    🤖
                  </span>
                  <div>
                    <h2 className="font-extrabold text-lg text-slate-900">
                      AI-Generated Game Recommendations Awaiting Teacher Approval
                    </h2>
                    <p className="text-xs text-slate-500">
                      Reinforcement Learning contextual policy synthesizes multi-source performance & behavioral observations.
                    </p>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-amber-100 text-amber-900 border border-amber-300">
                  {recommendations.length} Pending Decision
                </span>
              </div>

              {recommendations.length === 0 ? (
                <div className="p-6 bg-white/80 rounded-2xl border border-amber-100 text-center text-sm font-semibold text-slate-500">
                  ✨ All automated recommendations have been reviewed and approved!
                </div>
              ) : (
                <div className="space-y-4">
                  {recommendations.filter((rec, idx, self) =>
                    idx === self.findIndex((r) => r.student_id === rec.student_id)
                  ).map(rec => {
                    const gameObj = getGameById(rec.recommended_game_id)
                    return (
                      <div
                        key={rec.id}
                        className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                      >
                        <div className="space-y-2 max-w-2xl">
                          <div className="flex items-center gap-3">
                            <span className="px-2.5 py-1 rounded-lg text-xs font-black bg-indigo-100 text-indigo-700">
                              {rec.student_name}
                            </span>
                            <span className="text-xs font-bold text-slate-400">•</span>
                            <span className="font-extrabold text-base text-slate-900 flex items-center gap-1.5">
                              <span>{gameObj?.icon || '🎮'}</span>
                              <span>{gameObj?.name || rec.recommended_game_id}</span>
                            </span>
                            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-slate-100 text-slate-600">
                              {rec.difficulty} Difficulty
                            </span>
                          </div>
                          <div className="text-xs font-bold text-emerald-700">
                            🎯 Target Skill: {rec.target_skill} (Model Confidence: {Math.round(rec.confidence * 100)}%)
                          </div>
                          <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-100">
                            💡 <span className="font-semibold text-slate-800">RL Rationale:</span> {rec.rationale}
                          </p>
                        </div>

                        <div className="flex items-center gap-2.5 shrink-0">
                          <button
                            onClick={() => handleApproveRecommendation(rec.id)}
                            className="px-4 py-2.5 rounded-xl font-bold text-xs bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-200 transition-all cursor-pointer flex items-center gap-1.5"
                          >
                            <span>✓</span> Approve & Assign to Student
                          </button>
                          <button
                            onClick={() => handleRejectRecommendation(rec.id)}
                            className="px-3 py-2.5 rounded-xl font-bold text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors cursor-pointer"
                          >
                            Decline
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Two Column Grid: Classroom vs Home Observations Feed */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Recent Classroom Observations */}
              <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                    <span>🏫</span> Recent Classroom Observations
                  </h3>
                  <button
                    onClick={() => setActiveTab('observations')}
                    className="text-xs font-bold text-indigo-600 hover:underline cursor-pointer"
                  >
                    + Record New
                  </button>
                </div>

                <div className="space-y-3">
                  {(dashboardData?.recent_teacher_observations || []).map((obs: any) => (
                    <div key={obs.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-slate-900">{obs.student_name}</span>
                        <span className="text-[11px] font-semibold text-slate-400">{obs.date}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-600">
                        <span>Attention: ⭐ {obs.attention_rating}/5</span>
                        <span>Motor: ⭐ {obs.motor_skills}/5</span>
                        <span>Emotion: ⭐ {obs.emotional_regulation}/5</span>
                      </div>
                      <p className="text-xs text-slate-700 italic">"{obs.notes}"</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Home Observations */}
              <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                    <span>🏡</span> Recent Home Observations from Parents
                  </h3>
                  <button
                    onClick={() => setActiveTab('messages')}
                    className="text-xs font-bold text-indigo-600 hover:underline cursor-pointer"
                  >
                    Open Messages
                  </button>
                </div>

                <div className="space-y-3">
                  {(dashboardData?.recent_parent_observations || []).map((obs: any) => (
                    <div key={obs.id} className="p-4 rounded-2xl bg-amber-50/50 border border-amber-100 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-slate-900">
                          {obs.student_name} <span className="text-slate-400 font-normal">({obs.parent_name})</span>
                        </span>
                        <span className="text-[11px] font-semibold text-slate-400">{obs.date}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-amber-900 font-medium">
                        <span>Transitions: ⭐ {obs.routine_transitions}/5</span>
                        <span>Communication: ⭐ {obs.communication_attempts}/5</span>
                      </div>
                      <p className="text-xs text-slate-700 italic">"{obs.home_notes}"</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB: CLASS PERFORMANCE & SPECIAL CARE RANKING */}
        {activeTab === 'ranking' && (
          <div className="space-y-6 animate-fadeInUp">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black text-slate-900 flex items-center gap-2.5">
                  <span>🏆</span> Class Performance & Special Care Cohort Ranking
                </h2>
                <p className="text-xs text-slate-500 mt-1 max-w-2xl">
                  Synthesizes game metrics (reaction latency, completion, streak), teacher classroom observations, and parent home routine data into composite readiness scores. Categorizes students into support tiers to allocate special 1-on-1 care.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-xs">
                  Class: Sunflower Room ({dashboardData?.class_cohort_ranking?.length || 2} Students)
                </span>
              </div>
            </div>

            {/* Support Tier Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-extrabold text-emerald-800 uppercase tracking-wider">🌟 High Independence</span>
                  <span className="text-2xl font-black text-emerald-950">
                    {(dashboardData?.class_cohort_ranking || []).filter((s: any) => s.cohort_tier === 'Thriving').length}
                  </span>
                </div>
                <p className="text-xs text-emerald-700 mt-1">Autonomous play with strong task completion.</p>
              </div>

              <div className="p-5 rounded-2xl bg-blue-50 border border-blue-200 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-extrabold text-blue-800 uppercase tracking-wider">📈 Steady Growth</span>
                  <span className="text-2xl font-black text-blue-950">
                    {(dashboardData?.class_cohort_ranking || []).filter((s: any) => s.cohort_tier === 'Steady Growth').length}
                  </span>
                </div>
                <p className="text-xs text-blue-700 mt-1">Consistent progress; benefits from periodic cues.</p>
              </div>

              <div className="p-5 rounded-2xl bg-rose-50 border border-rose-200 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-extrabold text-rose-800 uppercase tracking-wider">🧡 Special Care Required</span>
                  <span className="text-2xl font-black text-rose-950">
                    {(dashboardData?.class_cohort_ranking || []).filter((s: any) => s.cohort_tier === 'Special Care Focus').length}
                  </span>
                </div>
                <p className="text-xs text-rose-700 mt-1">Priority focus; requires 1-on-1 teacher scaffolding.</p>
              </div>
            </div>

            {/* Ranking Table */}
            <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider">
                      <th className="pb-3 px-3">Class Rank</th>
                      <th className="pb-3 px-3">Student Name</th>
                      <th className="pb-3 px-3">Composite Readiness Score</th>
                      <th className="pb-3 px-3">Practice Time</th>
                      <th className="pb-3 px-3">Support Tier Classification</th>
                      <th className="pb-3 px-3">Special Care Scaffolding Alerts</th>
                      <th className="pb-3 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(dashboardData?.class_cohort_ranking || []).map((stu: any) => (
                      <tr key={stu.student_id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-4 px-3 font-black text-sm text-slate-800">
                          <span className={`w-8 h-8 rounded-full flex items-center justify-center font-black ${
                            stu.class_rank === 1 ? 'bg-amber-100 text-amber-900 border border-amber-300' :
                            stu.class_rank === 2 ? 'bg-slate-200 text-slate-800' :
                            'bg-slate-100 text-slate-600'
                          }`}>
                            #{stu.class_rank}
                          </span>
                        </td>
                        <td className="py-4 px-3">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">{stu.avatar === 'girl-1' ? '👧' : '👦'}</span>
                            <div>
                              <div className="font-extrabold text-slate-900 text-sm">{stu.full_name}</div>
                              <div className="text-[11px] text-slate-400">ID: {stu.student_id} • Age {stu.age}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-3">
                          <div className="space-y-1 w-36">
                            <div className="flex justify-between font-bold text-xs">
                              <span className="text-slate-700">Readiness</span>
                              <span className="text-slate-900">{stu.composite_score}%</span>
                            </div>
                            <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  stu.composite_score >= 75 ? 'bg-emerald-500' :
                                  stu.composite_score >= 60 ? 'bg-blue-500' : 'bg-rose-500'
                                }`}
                                style={{ width: `${stu.composite_score}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-3 font-semibold text-slate-600">
                          <div>{stu.sessions_played} games played</div>
                          <div className="text-[11px] text-slate-400">{stu.total_minutes} mins practice</div>
                        </td>
                        <td className="py-4 px-3">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-black inline-block ${
                            stu.cohort_tier === 'Thriving' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                            stu.cohort_tier === 'Steady Growth' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                            'bg-rose-100 text-rose-800 border border-rose-300'
                          }`}>
                            {stu.badge}
                          </span>
                        </td>
                        <td className="py-4 px-3">
                          <div className="flex flex-wrap gap-1 max-w-xs">
                            {stu.special_care_flags.map((flag: string, i: number) => (
                              <span key={i} className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                                ⚠️ {flag}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="py-4 px-3 text-right">
                          <button
                            onClick={() => {
                              setSelectedStudentId(stu.student_id)
                              loadStudentDetail(stu.student_id)
                              setActiveTab('students')
                            }}
                            className="px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 transition-all cursor-pointer"
                          >
                            Inspect Profile →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB: DEDICATED CURRICULUM & GAME ASSIGNMENT MANAGER */}
        {activeTab === 'curriculum' && (
          <div className="space-y-6 animate-fadeInUp">
            {/* Header with Title and Student Switcher */}
            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-black text-slate-900 flex items-center gap-2.5">
                    <span>🎮</span> Game Assignment & Sequential Curriculum Management
                  </h2>
                  <p className="text-xs text-slate-500 mt-1 max-w-3xl">
                    Select games from Level 1 to Level 5 and assign them to students in a specific order.
                    Unselect or delete any game at any time. Changes reflect immediately on all student and parent portals.
                    Unassigned games remain strictly hidden from students.
                  </p>
                </div>

                {/* Target Student Switcher */}
                <div className="flex flex-wrap items-center gap-2 bg-slate-50 p-2 rounded-2xl border border-slate-200">
                  <span className="text-xs font-bold text-slate-600 px-2">Assigning to:</span>
                  {students.map(stu => (
                    <button
                      key={stu.id}
                      onClick={() => {
                        setCurriculumStudentId(stu.id)
                        loadCurriculumAssignments(stu.id)
                      }}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                        curriculumStudentId === stu.id
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      <span>{stu.avatar === 'girl-1' ? '👧' : '👦'}</span>
                      <span>{stu.full_name}</span>
                      <span className="text-[10px] opacity-80 font-mono font-normal">({stu.id})</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Toolbar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
                <div className="flex items-center gap-2">
                  <label className="flex items-center gap-2 text-xs font-bold text-slate-700 cursor-pointer bg-slate-50 hover:bg-slate-100 px-3 py-2 rounded-xl border border-slate-200 transition-colors">
                    <input
                      type="checkbox"
                      checked={applyToAllClass}
                      onChange={(e) => setApplyToAllClass(e.target.checked)}
                      className="w-4 h-4 rounded text-indigo-600 border-slate-300 focus:ring-indigo-500 cursor-pointer"
                    />
                    <span>👥 Apply changes to all students in classroom (Sunflower Room)</span>
                  </label>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={handleLoadRecommendedSequence}
                    className="btn-3d btn-3d-amber px-4 py-2 rounded-xl text-xs font-black text-white shadow-xs cursor-pointer flex items-center gap-1.5"
                  >
                    <span>⭐</span> Load Recommended 5-Level Path
                  </button>
                  <button
                    onClick={handleSyncClassroom}
                    className="btn-3d btn-3d-blue px-4 py-2 rounded-xl text-xs font-black text-white shadow-xs cursor-pointer flex items-center gap-1.5"
                  >
                    <span>👥</span> Push to All Students
                  </button>
                  <button
                    onClick={handleClearPending}
                    className="btn-3d btn-3d-rose px-3.5 py-2 rounded-xl text-xs font-black text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 cursor-pointer flex items-center gap-1.5"
                  >
                    <span>✕</span> Clear Pending
                  </button>
                  <button
                    onClick={() => loadCurriculumAssignments(curriculumStudentId)}
                    className="btn-3d btn-3d-slate px-3.5 py-2 rounded-xl text-xs font-black text-slate-700 bg-white border border-slate-200 cursor-pointer flex items-center gap-1"
                  >
                    <span>🔄</span> Refresh
                  </button>
                </div>
              </div>

              {/* Feedback Success Toast */}
              {curriculumSuccessMsg && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center justify-between">
                  <span>{curriculumSuccessMsg}</span>
                  <button onClick={() => setCurriculumSuccessMsg(null)} className="text-emerald-600 hover:text-emerald-900 cursor-pointer">✕</button>
                </div>
              )}
            </div>

            {/* Current Assigned Sequence / Learning Path (Live Reorder & Delete) */}
            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                    <span>📋</span> Assigned Sequence for {students.find(s => s.id === curriculumStudentId)?.full_name || curriculumStudentId}
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-indigo-100 text-indigo-800 font-mono">
                      {curriculumAssignments.length} Quests Total
                    </span>
                  </h3>
                  <p className="text-xs text-slate-500">
                    The student can only play these activities in this exact sequential order. Reorder using ▲ ▼, set difficulty, or click Delete to remove.
                  </p>
                </div>
              </div>

              {curriculumAssignments.length === 0 ? (
                <div className="p-8 text-center bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200 space-y-2">
                  <span className="text-3xl">📭</span>
                  <div className="font-extrabold text-sm text-slate-700">No Games Currently Assigned</div>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Select games from the Level-Badged library below or click "Load Recommended 5-Level Path" to assign activities.
                  </p>
                  <button
                    onClick={handleLoadRecommendedSequence}
                    className="mt-2 px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs cursor-pointer"
                  >
                    ⭐ Assign Recommended 5-Level Path
                  </button>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {curriculumAssignments.map((asg: any, index: number) => {
                    const game = getGameById(asg.game_id)
                    const lvl = game?.level || 1
                    const lvlColor = LEVEL_INFO[lvl]?.color || '#3B82F6'
                    const meta = GAME_ENHANCED_META[asg.game_id]

                    return (
                      <div
                        key={asg.id || `${asg.game_id}-${index}`}
                        className={`p-4 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-3 ${
                          asg.status === 'completed'
                            ? 'bg-emerald-50/40 border-emerald-200'
                            : asg.status === 'in_progress' || asg.is_unlocked === 1
                            ? 'bg-sky-50/50 border-sky-300 ring-1 ring-sky-300'
                            : 'bg-white border-slate-200'
                        }`}
                      >
                        <div className="flex items-center gap-3.5">
                          {/* Step Number Circle */}
                          <div className="w-9 h-9 rounded-xl bg-slate-900 text-white font-black text-sm flex items-center justify-center shrink-0">
                            #{asg.sequence_order || index + 1}
                          </div>

                          {/* Game Icon */}
                          <div className="w-11 h-11 rounded-xl bg-slate-100 flex items-center justify-center text-2xl shrink-0 border border-slate-200">
                            {game?.icon || '🎮'}
                          </div>

                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-extrabold text-sm text-slate-900">
                                {game?.name || asg.game_id}
                              </span>
                              {/* Level Badge */}
                              <span
                                className="px-2 py-0.5 rounded-full text-[10px] font-black text-white"
                                style={{ backgroundColor: lvlColor }}
                              >
                                Level {lvl}
                              </span>
                              {/* Domain Badge */}
                              {meta && (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                                  {meta.domainIcon} {meta.domain}
                                </span>
                              )}
                              {/* Status Badge */}
                              {asg.status === 'completed' ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                                  ✓ Completed
                                </span>
                              ) : asg.status === 'in_progress' || asg.is_unlocked === 1 ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-100 text-sky-800 border border-sky-200 animate-pulse">
                                  🎯 Active Mission
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
                                  🔒 Locked Step
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-slate-500 mt-0.5 line-clamp-1 max-w-xl">
                              {meta?.shortDesc || game?.description || 'Curriculum activity for student development.'}
                            </p>
                          </div>
                        </div>

                        {/* Controls: Test Game, Difficulty, Reorder, Delete */}
                        <div className="flex items-center gap-2 self-end md:self-auto shrink-0">
                          {/* Test Game Play Button */}
                          <button
                            onClick={() => navigate(`/kid/games/${asg.game_id}`)}
                            title="Play and test this game as educator"
                            className="px-2.5 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-2xs transition-colors cursor-pointer flex items-center gap-1"
                          >
                            <span>▶️</span> Test
                          </button>
                          <button
                            onClick={() => window.open(`/kid/games/${asg.game_id}`, '_blank')}
                            title="Open test game in a new browser tab"
                            className="p-1.5 rounded-lg text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-200 transition-colors cursor-pointer"
                          >
                            ↗
                          </button>

                          {/* Difficulty Selector */}
                          <div className="flex items-center gap-1 pl-1 border-l border-slate-200">
                            <span className="text-[11px] font-bold text-slate-500">Diff:</span>
                            <select
                              value={asg.difficulty || 'easy'}
                              onChange={(e) => handleUpdateDifficulty(asg.id, e.target.value)}
                              className="text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-slate-700 cursor-pointer focus:ring-1 focus:ring-indigo-500"
                            >
                              <option value="easy">Easy</option>
                              <option value="medium">Medium</option>
                              <option value="hard">Hard</option>
                            </select>
                          </div>

                          {/* Reorder Buttons */}
                          <button
                            onClick={() => handleMoveAssignment(index, 'up')}
                            disabled={index === 0}
                            title="Move Up in Sequence"
                            className={`w-7 h-7 rounded-lg border flex items-center justify-center text-xs font-bold transition-colors cursor-pointer ${
                              index === 0
                                ? 'bg-slate-100 text-slate-300 border-slate-200 cursor-not-allowed'
                                : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-200'
                            }`}
                          >
                            ▲
                          </button>
                          <button
                            onClick={() => handleMoveAssignment(index, 'down')}
                            disabled={index === curriculumAssignments.length - 1}
                            title="Move Down in Sequence"
                            className={`w-7 h-7 rounded-lg border flex items-center justify-center text-xs font-bold transition-colors cursor-pointer ${
                              index === curriculumAssignments.length - 1
                                ? 'bg-slate-100 text-slate-300 border-slate-200 cursor-not-allowed'
                                : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-200'
                            }`}
                          >
                            ▼
                          </button>

                          {/* Delete / Remove Assignment */}
                          <button
                            onClick={() => handleUnassignGameFromCurriculum(asg.game_id, asg.id)}
                            title="Remove/Delete this game from student assignments"
                            className="px-2.5 py-1.5 rounded-lg text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition-colors cursor-pointer flex items-center gap-1"
                          >
                            <span>🗑️</span> Remove
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Level Filter Tabs & Game Library Cards */}
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-xl font-black text-slate-900 flex items-center gap-2">
                    <span>📚</span> Available Serious Games Library (15 Games by Level Badge)
                  </h3>
                  <p className="text-xs text-slate-500">
                    Use checkboxes to select/unselect games, manage sequential order, adjust difficulty, or test-play any game.
                  </p>
                </div>

                {/* Level Filter Pills */}
                <div className="flex flex-wrap items-center gap-1.5 bg-slate-100 p-1.5 rounded-2xl border border-slate-200">
                  <button
                    onClick={() => setSelectedLevelFilter('all')}
                    className={`px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                      selectedLevelFilter === 'all'
                        ? 'bg-white text-indigo-700 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    All Levels (15)
                  </button>
                  {[1, 2, 3, 4, 5].map(lvl => (
                    <button
                      key={lvl}
                      onClick={() => setSelectedLevelFilter(lvl)}
                      className={`px-2.5 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1 ${
                        selectedLevelFilter === lvl
                          ? 'bg-white text-slate-900 shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: LEVEL_INFO[lvl]?.color }}
                      ></span>
                      Level {lvl} (3)
                    </button>
                  ))}
                </div>
              </div>

              {/* Levels Container */}
              {[1, 2, 3, 4, 5]
                .filter(lvl => selectedLevelFilter === 'all' || selectedLevelFilter === lvl)
                .map(lvl => {
                  const levelGames = GAME_CATALOGUE.filter(g => g.level === lvl)
                  const lvlInfo = LEVEL_INFO[lvl]
                  const assignedCountInLevel = levelGames.filter(g => curriculumAssignments.some(a => a.game_id === g.id)).length

                  return (
                    <div key={lvl} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
                      {/* Level Header with Distinct Badge and Batch Action Controls */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
                        <div className="flex items-center gap-3">
                          <span
                            className="px-3.5 py-1 rounded-full text-xs font-black text-white shadow-xs uppercase tracking-wider"
                            style={{ backgroundColor: lvlInfo?.color || '#3B82F6' }}
                          >
                            Level {lvl}: {lvlInfo?.name}
                          </span>
                          <span className="text-xs text-slate-500 font-semibold hidden md:inline">
                            {lvlInfo?.description}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-500 mr-1">
                            {assignedCountInLevel}/{levelGames.length} Assigned
                          </span>
                          <button
                            onClick={() => handleSelectAllInLevel(lvl)}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 transition-colors cursor-pointer"
                            title={`Select and assign all ${levelGames.length} games in Level ${lvl}`}
                          >
                            ✓ Select All Level {lvl}
                          </button>
                          <button
                            onClick={() => handleUnselectAllInLevel(lvl)}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-200 transition-colors cursor-pointer"
                            title={`Unselect all games in Level ${lvl}`}
                          >
                            ✕ Unselect All
                          </button>
                        </div>
                      </div>

                      {/* Games in this Level */}
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {levelGames.map(game => {
                          const assignedMatch = curriculumAssignments.find(a => a.game_id === game.id)
                          const isAssigned = !!assignedMatch
                          const assignedIndex = curriculumAssignments.findIndex(a => a.game_id === game.id)
                          const assignedOrder = assignedMatch?.sequence_order || (assignedIndex >= 0 ? assignedIndex + 1 : null)
                          const meta = GAME_ENHANCED_META[game.id]

                          return (
                            <div
                              key={game.id}
                              className={`p-5 rounded-2xl border-2 transition-all flex flex-col justify-between gap-4 ${
                                isAssigned
                                  ? 'border-emerald-500 bg-emerald-50/25 shadow-sm ring-1 ring-emerald-400/70'
                                  : 'border-slate-200 bg-white hover:border-slate-300'
                              }`}
                            >
                              <div className="space-y-3">
                                {/* Top Header: Interactive Checkbox & Sequence Order Badge */}
                                <div className="flex items-center justify-between gap-2 pb-2 border-b border-slate-100">
                                  <label className="flex items-center gap-2.5 cursor-pointer select-none group">
                                    <input
                                      type="checkbox"
                                      checked={isAssigned}
                                      onChange={() => handleToggleGame(game.id, isAssigned, assignedMatch?.id)}
                                      className="w-5 h-5 rounded-md text-emerald-600 border-slate-300 focus:ring-emerald-500 cursor-pointer accent-emerald-600 transition-transform group-hover:scale-110"
                                    />
                                    <span className={`text-xs font-black tracking-wide ${isAssigned ? 'text-emerald-800' : 'text-slate-600'}`}>
                                      {isAssigned ? 'Assigned' : 'Select Game'}
                                    </span>
                                  </label>

                                  {isAssigned ? (
                                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-black bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs">
                                      ✓ Order #{assignedOrder}
                                    </span>
                                  ) : (
                                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-400 border border-slate-200">
                                      Unassigned
                                    </span>
                                  )}
                                </div>

                                {/* Game Identity & Icon */}
                                <div className="flex items-start gap-3">
                                  <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-2xl border border-slate-200 shrink-0 shadow-2xs">
                                    {game.icon}
                                  </div>
                                  <div className="space-y-0.5">
                                    <h4 className="font-extrabold text-sm text-slate-900 leading-tight">
                                      {game.name}
                                    </h4>
                                    <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                                      <span
                                        className="inline-block text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded text-white"
                                        style={{ backgroundColor: lvlInfo?.color || '#3B82F6' }}
                                      >
                                        Level {lvl} Badge
                                      </span>
                                      {meta && (
                                        <span className="text-[10px] font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                                          {meta.domainIcon} {meta.domain}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>

                                {/* Short Developmental Description */}
                                <p className="text-xs text-slate-600 leading-relaxed min-h-[2.5rem]">
                                  {meta?.shortDesc || game.description}
                                </p>

                                {/* Target Skill Pill */}
                                {meta?.skillTarget && (
                                  <div className="text-[11px] font-semibold text-slate-700 bg-slate-50 p-2 rounded-xl border border-slate-100">
                                    <span className="text-indigo-600 font-bold">🎯 Target:</span> {meta.skillTarget}
                                  </div>
                                )}

                                {/* Technical Modes Tags */}
                                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                                    {game.runtime === 'python-launched' ? '🐍 Python CV' : '🌐 WebGL 3D'}
                                  </span>
                                  {game.needs.camera && (
                                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                                      📷 Camera
                                    </span>
                                  )}
                                  {game.needs.microphone && (
                                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                                      🎤 Voice
                                    </span>
                                  )}
                                  {game.needs.webgl && (
                                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
                                      🖥️ 3D Campus
                                    </span>
                                  )}
                                </div>

                                {/* Direct In-Card Order & Difficulty Controls (when assigned) */}
                                {isAssigned && (
                                  <div className="p-2.5 rounded-xl bg-emerald-50/70 border border-emerald-200 flex items-center justify-between gap-2">
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-[11px] font-bold text-emerald-900">Sequence:</span>
                                      <span className="w-6 h-6 rounded-lg bg-emerald-700 text-white text-xs font-black flex items-center justify-center shadow-xs">
                                        #{assignedOrder}
                                      </span>
                                      <div className="flex items-center gap-1">
                                        <button
                                          onClick={() => handleMoveAssignment(assignedIndex, 'up')}
                                          disabled={assignedIndex === 0}
                                          title="Move Up in Sequence"
                                          className="w-6 h-6 rounded border bg-white hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed text-[10px] font-black text-slate-700 flex items-center justify-center cursor-pointer shadow-2xs"
                                        >
                                          ▲
                                        </button>
                                        <button
                                          onClick={() => handleMoveAssignment(assignedIndex, 'down')}
                                          disabled={assignedIndex === curriculumAssignments.length - 1}
                                          title="Move Down in Sequence"
                                          className="w-6 h-6 rounded border bg-white hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed text-[10px] font-black text-slate-700 flex items-center justify-center cursor-pointer shadow-2xs"
                                        >
                                          ▼
                                        </button>
                                      </div>
                                    </div>

                                    <div className="flex items-center gap-1">
                                      <span className="text-[11px] font-bold text-emerald-900">Diff:</span>
                                      <select
                                        value={assignedMatch.difficulty || 'easy'}
                                        onChange={(e) => handleUpdateDifficulty(assignedMatch.id, e.target.value)}
                                        className="text-xs font-bold bg-white border border-emerald-300 rounded-lg px-2 py-0.5 text-slate-700 cursor-pointer shadow-2xs focus:ring-1 focus:ring-emerald-500"
                                      >
                                        <option value="easy">Easy</option>
                                        <option value="medium">Medium</option>
                                        <option value="hard">Hard</option>
                                      </select>
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* Action Footer: Assignment Actions and Test Play Buttons */}
                              <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
                                {isAssigned ? (
                                  <button
                                    onClick={() => handleUnassignGameFromCurriculum(game.id, assignedMatch.id)}
                                    className="px-3 py-1.5 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition-colors cursor-pointer flex items-center gap-1"
                                    title="Remove from assigned sequence"
                                  >
                                    <span>🗑️</span> Remove
                                  </button>
                                ) : (
                                  <div className="flex items-center gap-1.5 flex-1">
                                    <select
                                      id={`diff-select-${game.id}`}
                                      defaultValue="easy"
                                      className="text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg px-2 py-1.5 text-slate-700 focus:ring-1 focus:ring-indigo-500 cursor-pointer"
                                    >
                                      <option value="easy">Easy</option>
                                      <option value="medium">Medium</option>
                                      <option value="hard">Hard</option>
                                    </select>
                                    <button
                                      onClick={() => {
                                        const selectEl = document.getElementById(`diff-select-${game.id}`) as HTMLSelectElement
                                        const diff = selectEl ? selectEl.value : 'easy'
                                        handleAssignGameToCurriculum(game.id, diff)
                                      }}
                                      disabled={assigningGameId === game.id}
                                      className="flex-1 px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-colors cursor-pointer flex items-center justify-center gap-1"
                                    >
                                      <span>+</span> Assign
                                    </button>
                                  </div>
                                )}

                                {/* Educator Test Play Action Buttons */}
                                <div className="flex items-center gap-1">
                                  <button
                                    onClick={() => navigate(`/kid/games/${game.id}`)}
                                    title="Play and test this game directly as educator"
                                    className="btn-3d btn-3d-blue px-3.5 py-1.5 rounded-xl text-xs font-black text-white cursor-pointer flex items-center gap-1 shadow-xs"
                                  >
                                    <span>▶️</span> Test Game
                                  </button>
                                  <button
                                    onClick={() => window.open(`/kid/games/${game.id}`, '_blank')}
                                    title="Open test game in a new browser tab"
                                    className="p-1.5 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-200 transition-colors cursor-pointer"
                                  >
                                    ↗
                                  </button>
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>
        )}

        {/* TAB 2: STUDENT MANAGEMENT & 360-DEGREE PROFILES */}
        {activeTab === 'students' && (
          <div className="space-y-6 animate-fadeInUp">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-black text-slate-900">Student Behavioral Profiles & Management</h2>
                <p className="text-xs text-slate-500">
                  Select a student to inspect multi-source radar metrics, learning path sequences, and session history.
                </p>
              </div>
              <div className="flex items-center gap-2.5">
                <button
                  onClick={() => setShowAddClassModal(true)}
                  className="btn-3d btn-3d-slate px-3.5 py-2 rounded-xl font-black text-xs bg-white text-indigo-700 border border-indigo-200 shadow-xs cursor-pointer flex items-center gap-1.5"
                >
                  <span>🏫</span> + Add Class
                </button>
                <button
                  onClick={() => setShowAddStudentModal(true)}
                  className="btn-3d btn-3d-blue px-4 py-2 rounded-xl font-black text-xs text-white shadow-xs cursor-pointer flex items-center gap-1.5"
                >
                  <span>+</span> Add New Student
                </button>
              </div>
            </div>

            {/* Student Selector Cards */}
            {students.length === 0 ? (
              <div className="p-8 text-center bg-white rounded-3xl border border-slate-200 space-y-3">
                <span className="text-4xl">👨‍🎓</span>
                <h3 className="font-extrabold text-base text-slate-800">No Student Profiles Loaded</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Click below to synchronize student behavioral profiles from the database, or register a new student account.
                </p>
                <div className="flex justify-center gap-3 pt-2">
                  <button
                    onClick={() => loadDashboard()}
                    className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm cursor-pointer"
                  >
                    🔄 Reload Student Profiles
                  </button>
                  <button
                    onClick={() => setShowAddStudentModal(true)}
                    className="px-4 py-2 rounded-xl text-xs font-bold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 cursor-pointer"
                  >
                    + Add New Student
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {students.map(stu => (
                  <div
                    key={stu.id}
                    onClick={() => loadStudentDetail(stu.id)}
                    className={`p-5 rounded-3xl border-2 transition-all cursor-pointer flex flex-col justify-between gap-3 ${selectedStudentId === stu.id
                      ? 'border-indigo-600 bg-indigo-50/40 shadow-sm'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                      }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3.5">
                        <div className="w-14 h-14 rounded-2xl bg-indigo-100 flex items-center justify-center text-3xl shadow-xs border border-indigo-200">
                          {stu.avatar === 'girl-1' ? '👧' : '👦'}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-extrabold text-base text-slate-900">{stu.full_name}</h3>
                            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-black bg-indigo-100 text-indigo-800 border border-indigo-200 font-mono">
                              ID: {stu.id}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">
                            Class: <span className="font-bold text-slate-700">{stu.class_name || 'Sunflower Room'}</span> • Age: {stu.age || 7}
                          </p>
                          <div className="text-xs text-slate-600 mt-1">
                            👨‍👩‍👧 Parent: <span className="font-bold text-slate-800">{stu.parent_name || 'Elena Miller'}</span>
                            {stu.parent_relationship && <span className="text-slate-400"> ({stu.parent_relationship})</span>}
                            {stu.parent_phone && <span className="block text-[11px] text-slate-500 font-mono">📞 {stu.parent_phone}</span>}
                            {stu.parent_email && <span className="block text-[11px] text-slate-500 font-mono">✉️ {stu.parent_email}</span>}
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-col items-end gap-1.5">
                        <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                          Readiness: {Math.round((stu.confidence_score || 0.8) * 100)}%
                        </span>
                        <span className="text-[11px] text-slate-400 font-semibold">
                          {stu.sessions_count || 0} sessions
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100 flex-wrap">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleOpenEditStudent(stu) }}
                        className="px-2.5 py-1.5 rounded-xl text-xs font-bold bg-white border border-slate-200 hover:bg-indigo-50 text-indigo-700 shadow-xs transition-colors cursor-pointer flex items-center gap-1"
                        title="Edit student profile details, name, username, IEP goals and accommodations"
                      >
                        <span>✏️</span> Edit Profile
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleTriggerRecommendation(stu.id) }}
                        disabled={rlLoadingStudentId === stu.id}
                        title="Generate adaptive reinforcement learning recommendation"
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shadow-xs ${
                          rlLoadingStudentId === stu.id
                            ? 'bg-amber-100 text-amber-900 border border-amber-300 animate-pulse'
                            : 'bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200'
                        }`}
                      >
                        {rlLoadingStudentId === stu.id ? (
                          <>
                            <span className="inline-block animate-spin">⚙️</span>
                            <span>Evaluating Policy...</span>
                          </>
                        ) : (
                          <>
                            <span>⚡</span>
                            <span>Run RL Suggestion</span>
                          </>
                        )}
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); loadReport(stu.id) }}
                        className="px-3 py-1.5 rounded-xl text-xs font-bold bg-white border border-slate-200 hover:bg-slate-50 text-indigo-700 shadow-xs transition-colors cursor-pointer"
                      >
                        📑 Progress Report
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setActiveTab('security')
                          setEditingStudentPinId(stu.id)
                          setNewStudentPinValue('1234')
                          loadCredentials()
                        }}
                        className="px-2.5 py-1.5 rounded-xl text-xs font-bold bg-white border border-slate-200 hover:bg-amber-50 text-amber-900 shadow-xs transition-colors cursor-pointer flex items-center gap-1"
                        title="Edit student login PIN / password"
                      >
                        <span>🔑</span> Login PIN
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* 360-Degree Profile Details for Selected Student */}
            {selectedStudentDetail && (() => {
              const currentStudentRec =
                (latestRlRecommendation && latestRlRecommendation.student_id === selectedStudentId && latestRlRecommendation.status === 'pending_approval'
                  ? latestRlRecommendation
                  : null) ||
                recommendations.find(r => r.student_id === selectedStudentId && r.status === 'pending_approval')

              return (
                <div className="space-y-6 pt-4">
                  {/* Action Notification Toast */}
                  {rlActionToast && (
                    <div className="p-3.5 rounded-2xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs font-bold flex items-center justify-between shadow-xs animate-fadeInUp">
                      <div className="flex items-center gap-2">
                        <span>🤖</span>
                        <span>{rlActionToast}</span>
                      </div>
                      <button onClick={() => setRlActionToast(null)} className="text-slate-400 hover:text-slate-700 font-bold px-1.5">✕</button>
                    </div>
                  )}

                  {/* Student 360° Comprehensive Clinical & Profile Console Banner */}
                  <div className="p-6 bg-gradient-to-r from-slate-900 via-indigo-950 to-indigo-900 text-white rounded-3xl shadow-xl border border-indigo-700/40 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 animate-fadeInUp">
                    <div className="flex items-center gap-5">
                      <div className="relative">
                        <div className="w-20 h-20 rounded-3xl bg-white/10 backdrop-blur-md flex items-center justify-center text-5xl shadow-md border-2 border-white/20">
                          {selectedStudentDetail.avatar === 'girl-1' ? '👧' : '👦'}
                        </div>
                        <span className="absolute -bottom-1 -right-1 px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-500 text-white border-2 border-slate-900">
                          Active
                        </span>
                      </div>
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-3 flex-wrap">
                          <h2 className="text-2xl font-black text-white">{selectedStudentDetail.full_name}</h2>
                          <span className="px-3 py-0.5 rounded-full text-xs font-black bg-indigo-500/40 text-indigo-200 border border-indigo-400/40 font-mono">
                            ID: {selectedStudentDetail.id}
                          </span>
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-white/15 text-indigo-100 font-mono">
                            @{selectedStudentDetail.username || (selectedStudentDetail.id === 'STU-1001' ? 'alex' : 'maya')}
                          </span>
                        </div>
                        <p className="text-xs text-indigo-200 flex items-center gap-3 flex-wrap">
                          <span>🏫 {selectedStudentDetail.class_name || 'Sunflower Room (Early Primary)'}</span>
                          <span>•</span>
                          <span>🎂 Age: {selectedStudentDetail.age || 7} (DOB: {selectedStudentDetail.dob || '2019-04-12'})</span>
                          <span>•</span>
                          <span className="font-semibold text-emerald-300">
                            🎯 Readiness: {Math.round((selectedStudentDetail.confidence_score || selectedStudentDetail.behavioral_profile?.confidence_score || 0.85) * 100)}%
                          </span>
                          <span>•</span>
                          <span className="text-indigo-300">
                            🎮 {(selectedStudentDetail.session_history || []).length} Sessions Logged
                          </span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 flex-wrap">
                      <button
                        onClick={() => handleOpenEditStudent(selectedStudentDetail)}
                        className="btn-3d btn-3d-blue px-4 py-2.5 rounded-xl font-black text-xs text-white shadow-md cursor-pointer flex items-center gap-1.5"
                        title="Edit student personal info, username, IEP goals, and classroom accommodations"
                      >
                        <span>✏️</span> Edit Profile
                      </button>
                      <button
                        onClick={() => {
                          setActiveTab('security')
                          setEditingStudentPinId(selectedStudentDetail.id)
                          setNewStudentPinValue('1234')
                          loadCredentials()
                        }}
                        className="btn-3d btn-3d-slate px-3.5 py-2.5 rounded-xl font-bold text-xs bg-white/10 hover:bg-white/20 text-white border border-white/20 cursor-pointer flex items-center gap-1.5"
                        title="Change student login PIN"
                      >
                        <span>🔑</span> Login PIN
                      </button>
                      <button
                        onClick={() => handleTriggerRecommendation(selectedStudentDetail.id)}
                        disabled={rlLoadingStudentId === selectedStudentDetail.id}
                        className="btn-3d btn-3d-amber px-4 py-2.5 rounded-xl font-black text-xs text-amber-950 cursor-pointer flex items-center gap-1.5 shadow-md"
                        title="Run adaptive contextual reinforcement learning policy evaluation"
                      >
                        <span>⚡</span> Run RL Policy
                      </button>
                      <button
                        onClick={() => setShowIepModal(true)}
                        className="btn-3d btn-3d-teal px-3.5 py-2.5 rounded-xl font-black text-xs text-white shadow-md cursor-pointer flex items-center gap-1.5"
                        title="Generate 1-Click Formal IEP Clinical Summary Report"
                      >
                        <span>📋</span> 1-Click IEP Summary
                      </button>
                      <button
                        onClick={() => loadReport(selectedStudentDetail.id)}
                        className="btn-3d btn-3d-slate px-3.5 py-2.5 rounded-xl font-bold text-xs bg-white/10 hover:bg-white/20 text-white border border-white/20 cursor-pointer flex items-center gap-1.5"
                      >
                        <span>📑</span> Clinical Report
                      </button>
                      <button
                        onClick={() => {
                          setCurriculumStudentId(selectedStudentDetail.id)
                          setActiveTab('curriculum')
                        }}
                        className="btn-3d btn-3d-slate px-3.5 py-2.5 rounded-xl font-bold text-xs bg-white/10 hover:bg-white/20 text-white border border-white/20 cursor-pointer flex items-center gap-1.5"
                        title="Open interactive questline manager"
                      >
                        <span>🎮</span> Questline
                      </button>
                    </div>
                  </div>

                  {/* Contextual Bandit RL Recommendation & Synthesis Card */}
                  {!rlBannerDismissed && currentStudentRec && (() => {
                    const recGame = getGameById(currentStudentRec.recommended_game_id)
                    const altGames = Array.isArray(currentStudentRec.alternative_games)
                      ? currentStudentRec.alternative_games
                      : typeof currentStudentRec.alternative_games_json === 'string'
                        ? JSON.parse(currentStudentRec.alternative_games_json || '[]')
                        : []

                    return (
                      <div className="p-6 bg-gradient-to-br from-amber-50/90 via-white to-indigo-50/50 rounded-3xl border-2 border-amber-300 shadow-sm space-y-4 animate-fadeInUp">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 to-amber-400 text-white flex items-center justify-center text-2xl shadow-sm">
                              ⚡
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase bg-amber-500 text-white tracking-wide">
                                  Contextual Bandit RL Recommendation
                                </span>
                                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-white border border-amber-200 text-amber-900 shadow-2xs">
                                  {Math.round((currentStudentRec.confidence || 0.9) * 100)}% Confidence
                                </span>
                              </div>
                              <h3 className="font-black text-lg text-slate-900 mt-0.5">
                                Targeted Adaptive Next Activity for {selectedStudentDetail.full_name}
                              </h3>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleApproveRecommendation(currentStudentRec.id)}
                              className="px-4 py-2.5 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm flex items-center gap-1.5 transition-transform hover:scale-105 cursor-pointer"
                            >
                              <span>✓</span> Approve & Assign to Quest Path
                            </button>
                            <button
                              onClick={() => handleRejectRecommendation(currentStudentRec.id)}
                              className="px-3 py-2.5 rounded-xl text-xs font-bold bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 cursor-pointer"
                            >
                              ✕ Dismiss
                            </button>
                          </div>
                        </div>

                        {/* Inputs Evaluated & Model Rationale Breakdown */}
                        <div className="grid md:grid-cols-3 gap-4">
                          {/* Primary Recommended Game */}
                          <div className="p-4 bg-white rounded-2xl border border-amber-200/80 shadow-xs space-y-2.5">
                            <div className="text-[11px] font-extrabold uppercase tracking-wider text-amber-700">Primary Suggested Game</div>
                            <div className="flex items-center gap-3">
                              <span className="text-3xl p-2 bg-amber-50 rounded-xl border border-amber-100">{recGame?.icon || '🎮'}</span>
                              <div>
                                <div className="font-black text-base text-slate-900">{recGame?.name || currentStudentRec.recommended_game_id}</div>
                                <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                                  <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold border border-indigo-100">
                                    Level {recGame?.level || 1}
                                  </span>
                                  <span className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 font-bold border border-amber-100 uppercase">
                                    {currentStudentRec.difficulty || 'medium'}
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div className="text-xs text-slate-600 pt-1 border-t border-slate-100">
                              <span className="font-bold text-slate-800">Target Skill: </span>
                              <span className="text-indigo-700 font-semibold">{currentStudentRec.target_skill}</span>
                            </div>
                          </div>

                          {/* Multi-Source Inputs Considered */}
                          <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-xs space-y-2 text-xs">
                            <div className="text-[11px] font-extrabold uppercase tracking-wider text-slate-500">Multi-Source Inputs Evaluated</div>
                            <ul className="space-y-1.5 text-slate-600">
                              <li className="flex items-center gap-1.5">
                                <span className="text-emerald-500 font-bold">✓</span>
                                <span><strong>Radar Mastery:</strong> Evaluates lowest 6-domain score</span>
                              </li>
                              <li className="flex items-center gap-1.5">
                                <span className="text-emerald-500 font-bold">✓</span>
                                <span><strong>IEP Goals & Accommodations:</strong> Tailored support</span>
                              </li>
                              <li className="flex items-center gap-1.5">
                                <span className="text-emerald-500 font-bold">✓</span>
                                <span><strong>Parent Game Reviews:</strong> Frustration & enjoyment</span>
                              </li>
                              <li className="flex items-center gap-1.5">
                                <span className="text-emerald-500 font-bold">✓</span>
                                <span><strong>Session Telemetry:</strong> Latency & completion stability</span>
                              </li>
                            </ul>
                          </div>

                          {/* Explainable AI Rationale */}
                          <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-xs space-y-1.5 text-xs">
                            <div className="text-[11px] font-extrabold uppercase tracking-wider text-slate-500">Explainable AI Rationale</div>
                            <p className="text-slate-700 leading-relaxed italic">
                              "{currentStudentRec.rationale}"
                            </p>
                          </div>
                        </div>

                        {/* Alternative Candidate Games */}
                        {altGames.length > 0 && (
                          <div className="pt-3 border-t border-amber-200/60 flex items-center gap-2.5 text-xs flex-wrap">
                            <span className="font-bold text-slate-700">Alternative Options (1-Click Select):</span>
                            {altGames.map((alt: any, idx: number) => (
                              <button
                                key={idx}
                                onClick={() => handleApproveRecommendation(currentStudentRec.id, alt.game_id)}
                                className="px-3 py-1.5 rounded-xl bg-white hover:bg-amber-50 border border-slate-200 hover:border-amber-300 text-slate-700 font-bold flex items-center gap-1.5 shadow-2xs cursor-pointer transition-all"
                                title={`Assign ${alt.game_name} instead`}
                              >
                                <span>{alt.icon}</span>
                                <span>{alt.game_name}</span>
                                <span className="text-[10px] text-slate-400 font-medium">(Lvl {alt.level})</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })()}

                  <div className="grid md:grid-cols-3 gap-6">
                {/* Left 2 Cols: Radar Domains, Learning Goals, and Sequential Assignments */}
                <div className="md:col-span-2 space-y-6">
                  {/* Multi-Domain Radar Metrics */}
                  <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-5">
                    <div className="flex items-center justify-between">
                      <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                        <span>📊</span> Multi-Source Behavioral Profile (6 Domains)
                      </h3>
                      <span className="text-xs font-semibold text-slate-500">
                        Synthesizes CV + Game Logs + Teacher + Parent Notes
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {[
                        { label: 'Motor Skills', score: selectedStudentDetail.behavioral_profile?.motor_skills, color: 'bg-emerald-500' },
                        { label: 'Attention & Focus', score: selectedStudentDetail.behavioral_profile?.attention_focus, color: 'bg-sky-500' },
                        { label: 'Emotion Recognition', score: selectedStudentDetail.behavioral_profile?.emotion_recognition, color: 'bg-amber-500' },
                        { label: 'Communication', score: selectedStudentDetail.behavioral_profile?.communication_language, color: 'bg-indigo-500' },
                        { label: 'Social Interaction', score: selectedStudentDetail.behavioral_profile?.social_interaction, color: 'bg-purple-500' },
                        { label: 'Daily Living', score: selectedStudentDetail.behavioral_profile?.daily_living, color: 'bg-teal-500' },
                      ].map((domain, i) => {
                        const pct = Math.round((domain.score || 0.5) * 100)
                        return (
                          <div key={i} className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
                            <div className="flex justify-between items-center text-xs font-bold mb-1.5">
                              <span className="text-slate-700">{domain.label}</span>
                              <span className="text-slate-900">{pct}%</span>
                            </div>
                            <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${domain.color}`} style={{ width: `${pct}%` }}></div>
                            </div>
                          </div>
                        )
                      })}
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-2 text-xs">
                      <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
                        <span className="font-bold text-emerald-800">🌟 Identified Strengths:</span>
                        <ul className="list-disc list-inside mt-1 text-emerald-700 space-y-0.5">
                          {(selectedStudentDetail.behavioral_profile?.strengths || []).map((s: string, idx: number) => (
                            <li key={idx}>{s}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="p-3 bg-amber-50 rounded-xl border border-amber-100">
                        <span className="font-bold text-amber-800">🌱 Target Growth Areas:</span>
                        <ul className="list-disc list-inside mt-1 text-amber-700 space-y-0.5">
                          {(selectedStudentDetail.behavioral_profile?.growth_areas || []).map((g: string, idx: number) => (
                            <li key={idx}>{g}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Individual Learning Objectives & Support Needs */}
                  <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                        <span>🎯</span> Learning Objectives & Classroom Accommodations
                      </h3>
                      <button
                        onClick={() => handleOpenEditStudent(selectedStudentDetail)}
                        className="px-3 py-1.5 rounded-xl font-bold text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 transition-colors cursor-pointer flex items-center gap-1 shadow-xs"
                      >
                        <span>✏️</span> Edit IEP & Needs
                      </button>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 text-xs space-y-2">
                      <div>
                        <span className="font-bold text-slate-800">Individual IEP Objectives: </span>
                        <span className="text-slate-600">{selectedStudentDetail.learning_objectives || 'None specified'}</span>
                      </div>
                      <div>
                        <span className="font-bold text-slate-800">Student Interests: </span>
                        <span className="text-slate-600">{selectedStudentDetail.interests || 'None specified'}</span>
                      </div>
                      <div>
                        <span className="font-bold text-slate-800">Sensory & Support Accommodations: </span>
                        <span className="text-slate-600">{selectedStudentDetail.support_requirements || 'Standard audio/visual cues'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Sequenced Game Assignments */}
                  <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                        <span>🎮</span> Assigned Learning Path Sequence
                      </h3>
                      <div className="flex items-center gap-2">
                        <select
                          value={assignGameId}
                          onChange={e => setAssignGameId(e.target.value)}
                          className="px-2 py-1 text-xs rounded-lg border border-slate-200 bg-slate-50"
                        >
                          {GAME_CATALOGUE.map(g => (
                            <option key={g.id} value={g.id}>{g.name} (Lvl {g.level})</option>
                          ))}
                        </select>
                        <select
                          value={assignDifficulty}
                          onChange={e => setAssignDifficulty(e.target.value)}
                          className="px-2 py-1 text-xs rounded-lg border border-slate-200 bg-slate-50"
                        >
                          <option value="easy">Easy</option>
                          <option value="medium">Medium</option>
                          <option value="hard">Hard</option>
                        </select>
                        <button
                          onClick={handleAssignGame}
                          className="px-3 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white cursor-pointer hover:bg-indigo-700"
                        >
                          + Assign
                        </button>
                      </div>
                    </div>

                    <div className="space-y-2.5">
                      {(selectedStudentDetail.assignments || []).map((asg: any) => {
                        const g = getGameById(asg.game_id)
                        return (
                          <div
                            key={asg.id}
                            className={`p-3.5 rounded-2xl border flex items-center justify-between text-xs ${asg.status === 'completed'
                              ? 'bg-emerald-50/60 border-emerald-200'
                              : asg.is_unlocked
                                ? 'bg-indigo-50/60 border-indigo-200'
                                : 'bg-slate-50 border-slate-200 opacity-60'
                              }`}
                          >
                            <div className="flex items-center gap-3">
                              <span className="w-6 h-6 rounded-full bg-white border border-slate-300 flex items-center justify-center font-bold text-[11px]">
                                {asg.sequence_order}
                              </span>
                              <span className="text-xl">{g?.icon || '🎮'}</span>
                              <div>
                                <div className="font-bold text-slate-900">{g?.name || asg.game_id}</div>
                                <div className="text-[11px] text-slate-500">
                                  Difficulty: {asg.difficulty} • Level {g?.level || 1}
                                </div>
                              </div>
                            </div>
                            <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold ${asg.status === 'completed'
                              ? 'bg-emerald-200 text-emerald-800'
                              : asg.is_unlocked
                                ? 'bg-indigo-200 text-indigo-800'
                                : 'bg-slate-200 text-slate-600'
                              }`}>
                              {asg.status === 'completed' ? '✓ Completed' : asg.is_unlocked ? 'Unlocked • Next' : '🔒 Locked'}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>

                {/* Right Col: Gameplay History & Quick Actions */}
                <div className="space-y-6">
                  {/* Linked Parent / Guardian Family Card */}
                  {(() => {
                    const linkedParent = (selectedStudentDetail.parents && selectedStudentDetail.parents[0]) ||
                      parents.find(p => p.student_id === selectedStudentDetail.id)
                    return linkedParent ? (
                      <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4 animate-fadeInUp">
                        <div className="flex items-center justify-between">
                          <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                            <span>👪</span> Linked Guardian
                          </h3>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-emerald-100 text-emerald-800">
                            Verified Link
                          </span>
                        </div>

                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-2xl bg-amber-100 flex items-center justify-center text-2xl border border-amber-200 shadow-xs">
                            🏡
                          </div>
                          <div>
                            <h4 className="font-extrabold text-sm text-slate-900">{linkedParent.display_name || linkedParent.full_name}</h4>
                            <p className="text-xs text-slate-500 font-semibold">{linkedParent.relationship || 'Parent / Guardian'} • <span className="font-mono text-indigo-700">@{linkedParent.username}</span></p>
                          </div>
                        </div>

                        <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 text-xs space-y-1.5 font-medium">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Contact Email:</span>
                            <span className="font-mono text-slate-700">{linkedParent.email || 'elena.miller@example.com'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Contact Phone:</span>
                            <span className="font-mono text-slate-700">{linkedParent.phone || '+1 (555) 234-5678'}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2 pt-1">
                          <button
                            onClick={() => handleOpenEditParent({
                              ...linkedParent,
                              student_id: selectedStudentDetail.id,
                            })}
                            className="py-2 px-3 rounded-xl font-bold text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 transition-colors cursor-pointer flex items-center justify-center gap-1.5 shadow-2xs"
                          >
                            <span>✏️</span> Edit Parent
                          </button>
                          <button
                            onClick={() => {
                              setSelectedStudentId(selectedStudentDetail.id)
                              loadMessages(selectedStudentDetail.id)
                              setActiveTab('messages')
                            }}
                            className="py-2 px-3 rounded-xl font-bold text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors cursor-pointer flex items-center justify-center gap-1.5"
                          >
                            <span>💬</span> Chat
                          </button>
                        </div>
                      </div>
                    ) : null
                  })()}

                  {/* Printable Report Action Card */}
                  <div className="p-6 bg-gradient-to-br from-indigo-600 to-indigo-800 text-white rounded-3xl shadow-md shadow-indigo-200 space-y-4">
                    <h3 className="font-extrabold text-base">Individual Progress Report</h3>
                    <p className="text-xs text-indigo-100 leading-relaxed">
                      Generate a professional, multi-domain progress report with printable PDF styling, observation summaries, and non-diagnostic educational disclaimers.
                    </p>
                    <button
                      onClick={() => loadReport(selectedStudentId)}
                      className="w-full py-2.5 rounded-xl font-bold text-xs bg-white text-indigo-700 hover:bg-indigo-50 shadow transition-all cursor-pointer"
                    >
                      📑 View & Print Full Progress Report
                    </button>
                  </div>

                  {/* Gameplay History Log */}
                  <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
                    <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                      <span>🕹️</span> Session History
                    </h3>

                    <div className="space-y-2.5">
                      {(selectedStudentDetail.session_history || []).slice(0, 6).map((sess: any) => {
                        const g = getGameById(sess.game_id)
                        return (
                          <div key={sess.id} className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-1">
                            <div className="flex justify-between font-bold text-slate-800">
                              <span>{g?.name || sess.game_id}</span>
                              <span className="text-emerald-600">
                                {sess.status === 'completed' ? '✓ Complete' : sess.status}
                              </span>
                            </div>
                            <div className="flex justify-between text-slate-400 text-[11px]">
                              <span>Mode: {sess.input_mode}</span>
                              <span>{Math.round(sess.duration_seconds || 120)}s</span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Parent Game Card Reviews & Home Feedback */}
                  <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                        <span>💬</span> Parent Game Reviews & Feedback
                      </h3>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-amber-100 text-amber-800">
                        {(selectedStudentDetail.parent_feedback || []).length} Submitted
                      </span>
                    </div>

                    {(selectedStudentDetail.parent_feedback || []).length === 0 ? (
                      <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-400 text-center">
                        No game reviews submitted by parents yet.
                      </div>
                    ) : (
                      <div className="space-y-2.5">
                        {(selectedStudentDetail.parent_feedback || []).slice(0, 5).map((fb: any) => {
                          const g = getGameById(fb.game_id)
                          return (
                            <div key={fb.id} className="p-3.5 rounded-xl bg-amber-50/40 border border-amber-200/70 text-xs space-y-1.5">
                              <div className="flex items-center justify-between font-bold text-slate-800">
                                <span className="flex items-center gap-1.5">
                                  <span>{g?.icon || '🎮'}</span>
                                  <span>{g?.name || fb.game_id}</span>
                                </span>
                                <span className="text-[10px] text-slate-400 font-mono">{fb.created_at?.slice(0, 10)}</span>
                              </div>
                              <div className="flex items-center gap-2.5 text-[11px] text-amber-900 font-semibold">
                                <span>Enjoyment: ⭐ {fb.enjoyment_rating}/5</span>
                                <span>Frustration: ⚡ {fb.frustration_level}/5</span>
                                <span>Assist: 🤝 {fb.assistance_needed}/5</span>
                              </div>
                              {fb.comments && (
                                <p className="text-[11px] text-slate-600 italic mt-1 bg-white/70 p-2 rounded-lg border border-amber-100">
                                  "{fb.comments}"
                                </p>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })()}
      </div>
    )}

        {/* TAB: PARENT ACCOUNTS MANAGEMENT */}
        {activeTab === 'parents' && (
          <div className="space-y-6 animate-fadeInUp">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black text-slate-900 flex items-center gap-2.5">
                  <span>👪</span> Parent Accounts & Home Portal Administration
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Only the educator administrator can create parent accounts. Assign login credentials, link guardians to students, and oversee home-school collaboration.
                </p>
              </div>
              <button
                onClick={() => setShowAddParentModal(true)}
                className="px-4 py-2.5 rounded-xl font-bold text-xs bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-200 transition-all cursor-pointer flex items-center gap-1.5"
              >
                <span>+</span> Create Parent Account
              </button>
            </div>

            {/* Parent Accounts Grid */}
            {parents.length === 0 ? (
              <div className="p-8 text-center bg-white rounded-3xl border border-slate-200 space-y-3">
                <span className="text-4xl">👪</span>
                <h3 className="font-extrabold text-base text-slate-800">No Parent Accounts Loaded</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Click below to synchronize parent accounts from the database or create a new parent login.
                </p>
                <div className="flex justify-center gap-3 pt-2">
                  <button
                    onClick={() => loadDashboard()}
                    className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm cursor-pointer"
                  >
                    🔄 Reload Parents
                  </button>
                  <button
                    onClick={() => setShowAddParentModal(true)}
                    className="px-4 py-2 rounded-xl text-xs font-bold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 cursor-pointer"
                  >
                    + Create Parent Account
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {parents.map((p: any) => (
                  <div key={p.id} className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between">
                    <div className="space-y-3">
                      <div className="flex items-center gap-3.5">
                        <div className="w-12 h-12 rounded-2xl bg-amber-100 flex items-center justify-center text-2xl shadow-xs border border-amber-200">
                          🏡
                        </div>
                        <div>
                          <h3 className="font-extrabold text-base text-slate-900">{p.full_name}</h3>
                          <span className="text-xs font-bold text-slate-500 font-mono">@{p.username}</span>
                        </div>
                      </div>

                      <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 space-y-2 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-500">Linked Student:</span>
                          <span className="font-extrabold text-indigo-700">{p.student_name || 'Alex Miller'}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-slate-500">Student Number / ID:</span>
                          <span className="font-black text-indigo-800 font-mono bg-indigo-100/70 px-2 py-0.5 rounded border border-indigo-200">
                            {p.student_id || 'STU-1001'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Relationship:</span>
                          <span className="font-bold text-slate-700">{p.relationship || 'Mother / Guardian'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Contact Email:</span>
                          <span className="font-semibold text-slate-700 font-mono text-[11px]">{p.email || 'elena.miller@example.com'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Contact Phone:</span>
                          <span className="font-semibold text-slate-700 font-mono text-[11px]">{p.phone || '+1 (555) 234-5678'}</span>
                        </div>
                        <div className="flex justify-between items-center pt-1 border-t border-slate-200/60">
                          <span className="text-slate-500">Access Status:</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-100 text-emerald-800">Verified Parent</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-2 pt-1">
                      <button
                        onClick={() => handleOpenEditParent(p)}
                        className="py-2.5 rounded-xl font-bold text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 transition-colors cursor-pointer flex items-center justify-center gap-1 shadow-2xs"
                        title="Edit parent details, contact info and linked student"
                      >
                        <span>✏️</span> Edit
                      </button>
                      <button
                        onClick={() => {
                          if (p.student_id) {
                            setSelectedStudentId(p.student_id)
                            loadMessages(p.student_id)
                          }
                          setActiveTab('messages')
                        }}
                        className="py-2.5 rounded-xl font-bold text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors cursor-pointer flex items-center justify-center gap-1"
                      >
                        <span>💬</span> Chat
                      </button>
                      <button
                        onClick={() => {
                          setActiveTab('security')
                          setEditingParentPwId(p.id)
                          setNewParentPwValue('parent123')
                          loadCredentials()
                        }}
                        className="py-2.5 rounded-xl font-bold text-xs bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 transition-colors cursor-pointer flex items-center justify-center gap-1"
                      >
                        <span>🔑</span> Pass
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB: PASSWORDS & SECURITY MANAGEMENT */}
        {activeTab === 'security' && (
          <div className="space-y-6 animate-fadeInUp">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black text-slate-900 flex items-center gap-2.5">
                  <span>🔐</span> Master Credentials & Password Security Hub
                </h2>
                <p className="text-xs text-slate-500 mt-1 max-w-3xl">
                  Centralized administrative management for all platform accounts. Create, edit, and reset login PINs and passwords for Students, Parents, and Lead Educators. Changes immediately sync across all portals and database records.
                </p>
              </div>
              <button
                onClick={() => loadCredentials()}
                className="px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <span>🔄</span> Refresh Accounts
              </button>
            </div>

            {/* Toast notification */}
            {securityToast && (
              <div className={`p-4 rounded-2xl text-xs font-bold flex items-center justify-between shadow-xs animate-fadeInUp ${
                securityToast.type === 'success'
                  ? 'bg-emerald-50 border border-emerald-200 text-emerald-900'
                  : 'bg-rose-50 border border-rose-200 text-rose-900'
              }`}>
                <div className="flex items-center gap-2">
                  <span>{securityToast.type === 'success' ? '✓' : '⚠️'}</span>
                  <span>{securityToast.message}</span>
                </div>
                <button onClick={() => setSecurityToast(null)} className="text-slate-400 hover:text-slate-700 px-1 font-bold">✕</button>
              </div>
            )}

            {/* Section 1: Teacher Master Account */}
            <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white flex items-center justify-center text-2xl shadow-sm">
                    👩‍🏫
                  </div>
                  <div>
                    <h3 className="font-black text-base text-slate-900">Lead Educator Master Password</h3>
                    <p className="text-xs text-slate-500">
                      Master Administrator Account: <strong className="font-mono text-indigo-700">teacher</strong> (Ms. Sarah Wilson)
                    </p>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-black bg-indigo-50 text-indigo-700 border border-indigo-200">
                  Master Administrator
                </span>
              </div>

              <form onSubmit={handleUpdateTeacherPassword} className="grid md:grid-cols-3 gap-4 pt-1">
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Current Password (optional)</label>
                  <input
                    type="password"
                    value={teacherCurrentPw}
                    onChange={e => setTeacherCurrentPw(e.target.value)}
                    placeholder="Enter current password"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">New Teacher Password</label>
                  <input
                    type="password"
                    value={teacherNewPw}
                    onChange={e => setTeacherNewPw(e.target.value)}
                    placeholder="Min 3 characters"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-mono"
                    required
                  />
                </div>
                <div className="flex items-end gap-2">
                  <div className="flex-1">
                    <label className="block text-xs font-bold text-slate-600 mb-1">Confirm New Password</label>
                    <input
                      type="password"
                      value={teacherConfirmPw}
                      onChange={e => setTeacherConfirmPw(e.target.value)}
                      placeholder="Confirm new password"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-mono"
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    className="px-4 py-2.5 rounded-xl font-bold text-xs bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-100 transition-all cursor-pointer whitespace-nowrap"
                  >
                    Update Teacher Password
                  </button>
                </div>
              </form>
            </div>

            {/* Section 2: Student Login PINs & Passwords */}
            <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-amber-500 text-white flex items-center justify-center text-2xl shadow-sm">
                    🧒
                  </div>
                  <div>
                    <h3 className="font-black text-base text-slate-900">Student Accounts & Login PIN Management</h3>
                    <p className="text-xs text-slate-500">
                      Students sign in using their username and 4-digit PIN/Password. Both teachers and parents can set or change student passwords.
                    </p>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-black bg-amber-50 text-amber-800 border border-amber-200">
                  {students.length} Student Accounts
                </span>
              </div>

              <div className="grid md:grid-cols-2 gap-4 pt-1">
                {students.map(stu => {
                  const isEditing = editingStudentPinId === stu.id
                  return (
                    <div key={stu.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-3xl p-1.5 bg-white rounded-xl border border-slate-100 shadow-2xs">
                            {stu.avatar === 'girl-1' ? '👧' : '👦'}
                          </span>
                          <div>
                            <h4 className="font-black text-sm text-slate-900">{stu.full_name}</h4>
                            <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                              <span className="font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-700 font-bold">
                                @{stu.username || 'student'}
                              </span>
                              <span>•</span>
                              <span className="font-mono text-slate-400 font-bold">{stu.id}</span>
                            </div>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          Active
                        </span>
                      </div>

                      <div className="p-3 bg-white rounded-xl border border-slate-100 space-y-1.5 text-xs">
                        <div className="flex justify-between items-center text-slate-600">
                          <span>Assigned Class:</span>
                          <span className="font-bold text-slate-800">{stu.class_name || 'Sunflower Room'}</span>
                        </div>
                        <div className="flex justify-between items-center text-slate-600">
                          <span>Login Mechanism:</span>
                          <span className="font-bold text-indigo-700">Username + 4-Digit PIN / Password</span>
                        </div>
                      </div>

                      {isEditing ? (
                        <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 space-y-2 animate-fadeInUp">
                          <label className="block text-xs font-bold text-amber-900">
                            Set New PIN / Password for {stu.full_name}:
                          </label>
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              value={newStudentPinValue}
                              onChange={e => setNewStudentPinValue(e.target.value)}
                              placeholder="e.g. 1234"
                              className="flex-1 px-3 py-2 rounded-lg border border-amber-300 bg-white text-xs font-mono font-bold"
                              autoFocus
                            />
                            <button
                              onClick={() => handleSaveStudentPin(stu.id)}
                              className="px-3 py-2 rounded-lg font-bold text-xs bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs cursor-pointer"
                            >
                              ✓ Save PIN
                            </button>
                            <button
                              onClick={() => {
                                setEditingStudentPinId(null)
                                setNewStudentPinValue('')
                              }}
                              className="px-2.5 py-2 rounded-lg font-bold text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 cursor-pointer"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-end pt-1">
                          <button
                            onClick={() => {
                              setEditingStudentPinId(stu.id)
                              setNewStudentPinValue('1234')
                            }}
                            className="px-3.5 py-2 rounded-xl font-bold text-xs bg-white hover:bg-amber-50 text-amber-900 border border-amber-200 shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer"
                          >
                            <span>🔑</span> Edit / Reset PIN
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Section 3: Parent Portal Passwords */}
            <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-emerald-600 text-white flex items-center justify-center text-2xl shadow-sm">
                    👪
                  </div>
                  <div>
                    <h3 className="font-black text-base text-slate-900">Parent Accounts & Portal Passwords</h3>
                    <p className="text-xs text-slate-500">
                      Guardians can change their password directly in the Parent Portal, or educators can reset it here.
                    </p>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-black bg-emerald-50 text-emerald-800 border border-emerald-200">
                  {parents.length} Parent Accounts
                </span>
              </div>

              <div className="grid md:grid-cols-2 gap-4 pt-1">
                {parents.map(par => {
                  const isEditing = editingParentPwId === par.id
                  return (
                    <div key={par.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-black text-sm text-slate-900">{par.display_name}</h4>
                          <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                            <span className="font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-700 font-bold">
                              @{par.username}
                            </span>
                            <span>•</span>
                            <span className="text-slate-600">{par.relationship || 'Guardian'}</span>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          Connected
                        </span>
                      </div>

                      <div className="p-3 bg-white rounded-xl border border-slate-100 space-y-1.5 text-xs">
                        <div className="flex justify-between items-center text-slate-600">
                          <span>Linked Student:</span>
                          <span className="font-bold text-slate-800">{par.student_name || 'Alex Miller'}</span>
                        </div>
                        <div className="flex justify-between items-center text-slate-600">
                          <span>Contact:</span>
                          <span className="font-mono text-slate-700">{par.phone || par.email || 'None on file'}</span>
                        </div>
                      </div>

                      {isEditing ? (
                        <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 space-y-2 animate-fadeInUp">
                          <label className="block text-xs font-bold text-emerald-900">
                            Set New Password for {par.display_name}:
                          </label>
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              value={newParentPwValue}
                              onChange={e => setNewParentPwValue(e.target.value)}
                              placeholder="e.g. parent123"
                              className="flex-1 px-3 py-2 rounded-lg border border-emerald-300 bg-white text-xs font-mono font-bold"
                              autoFocus
                            />
                            <button
                              onClick={() => handleSaveParentPassword(par.id)}
                              className="px-3 py-2 rounded-lg font-bold text-xs bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs cursor-pointer"
                            >
                              ✓ Save Password
                            </button>
                            <button
                              onClick={() => {
                                setEditingParentPwId(null)
                                setNewParentPwValue('')
                              }}
                              className="px-2.5 py-2 rounded-lg font-bold text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 cursor-pointer"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-end pt-1">
                          <button
                            onClick={() => {
                              setEditingParentPwId(par.id)
                              setNewParentPwValue('parent123')
                            }}
                            className="px-3.5 py-2 rounded-xl font-bold text-xs bg-white hover:bg-emerald-50 text-emerald-900 border border-emerald-200 shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer"
                          >
                            <span>🔑</span> Reset Password
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: ADD CLASSROOM OBSERVATION */}
        {activeTab === 'observations' && (
          <div className="max-w-2xl mx-auto p-8 bg-white rounded-3xl border border-slate-200 shadow-sm space-y-6 animate-fadeInUp">
            <div>
              <h2 className="text-2xl font-black text-slate-900">Record Classroom Observation</h2>
              <p className="text-xs text-slate-500 mt-1">
                Observations feed directly into the student's multi-source behavioral profile to update adaptation recommendations.
              </p>
            </div>

            {obsSavedMessage && (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold text-center">
                ✓ {obsSavedMessage}
              </div>
            )}

            <form onSubmit={handleSubmitObservation} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1 uppercase tracking-wider">
                  Target Student
                </label>
                <select
                  value={obsForm.student_id}
                  onChange={e => setObsForm(prev => ({ ...prev, student_id: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-semibold text-xs"
                >
                  {students.map(s => (
                    <option key={s.id} value={s.id}>{s.full_name} ({s.id})</option>
                  ))}
                </select>
              </div>

              {/* 1-5 Ratings Grid */}
              <div className="grid grid-cols-2 gap-4">
                {[
                  { key: 'attention_rating', label: 'Attention & Focus (1-5)' },
                  { key: 'emotional_regulation', label: 'Emotional Regulation (1-5)' },
                  { key: 'peer_interaction', label: 'Peer Interaction (1-5)' },
                  { key: 'motor_skills', label: 'Motor Coordination (1-5)' },
                ].map((item: any) => (
                  <div key={item.key}>
                    <label className="block text-xs font-bold text-slate-600 mb-1">
                      {item.label}
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      value={(obsForm as any)[item.key]}
                      onChange={e => setObsForm(prev => ({ ...prev, [item.key]: Number(e.target.value) }))}
                      className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-bold text-slate-800"
                    />
                  </div>
                ))}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Triggers / Sensory Observations (Optional)
                </label>
                <input
                  type="text"
                  value={obsForm.triggers_observed}
                  onChange={e => setObsForm(prev => ({ ...prev, triggers_observed: e.target.value }))}
                  placeholder="e.g. Activity transitions, loud environmental noise"
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Support Strategies Used (Optional)
                </label>
                <input
                  type="text"
                  value={obsForm.strategies_used}
                  onChange={e => setObsForm(prev => ({ ...prev, strategies_used: e.target.value }))}
                  placeholder="e.g. Visual timer countdown, verbal encouragement"
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Educator Detailed Notes & Observations *
                </label>
                <textarea
                  rows={4}
                  required
                  value={obsForm.notes}
                  onChange={e => setObsForm(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="Describe task engagement, waiting patience, interaction with mascot/prompts, and general emotional state..."
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-medium"
                ></textarea>
              </div>

              <button
                type="submit"
                className="w-full py-3 rounded-xl font-bold text-xs bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-200 transition-all cursor-pointer"
              >
                Submit Classroom Observation
              </button>
            </form>
          </div>
        )}

        {/* TAB 4: PARENT-TEACHER MESSAGING */}
        {activeTab === 'messages' && (
          <div className="max-w-3xl mx-auto bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden animate-fadeInUp">
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <h3 className="font-extrabold text-base text-slate-900">Parent-Teacher Communication</h3>
                <p className="text-xs text-slate-500">Student: Alex Miller (Parent: Elena Miller)</p>
              </div>
              <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                Connected
              </span>
            </div>

            {/* Message History */}
            <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
              {messages.map((m: any) => {
                const isMe = m.sender_role === 'teacher'
                return (
                  <div key={m.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-md p-4 rounded-2xl text-xs space-y-1 ${isMe ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-800'
                      }`}>
                      <div className={`font-bold text-[11px] ${isMe ? 'text-indigo-200' : 'text-slate-500'}`}>
                        {m.sender_name}
                      </div>
                      <p className="leading-relaxed">{m.content}</p>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Send Message Input */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-200 bg-slate-50 flex gap-3">
              <input
                type="text"
                value={newMessageText}
                onChange={e => setNewMessageText(e.target.value)}
                placeholder="Type a message or note to the parent..."
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-xs font-medium focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl font-bold text-xs bg-indigo-600 hover:bg-indigo-700 text-white shadow transition-all cursor-pointer"
              >
                Send
              </button>
            </form>
          </div>
        )}

        {/* TAB 5: PRINTABLE STUDENT PROGRESS REPORT */}
        {activeTab === 'report' && reportData && (
          <div className="max-w-4xl mx-auto bg-white p-10 rounded-3xl border border-slate-200 shadow-md space-y-8 animate-fadeInUp">
            {/* Report Header */}
            <div className="flex items-center justify-between border-b pb-6">
              <div>
                <span className="text-xs font-extrabold uppercase tracking-widest text-indigo-600">
                  Adaptive Learning Platform Progress Report
                </span>
                <h1 className="text-2xl font-black text-slate-900 mt-1">{reportData.title}</h1>
                <p className="text-xs text-slate-500 mt-1">Generated: {reportData.generated_at}</p>
              </div>
              <button
                onClick={() => window.print()}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow transition-all cursor-pointer"
              >
                🖨️ Print / Save PDF
              </button>
            </div>

            {/* Section 1: Student Demographics */}
            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="font-bold text-slate-400 block">STUDENT NAME</span>
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
                <span className="font-bold text-slate-400 block">TOTAL SESSIONS</span>
                <span className="font-extrabold text-slate-800 text-sm">
                  {reportData.student?.total_sessions} ({reportData.student?.total_minutes} mins)
                </span>
              </div>
            </div>

            {/* Section 2: Multi-Domain Radar Scores */}
            <div className="space-y-4">
              <h3 className="font-extrabold text-base text-slate-900">Skill Domain Performance Index</h3>
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

            {/* Section 3: Recommendations & Alignment */}
            <div className="space-y-3">
              <h3 className="font-extrabold text-base text-slate-900">Educator-Approved Recommended Activities</h3>
              <div className="space-y-2.5">
                {(reportData.recommendations || []).map((rec: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-100 text-xs space-y-1">
                    <div className="flex justify-between font-bold">
                      <span className="text-slate-900">{rec.activity} — {rec.target}</span>
                      <span className="text-emerald-700 font-extrabold">{rec.status}</span>
                    </div>
                    <p className="text-slate-600">{rec.rationale}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Mandatory Non-Diagnostic Disclaimer */}
            <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-slate-500 text-xs italic leading-relaxed text-center">
              ⚠️ {reportData.disclaimer}
            </div>
          </div>
        )}
          </>
        )}
      </main>

      {/* ADD STUDENT MODAL */}
      {showAddStudentModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-6 z-50 animate-fadeIn">
          <div className="bg-white max-w-lg w-full p-8 rounded-3xl shadow-2xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-extrabold text-slate-900">Create Student Profile</h3>
              <button
                onClick={() => setShowAddStudentModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateStudent} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-600 mb-1">Student Full Name *</label>
                <input
                  type="text"
                  required
                  value={newStudentForm.full_name}
                  onChange={e => setNewStudentForm(prev => ({ ...prev, full_name: e.target.value }))}
                  placeholder="e.g. Leo Carter"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Username *</label>
                  <input
                    type="text"
                    required
                    value={newStudentForm.username}
                    onChange={e => setNewStudentForm(prev => ({ ...prev, username: e.target.value }))}
                    placeholder="e.g. leo"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Secret PIN *</label>
                  <input
                    type="text"
                    required
                    value={newStudentForm.password}
                    onChange={e => setNewStudentForm(prev => ({ ...prev, password: e.target.value }))}
                    placeholder="e.g. 1234"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">Individual Learning Objectives</label>
                <textarea
                  rows={2}
                  value={newStudentForm.learning_objectives}
                  onChange={e => setNewStudentForm(prev => ({ ...prev, learning_objectives: e.target.value }))}
                  placeholder="e.g. Fine motor tracing, reciprocal turn-taking waiting"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50"
                ></textarea>
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">Interests & Favorites</label>
                <input
                  type="text"
                  value={newStudentForm.interests}
                  onChange={e => setNewStudentForm(prev => ({ ...prev, interests: e.target.value }))}
                  placeholder="e.g. Trains, animals, space, drawing"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">Sensory & Support Accommodations</label>
                <input
                  type="text"
                  value={newStudentForm.support_requirements}
                  onChange={e => setNewStudentForm(prev => ({ ...prev, support_requirements: e.target.value }))}
                  placeholder="e.g. Needs visual timer, quiet audio cues"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50"
                />
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowAddStudentModal(false)}
                  className="flex-1 py-2.5 rounded-xl font-bold bg-slate-100 text-slate-600 hover:bg-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 rounded-xl font-bold bg-indigo-600 text-white hover:bg-indigo-700 shadow"
                >
                  Create Student
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* ADD CLASS MODAL */}
      {showAddClassModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-6 z-50 animate-fadeIn">
          <div className="bg-white max-w-md w-full p-8 rounded-3xl shadow-2xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-extrabold text-slate-900">Create New Class</h3>
              <button
                onClick={() => setShowAddClassModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateClass} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-600 mb-1">Class Name *</label>
                <input
                  type="text"
                  required
                  value={newClassName}
                  onChange={e => setNewClassName(e.target.value)}
                  placeholder="e.g. Lavender Room (Early Years)"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">Description / Focus</label>
                <textarea
                  rows={3}
                  value={newClassDesc}
                  onChange={e => setNewClassDesc(e.target.value)}
                  placeholder="e.g. Focus on foundational joint attention and communication skills"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50"
                ></textarea>
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowAddClassModal(false)}
                  className="flex-1 py-2.5 rounded-xl font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 rounded-xl font-bold bg-indigo-600 text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 cursor-pointer"
                >
                  Create Class
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* ADD PARENT MODAL */}
      {showAddParentModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-6 z-50 animate-fadeIn">
          <div className="bg-white max-w-md w-full p-8 rounded-3xl shadow-2xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-extrabold text-slate-900">Create Parent Account</h3>
              <button
                onClick={() => setShowAddParentModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateParent} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-bold text-slate-600 mb-1">Parent / Guardian Full Name *</label>
                <input
                  type="text"
                  required
                  value={newParentForm.full_name}
                  onChange={e => setNewParentForm(prev => ({ ...prev, full_name: e.target.value }))}
                  placeholder="e.g. David Lin"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Username *</label>
                  <input
                    type="text"
                    required
                    value={newParentForm.username}
                    onChange={e => setNewParentForm(prev => ({ ...prev, username: e.target.value }))}
                    placeholder="e.g. david_parent"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Temporary Password *</label>
                  <input
                    type="text"
                    required
                    value={newParentForm.password}
                    onChange={e => setNewParentForm(prev => ({ ...prev, password: e.target.value }))}
                    placeholder="e.g. parent123"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">Link to Student *</label>
                <select
                  value={newParentForm.student_id}
                  onChange={e => setNewParentForm(prev => ({ ...prev, student_id: e.target.value }))}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium"
                >
                  {students.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.full_name} ({s.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">Relationship</label>
                <input
                  type="text"
                  value={newParentForm.relationship}
                  onChange={e => setNewParentForm(prev => ({ ...prev, relationship: e.target.value }))}
                  placeholder="e.g. Mother, Father, Guardian"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Contact Email</label>
                  <input
                    type="email"
                    value={newParentForm.email}
                    onChange={e => setNewParentForm(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="parent@example.com"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Contact Phone</label>
                  <input
                    type="tel"
                    value={newParentForm.phone}
                    onChange={e => setNewParentForm(prev => ({ ...prev, phone: e.target.value }))}
                    placeholder="+1 (555) 000-0000"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50"
                  />
                </div>
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowAddParentModal(false)}
                  className="flex-1 py-2.5 rounded-xl font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 rounded-xl font-bold bg-indigo-600 text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 cursor-pointer"
                >
                  Create Parent Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* EDIT STUDENT PROFILE MODAL */}
      {showEditStudentModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 z-50 animate-fadeIn overflow-y-auto">
          <div className="bg-white max-w-2xl w-full p-6 sm:p-8 rounded-3xl shadow-2xl border border-slate-200 space-y-4 my-8 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b pb-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">✏️</span>
                <div>
                  <h3 className="text-xl font-extrabold text-slate-900">Edit Student Profile & IEP Goals</h3>
                  <span className="text-xs text-slate-500 font-mono">ID: {editStudentForm.id}</span>
                </div>
              </div>
              <button
                onClick={() => setShowEditStudentModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            {editStudentSuccess && (
              <div className="p-3 rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-900 text-xs font-bold">
                {editStudentSuccess}
              </div>
            )}
            {editStudentError && (
              <div className="p-3 rounded-xl bg-rose-100 border border-rose-300 text-rose-900 text-xs font-bold">
                {editStudentError}
              </div>
            )}

            <form onSubmit={handleSaveStudentEdit} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Student Full Name *</label>
                  <input
                    type="text"
                    required
                    value={editStudentForm.full_name}
                    onChange={e => setEditStudentForm(prev => ({ ...prev, full_name: e.target.value }))}
                    placeholder="e.g. Alex Miller"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-semibold"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Login Username *</label>
                  <input
                    type="text"
                    required
                    value={editStudentForm.username}
                    onChange={e => setEditStudentForm(prev => ({ ...prev, username: e.target.value }))}
                    placeholder="e.g. alex"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono font-semibold"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">Student uses this to log into games portal</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Age *</label>
                  <input
                    type="number"
                    min={3}
                    max={18}
                    required
                    value={editStudentForm.age}
                    onChange={e => setEditStudentForm(prev => ({ ...prev, age: parseInt(e.target.value) || 7 }))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Date of Birth</label>
                  <input
                    type="date"
                    value={editStudentForm.dob}
                    onChange={e => setEditStudentForm(prev => ({ ...prev, dob: e.target.value }))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-xs"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Assigned Classroom</label>
                  <select
                    value={editStudentForm.class_id}
                    onChange={e => setEditStudentForm(prev => ({ ...prev, class_id: e.target.value }))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium"
                  >
                    {classes.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Avatar Selection */}
              <div>
                <label className="block font-bold text-slate-700 mb-1.5">Avatar Persona</label>
                <div className="flex gap-3">
                  {[
                    { id: 'boy-1', label: '👦 Boy 1' },
                    { id: 'boy-2', label: '🧒 Boy 2' },
                    { id: 'girl-1', label: '👧 Girl 1' },
                    { id: 'girl-2', label: '👱‍♀️ Girl 2' },
                  ].map(av => (
                    <button
                      key={av.id}
                      type="button"
                      onClick={() => setEditStudentForm(prev => ({ ...prev, avatar: av.id }))}
                      className={`flex-1 py-2 rounded-xl border text-xs font-bold transition-all cursor-pointer ${
                        editStudentForm.avatar === av.id
                          ? 'border-indigo-600 bg-indigo-50 text-indigo-700 shadow-xs'
                          : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {av.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* IEP Objectives */}
              <div>
                <label className="block font-bold text-slate-700 mb-1">Individualized Education Program (IEP) Objectives</label>
                <textarea
                  rows={2}
                  value={editStudentForm.learning_objectives}
                  onChange={e => setEditStudentForm(prev => ({ ...prev, learning_objectives: e.target.value }))}
                  placeholder="e.g. Develop joint attention, practice turn-taking, expand expressive vocabulary"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium leading-relaxed"
                />
              </div>

              {/* Interests & Preferred Activities */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Student Interests & High-Motivation Topics</label>
                  <input
                    type="text"
                    value={editStudentForm.interests}
                    onChange={e => setEditStudentForm(prev => ({ ...prev, interests: e.target.value }))}
                    placeholder="e.g. Trains, bubbles, water play, animals"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Preferred Classroom Activities</label>
                  <input
                    type="text"
                    value={editStudentForm.preferred_activities}
                    onChange={e => setEditStudentForm(prev => ({ ...prev, preferred_activities: e.target.value }))}
                    placeholder="e.g. Visual matching, sensory sorting"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium"
                  />
                </div>
              </div>

              {/* Support Requirements */}
              <div>
                <label className="block font-bold text-slate-700 mb-1">Classroom Accommodations & Sensory Support</label>
                <textarea
                  rows={2}
                  value={editStudentForm.support_requirements}
                  onChange={e => setEditStudentForm(prev => ({ ...prev, support_requirements: e.target.value }))}
                  placeholder="e.g. Responds best to visual timers and gentle auditory chimes; avoid sudden loud buzzer sounds"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium leading-relaxed"
                />
              </div>

              <div className="pt-3 border-t border-slate-100 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowEditStudentModal(false)}
                  className="flex-1 py-2.5 rounded-xl font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editStudentSaving}
                  className="flex-1 py-2.5 rounded-xl font-bold bg-indigo-600 text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {editStudentSaving ? 'Saving...' : 'Save Student Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT PARENT PROFILE MODAL */}
      {showEditParentModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 z-50 animate-fadeIn overflow-y-auto">
          <div className="bg-white max-w-lg w-full p-6 sm:p-8 rounded-3xl shadow-2xl border border-slate-200 space-y-4 my-8">
            <div className="flex justify-between items-center border-b pb-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">👪</span>
                <div>
                  <h3 className="text-xl font-extrabold text-slate-900">Edit Parent Account & Link</h3>
                  <span className="text-xs text-slate-500 font-mono">ID: {editParentForm.id}</span>
                </div>
              </div>
              <button
                onClick={() => setShowEditParentModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            {editParentSuccess && (
              <div className="p-3 rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-900 text-xs font-bold">
                {editParentSuccess}
              </div>
            )}
            {editParentError && (
              <div className="p-3 rounded-xl bg-rose-100 border border-rose-300 text-rose-900 text-xs font-bold">
                {editParentError}
              </div>
            )}

            <form onSubmit={handleSaveParentEdit} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Guardian Full Name *</label>
                <input
                  type="text"
                  required
                  value={editParentForm.display_name}
                  onChange={e => setEditParentForm(prev => ({ ...prev, display_name: e.target.value }))}
                  placeholder="e.g. Elena Miller"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-semibold"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Username *</label>
                  <input
                    type="text"
                    required
                    value={editParentForm.username}
                    onChange={e => setEditParentForm(prev => ({ ...prev, username: e.target.value }))}
                    placeholder="e.g. parent"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono font-semibold"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Relationship</label>
                  <input
                    type="text"
                    value={editParentForm.relationship}
                    onChange={e => setEditParentForm(prev => ({ ...prev, relationship: e.target.value }))}
                    placeholder="e.g. Mother, Father, Guardian"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Linked Student *</label>
                <select
                  value={editParentForm.student_id}
                  onChange={e => setEditParentForm(prev => ({ ...prev, student_id: e.target.value }))}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-semibold text-slate-800"
                >
                  {students.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.full_name} ({s.id})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Contact Email</label>
                  <input
                    type="email"
                    value={editParentForm.email}
                    onChange={e => setEditParentForm(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="parent@example.com"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Contact Phone</label>
                  <input
                    type="tel"
                    value={editParentForm.phone}
                    onChange={e => setEditParentForm(prev => ({ ...prev, phone: e.target.value }))}
                    placeholder="+1 (555) 000-0000"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowEditParentModal(false)}
                  className="flex-1 py-2.5 rounded-xl font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editParentSaving}
                  className="flex-1 py-2.5 rounded-xl font-bold bg-indigo-600 text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {editParentSaving ? 'Saving...' : 'Save Parent Details'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 1-Click IEP Clinical Summary Modal */}
      {showIepModal && selectedStudentDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-4xl w-full p-8 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto space-y-6">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b pb-5">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-3 py-0.5 rounded-full text-xs font-black bg-indigo-100 text-indigo-800 border border-indigo-200 uppercase tracking-widest">
                    Official IEP Clinical Summary
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Date: {new Date().toLocaleDateString()}</span>
                </div>
                <h2 className="text-2xl font-black text-slate-900 tracking-tight">
                  Individualized Education Program Progress Record
                </h2>
                <p className="text-xs text-slate-500">
                  Autism Spectrum & Developmental Skill Coordination Record • Lead Educator: Ms. Sarah Wilson
                </p>
              </div>

              <div className="flex items-center gap-2 no-print">
                <button
                  onClick={() => window.print()}
                  className="btn-3d btn-3d-blue px-4 py-2 rounded-xl text-xs font-black text-white shadow-xs cursor-pointer flex items-center gap-1.5"
                >
                  <span>🖨️</span> Print / Save PDF
                </button>
                <button
                  onClick={() => setShowIepModal(false)}
                  className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 font-black flex items-center justify-center cursor-pointer"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Student Identification Strip */}
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-slate-400 font-bold block uppercase text-[10px]">Student Name</span>
                <span className="font-black text-slate-800 text-sm">{selectedStudentDetail.full_name}</span>
              </div>
              <div>
                <span className="text-slate-400 font-bold block uppercase text-[10px]">Student ID / Roll No</span>
                <span className="font-black text-indigo-700 font-mono text-sm">{selectedStudentDetail.id}</span>
              </div>
              <div>
                <span className="text-slate-400 font-bold block uppercase text-[10px]">Age & Classroom</span>
                <span className="font-bold text-slate-800 text-sm">{selectedStudentDetail.age || 7} yrs • {selectedStudentDetail.class_name || 'Sunflower Room'}</span>
              </div>
              <div>
                <span className="text-slate-400 font-bold block uppercase text-[10px]">Primary Guardian</span>
                <span className="font-bold text-slate-800 text-sm">{selectedStudentDetail.parent_name || 'Elena Miller'}</span>
              </div>
            </div>

            {/* IEP Learning Goals & Sensory Accommodations */}
            <div className="grid md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-amber-50/70 rounded-2xl border border-amber-200 space-y-1.5">
                <span className="font-black text-amber-900 block text-xs flex items-center gap-1.5">
                  <span>🎯</span> Targeted IEP Behavioral Objectives
                </span>
                <p className="text-slate-700 leading-relaxed font-medium">
                  {selectedStudentDetail.learning_objectives || 'Develop joint attention, practice reciprocal waiting during turn-taking routines, and expand spoken sentence complexity.'}
                </p>
              </div>

              <div className="p-4 bg-sky-50/70 rounded-2xl border border-sky-200 space-y-1.5">
                <span className="font-black text-sky-900 block text-xs flex items-center gap-1.5">
                  <span>🛡️</span> Sensory Accommodations & Support Protocols
                </span>
                <p className="text-slate-700 leading-relaxed font-medium">
                  {selectedStudentDetail.support_requirements || 'Low auditory stress, visual countdown timer, positive reinforcement tokens, prompt fading on motor cues.'}
                </p>
              </div>
            </div>

            {/* Developmental Skill Radar Metrics */}
            <div className="space-y-3">
              <h3 className="font-extrabold text-sm text-slate-900 flex items-center gap-1.5">
                <span>📊</span> Standardized Skill Domain Assessment
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                {[
                  { domain: 'Motor Coordination', score: 85, color: 'bg-emerald-500' },
                  { domain: 'Visual & Gaze Focus', score: 90, color: 'bg-sky-500' },
                  { domain: 'Emotion Recognition', score: 75, color: 'bg-amber-500' },
                  { domain: 'Spoken Communication', score: 80, color: 'bg-indigo-500' },
                  { domain: 'Social Turn-Taking', score: 70, color: 'bg-purple-500' },
                  { domain: 'Daily Living Routines', score: 82, color: 'bg-teal-500' },
                ].map(item => (
                  <div key={item.domain} className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
                    <div className="flex justify-between font-bold text-slate-700">
                      <span>{item.domain}</span>
                      <span className="font-black text-indigo-700">{item.score}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div className={`h-full ${item.color} rounded-full`} style={{ width: `${item.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Teacher Clinical Sign-Off */}
            <div className="pt-4 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs text-slate-500">
              <div>
                <span className="block font-bold text-slate-700">Educator Evaluation Status: Verified & Completed</span>
                <span>Document prepared for district multi-disciplinary team evaluation.</span>
              </div>
              <div className="text-right">
                <span className="font-mono text-slate-400">Signature: _______________________</span>
                <span className="block text-[11px] font-bold text-slate-600 mt-1">Ms. Sarah Wilson, Lead Special Educator</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
