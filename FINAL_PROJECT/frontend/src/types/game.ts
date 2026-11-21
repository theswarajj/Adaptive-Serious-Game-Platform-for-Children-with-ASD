/* ─── Shared Game Integration Contract ──────────────────────────── */

export type RuntimeKind = 'web-embedded' | 'python-launched' | 'python-streamed'

export type InputMode =
  | 'camera-hand'
  | 'camera-pose'
  | 'camera-face'
  | 'speech'
  | 'pointer'
  | 'touch'
  | 'keyboard'
  | 'choice-select'

export type SessionStatus = 'created' | 'running' | 'completed' | 'abandoned' | 'error'

export type GameAvailability = 'available' | 'needs-attention' | 'planned' | 'unavailable'

export interface GameDefinition {
  id: string
  level: 1 | 2 | 3 | 4 | 5
  name: string
  description: string
  runtime: RuntimeKind
  inputModes: InputMode[]
  needs: {
    camera: boolean
    microphone: boolean
    webgl?: boolean
  }
  difficultyScale: string[]
  status: GameAvailability
  sourcePath?: string
  version: string
  icon: string
}

export interface LevelInfo {
  name: string
  color: string
  description: string
}

export interface GameSessionResult {
  schemaVersion: 1
  sessionId: string
  idempotencyKey: string
  gameId: string
  level: 1 | 2 | 3 | 4 | 5
  status: 'completed' | 'abandoned'
  inputMode: InputMode
  difficulty: string
  startedAt: string
  endedAt: string
  durationSeconds: number
  metrics: Record<string, number | string | boolean>
  appVersion: string
  gameVersion: string
}
