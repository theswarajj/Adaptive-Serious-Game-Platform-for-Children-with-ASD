import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type UserRole = 'kid' | 'parent' | 'teacher' | 'student'

export interface UserState {
  role: UserRole | null
  name: string
  childId: string
  userId?: string
  username?: string
  token?: string
  isLoggedIn: boolean

  // Level progression: which levels the kid has unlocked
  // Level 1 is always unlocked. Must complete a level to unlock next.
  unlockedLevels: number[]
  completedLevels: number[]

  // Session history (simple tracking)
  sessionsPlayed: number
  totalMinutes: number
  gamesCompleted: Record<string, number> // gameId -> completionCount

  // Actions
  login: (role: UserRole, name: string) => void
  setAuthSession: (user: { id: string; username: string; display_name: string; role: string; student_id?: string }, token: string) => void
  logout: () => void
  completeLevel: (level: number) => void
  recordSession: (gameId: string, durationMinutes: number) => void
}

export const useAuthStore = create<UserState>()(
  persist(
    (set, get) => ({
      role: null,
      name: '',
      childId: 'STU-1001',
      userId: undefined,
      username: undefined,
      token: undefined,
      isLoggedIn: false,
      unlockedLevels: [1],
      completedLevels: [],
      sessionsPlayed: 0,
      totalMinutes: 0,
      gamesCompleted: {},

      login: (role, name) => set({
        role,
        name,
        isLoggedIn: true,
      }),

      setAuthSession: (user, token) => {
        const mappedRole: UserRole = user.role === 'student' ? 'kid' : (user.role as UserRole)
        set({
          role: mappedRole,
          name: user.display_name,
          userId: user.id,
          username: user.username,
          childId: user.student_id || 'STU-1001',
          token,
          isLoggedIn: true,
        })
      },

      logout: () => set({
        role: null,
        name: '',
        userId: undefined,
        username: undefined,
        token: undefined,
        isLoggedIn: false,
      }),

      completeLevel: (level) => {
        const state = get()
        const newCompleted = state.completedLevels.includes(level)
          ? state.completedLevels
          : [...state.completedLevels, level]
        const nextLevel = level + 1
        const newUnlocked = nextLevel <= 5 && !state.unlockedLevels.includes(nextLevel)
          ? [...state.unlockedLevels, nextLevel]
          : state.unlockedLevels
        set({ completedLevels: newCompleted, unlockedLevels: newUnlocked })
      },

      recordSession: (gameId, durationMinutes) => {
        const state = get()
        const newGamesCompleted = { ...state.gamesCompleted }
        newGamesCompleted[gameId] = (newGamesCompleted[gameId] || 0) + 1
        set({
          sessionsPlayed: state.sessionsPlayed + 1,
          totalMinutes: state.totalMinutes + durationMinutes,
          gamesCompleted: newGamesCompleted,
        })
      },
    }),
    {
      name: 'skillspark-auth',
    }
  )
)
