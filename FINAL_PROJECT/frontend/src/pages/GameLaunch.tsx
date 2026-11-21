import { useParams, Link, useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../store/authStore'
import { getGameById, LEVEL_INFO } from '../data/games'
import EvaluationGameCard, { EvaluationGameStats } from '../components/EvaluationGameCard'
import GameIntroOutro from '../components/GameIntroOutro'
import {
  apiLaunchGame,
  apiStopGame,
  apiUpdateStudentModel,
  getGameStreamUrl,
  apiGameClick,
  apiGameSpeech,
  apiStreamStatus,
  apiReloadGame,
  apiGetStudentAssignments,
  apiCompleteAssignment
} from '../api/client'

export default function GameLaunch() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()
  const { unlockedLevels, completeLevel, recordSession, childId, name: childName, role } = useAuthStore()
  const effectiveChildId = childId || 'STU-1001'

  const [gameState, setGameState] = useState<'launch' | 'playing' | 'done'>('launch')
  const [stage, setStage] = useState<'intro' | 'active' | 'outro'>('intro')
  const [playMode, setPlayMode] = useState<'stream' | 'external'>('stream')
  const [viewMode, setViewMode] = useState<'fit' | 'fill'>('fit')
  const [launchError, setLaunchError] = useState<string | null>(null)
  const [evaluationStats, setEvaluationStats] = useState<EvaluationGameStats>({})
  const [streamStats, setStreamStats] = useState<{
    score: number
    streak: number
    status?: string
    fps?: number
    resolution?: string
  }>({
    score: 0,
    streak: 0,
    status: '',
    fps: 30,
    resolution: '1280x720 HD',
  })
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [streamKey, setStreamKey] = useState(0)
  const [isReloading, setIsReloading] = useState(false)
  const [isStreamLoaded, setIsStreamLoaded] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [liveSpeech, setLiveSpeech] = useState<string>('')
  const [isListeningMic, setIsListeningMic] = useState<boolean>(false)
  const [assignments, setAssignments] = useState<any[]>([])
  const [isAssignmentLoaded, setIsAssignmentLoaded] = useState(false)
  const playerContainerRef = useRef<HTMLDivElement>(null)
  const lastSpokenRef = useRef<string>('')
  const lastScoreRef = useRef<number>(0)
  const lastSentSpeechRef = useRef<string>('')
  const speechTimeoutRef = useRef<number | null>(null)
  const interimDebounceRef = useRef<number | null>(null)

  const game = gameId ? getGameById(gameId) : undefined

  useEffect(() => {
    const studentTarget = childId || 'STU-1001'
    apiGetStudentAssignments(studentTarget)
      .then((data) => {
        if (Array.isArray(data)) {
          setAssignments(data)
        }
      })
      .finally(() => {
        setIsAssignmentLoaded(true)
      })
  }, [childId])

  const handleReload = async () => {
    if (!game) return
    setIsReloading(true)
    setIsStreamLoaded(false)
    try {
      await Promise.race([
        apiReloadGame(game.id, effectiveChildId),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 2000))
      ])
    } catch {
      // Reconnect
    } finally {
      setStreamKey(k => k + 1)
      setTimeout(() => setIsReloading(false), 500)
    }
  }

  // Auditory Guidance & Celebratory Chimes for Emotion Mirror
  useEffect(() => {
    if (gameState !== 'playing' || !game || game.id !== 'emotion-mirror' || isMuted) return

    const targetEmotion = (evaluationStats as any)?.target_emotion
    if (targetEmotion && targetEmotion !== lastSpokenRef.current) {
      lastSpokenRef.current = targetEmotion
      const prompts: Record<string, string> = {
        Happy: 'Show me your biggest, brightest smile!',
        Surprised: 'Whoa! Show me your most surprised face!',
        Sad: 'Can you make a gentle sad face?',
        Angry: 'Grrr! Show me an angry face!',
      }
      const prompt = prompts[targetEmotion] || `Can you make a ${targetEmotion} face?`
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel()
        const utterance = new SpeechSynthesisUtterance(prompt)
        utterance.rate = 1.05
        utterance.pitch = 1.15
        window.speechSynthesis.speak(utterance)
      }
    }

    if (streamStats.score > lastScoreRef.current && lastScoreRef.current > 0) {
      try {
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
        if (AudioCtx) {
          const ctx = new AudioCtx()
          const notes = [523.25, 659.25, 783.99, 1046.50]
          notes.forEach((freq, idx) => {
            const osc = ctx.createOscillator()
            const gain = ctx.createGain()
            osc.type = 'sine'
            osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.08)
            gain.gain.setValueAtTime(0.18, ctx.currentTime + idx * 0.08)
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.08 + 0.25)
            osc.connect(gain)
            gain.connect(ctx.destination)
            osc.start(ctx.currentTime + idx * 0.08)
            osc.stop(ctx.currentTime + idx * 0.08 + 0.28)
          })
        }
      } catch {}
    }
    lastScoreRef.current = streamStats.score
  }, [evaluationStats, streamStats.score, gameState, game, isMuted])

  // Periodic poll of stream stats while playing in-browser
  useEffect(() => {
    if (gameState !== 'playing' || playMode !== 'stream' || !game || game.id === 'shopping-adventure' || game.id === 'community-travel-simulator' || game.id === 'school-day-simulator') {
      return
    }

    const interval = setInterval(async () => {
      try {
        const stats = await apiStreamStatus(game.id, effectiveChildId)
        if (stats && stats.is_running) {
          setStreamStats({
            score: stats.score ?? 0,
            streak: stats.streak ?? 0,
            status: stats.status,
            fps: stats.fps ?? 30,
            resolution: stats.resolution ?? '1280x720 HD',
          })
          setEvaluationStats((prev) => ({ ...prev, ...(stats as unknown as EvaluationGameStats) }))
        }
      } catch {
        // Stream not polling or backend busy
      }
    }, 1500)

    return () => clearInterval(interval)
  }, [gameState, playMode, game, childId])

  // Listen for Shopping Adventure, Community Travel & School Day postMessage events from embedded 3D iframes
  useEffect(() => {
    if (gameState !== 'playing' || !game || (game.id !== 'shopping-adventure' && game.id !== 'community-travel-simulator' && game.id !== 'school-day-simulator')) return

    const handleMessage = (e: MessageEvent) => {
      if (!e.data) return

      if (e.data.gameId === 'shopping-adventure' && e.data.type === 'game:completed') {
        const metrics = e.data.metrics || {}
        setEvaluationStats((prev) => ({
          ...prev,
          score: metrics.score ?? 95,
          items_collected: metrics.items_collected ?? 4,
          duration_seconds: metrics.duration_seconds ?? 60,
          accuracy_pct: metrics.accuracy_pct ?? 96,
          social_score: metrics.social_score ?? 100,
          wrong_picks: metrics.wrong_picks ?? 0,
        }))
        handleFinish()
      } else if (e.data.gameId === 'community-travel-simulator' && e.data.type === 'game:completed') {
        const metrics = e.data.metrics || {}
        setEvaluationStats((prev) => ({
          ...prev,
          score: metrics.score ?? 100,
          destination: metrics.destination ?? 'Library',
          route_number: metrics.route_number ?? 12,
          fare_paid: metrics.fare_paid ?? 20,
          payment_method: metrics.payment_method ?? 'Card',
          completed_stages: metrics.completed_stages ?? 6,
          total_stages: 6,
          accuracy_pct: metrics.accuracy_pct ?? 100,
          hints_used: metrics.hints_used ?? 0,
          duration_seconds: metrics.duration_seconds ?? 65,
        }))
        handleFinish()
      } else if (e.data.gameId === 'school-day-simulator' && e.data.type === 'game:completed') {
        const metrics = e.data.metrics || {}
        setEvaluationStats((prev) => ({
          ...prev,
          score: metrics.score ?? 100,
          tasks_completed: metrics.tasks_completed ?? 8,
          total_tasks: 8,
          accuracy_pct: metrics.accuracy_pct ?? 100,
          hints_used: metrics.hints_used ?? 0,
          duration_seconds: metrics.duration_seconds ?? 80,
          social_rating: metrics.social_rating ?? 'Friendly & Cooperative Student',
        }))
        handleFinish()
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [gameState, game?.id])

  // Reset speech buffers and live transcription display on score or round advancement
  useEffect(() => {
    lastSentSpeechRef.current = ''
    setLiveSpeech('')
    if (speechTimeoutRef.current) {
      clearTimeout(speechTimeoutRef.current)
      speechTimeoutRef.current = null
    }
  }, [streamStats.score, streamStats.status, gameState])

  // Dual-Engine Browser Speech Recognition for Talk & Build, Describe the Scene & Object Quest
  useEffect(() => {
    if (gameState !== 'playing' || !game || (game.id !== 'talk-and-build' && game.id !== 'describe-the-scene' && game.id !== 'object-quest-see-say' && game.id !== 'object-quest-3' && game.id !== 'object-quest')) return

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      return
    }

    let recognition: any = null
    let active = true
    let restartTimer: any = null

    const initAndStart = () => {
      if (!active) return
      try {
        recognition = new SpeechRecognition()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = 'en-US'

        const dispatchSpeech = (spoken: string) => {
          const clean = spoken.trim().toLowerCase()
          if (!clean || clean === lastSentSpeechRef.current) return
          lastSentSpeechRef.current = clean
          console.log('[SkillSpark Speech] Dispatching:', clean, 'for game:', game.id, 'child:', effectiveChildId)

          // Clear after 1.5s so child can say same or new word in next round
          window.setTimeout(() => {
            if (lastSentSpeechRef.current === clean) {
              lastSentSpeechRef.current = ''
            }
          }, 1500)

          apiGameSpeech(game.id, effectiveChildId, clean)
            .then((res) => {
              console.log('[SkillSpark Speech] Result:', res)
              if (res.stats) {
                setEvaluationStats((prev) => ({ ...prev, ...res.stats }))
                if (typeof res.stats.score === 'number') {
                  setStreamStats((prev) => ({
                    ...prev,
                    score: res.stats.score,
                    streak: res.stats.streak ?? prev.streak,
                  }))
                }
              }
            })
            .catch((err) => {
              console.warn('[SkillSpark Speech Error]:', err)
            })
        }

        recognition.onstart = () => {
          setIsListeningMic(true)
        }

        recognition.onresult = (event: any) => {
          let interim = ''
          let final = ''
          for (let i = event.resultIndex || 0; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              final += event.results[i][0].transcript
            } else {
              interim += event.results[i][0].transcript
            }
          }

          const heard = (final || interim).trim()
          if (heard) {
            setLiveSpeech(heard)
            if (speechTimeoutRef.current) clearTimeout(speechTimeoutRef.current)
            speechTimeoutRef.current = window.setTimeout(() => {
              setLiveSpeech('')
            }, 1800)
          }

          if (final.trim()) {
            if (interimDebounceRef.current) clearTimeout(interimDebounceRef.current)
            dispatchSpeech(final)
          } else if (interim.trim()) {
            if (interimDebounceRef.current) clearTimeout(interimDebounceRef.current)
            interimDebounceRef.current = window.setTimeout(() => {
              dispatchSpeech(interim)
            }, 250)
          }
        }

        recognition.onerror = (e: any) => {
          if (e?.error === 'not-allowed') {
            setIsListeningMic(false)
          }
        }

        recognition.onend = () => {
          if (active) {
            restartTimer = setTimeout(() => {
              if (active) initAndStart()
            }, 150)
          } else {
            setIsListeningMic(false)
          }
        }

        recognition.start()
      } catch {
        // Recognition not permitted or microphone unavailable
      }
    }

    initAndStart()

    return () => {
      active = false
      if (restartTimer) clearTimeout(restartTimer)
      if (speechTimeoutRef.current) clearTimeout(speechTimeoutRef.current)
      if (interimDebounceRef.current) clearTimeout(interimDebounceRef.current)
      if (recognition) {
        try {
          recognition.abort()
        } catch {}
      }
      setIsListeningMic(false)
      setLiveSpeech('')
      lastSentSpeechRef.current = ''
    }
  }, [gameState, game, childId])

  if (!game) {
    return (
      <div className="min-h-screen bg-playground flex items-center justify-center p-6">
        <div className="fun-card-flat p-10 text-center max-w-md animate-bounceIn">
          <div className="text-6xl mb-4">😕</div>
          <h2 className="font-[var(--font-fun)] font-bold text-2xl mb-2">Game Not Found!</h2>
          <p className="text-[var(--color-text-light)] text-sm mb-6">We couldn't find that game. It might not be ready yet!</p>
          <Link to="/kid/games" className="btn-fun btn-fun-md bg-ocean text-white shadow-lg no-underline">
            🎮 Back to Games
          </Link>
        </div>
      </div>
    )
  }

  const levelInfo = LEVEL_INFO[game.level]
  const isPythonGame = game.runtime === 'python-launched'

  // Teacher-Assigned Quest checks: ONLY apply restrictions to student/kid logins!
  // Teachers (and parents previewing) can play ANY game with zero order or sequence restrictions!
  const isStudent = role === 'kid' || role === 'student'
  const thisAssignment = assignments.find(a => a.game_id === game.id)
  const isAssigned = assignments.length === 0 || !!thisAssignment
  const isUnlockedBySequence = !thisAssignment || thisAssignment.status === 'completed' || thisAssignment.is_unlocked === 1

  const activeAssignment = assignments.find(
    a => a.status !== 'completed' && (a.is_unlocked === 1 || a.is_unlocked === true)
  ) || assignments[0]
  const activeGame = activeAssignment ? getGameById(activeAssignment.game_id) : undefined

  // 1. If student and not assigned by teacher -> Hidden activity
  if (isStudent && isAssignmentLoaded && assignments.length > 0 && !isAssigned) {
    return (
      <div className="min-h-screen bg-playground flex items-center justify-center p-6">
        <div className="fun-card-flat p-10 text-center max-w-lg animate-bounceIn bg-white rounded-3xl shadow-xl border-3 border-amber-300 space-y-4">
          <div className="text-6xl animate-bounce">🛡️</div>
          <div className="inline-block px-3 py-1 rounded-full text-xs font-black bg-amber-100 text-amber-900 border border-amber-300">
            Personalized Quest Mode
          </div>
          <h2 className="font-[var(--font-fun)] font-bold text-2xl text-slate-800">Activity Hidden for Now</h2>
          <p className="text-slate-600 text-sm leading-relaxed">
            Your educator has designed a customized learning quest for you. 
            <span className="font-bold text-slate-800"> "{game.name}"</span> is currently hidden to keep your learning path calm and focused.
          </p>
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            {activeGame && (
              <Link to={`/kid/games/${activeGame.id}`} className="btn-fun bg-emerald-500 hover:bg-emerald-600 text-white font-extrabold px-6 py-3 shadow-md no-underline">
                🚀 Play Active Mission ({activeGame.name})
              </Link>
            )}
            <Link to="/kid" className="btn-fun bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-5 py-3 no-underline border border-slate-300">
              🏠 My Quest Path
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // 2. If student and assigned but sequence locked -> Locked screen
  if (isStudent && isAssignmentLoaded && assignments.length > 0 && !isUnlockedBySequence) {
    return (
      <div className="min-h-screen bg-playground flex items-center justify-center p-6">
        <div className="fun-card-flat p-10 text-center max-w-lg animate-bounceIn bg-white rounded-3xl shadow-xl border-3 border-blue-300 space-y-4">
          <div className="text-6xl animate-bounce">🔒</div>
          <div className="inline-block px-3 py-1 rounded-full text-xs font-black bg-blue-100 text-blue-900 border border-blue-300">
            Step #{thisAssignment?.sequence_order} Locked
          </div>
          <h2 className="font-[var(--font-fun)] font-bold text-2xl text-slate-800">Step Locked in Sequence!</h2>
          <p className="text-slate-600 text-sm leading-relaxed">
            Please complete your previous step first before unlocking <span className="font-bold text-slate-800">"{game.name}"</span>. 
            Step-by-step progress ensures your skills grow steadily!
          </p>
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            {activeGame && (
              <Link to={`/kid/games/${activeGame.id}`} className="btn-fun bg-blue-600 hover:bg-blue-700 text-white font-extrabold px-6 py-3 shadow-md no-underline">
                ▶ Play Current Step ({activeGame.name})
              </Link>
            )}
            <Link to="/kid" className="btn-fun bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-5 py-3 no-underline border border-slate-300">
              🏠 Back to Quest Path
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const handleStartInBrowser = () => {
    setLaunchError(null)
    setPlayMode('stream')
    setStage('intro')
    setGameState('playing')
  }

  const handleStartExternal = async () => {
    setLaunchError(null)
    setPlayMode('external')
    try {
      const result = await apiLaunchGame(game.id, effectiveChildId)
      if (result.success) {
        setGameState('playing')
      } else {
        setLaunchError(result.error || 'Could not launch game')
        setGameState('playing')
      }
    } catch {
      setGameState('playing')
    }
  }

  const handleFinish = () => {
    // If playing in stream, show the themed celebratory outro
    if (playMode === 'stream') {
      setStage('outro')
    } else {
      handleOutroComplete()
    }
  }

  const handleOutroComplete = async () => {
    let finalStats: EvaluationGameStats = {
      score: streamStats.score,
      streak: streamStats.streak,
      ...evaluationStats,
    }

    // Stop active stream or process and retrieve final evaluation stats with timeout safety
    try {
      const stopPromise = apiStopGame(game.id, effectiveChildId)
      const timeoutPromise = new Promise<{ success: boolean; stats?: any }>((resolve) =>
        setTimeout(() => resolve({ success: true, stats: {} }), 1200)
      )
      const stopRes = await Promise.race([stopPromise, timeoutPromise])
      if (stopRes && stopRes.stats) {
        finalStats = { ...finalStats, ...stopRes.stats }
      }
    } catch {
      /* ok */
    }

    setEvaluationStats(finalStats)
    recordSession(game.id, 5)
    completeLevel(game.level)
    setStage('active')
    setGameState('done')

    // Update backend student model (non-blocking)
    try {
      const finalScore = finalStats.score || finalStats.bubbles_popped || finalStats.stars_caught || finalStats.patterns_completed || 10
      await apiUpdateStudentModel(effectiveChildId, {
        game_id: game.id,
        metrics: { score: finalScore, completion_pct: 100, status: 'completed', ...finalStats },
        difficulty: 'easy',
      })
    } catch {
      // Backend busy
    }

    // Complete assignment in database so next sequential game unlocks
    const matchingAsg = assignments.find(a => a.game_id === game.id)
    if (matchingAsg && matchingAsg.status !== 'completed') {
      try {
        await apiCompleteAssignment(matchingAsg.id)
      } catch (err) {
        console.error('Error completing assignment:', err)
      }
    }
  }

  const handleStreamClick = (e: React.MouseEvent<HTMLImageElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const xPct = (e.clientX - rect.left) / rect.width
    const yPct = (e.clientY - rect.top) / rect.height
    apiGameClick(game.id, effectiveChildId, xPct, yPct)
      .then((res) => {
        if (res.stats) {
          setStreamStats({
            score: res.stats.score || streamStats.score,
            streak: res.stats.streak || streamStats.streak,
            status: res.stats.status,
          })
        }
      })
      .catch(() => {})
  }

  const toggleFullscreen = () => {
    if (!playerContainerRef.current) return
    if (!document.fullscreenElement) {
      playerContainerRef.current.requestFullscreen().catch(() => {})
      setIsFullscreen(true)
    } else {
      document.exitFullscreen().catch(() => {})
      setIsFullscreen(false)
    }
  }

  // ─── Playing: Embedded 3D Games (Shopping Adventure, Community Travel & School Day Simulator) ──
  if (gameState === 'playing' && (game.id === 'shopping-adventure' || game.id === 'community-travel-simulator' || game.id === 'school-day-simulator' || game.runtime === 'web-embedded')) {
    const isSchool = game.id === 'school-day-simulator'
    const isTravel = game.id === 'community-travel-simulator'
    const iframeSrc = isSchool
      ? '/games/school-day-simulator/index.html'
      : isTravel
      ? '/games/community-travel-simulator/index.html'
      : '/games/shopping-adventure/index.html'
    const badgeLabel = isSchool
      ? 'Level 5 3D School Campus'
      : isTravel
      ? 'Level 5 3D Community Bus'
      : 'Level 5 3D Supermarket'

    return (
      <div className="fixed inset-0 bg-slate-950 z-50 flex flex-col select-none">
        <div className="h-14 bg-slate-900 border-b border-slate-700/60 px-6 flex items-center justify-between z-50">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{game.icon}</span>
            <span className="text-white font-[var(--font-fun)] font-bold text-base">
              {game.name}
            </span>
            <span className="badge-fun bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs">
              {badgeLabel}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsPaused(true)}
              className="btn-fun btn-fun-sm bg-teal-800 hover:bg-teal-700 text-teal-200 border border-teal-500/50 shadow flex items-center gap-1.5 cursor-pointer"
              title="Take a sensory pause"
            >
              <span>☕</span>
              <span>Take a Break</span>
            </button>
            <button onClick={handleFinish} className="btn-fun btn-fun-sm bg-[var(--color-success)] text-white shadow-lg">
              ✅ I'm Done!
            </button>
            <button
              onClick={async () => {
                try { await apiStopGame(game.id, effectiveChildId) } catch {}
                if (role === 'teacher') {
                  navigate('/teacher')
                } else {
                  setGameState('launch')
                }
              }}
              className="btn-fun btn-fun-sm bg-rose-500 text-white shadow font-bold cursor-pointer"
              title="Exit Game"
            >
              ✕ {role === 'teacher' ? 'Exit Test' : 'Exit'}
            </button>
          </div>
        </div>
        <iframe
          src={iframeSrc}
          className="flex-1 w-full border-none bg-black"
          title={game.name}
          allow="autoplay; camera; microphone"
          sandbox="allow-scripts allow-same-origin"
        />

        {/* Themed Game Outro Experience for 3D Embedded Games */}
        {stage === 'outro' && (
          <GameIntroOutro
            gameId={game.id}
            gameTitle={game.name}
            gameIcon={game.icon}
            type="outro"
            childName={childName || 'Champion'}
            onComplete={handleOutroComplete}
            onSkip={handleOutroComplete}
          />
        )}

        {/* Sensory Break Modal for 3D Embedded Games */}
        {isPaused && (
          <div className="fixed inset-0 z-[100] bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-6 animate-fadeIn">
            <div className="max-w-md w-full bg-white rounded-3xl p-8 text-center shadow-2xl border-4 border-teal-300 animate-bounceIn space-y-5">
              <div className="w-24 h-24 mx-auto rounded-full bg-teal-50 border-4 border-teal-200 flex items-center justify-center text-5xl animate-pulse">
                ☕
              </div>
              <div>
                <h2 className="text-2xl font-black font-[var(--font-fun)] text-slate-800">
                  Sensory Break Time 🌿
                </h2>
                <p className="text-sm font-semibold text-teal-700 mt-1">
                  Take all the time you need. There is no rush!
                </p>
              </div>
              <div className="p-4 bg-teal-50 rounded-2xl border border-teal-100 flex flex-col items-center">
                <div className="w-12 h-12 rounded-full bg-teal-300/60 animate-ping mb-2" style={{ animationDuration: '3s' }} />
                <span className="text-xs font-bold text-teal-800">Breathe in slowly... and breathe out gently 🌸</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Drink some water, stretch your fingers, or just look away from the screen for a moment.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  onClick={() => setIsPaused(false)}
                  className="btn-fun btn-fun-md flex-1 bg-gradient-to-r from-teal-500 to-emerald-500 text-white font-extrabold shadow-lg cursor-pointer"
                >
                  ▶ Ready to Play!
                </button>
                <button
                  onClick={() => { setIsPaused(false); handleFinish(); }}
                  className="btn-fun btn-fun-md flex-1 bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 font-bold text-xs cursor-pointer"
                >
                  ⭐ Save & Finish
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ─── Playing: In-Browser Stream (SAME WINDOW, SAME SCREEN) ──
  if (gameState === 'playing' && playMode === 'stream') {
    const streamUrl = `${getGameStreamUrl(game.id, effectiveChildId)}${streamKey ? `&_k=${streamKey}` : ''}`

    return (
      <div ref={playerContainerRef} className="fixed inset-0 bg-[#0F172A] z-50 flex flex-col select-none">
        {/* Top Control Bar */}
        <header className="h-16 px-6 bg-slate-900/95 backdrop-blur border-b border-slate-700/80 flex items-center justify-between text-white shadow-md">
          <div className="flex items-center gap-3">
            <span className="text-3xl animate-float">{game.icon}</span>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-[var(--font-fun)] font-extrabold text-lg leading-tight tracking-wide">{game.name}</h2>
                <span className="badge-fun text-xs text-white" style={{backgroundColor: levelInfo.color}}>
                  Level {game.level}
                </span>
              </div>
              <span className="text-xs text-sky-300/80 font-medium">{levelInfo.name} • Live in this Window</span>
            </div>
          </div>

          {/* Real-time Game HUD */}
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-2 bg-emerald-950/80 border-2 border-emerald-400/50 px-3.5 py-1.5 rounded-2xl text-emerald-300 font-bold text-sm shadow-md">
              <span className="text-lg">⭐</span>
              <span>Score:</span>
              <span className="text-white text-base font-extrabold">{streamStats.score}</span>
            </div>
            {streamStats.streak > 1 && (
              <div className="hidden sm:flex items-center gap-1.5 bg-amber-950/80 border border-amber-400/50 px-3 py-1.5 rounded-2xl text-amber-300 font-bold text-xs animate-pulse">
                <span>🔥</span>
                <span>x{streamStats.streak} Streak!</span>
              </div>
            )}
            <div className="hidden md:flex items-center gap-1.5 bg-sky-950/80 border border-sky-400/40 px-3 py-1.5 rounded-2xl text-sky-300 font-semibold text-xs shadow">
              <span className="text-emerald-400 font-bold">⚡ {streamStats.fps || 30} FPS</span>
              <span className="text-slate-500">•</span>
              <span className="text-sky-200">{streamStats.resolution || '720p HD'}</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {game.id === 'emotion-mirror' && (
              <button
                onClick={() => setIsMuted(m => !m)}
                className={`btn-3d text-xs px-3.5 py-2 ${
                  isMuted ? 'btn-3d-slate text-slate-400' : 'btn-3d-blue text-sky-100'
                }`}
                title={isMuted ? 'Unmute voice prompts' : 'Mute voice prompts'}
              >
                <span>{isMuted ? '🔇 Muted' : '🔊 Voice ON'}</span>
              </button>
            )}
            <button
              onClick={handleReload}
              disabled={isReloading}
              className="btn-3d btn-3d-amber text-xs px-3.5 py-2 text-amber-950 flex items-center gap-1.5"
              title="Reload game engine and camera"
            >
              <span className={isReloading ? 'animate-spin' : ''}>🔄</span>
              <span>{isReloading ? 'Reloading...' : 'Reload'}</span>
            </button>
            <button
              onClick={() => setViewMode(v => v === 'fill' ? 'fit' : 'fill')}
              className="btn-3d btn-3d-slate text-xs px-3.5 py-2 text-slate-700 flex items-center gap-1.5"
              title="Toggle Fit or Fill screen size"
            >
              <span>{viewMode === 'fill' ? '📺 Fit (16:9)' : '🔲 Fill Screen'}</span>
            </button>
            <button
              onClick={() => setIsPaused(true)}
              className="btn-3d btn-3d-teal text-xs px-3.5 py-2 text-white flex items-center gap-1.5"
              title="Take a sensory pause"
            >
              <span>☕</span>
              <span>Take a Break</span>
            </button>
            <button
              onClick={toggleFullscreen}
              className="btn-3d btn-3d-slate text-xs px-3 py-2 text-slate-700 flex items-center gap-1.5"
              title="Toggle Fullscreen"
            >
              <span>{isFullscreen ? '✕ Normal' : '⛶ Fullscreen'}</span>
            </button>
            <button
              onClick={handleFinish}
              className="btn-3d btn-3d-green text-sm px-5 py-2 text-white flex items-center gap-1.5"
            >
              <span>✅</span>
              <span>I'm Done!</span>
            </button>
            <button
              onClick={async () => {
                try { await apiStopGame(game.id, effectiveChildId) } catch {}
                if (role === 'teacher') {
                  navigate('/teacher')
                } else {
                  setGameState('launch')
                }
              }}
              className="btn-3d btn-3d-rose text-xs px-3.5 py-2 text-white font-black"
              title={role === 'teacher' ? 'Exit test to Teacher Dashboard' : 'Exit to menu'}
            >
              ✕ {role === 'teacher' ? 'Exit Test' : ''}
            </button>
          </div>
        </header>

        {/* TEACCH Visual Schedule Strip */}
        <div className="bg-slate-950/95 border-b border-slate-800 px-6 py-2 flex items-center justify-between text-xs font-bold text-slate-300">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-black tracking-widest text-slate-400">Activity Schedule:</span>
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/90 text-emerald-300 border border-emerald-500/50 text-[11px] font-bold">
                <span>✓</span> 1. Warm-Up & Mic Ready
              </span>
              <span className="text-slate-600 font-black">→</span>
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-500/25 text-sky-200 border border-sky-400/70 text-[11px] font-black animate-pulse shadow-xs">
                <span>🎯</span> 2. Active Quest Play
              </span>
              <span className="text-slate-600 font-black">→</span>
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 text-slate-400 border border-slate-700 text-[11px]">
                <span>⭐</span> 3. Star Celebration
              </span>
            </div>
          </div>
          <span className="text-[11px] text-slate-400 hidden lg:inline">
            Tap <strong className="text-emerald-400">"✅ I'm Done!"</strong> whenever you want to finish and collect your stars!
          </span>
        </div>

        {/* Live Game Stream Area — Strictly 16:9 Native Aspect Ratio Canvas */}
        <div className="flex-1 relative bg-slate-950 flex items-center justify-center p-2 sm:p-4 overflow-hidden w-full h-full">
          <div className="relative aspect-[16/9] w-full max-w-[calc((100vh-4.5rem)*16/9)] max-h-[calc(100vh-4.5rem)] bg-black rounded-2xl overflow-hidden shadow-2xl border border-slate-700/50 flex items-center justify-center group">
            <img
              src={streamUrl}
              alt={`${game.name} live camera stream`}
              onClick={handleStreamClick}
              onLoad={() => setIsStreamLoaded(true)}
              onError={() => {
                setIsStreamLoaded(false)
                setTimeout(() => setStreamKey(k => k + 1), 2000)
              }}
              className={`w-full h-full select-none cursor-crosshair block transition-all duration-300 ${
                viewMode === 'fill' ? 'object-cover' : 'object-contain'
              }`}
            />

            {/* Connecting / Loading Feedback Overlay */}
            {!isStreamLoaded && stage === 'active' && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/85 backdrop-blur-sm z-10 pointer-events-none">
                <div className="w-14 h-14 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-white font-[var(--font-fun)] font-bold text-lg animate-pulse">
                  Starting {game.name}...
                </p>
                <p className="text-sky-300/80 text-xs mt-1 font-medium">Connecting camera & high-FPS video stream</p>
              </div>
            )}

            {/* Level 1 Themed Game Intro & Outro Experience */}
            {stage === 'intro' && (
              <GameIntroOutro
                gameId={game.id}
                gameTitle={game.name}
                gameIcon={game.icon}
                type="intro"
                childName={childName || 'Champion'}
                onComplete={() => setStage('active')}
                onSkip={() => setStage('active')}
              />
            )}

            {stage === 'outro' && (
              <GameIntroOutro
                gameId={game.id}
                gameTitle={game.name}
                gameIcon={game.icon}
                type="outro"
                childName={childName || 'Champion'}
                onComplete={handleOutroComplete}
                onSkip={handleOutroComplete}
              />
            )}

            {/* In-stream interaction banner */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-slate-950/90 backdrop-blur-xl px-6 py-2.5 rounded-full border-2 border-white/20 text-white text-xs font-bold flex items-center gap-3 shadow-2xl pointer-events-auto">
              <span className="flex items-center gap-2 text-emerald-300 font-black">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
                <span>30+ FPS HD Hardware Stream</span>
              </span>
              <span className="text-white/30">•</span>
              <div className="flex items-center gap-2 text-sky-200">
                {liveSpeech && (
                  <span className="flex items-center gap-1 text-amber-300 animate-pulse">
                    <span className="inline-block w-1.5 h-3 bg-amber-400 rounded-full animate-bounce" />
                    <span className="inline-block w-1.5 h-4 bg-amber-400 rounded-full animate-bounce" style={{animationDelay:'0.1s'}} />
                    <span className="inline-block w-1.5 h-2 bg-amber-400 rounded-full animate-bounce" style={{animationDelay:'0.2s'}} />
                  </span>
                )}
                <span>
                {game.id === 'emotion-mirror'
                  ? '🎭 Match the face & watch magical AR props appear!'
                  : game.id === 'body-says-it'
                  ? '🧍 Watch the body language & hold up 1-4 fingers (or tap a card)!'
                  : game.id === 'object-quest'
                  ? liveSpeech
                    ? `🗣️ Hearing: "${liveSpeech}"`
                    : isListeningMic
                    ? '🎙️ Mic Active • Hold object or tap screen to scan!'
                    : '🔍 Hold an object up to camera, tap to scan, or speak your answer!'
                  : game.id === 'talk-and-build'
                  ? liveSpeech
                    ? `🗣️ Hearing: "${liveSpeech}"`
                    : isListeningMic
                    ? '🎙️ Mic Active • Speak aloud or tap a candy button!'
                    : '🐿️ Talk to Nutmeg the Squirrel or tap your answers!'
                  : game.id === 'describe-the-scene'
                  ? liveSpeech
                    ? `🗣️ Hearing: "${liveSpeech}"`
                    : isListeningMic
                    ? '🎙️ Mic Active • Describe what you see in the video or tap a card!'
                    : '🎬 Watch the scene and describe what is happening!'
                  : game.id === 'object-quest-see-say' || game.id === 'object-quest-3'
                  ? liveSpeech
                    ? `🗣️ Hearing: "${liveSpeech}"`
                    : isListeningMic
                    ? "🎙️ Mic Active • Say the object's name or tap a candy card!"
                    : "🔍 Look at the video and say what you see, or tap a candy card!"
                  : game.id === 'look-point-share' || game.id.includes('point')
                  ? (evaluationStats as any)?.target_animal
                    ? `👉 Point to the ${String((evaluationStats as any).target_animal).toUpperCase()}!`
                    : '👆 Point with your index finger at the animal, or tap it on screen!'
                  : game.id === 'my-turn-your-turn' || game.id.includes('turn')
                  ? (evaluationStats as any)?.turn_state === 'green'
                    ? '🟢 GREEN LIGHT! RAISE YOUR HAND NOW!'
                    : (evaluationStats as any)?.turn_state === 'red'
                    ? '🛑 RED LIGHT! Keep hands down and wait your turn!'
                    : '🔄 Watch the traffic light and take turns!'
                  : game.id === 'copy-my-move' || game.id.includes('copy') || game.id.includes('echo')
                  ? (evaluationStats as any)?.current_gesture
                    ? `🤹 Do this: ${String((evaluationStats as any).current_gesture)}!`
                    : '🤹 Mirror the stick figure pose or hand sign in front of the camera!'
                  : game.id === 'follow-the-star'
                  ? '⭐ Move your hand to guide the star along the trail!'
                  : game.id === 'pattern-trail'
                  ? '✏️ Trace the glowing shape smoothly with your index finger!'
                  : '🫧 Tap or pinch bubbles to pop them!'}
                </span>
              </div>
              <span className="text-white/30">•</span>
              <button
                onClick={() => setViewMode(v => v === 'fill' ? 'fit' : 'fill')}
                className="px-2.5 py-0.5 bg-sky-500/20 hover:bg-sky-500/30 rounded-md text-sky-300 transition-colors cursor-pointer text-xs font-semibold"
              >
                {viewMode === 'fill' ? 'Fit Aspect' : 'Fill Viewport'}
              </button>
            </div>
          </div>
        </div>

        {/* Sensory Break Modal for Stream */}
        {isPaused && (
          <div className="fixed inset-0 z-[100] bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-6 animate-fadeIn">
            <div className="max-w-md w-full bg-white rounded-3xl p-8 text-center shadow-2xl border-4 border-teal-300 animate-bounceIn space-y-5">
              <div className="w-24 h-24 mx-auto rounded-full bg-teal-50 border-4 border-teal-200 flex items-center justify-center text-5xl animate-pulse">
                ☕
              </div>
              <div>
                <h2 className="text-2xl font-black font-[var(--font-fun)] text-slate-800">
                  Sensory Break Time 🌿
                </h2>
                <p className="text-sm font-semibold text-teal-700 mt-1">
                  Take all the time you need. There is no rush!
                </p>
              </div>
              <div className="p-4 bg-teal-50 rounded-2xl border border-teal-100 flex flex-col items-center">
                <div className="w-12 h-12 rounded-full bg-teal-300/60 animate-ping mb-2" style={{ animationDuration: '3s' }} />
                <span className="text-xs font-bold text-teal-800">Breathe in slowly... and breathe out gently 🌸</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Drink some water, stretch your fingers, or just look away from the screen for a moment.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  onClick={() => setIsPaused(false)}
                  className="btn-fun btn-fun-md flex-1 bg-gradient-to-r from-teal-500 to-emerald-500 text-white font-extrabold shadow-lg cursor-pointer"
                >
                  ▶ Ready to Play!
                </button>
                <button
                  onClick={() => { setIsPaused(false); handleFinish(); }}
                  className="btn-fun btn-fun-md flex-1 bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 font-bold text-xs cursor-pointer"
                >
                  ⭐ Save & Finish
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ─── Playing: External Desktop Window (Fallback) ─────────
  if (gameState === 'playing' && playMode === 'external') {
    return (
      <div className="min-h-screen bg-playground flex items-center justify-center p-6">
        <div className="fun-card-flat p-10 text-center max-w-lg animate-fadeInUp">
          <div className="w-24 h-24 rounded-3xl flex items-center justify-center text-5xl mx-auto mb-6 animate-pulse-ring" style={{background: `linear-gradient(135deg, ${levelInfo.color}30, ${levelInfo.color}15)`}}>
            {game.icon}
          </div>
          <h2 className="font-[var(--font-fun)] font-bold text-2xl mb-3">{game.name}</h2>
          {launchError ? (
            <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-800 px-5 py-3 rounded-2xl text-sm font-bold mb-6">
              ⚠️ Note: {launchError}
            </div>
          ) : (
            <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-5 py-3 rounded-2xl text-sm font-bold mb-6 animate-pulse-ring">
              🖥️ Your game is open in another desktop window!
            </div>
          )}
          <p className="text-[var(--color-text-light)] text-sm mb-8">
            Play the game in the other window. When you're done, press <strong>Q</strong> in the game window or click the button below.
          </p>
          <div className="flex flex-col gap-3">
            <button onClick={handleFinish} className="btn-fun btn-fun-lg bg-[var(--color-success)] text-white shadow-lg">
              ✅ I'm Done!
            </button>
            <button
              onClick={() => { setPlayMode('stream'); }}
              className="btn-fun btn-fun-md bg-ocean text-white shadow"
            >
              📺 Switch to In-Browser Screen
            </button>
            <Link to="/kid/games" className="text-[var(--color-text-light)] text-sm font-bold hover:text-[var(--color-text)] transition-colors no-underline">
              ← Back to Games
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // ─── Done: Premium Kid-Friendly Evaluation Game Card ─────────
  if (gameState === 'done') {
    const isLevel2 = game.level === 2
    const isLevel3 = game.level === 3
    return (
      <div className={`min-h-screen ${
        isLevel3
          ? 'bg-gradient-to-b from-[#1C1204] via-[#2A1805] to-[#120B02]'
          : isLevel2
          ? 'bg-gradient-to-b from-[#080518] via-[#100B29] to-[#0A071E]'
          : 'bg-playground'
      } flex items-center justify-center p-4 sm:p-6 transition-colors duration-700`}>
        <EvaluationGameCard
          game={game}
          levelInfo={levelInfo}
          stats={evaluationStats}
          childName={childName || 'Champion'}
          onPlayAgain={() => {
            setStreamStats({
              score: 0,
              streak: 0,
              status: '',
              fps: 30,
              resolution: '1280x720 HD',
            })
            setEvaluationStats({})
            setStage('intro')
            setPlayMode('stream')
            setGameState('playing')
          }}
        />
      </div>
    )
  }

  // ─── Launch Page ──────────────────────────────────────
  return (
    <div className="min-h-screen bg-playground">
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/80 border-b-3 border-[var(--color-border)]">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          {role === 'teacher' ? (
            <Link to="/teacher" className="flex items-center gap-2 no-underline text-indigo-700 hover:text-indigo-900 transition-colors font-extrabold text-sm">
              ← Back to Educator Console
            </Link>
          ) : (
            <Link to="/kid/games" className="flex items-center gap-2 no-underline text-[var(--color-text-light)] hover:text-[var(--color-text)] transition-colors font-bold text-sm">
              ← Back to Games
            </Link>
          )}

          {role === 'teacher' && (
            <span className="px-3 py-1 rounded-full text-xs font-black bg-indigo-100 text-indigo-800 border border-indigo-200 flex items-center gap-1.5">
              <span>👨‍🏫</span>
              <span>Teacher Test Preview Mode</span>
            </span>
          )}
        </div>
      </nav>

      <div className="max-w-xl mx-auto px-6 py-10">
        {role === 'teacher' && (
          <div className="mb-6 p-4 rounded-2xl bg-indigo-50 border-2 border-indigo-200 text-indigo-950 text-xs shadow-xs animate-fadeInUp flex items-start gap-3">
            <span className="text-2xl shrink-0">👨‍🏫</span>
            <div className="space-y-0.5">
              <div className="font-extrabold text-sm text-indigo-900">Educator Test Sandbox</div>
              <p className="text-indigo-700">
                You are testing <strong>{game.name}</strong> (Level {game.level}). All AI camera tracking, speech models, and interactive controls run live in this preview.
              </p>
            </div>
          </div>
        )}

        {/* Game Header Card */}
        <div className="fun-card-flat p-10 text-center mb-6 animate-fadeInUp" style={{background: `linear-gradient(135deg, ${levelInfo.color}15, ${levelInfo.color}05)`}}>
          <div className="w-28 h-28 rounded-3xl flex items-center justify-center text-6xl mx-auto mb-6 bg-white shadow-xl border-3 animate-float" style={{borderColor: levelInfo.color}}>
            {game.icon}
          </div>
          <div className="flex items-center justify-center gap-2 mb-3">
            <span className="badge-fun text-white" style={{backgroundColor: levelInfo.color}}>
              Level {game.level}
            </span>
            <span className="badge-fun bg-gray-100 text-[var(--color-text-light)]">{levelInfo.name}</span>
          </div>
          <h1 className="text-3xl font-extrabold mb-3 font-[var(--font-fun)]">{game.name}</h1>
          <p className="text-[var(--color-text-light)] text-sm leading-relaxed max-w-sm mx-auto">{game.description}</p>
        </div>

        {/* What You Need */}
        <div className="fun-card-flat p-6 mb-6 animate-fadeInUp" style={{animationDelay:'0.1s'}}>
          <h3 className="font-[var(--font-fun)] font-bold text-sm mb-4 text-[var(--color-text-light)] uppercase tracking-wider">
            📋 What You'll Need
          </h3>
          <div className="grid gap-3">
            {game.needs.camera && (
              <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-2xl border-2 border-blue-200">
                <span className="text-2xl">📷</span>
                <div><div className="font-bold text-sm text-blue-900">Camera</div><div className="text-xs text-blue-600">For hand or face tracking in this screen</div></div>
              </div>
            )}
            {game.needs.microphone && (
              <div className="flex items-center gap-3 p-4 bg-purple-50 rounded-2xl border-2 border-purple-200">
                <span className="text-2xl">🎤</span>
                <div><div className="font-bold text-sm text-purple-900">Microphone</div><div className="text-xs text-purple-600">For voice input</div></div>
              </div>
            )}
            {game.needs.webgl && (
              <div className="flex items-center gap-3 p-4 bg-orange-50 rounded-2xl border-2 border-orange-200">
                <span className="text-2xl">🖥️</span>
                <div><div className="font-bold text-sm text-orange-900">3D Graphics</div><div className="text-xs text-orange-600">Plays right in your browser</div></div>
              </div>
            )}
            {!game.needs.camera && !game.needs.microphone && !game.needs.webgl && (
              <div className="flex items-center gap-3 p-4 bg-green-50 rounded-2xl border-2 border-green-200">
                <span className="text-2xl">✅</span>
                <div><div className="font-bold text-sm text-green-900">No special hardware</div><div className="text-xs text-green-600">Just your keyboard, touch, and mouse!</div></div>
              </div>
            )}
          </div>
        </div>

        {/* Start Button (In-Browser, Same Screen) */}
        <button
          onClick={handleStartInBrowser}
          className="btn-fun btn-fun-lg w-full text-white shadow-xl animate-fadeInUp flex items-center justify-center gap-2 mb-3"
          style={{backgroundColor: levelInfo.color, animationDelay:'0.2s'}}
        >
          <span>▶</span>
          <span>Play in this Window</span>
        </button>

        {/* Optional External Window Launch */}
        {isPythonGame && (
          <div className="text-center">
            <button
              onClick={handleStartExternal}
              className="text-xs font-semibold text-slate-500 hover:text-slate-700 transition-colors py-2"
            >
              🖥️ Or play in external desktop window
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
