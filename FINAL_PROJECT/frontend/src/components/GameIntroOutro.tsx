import React, { useEffect, useState, useRef } from 'react'

export type IntroOutroType = 'intro' | 'outro'

interface GameIntroOutroProps {
  gameId: string
  gameTitle: string
  gameIcon: string
  type: IntroOutroType
  childName?: string
  onComplete: () => void
  onSkip?: () => void
}

// ─────────────────────────────────────────────────────────────────────────────
// Audio Synthesizers using browser Web Audio API
// ─────────────────────────────────────────────────────────────────────────────

function playTone(freq: number, type: OscillatorType, duration: number, delay = 0, gainLevel = 0.2) {
  try {
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = type
    osc.frequency.setValueAtTime(freq, ctx.currentTime + delay)

    gain.gain.setValueAtTime(0.001, ctx.currentTime + delay)
    gain.gain.exponentialRampToValueAtTime(gainLevel, ctx.currentTime + delay + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + duration)

    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(ctx.currentTime + delay)
    osc.stop(ctx.currentTime + delay + duration)
  } catch {
    // Restricted by gesture policy
  }
}

function playPopSound() {
  try {
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    // Pitch drop creates realistic bubble/balloon pop
    osc.frequency.setValueAtTime(800, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(140, ctx.currentTime + 0.08)

    gain.gain.setValueAtTime(0.28, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.09)

    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.09)
  } catch {
    /* ok */
  }
}

