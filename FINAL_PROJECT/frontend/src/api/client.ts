/**
 * API Client — Connects frontend to FastAPI backend
 */

const API_BASE = '/api'

function getAuthHeader(): Record<string, string> {
  try {
    const raw = localStorage.getItem('skillspark-auth')
    if (raw) {
      const parsed = JSON.parse(raw)
      const token = parsed?.state?.token
      if (token) {
        return { Authorization: `Bearer ${token}` }
      }
    }
  } catch (e) {
    // ignore
  }
  return {}
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const authHeader = getAuthHeader()
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...authHeader,
      ...options?.headers,
    },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json()
}

// ─── Health ──────────────────────────────────────────────────────────

export const apiHealth = () => apiFetch<{ status: string }>('/health')

// ─── Games Catalogue ─────────────────────────────────────────────────

export const apiGetGames = () => apiFetch<any[]>('/games')

// ─── Game Launcher (Python games) ────────────────────────────────────

export const apiLaunchGame = (gameId: string, childId: string) =>
  apiFetch<{ success: boolean; pid?: number; error?: string }>(`/games/${gameId}/launch`, {
    method: 'POST',
    body: JSON.stringify({ child_id: childId }),
  })

export const apiStopGame = (gameId: string, childId: string) =>
  apiFetch<{ success: boolean; stats?: any }>(`/games/${gameId}/stop`, {
    method: 'POST',
    body: JSON.stringify({ child_id: childId }),
  })

export const apiGameStatus = (gameId: string, childId: string) =>
  apiFetch<{ running: boolean; pid?: number }>(`/games/${gameId}/status/${childId}`)

export const getGameStreamUrl = (gameId: string, childId: string) =>
  `/api/games/${gameId}/stream?child_id=${encodeURIComponent(childId)}`

export const apiGameClick = (gameId: string, childId: string, xPct: number, yPct: number) =>
  apiFetch<{ success: boolean; stats?: any }>(`/games/${gameId}/click`, {
    method: 'POST',
    body: JSON.stringify({ child_id: childId, x_pct: xPct, y_pct: yPct }),
  })

export const apiGameSpeech = (gameId: string, childId: string, text: string) =>
  apiFetch<{ success: boolean; stats?: any }>(`/games/${gameId}/speech`, {
    method: 'POST',
    body: JSON.stringify({ child_id: childId, text }),
  })

export const apiStreamStatus = (gameId: string, childId: string) =>
  apiFetch<{ is_running: boolean; score: number; streak: number; status?: string; accuracy?: number; fps?: number; resolution?: string }>(
    `/games/${gameId}/stream-status/${childId}`
  )

export const apiReloadGame = (gameId: string, childId: string = 'demo-child') =>
  apiFetch<{ success: boolean; message: string; stats?: any }>(`/games/${gameId}/reload`, {
    method: 'POST',
    body: JSON.stringify({ child_id: childId }),
  })

// ─── Sessions ────────────────────────────────────────────────────────

export const apiCreateSession = (data: {
  child_id: string; game_id: string; difficulty?: string
}) =>
  apiFetch<{ session_id: string }>('/sessions', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiEndSession = (sessionId: string, data: {
  status: string; metrics?: Record<string, any>
}) =>
  apiFetch<any>(`/sessions/${sessionId}/end`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

// ─── Student Model ───────────────────────────────────────────────────

export const apiGetStudentModel = (childId: string) =>
  apiFetch<{
    child_id: string
    skills: Record<string, { estimate: number; label: string; sessions: number }>
    level_readiness: Record<number, { ready: boolean; score: number }>
  }>(`/student-model/${childId}`)

export const apiUpdateStudentModel = (childId: string, data: {
  game_id: string; metrics?: Record<string, any>; difficulty?: string
}) =>
  apiFetch<{ updated_skills: Record<string, number> }>(`/student-model/${childId}/update`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

// ─── Adaptation ──────────────────────────────────────────────────────

export const apiGetAdaptation = (childId: string, data: {
  game_id: string; current_difficulty?: string; recent_performance?: number
}) =>
  apiFetch<{
    decision: { action: string; difficulty: string; source: string; reason?: string }
  }>(`/adaptation/${childId}/decide`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

// ─── Levels ──────────────────────────────────────────────────────────

export const apiGetLevels = (childId: string) =>
  apiFetch<{
    levels: Record<number, { unlocked: boolean; readiness_score: number }>
  }>(`/levels/${childId}`)

// ─── Consent ─────────────────────────────────────────────────────────

export const apiRecordConsent = (childId: string, data: {
  consent_type: string; granted: boolean
}) =>
  apiFetch<any>(`/consent/${childId}`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiGetConsent = (childId: string) =>
  apiFetch<{ consents: Record<string, boolean> }>(`/consent/${childId}`)

// ─── Settings ────────────────────────────────────────────────────────

export const apiGetSettings = (childId: string) =>
  apiFetch<{ settings: Record<string, any> }>(`/settings/${childId}`)

export const apiUpdateSettings = (childId: string, data: Record<string, any>) =>
  apiFetch<any>(`/settings/${childId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })

// ─── Progress ────────────────────────────────────────────────────────

export const apiGetProgress = (childId: string) =>
  apiFetch<{
    child_id: string
    total_sessions: number
    total_duration_seconds: number
    games_played: Record<string, number>
    recent_sessions: any[]
  }>(`/progress/${childId}`)

// ─── Children ────────────────────────────────────────────────────────

export const apiGetChildren = () => apiFetch<any[]>('/children')

export const apiCreateChild = (data: {
  display_name: string; avatar?: string; caregiver_id?: string
}) =>
  apiFetch<{ child_id: string }>('/children', {
    method: 'POST',
    body: JSON.stringify(data),
  })

// ─── Phase 1 & 2 Platform Management & Auth APIs ─────────────────────

export const apiLogin = (data: { username: string; password?: string; pin?: string; role?: string }) =>
  apiFetch<{ success: boolean; token: string; user: any }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiTeacherDashboard = () =>
  apiFetch<any>('/teacher/dashboard')

export const apiTeacherStudents = () =>
  apiFetch<any[]>('/teacher/students')

export const apiCreateStudent = (data: any) =>
  apiFetch<any>('/teacher/students', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiStudentDetail = (studentId: string) =>
  apiFetch<any>(`/teacher/students/${studentId}`)

export const apiUpdateStudent = (studentId: string, data: any) =>
  apiFetch<any>(`/teacher/students/${studentId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })

export const apiTeacherClasses = () =>
  apiFetch<any[]>('/teacher/classes')

export const apiCreateClass = (data: { name: string; description?: string }) =>
  apiFetch<any>('/teacher/classes', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiGetParents = () =>
  apiFetch<any[]>('/teacher/parents')

export const apiCreateParent = (data: { full_name: string; username: string; password?: string; student_id: string; relationship?: string; email?: string; phone?: string }) =>
  apiFetch<any>('/teacher/parents', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiAddTeacherObservation = (data: any) =>
  apiFetch<any>('/teacher/observations', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiParentChildren = (parentId?: string) =>
  apiFetch<any[]>(`/parent/children${parentId ? `?parent_id=${parentId}` : ''}`)

export const apiAddParentObservation = (data: any) =>
  apiFetch<any>('/parent/observations', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiAddParentFeedback = (data: any) =>
  apiFetch<any>('/parent/feedback', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiGetMessages = (studentId: string = 'STU-1001') =>
  apiFetch<any[]>(`/messages?student_id=${studentId}`)

export const apiSendMessage = (data: { sender_id: string; receiver_id: string; student_id?: string; content: string }) =>
  apiFetch<any>('/messages', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiGetStudentAssignments = (studentId: string) =>
  apiFetch<any[]>(`/students/${studentId}/assignments`)

export const apiGetStudentProfile = (studentId: string) =>
  apiFetch<{
    student_id: string
    full_name: string
    dob?: string
    age?: number
    avatar?: string
    class_name?: string
    learning_objectives?: string
    support_requirements?: string
    teacher_name?: string
    stars_earned?: number
    completed_quests?: number
  }>(`/students/${studentId}/profile`)

export const apiCreateAssignment = (data: any) =>
  apiFetch<any>('/teacher/assignments', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiDeleteAssignment = (assignmentId: string) =>
  apiFetch<any>(`/teacher/assignments/${assignmentId}`, {
    method: 'DELETE',
  })

export const apiUnassignGame = (studentId: string, gameId: string) =>
  apiFetch<any>(`/teacher/students/${studentId}/assignments/game/${gameId}`, {
    method: 'DELETE',
  })

export const apiUpdateAssignmentDifficulty = (assignmentId: string, difficulty: string) =>
  apiFetch<any>(`/teacher/assignments/${assignmentId}/difficulty`, {
    method: 'PUT',
    body: JSON.stringify({ difficulty }),
  })

export const apiReorderAssignments = (studentId: string, assignmentIds: string[]) =>
  apiFetch<any>(`/teacher/students/${studentId}/assignments/reorder`, {
    method: 'POST',
    body: JSON.stringify({ assignment_ids: assignmentIds }),
  })

export const apiBulkAssignStudent = (studentId: string, assignments: { game_id: string; difficulty?: string }[]) =>
  apiFetch<any>(`/teacher/students/${studentId}/assignments/bulk`, {
    method: 'POST',
    body: JSON.stringify({ assignments }),
  })

export const apiBulkAssignClass = (classId: string, assignments: { game_id: string; difficulty?: string }[]) =>
  apiFetch<any>(`/teacher/classes/${classId}/assignments/bulk`, {
    method: 'POST',
    body: JSON.stringify({ assignments }),
  })

export const apiClearPendingAssignments = (studentId: string) =>
  apiFetch<any>(`/teacher/students/${studentId}/assignments/clear-pending`, {
    method: 'DELETE',
  })

export const apiCompleteAssignment = (assignmentId: string) =>
  apiFetch<any>(`/assignments/${assignmentId}/complete`, {
    method: 'POST',
  })

export const apiGetRecommendations = (studentId?: string, status?: string) => {
  const params = new URLSearchParams()
  if (studentId) params.append('student_id', studentId)
  if (status) params.append('status', status)
  const qs = params.toString()
  return apiFetch<any[]>(`/recommendations${qs ? `?${qs}` : ''}`)
}

export const apiTriggerRecommendation = (studentId: string) =>
  apiFetch<any>(`/recommendations/generate/${studentId}`, {
    method: 'POST',
  })

export const apiApproveRecommendation = (recId: string, data?: { teacher_notes?: string; modified_game_id?: string; modified_difficulty?: string }) =>
  apiFetch<any>(`/recommendations/${recId}/approve`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  })

export const apiRejectRecommendation = (recId: string, notes?: string) =>
  apiFetch<any>(`/recommendations/${recId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ teacher_notes: notes || '' }),
  })

export const apiGetStudentReport = (studentId: string) =>
  apiFetch<any>(`/reports/student/${studentId}`)

export const apiGetParentProfile = (parentId?: string) =>
  apiFetch<{ parent: any; children: any[] }>(`/parent/profile${parentId ? `?parent_id=${parentId}` : ''}`)

export const apiUpdateParentProfile = (data: { display_name?: string; email?: string; phone?: string; relationship?: string; password?: string }) =>
  apiFetch<{ success: boolean; message: string }>('/parent/profile', {
    method: 'PUT',
    body: JSON.stringify(data),
  })

// ─── Account Credentials & Password Security Endpoints ──────────────────────

export const apiGetCredentials = () =>
  apiFetch<{
    teacher: any
    students: any[]
    parents: any[]
  }>('/teacher/credentials')

export const apiUpdateTeacherPassword = (newPassword: string, currentPassword?: string) =>
  apiFetch<{ success: boolean; message: string }>('/teacher/password', {
    method: 'PUT',
    body: JSON.stringify({ new_password: newPassword, current_password: currentPassword }),
  })

export const apiUpdateStudentPassword = (studentId: string, newPassword: string) =>
  apiFetch<{ success: boolean; student_id: string; message: string }>(`/teacher/students/${studentId}/password`, {
    method: 'PUT',
    body: JSON.stringify({ new_password: newPassword }),
  })

export const apiUpdateParentPasswordByTeacher = (parentId: string, newPassword: string) =>
  apiFetch<{ success: boolean; parent_id: string; message: string }>(`/teacher/parents/${parentId}/password`, {
    method: 'PUT',
    body: JSON.stringify({ new_password: newPassword }),
  })

export const apiUpdateParentByTeacher = (parentId: string, data: {
  display_name?: string;
  username?: string;
  email?: string;
  phone?: string;
  relationship?: string;
  student_id?: string;
  password?: string;
}) =>
  apiFetch<{ success: boolean; message: string }>(`/teacher/parents/${parentId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })

export const apiParentUpdateChildPassword = (studentId: string, newPassword: string) =>
  apiFetch<{ success: boolean; student_id: string; message: string }>(`/parent/children/${studentId}/password`, {
    method: 'PUT',
    body: JSON.stringify({ new_password: newPassword }),
  })

export const apiParentUpdateOwnPassword = (newPassword: string, currentPassword?: string) =>
  apiFetch<{ success: boolean; message: string }>('/parent/password', {
    method: 'PUT',
    body: JSON.stringify({ new_password: newPassword, current_password: currentPassword }),
  })