function playCelebrationFanfare(isStar = false) {
  if (isStar) {
    // Twinkling celestial arpeggio
    const notes = [659.25, 783.99, 987.77, 1318.51, 1567.98]
    notes.forEach((f, i) => playTone(f, 'sine', 0.28, i * 0.1, 0.18))
  } else {
    // Energetic brassy triumph
    const notes = [523.25, 659.25, 783.99, 1046.5]
    notes.forEach((f, i) => playTone(f, 'triangle', 0.22, i * 0.12, 0.25))
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Interactive Balloon Item (Click to Pop in Outro)
// ─────────────────────────────────────────────────────────────────────────────

interface BalloonData {
  id: number
  x: number // percent 5% to 92%
  speed: number // seconds to float up
  delay: number // seconds delay
  size: number // px
  color: string
  highlight: string
  popped: boolean
}

const BALLOON_PALETTE = [
  { color: '#EF4444', highlight: '#FCA5A5' }, // Crimson
  { color: '#3B82F6', highlight: '#93C5FD' }, // Sky
  { color: '#10B981', highlight: '#6EE7B7' }, // Emerald
  { color: '#F59E0B', highlight: '#FDE68A' }, // Amber
  { color: '#8B5CF6', highlight: '#C4B5FD' }, // Purple
  { color: '#EC4899', highlight: '#FBCFE8' }, // Pink
  { color: '#06B6D4', highlight: '#67E8F9' }, // Cyan
]

export default function GameIntroOutro({
  gameId,
  gameTitle,
  gameIcon,
  type,
  childName = 'Champion',
  onComplete,
  onSkip,
}: GameIntroOutroProps) {
  const [countdown, setCountdown] = useState(3)
  const [balloons, setBalloons] = useState<BalloonData[]>([])
  const [popCount, setPopCount] = useState(0)
  const [progress, setProgress] = useState(0)

  const isBubbleHunt = gameId.includes('bubble') || gameId.includes('hunt')
  const isFollowStar = gameId.includes('follow') || gameId.includes('star')
  const isPatternTrail = gameId.includes('pattern') || gameId.includes('trail')
  const isEmotionMirror = gameId.includes('emotion') || gameId.includes('mirror')
  const isBodySaysIt = gameId.includes('body')
  const isObjectQuestL3 = (gameId.includes('object') || gameId.includes('quest')) && (gameId.includes('3') || gameId.includes('see') || gameId.includes('say'))
  const isObjectQuest = (gameId.includes('object') || gameId.includes('quest')) && !isObjectQuestL3
  const isTalkAndBuild = gameId.includes('talk') || gameId.includes('build')
  const isDescribeScene = gameId.includes('describe') || gameId.includes('scene')
  const isLookPointShare = gameId.includes('look') || gameId.includes('point') || gameId.includes('share')
  const isMyTurnYourTurn = gameId.includes('turn')
  const isCopyMyMove = gameId.includes('copy') || gameId.includes('move')
  const isSchoolDay = gameId.includes('school')
  const isCommunityTravel = gameId.includes('travel') || gameId.includes('community')
  const isShoppingAdventure = gameId.includes('shop') || gameId.includes('adventure')

  // Generate balloons for Balloon Pop intro/outro
  useEffect(() => {
    if (isBubbleHunt) {
      const count = type === 'intro' ? 14 : 26
      const generated: BalloonData[] = Array.from({ length: count }, (_, i) => {
        const pal = BALLOON_PALETTE[i % BALLOON_PALETTE.length]
        return {
          id: i,
          x: Math.floor(6 + Math.random() * 88),
          speed: 3.5 + Math.random() * 3.0,
          delay: Math.random() * 1.6,
          size: 55 + Math.floor(Math.random() * 45),
          color: pal.color,
          highlight: pal.highlight,
          popped: false,
        }
      })
      setBalloons(generated)
    }
  }, [isBubbleHunt, type])

  // Play audio when mounting
  useEffect(() => {
    if (type === 'intro') {
      playTone(440, 'triangle', 0.15, 0.05)
      playTone(554.37, 'triangle', 0.15, 0.2)
      playTone(659.25, 'triangle', 0.35, 0.35)
    } else {
      playCelebrationFanfare(isFollowStar)
    }
  }, [type, isFollowStar])

  // Countdown timer for Intro (3 -> 2 -> 1 -> GO)
  useEffect(() => {
    if (type !== 'intro') return

    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval)
          setTimeout(onComplete, 550)
          return 0
        }
        playTone(300 + prev * 120, 'sine', 0.12)
        return prev - 1
      })
    }, 900)

    return () => clearInterval(interval)
  }, [type, onComplete])

  // Outro auto-advance timer (e.g. 3.4 seconds)
  useEffect(() => {
    if (type !== 'outro') return

    const timer = setTimeout(() => {
      onComplete()
    }, 3400)

    // Progress bar fill
    const start = Date.now()
    const pInterval = setInterval(() => {
      const elapsed = Date.now() - start
      const pct = Math.min(100, (elapsed / 3400) * 100)
      setProgress(pct)
      if (pct >= 100) clearInterval(pInterval)
    }, 40)

    return () => {
      clearTimeout(timer)
      clearInterval(pInterval)
    }
  }, [type, onComplete])

  // User click on a balloon to pop it!
  const handlePopBalloon = (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    playPopSound()
    setBalloons((prev) =>
      prev.map((b) => (b.id === id ? { ...b, popped: true } : b))
    )
    setPopCount((c) => c + 1)
  }

  // ───────────────────────────────────────────────────────────────────────────
  // 1. INTRO RENDERING
  // ───────────────────────────────────────────────────────────────────────────
  if (type === 'intro') {
    return (
      <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md select-none animate-fadeIn overflow-hidden">
        
        {/* Floating Balloons Background (for Balloon Pop) */}
        {isBubbleHunt && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {balloons.map((b) => (
              <div
                key={b.id}
                className="absolute -bottom-24"
                style={{
                  left: `${b.x}%`,
                  animation: `floatUpward ${b.speed}s ease-in infinite`,
                  animationDelay: `${b.delay}s`,
                }}
              >
                <div
                  className="rounded-full shadow-lg relative flex items-center justify-center transition-transform hover:scale-110"
                  style={{
                    width: `${b.size}px`,
                    height: `${b.size * 1.25}px`,
                    backgroundColor: b.color,
                    boxShadow: `0 10px 25px ${b.color}66`,
                  }}
                >
                  {/* Gloss shine */}
                  <div
                    className="absolute top-2 left-3 rounded-full opacity-70"
                    style={{
                      width: `${b.size * 0.28}px`,
                      height: `${b.size * 0.45}px`,
                      backgroundColor: b.highlight,
                      transform: 'rotate(-25deg)',
                    }}
                  />
                  {/* String */}
                  <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 w-0.5 h-8 bg-white/40" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Floating Stars Background (for Follow the Star) */}
        {isFollowStar && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {[...Array(24)].map((_, i) => (
              <div
                key={i}
                className="absolute text-amber-300 animate-pulse"
                style={{
                  top: `${Math.random() * 90}%`,
                  left: `${Math.random() * 95}%`,
                  fontSize: `${14 + Math.random() * 26}px`,
                  animationDuration: `${1.2 + Math.random() * 2}s`,
                  animationDelay: `${Math.random() * 2}s`,
                  filter: 'drop-shadow(0 0 10px rgba(251, 191, 36, 0.8))',
                }}
              >
                {i % 3 === 0 ? '✨' : i % 2 === 0 ? '⭐' : '🌟'}
              </div>
            ))}
          </div>
        )}

        {/* Floating Expressive Faces Background (for Emotion Mirror) */}
        {isEmotionMirror && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {['😊', '😮', '😢', '😠', '🎭', '⭐', '✨', '💖'].map((emoji, i) => (
              <div
                key={i}
                className="absolute animate-float"
                style={{
                  top: `${10 + (i * 11) % 80}%`,
                  left: `${8 + (i * 13) % 84}%`,
                  fontSize: `${28 + (i % 3) * 10}px`,
                  animationDuration: `${2.2 + (i % 3) * 0.8}s`,
                  animationDelay: `${i * 0.25}s`,
                  filter: 'drop-shadow(0 4px 12px rgba(139, 92, 246, 0.4))',
                }}
              >
                {emoji}
              </div>
            ))}
          </div>
        )}

        {/* Neon Light Ribbons (for Pattern Trail) */}
        {isPatternTrail && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <svg className="w-full h-full opacity-40">
              <path
                d="M 50 300 Q 300 50, 600 300 T 1200 300"
                fill="none"
                stroke="url(#neonGrad)"
                strokeWidth="16"
                strokeDasharray="20 10"
                className="animate-pulse"
              />
              <defs>
                <linearGradient id="neonGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#38BDF8" />
                  <stop offset="50%" stopColor="#F59E0B" />
                  <stop offset="100%" stopColor="#10B981" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        )}

        {/* Floating Animals & Stars (for Look–Point–Share) */}
        {isLookPointShare && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {['🐶', '🐱', '🐰', '🐷', '👆', '✨', '⭐', '🌟'].map((emoji, i) => (
              <div
                key={i}
                className="absolute animate-float"
                style={{
                  top: `${12 + (i * 11) % 76}%`,
                  left: `${10 + (i * 13) % 80}%`,
                  fontSize: `${28 + (i % 3) * 10}px`,
                  animationDuration: `${2.2 + (i % 3) * 0.8}s`,
                  animationDelay: `${i * 0.25}s`,
                  filter: 'drop-shadow(0 4px 12px rgba(99, 102, 241, 0.45))',
                }}
              >
                {emoji}
              </div>
            ))}
          </div>
        )}

        {/* Floating Storybook & Object Elements (for Level 3 Games) */}
        {(isTalkAndBuild || isDescribeScene || isObjectQuestL3) && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {(isObjectQuestL3 ? ['🍎', '⚽', '📖', '🍊', '☕', '🔑', '⌚', '🎒'] : isDescribeScene ? ['🎬', '🎥', '🍿', '✨', '🌟', '🗣️', '💭', '⭐'] : ['🐿️', '📖', '🌰', '✨', '🌟', '🗣️', '🎈', '⭐']).map((emoji, i) => (
              <div
                key={i}
                className="absolute animate-float"
                style={{
                  top: `${12 + (i * 11) % 76}%`,
                  left: `${10 + (i * 13) % 80}%`,
                  fontSize: `${28 + (i % 3) * 10}px`,
                  animationDuration: `${2.2 + (i % 3) * 0.8}s`,
                  animationDelay: `${i * 0.25}s`,
                  filter: 'drop-shadow(0 4px 12px rgba(245, 158, 11, 0.45))',
                }}
              >
                {emoji}
              </div>
            ))}
          </div>
        )}

        {/* Center Intro Card */}
        <div className="relative bg-white/95 backdrop-blur-xl border-4 border-white/80 rounded-3xl p-6 sm:p-8 max-w-lg w-full text-center shadow-2xl animate-bounceIn z-10">
          
          {/* Badge Icon */}
          <div className="w-24 h-24 mx-auto mb-4 rounded-3xl bg-gradient-to-br from-amber-100 via-sky-100 to-rose-100 flex items-center justify-center text-5xl shadow-md border-3 border-white animate-float">
            {gameIcon}
          </div>

          {/* Level Pill */}
          <span
            className="inline-block px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider text-white shadow-xs mb-2"
            style={{ backgroundColor: isLookPointShare ? '#6366F1' : isTalkAndBuild || isDescribeScene || isObjectQuestL3 ? '#F59E0B' : isEmotionMirror || isBodySaysIt || isObjectQuest ? '#8B5CF6' : '#0284C7' }}
          >
            {isLookPointShare ? 'Level 4 • Joint Attention & Social' : isTalkAndBuild || isDescribeScene || isObjectQuestL3 ? 'Level 3 • Communication' : isEmotionMirror || isBodySaysIt || isObjectQuest ? 'Level 2 • Emotion & Visual' : 'Level 1 • Ready to Play!'}
          </span>

          <h2 className="text-3xl font-black font-[var(--font-fun)] text-slate-800 tracking-tight mb-2">
            {isBubbleHunt && '🎈 Bubble Hunt!'}
            {isFollowStar && '⭐ Follow the Star!'}
            {isPatternTrail && '✏️ Pattern Trail!'}
            {isEmotionMirror && '🎭 Emotion Mirror!'}
            {isBodySaysIt && '🧍 Body Says It!'}
            {isObjectQuest && '🔍 Object Quest!'}
            {isObjectQuestL3 && '🔍 Object Quest: See & Say!'}
            {isTalkAndBuild && '🐿️ Talk & Build!'}
            {isDescribeScene && '🎬 Describe the Scene!'}
            {isLookPointShare && '👆 Look–Point–Share!'}
          </h2>

          <p className="text-sm font-semibold text-slate-600 mb-6 max-w-sm mx-auto">
            {isBubbleHunt && 'Use your fingers to pinch or tap to pop the colorful balloons!'}
            {isFollowStar && 'Move your head and nose into the glowing Star Face and hold steady!'}
            {isPatternTrail && 'Trace along the glowing runway with your index finger!'}
            {isEmotionMirror && 'Watch the cartoon face and copy its emotion with your face!'}
            {isBodySaysIt && 'Watch how the character moves their body and identify their emotion using 1-4 fingers or by tapping!'}
            {isObjectQuest && 'Hold everyday objects up to your camera, let the AI scan them, and tap your answer!'}
            {isObjectQuestL3 && 'Watch the object in the video, speak its name into your microphone, or tap a candy card!'}
            {isTalkAndBuild && 'Watch the scene, listen to Nutmeg the Squirrel, and speak your answer aloud or tap a candy button!'}
            {isDescribeScene && 'Watch the video scene and describe what you see in your own words, or tap clue cards!'}
            {isLookPointShare && 'Look at the target animal, point directly at it with your index finger, or tap it on screen!'}
          </p>

          {/* Big Pulsing Countdown Ring */}
          <div className="relative w-24 h-24 mx-auto mb-6 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-4 border-sky-400 animate-ping opacity-60" />
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-sky-400 to-blue-600 text-white flex items-center justify-center text-4xl font-black font-[var(--font-fun)] shadow-lg transform transition-transform duration-300 scale-105">
              {countdown > 0 ? countdown : 'GO!'}
            </div>
          </div>

          {/* Skip Button */}
          <button
            onClick={onSkip || onComplete}
            className="text-xs font-black tracking-wider uppercase text-slate-400 hover:text-slate-700 py-1 px-4 rounded-full transition-colors cursor-pointer"
          >
            Skip Intro →
          </button>
        </div>
      </div>
    )
  }

  // ───────────────────────────────────────────────────────────────────────────
  // 2. OUTRO RENDERING (Grand Celebration with Balloons / Stars / Ribbons)
  // ───────────────────────────────────────────────────────────────────────────
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-lg select-none animate-fadeIn overflow-hidden">
      
      {/* ── Balloon Pop Outro: Massive Floating Balloon Fiesta ── */}
      {isBubbleHunt && (
        <div className="absolute inset-0 overflow-hidden">
          {balloons.map((b) => (
            <div
              key={b.id}
              onClick={(e) => handlePopBalloon(b.id, e)}
              className="absolute cursor-pointer transition-transform hover:scale-115 active:scale-95"
              style={{
                left: `${b.x}%`,
                bottom: '-120px',
                animation: `floatUpward ${b.speed * 0.9}s ease-in infinite`,
                animationDelay: `${b.delay}s`,
                display: b.popped ? 'none' : 'block',
              }}
              title="Pop me!"
            >
              <div
                className="rounded-full relative flex items-center justify-center shadow-2xl"
                style={{
                  width: `${b.size}px`,
                  height: `${b.size * 1.25}px`,
                  backgroundColor: b.color,
                  boxShadow: `0 12px 30px ${b.color}88`,
                }}
              >
                {/* Gloss highlight */}
                <div
                  className="absolute top-2.5 left-3.5 rounded-full opacity-80"
                  style={{
                    width: `${b.size * 0.3}px`,
                    height: `${b.size * 0.48}px`,
                    backgroundColor: b.highlight,
                    transform: 'rotate(-25deg)',
                  }}
                />
                {/* String */}
                <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-0.5 h-10 bg-white/50" />
                {/* Cute smiling face */}
                <div className="text-white text-xs font-black select-none opacity-80">
                  ✨
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Follow the Star Outro: Cosmic Supernova Star Shower ── */}
      {isFollowStar && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {/* Pulsing Concentric Rings */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-80 h-80 rounded-full border-4 border-amber-400/40 animate-ping" />
            <div
              className="w-96 h-96 rounded-full border-2 border-sky-400/30 animate-ping"
              style={{ animationDelay: '0.4s' }}
            />
          </div>
          {/* Shooting stars */}
          {[...Array(30)].map((_, i) => (
            <div
              key={i}
              className="absolute text-amber-300 animate-wiggle"
              style={{
                top: `${Math.random() * 95}%`,
                left: `${Math.random() * 95}%`,
                fontSize: `${18 + Math.random() * 32}px`,
                filter: 'drop-shadow(0 0 16px rgba(251, 191, 36, 0.9))',
                animationDuration: `${0.8 + Math.random() * 1.2}s`,
              }}
            >
              ⭐
            </div>
          ))}
        </div>
      )}

      {/* ── Pattern Trail Outro: Rainbow Ribbon Streamers & Sparks ── */}
      {isPatternTrail && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(32)].map((_, i) => (
            <div
              key={i}
              className="absolute animate-float"
              style={{
                top: `${Math.random() * 90}%`,
                left: `${Math.random() * 95}%`,
                fontSize: `${20 + Math.random() * 26}px`,
                animationDelay: `${Math.random() * 1.5}s`,
              }}
            >
              {i % 4 === 0 ? '🎨' : i % 3 === 0 ? '✨' : i % 2 === 0 ? '🌈' : '✏️'}
            </div>
          ))}
        </div>
      )}

      {/* Floating celebratory confetti */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <span className="absolute top-10 left-12 text-4xl animate-bounce">🎉</span>
        <span className="absolute top-12 right-14 text-4xl animate-bounce" style={{ animationDelay: '0.3s' }}>✨</span>
        <span className="absolute bottom-12 left-16 text-3xl animate-bounce" style={{ animationDelay: '0.6s' }}>🎊</span>
        <span className="absolute bottom-14 right-16 text-3xl animate-bounce" style={{ animationDelay: '0.9s' }}>🎈</span>
      </div>

      {/* Center Outro Celebration Card */}
      <div className="relative bg-white/95 backdrop-blur-2xl border-4 border-amber-300/80 rounded-3xl p-6 sm:p-9 max-w-lg w-full text-center shadow-[0_25px_60px_-15px_rgba(0,0,0,0.35)] animate-bounceIn z-10">
        
        {/* Celebration Trophy Icon */}
        <div className="w-24 h-24 mx-auto mb-4 rounded-3xl bg-gradient-to-br from-amber-300 to-yellow-500 flex items-center justify-center text-5xl shadow-xl border-4 border-white animate-wiggle">
          🏆
        </div>

        {/* Outro Title */}
        <h2 className="text-3xl sm:text-4xl font-black font-[var(--font-fun)] text-slate-800 tracking-tight mb-2">
          {isBubbleHunt && '🎉 Balloon Pop Victory! 🎈'}
          {isFollowStar && '🌟 Star Catcher Champion! ⭐'}
          {isPatternTrail && '✨ Master Path Tracer! ✏️'}
          {isEmotionMirror && '🎭 Emotion Mirror Master! 🌟'}
          {isBodySaysIt && '🧍 Body Language Champion! 🌟'}
          {isObjectQuest && '🔍 Object Detective Victory! 🌟'}
          {isObjectQuestL3 && '🔍 Object Quest Champion! 🌟'}
          {isTalkAndBuild && '🐿️ Fantastic Storyteller! 📖'}
          {isDescribeScene && '🎬 Master Scene Narrator! 🌟'}
          {isLookPointShare && '🌟 Joint Attention Champion! 👆'}
          {isMyTurnYourTurn && '🔄 Patient Turn-Taking Master! 🚦'}
          {isCopyMyMove && '🤹 Gesture & Pose Champion! 🌟'}
          {isSchoolDay && '🏫 School Day Routine Hero! 🎒'}
          {isCommunityTravel && '🚌 Community Travel Explorer! 🗺️'}
          {isShoppingAdventure && '🛒 Supermarket Shopping Pro! 🛍️'}
        </h2>

        {/* Personalized Praise */}
        <p className="text-base font-bold text-amber-600 mb-2 font-[var(--font-fun)]">
          Sensational Job, {childName}!
        </p>

        <p className="text-sm font-semibold text-slate-600 mb-6 max-w-xs mx-auto">
          {isBubbleHunt && (popCount > 0 ? `You tapped and popped ${popCount} celebration balloons!` : 'You popped all the bubbles with incredible reflexes!')}
          {isFollowStar && 'Super steady head control and stellar tracking precision!'}
          {isPatternTrail && 'Silky-smooth ribbon tracing with razor-sharp accuracy!'}
          {isEmotionMirror && 'Brilliant facial expression control and empathetic mimicry!'}
          {isBodySaysIt && 'Superb postural decoding and body language perception!'}
          {isObjectQuest && 'Awesome object scanning and real-world clue discovery!'}
          {isObjectQuestL3 && 'Sensational spoken vocabulary and lightning-fast everyday object naming!'}
          {isTalkAndBuild && 'You helped Nutmeg discover every clue and built wonderful sentences!'}
          {isDescribeScene && 'Brilliant expressive language, vivid scene descriptions, and great storytelling!'}
          {isLookPointShare && 'Superb gaze following, swift visual search, and razor-sharp pointing accuracy!'}
          {isMyTurnYourTurn && 'Brilliant patience on red lights and quick reactions on green lights!'}
          {isCopyMyMove && 'Incredible movement mirroring, balance, and pose alignment!'}
          {isSchoolDay && 'Fantastic independence navigating daily classroom routines and asking for help!'}
          {isCommunityTravel && 'Wonderful transit navigation, safe community decisions, and bus travel skills!'}
          {isShoppingAdventure && 'Great focus finding items from your list, greeting the cashier, and checking out!'}
        </p>

        {/* Progress Bar auto-filling to Evaluation Card */}
        <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden mb-6 shadow-inner">
          <div
            className="h-full bg-gradient-to-r from-sky-400 via-amber-400 to-emerald-400 transition-all duration-75"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Big Action Button */}
        <button
          onClick={onComplete}
          className="w-full py-4 px-6 rounded-2xl font-black font-[var(--font-fun)] text-lg text-white shadow-xl transition-all transform hover:scale-[1.03] active:scale-[0.98] flex items-center justify-center gap-2 cursor-pointer bg-gradient-to-r from-sky-500 to-emerald-500 hover:from-sky-600 hover:to-emerald-600"
        >
          <span>⭐</span>
          <span>See My Score & Awards!</span>
          <span>→</span>
        </button>
      </div>

      {/* Global CSS for floating upward balloons */}
      <style>{`
        @keyframes floatUpward {
          0% {
            transform: translateY(0) rotate(0deg);
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          90% {
            opacity: 1;
          }
          100% {
            transform: translateY(-110vh) rotate(15deg);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}

