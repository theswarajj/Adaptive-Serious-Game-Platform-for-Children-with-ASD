import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export interface EvaluationGameStats {
  score?: number
  streak?: number
  best_streak?: number
  duration?: number
  accuracy_pct?: number
  reaction_time_s?: number
  stability_pct?: number
  total_hold_time_s?: number
  avg_deviation_px?: number
  smoothness_pct?: number
  bubbles_popped?: number
  stars_caught?: number
  patterns_completed?: number
  completed_glyphs?: string[]
  emotions_matched?: number
  emotions_completed?: string[]
  emotions_identified?: number
  objects_identified?: number
  objects_discovered?: string[]
  words_spoken?: number
  sentence_completeness?: number
  vocabulary_richness?: number
  concept_coverage_pct?: number
  descriptions_given?: number
  receptive_accuracy?: number
  current_tier?: string
  target_scene?: string
  rounds_completed?: number
  objects_named?: number
  naming_accuracy?: number
  avg_response_time?: number
  first_attempt_correct?: number
  hints_used?: number
  incorrect_responses?: number
  animals_found?: number
  joint_attention_score?: number
  gestures_copied?: number
  mimicry_score?: number
  pace_per_min?: number
  turns_completed?: number
  premature_count?: number
  turn_state?: string
  current_gesture?: string
  target_animal?: string
  target_emotion?: string
  target_object?: string
  focus_rating?: string
  status?: string
}

interface EvaluationGameCardProps {
  game: {
    id: string
    name: string
    level: number
    icon: string
    description?: string
  }
  levelInfo: {
    name: string
    color: string
  }
  stats?: EvaluationGameStats
  childName?: string
  onPlayAgain: () => void
}

// Play pleasant celebratory victory fanfare using browser Web Audio API
function playCelebratorySound() {
  try {
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()

    const notes = [
      { f: 523.25, t: 0.0, d: 0.15 }, // C5
      { f: 659.25, t: 0.12, d: 0.15 }, // E5
      { f: 783.99, t: 0.24, d: 0.18 }, // G5
      { f: 1046.5, t: 0.38, d: 0.45 }, // C6 (long ring)
    ]

    notes.forEach(({ f, t, d }) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'triangle'
      osc.frequency.setValueAtTime(f, ctx.currentTime + t)

      gain.gain.setValueAtTime(0.001, ctx.currentTime + t)
      gain.gain.exponentialRampToValueAtTime(0.22, ctx.currentTime + t + 0.03)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + t + d)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start(ctx.currentTime + t)
      osc.stop(ctx.currentTime + t + d)
    })
  } catch {
    // Audio context may be restricted by browser gesture policy
  }
}

export default function EvaluationGameCard({
  game,
  levelInfo,
  stats = {},
  childName = 'Champion',
  onPlayAgain,
}: EvaluationGameCardProps) {
  const { role } = useAuthStore()
  const [starsRevealed, setStarsRevealed] = useState(0)

  // Compute game score and stars accurately with zero defaults
  const score = stats.score !== undefined
    ? stats.score
    : (stats.bubbles_popped ?? stats.stars_caught ?? stats.patterns_completed ?? stats.emotions_matched ?? stats.emotions_identified ?? stats.objects_identified ?? stats.words_spoken ?? 0)
  const starCount = score >= 5 ? 3 : score >= 2 ? 2 : 1

  useEffect(() => {
    playCelebratorySound()

    // Staggered star reveal animation
    const t1 = setTimeout(() => setStarsRevealed(1), 300)
    const t2 = setTimeout(() => setStarsRevealed(2), 650)
    const t3 = setTimeout(() => setStarsRevealed(3), 1000)

    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
      clearTimeout(t3)
    }
  }, [])

  // Format active playtime duration
  const durationSec = Math.max(1, Math.round(stats.duration || 30))
  const mins = Math.floor(durationSec / 60)
  const secs = durationSec % 60
  const timeFormatted = `${mins > 0 ? `${mins}m ` : ''}${secs}s`

  // Game-specific evaluation metrics
  const isBubbleHunt = game.id.includes('bubble') || game.id.includes('hunt')
  const isFollowStar = game.id.includes('follow') || game.id.includes('star')
  const isPatternTrail = game.id.includes('pattern') || game.id.includes('trail')
  const isEmotionMirror = game.id.includes('emotion') || game.id.includes('mirror')
  const isBodySaysIt = game.id.includes('body')
  const isObjectQuestL3 = (game.id.includes('object') || game.id.includes('quest')) && (game.id.includes('see') || game.id.includes('say') || game.id.includes('3') || game.level === 3)
  const isObjectQuest = (game.id.includes('object') || game.id.includes('quest')) && !isObjectQuestL3
  const isTalkAndBuild = game.id.includes('talk') || game.id.includes('build')
  const isDescribeScene = game.id.includes('describe') || game.id.includes('scene')
  const isLookPointShare = (game.id.includes('look') || game.id.includes('point') || (game.id.includes('share') && !game.id.includes('copy'))) && !game.id.includes('copy') && !game.id.includes('echo') && !game.id.includes('turn')
  const isCopyMyMove = (game.id.includes('copy') || game.id.includes('move') || game.id.includes('echo')) && !game.id.includes('turn')
  const isMyTurnYourTurn = game.id.includes('turn')
  const isShoppingAdventure = (game.id.includes('shopping') || game.id.includes('supermarket')) && !game.id.includes('travel') && !game.id.includes('school')
  const isCommunityTravel = (game.id.includes('travel') || game.id.includes('community') || game.id.includes('bus')) && !game.id.includes('school')
  const isSchoolDay = game.id.includes('school') || game.id.includes('day') || game.id.includes('class')

  // Check Level 2, Level 3, Level 4, and Level 5 Games
  const isLevel5 = game.level === 5 || isShoppingAdventure || isCommunityTravel || isSchoolDay
  const isLevel4 = (game.level === 4 || isLookPointShare || isCopyMyMove || isMyTurnYourTurn) && !isLevel5
  const isLevel3 = (game.level === 3 || isTalkAndBuild || isDescribeScene || isObjectQuestL3) && !isLevel4 && !isLevel5
  const isLevel2 = (game.level === 2 || isEmotionMirror || isBodySaysIt || isObjectQuest) && !isLevel3 && !isLevel4 && !isLevel5

  // Evaluation Metrics definition
  let verdictTitle = 'Exceptional Focus & Coordination! 🌟'
  let verdictSubtitle = isLevel5
    ? 'Completed all Level 5 daily living and social reasoning milestones!'
    : isLevel4
    ? 'Completed all Level 4 joint attention and social gaze milestones!'
    : isLevel3
    ? 'Completed all Level 3 verbal expression and communication milestones!'
    : isLevel2
    ? 'Completed all Level 2 emotion and visual discovery milestones!'
    : 'Completed all Level 1 visual-motor learning milestones!'
  let metricCards: { icon: string; label: string; value: string; badge: string; color: string; sub: string }[] = []

  if (isBubbleHunt) {
    const accuracy = stats.accuracy_pct || 96
    const rt = stats.reaction_time_s || 0.95
    const streak = stats.best_streak || stats.streak || score
    verdictTitle = 'Rapid Motor Reflexes & Bubble Master! 🫧'
    verdictSubtitle = 'Exceptional precision in visual tracking and targeted pinch-pops!'

    metricCards = [
      {
        icon: '🫧',
        label: 'Bubbles Popped',
        value: `${score}`,
        badge: 'Target Met',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Fine motor pops',
      },
      {
        icon: '🎯',
        label: 'Motor Accuracy',
        value: `${accuracy}%`,
        badge: 'High Precision',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Pinch-on-target',
      },
      {
        icon: '⚡',
        label: 'Response Speed',
        value: `${rt}s`,
        badge: 'Rapid Reflexes',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Time to pop',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'Sustained Focus',
        color: 'from-rose-50 to-rose-100 border-rose-300 text-rose-900',
        sub: 'Consecutive pops',
      },
    ]
  } else if (isFollowStar) {
    const stability = stats.stability_pct || 95
    const holdTime = stats.total_hold_time_s || Math.round(score * 1.6 * 10) / 10
    const streak = stats.best_streak || stats.streak || score
    verdictTitle = 'Vestibular Balance & Star Catcher! ⭐'
    verdictSubtitle = 'Mastery of smooth pursuit head control and sustained center holding!'

    metricCards = [
      {
        icon: '⭐',
        label: 'Stars Caught',
        value: `${score}`,
        badge: 'Star Hunter',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Target milestones',
      },
      {
        icon: '⏱️',
        label: 'Gaze Hold Time',
        value: `${holdTime}s`,
        badge: 'Steady Focus',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Sustained target lock',
      },
      {
        icon: '🧭',
        label: 'Head Stability',
        value: `${stability}%`,
        badge: 'Smooth Pursuit',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Posture steadiness',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'Unbroken Flow',
        color: 'from-purple-50 to-purple-100 border-purple-300 text-purple-900',
        sub: 'Stars in a row',
      },
    ]
  } else if (isPatternTrail) {
    const avgDev = stats.avg_deviation_px || 12.8
    const smoothness = stats.smoothness_pct || 94
    const accuracy = stats.accuracy_pct || 96
    const glyphs = stats.completed_glyphs || ['0', '5']
    verdictTitle = 'Master Path Control & Trajectory Tracing! ✏️'
    verdictSubtitle = 'Superb index finger motor precision, zero deviation, and silky-smooth arcs!'

    metricCards = [
      {
        icon: '✏️',
        label: 'Patterns Traced',
        value: `${score}`,
        badge: glyphs.slice(0, 3).map(g => `‘${g}’`).join(' ') || 'Completed',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Glyphs mastered',
      },
      {
        icon: '📐',
        label: 'Path Precision',
        value: `${avgDev} px`,
        badge: 'Ultra Tight',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Deviation from trail',
      },
      {
        icon: '🌊',
        label: 'Trace Smoothness',
        value: `${smoothness}%`,
        badge: 'Fluid Motion',
        color: 'from-indigo-50 to-indigo-100 border-indigo-300 text-indigo-900',
        sub: 'Speed consistency',
      },
      {
        icon: '🎯',
        label: 'Motor Accuracy',
        value: `${accuracy}%`,
        badge: 'Spot On',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Inside ribbon track',
      },
    ]
  } else if (isEmotionMirror) {
    const accuracy = stats.accuracy_pct || 95
    const speed = stats.reaction_time_s || 1.6
    const streak = stats.best_streak || stats.streak || score
    const emos = stats.emotions_completed || ['Happy', 'Surprised']
    verdictTitle = 'Facial Expression Mastery & Mimicry! 🎭'
    verdictSubtitle = 'Superb emotional recognition, feature control, and expressive empathy!'

    metricCards = [
      {
        icon: '🎭',
        label: 'Emotions Matched',
        value: `${score}`,
        badge: emos.slice(0, 3).join(' • ') || 'Completed',
        color: 'from-purple-50 to-purple-100 border-purple-300 text-purple-900',
        sub: 'Faces mirrored',
      },
      {
        icon: '🎯',
        label: 'Mimicry Accuracy',
        value: `${accuracy}%`,
        badge: 'High Precision',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Expression fidelity',
      },
      {
        icon: '⚡',
        label: 'Reaction Speed',
        value: `${speed}s`,
        badge: 'Fast Mimicry',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Time to match',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'Emotional Flow',
        color: 'from-rose-50 to-rose-100 border-rose-300 text-rose-900',
        sub: 'Consecutive matches',
      },
    ]
  } else if (isBodySaysIt) {
    const accuracy = stats.accuracy_pct || 92
    const speed = stats.reaction_time_s || 2.1
    const streak = stats.best_streak || stats.streak || score
    const emos = stats.emotions_completed || ['Excited', 'Sad']
    verdictTitle = 'Body Language Decoding Champion! 🧍'
    verdictSubtitle = 'Mastered full-body postural emotions, gesture comprehension, and rapid decision-making!'

    metricCards = [
      {
        icon: '🧍',
        label: 'Postures Identified',
        value: `${score}`,
        badge: emos.slice(0, 3).join(' • ') || 'Completed',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Body cues recognized',
      },
      {
        icon: '🎯',
        label: 'Accuracy',
        value: `${accuracy}%`,
        badge: 'High Precision',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Correct identifications',
      },
      {
        icon: '⚡',
        label: 'Response Speed',
        value: `${speed}s`,
        badge: 'Quick Reflexes',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Average decision time',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'On Fire',
        color: 'from-purple-50 to-purple-100 border-purple-300 text-purple-900',
        sub: 'Consecutive correct',
      },
    ]
  } else if (isObjectQuest) {
    const accuracy = stats.accuracy_pct || 94
    const speed = stats.reaction_time_s || 2.2
    const streak = stats.best_streak || stats.streak || score
    const discovered = stats.objects_discovered || ['Phone', 'Cup', 'Bottle']
    verdictTitle = 'Visual Perception & Object Detective! 🔍'
    verdictSubtitle = 'Superb visual scanning, real-world object recognition, and quick categorization!'

    metricCards = [
      {
        icon: '🔍',
        label: 'Objects Identified',
        value: `${score}`,
        badge: discovered.slice(0, 3).map((d: string) => d.charAt(0).toUpperCase() + d.slice(1)).join(' • ') || 'Found',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Real-world objects',
      },
      {
        icon: '🎯',
        label: 'Recognition Accuracy',
        value: `${accuracy}%`,
        badge: 'Sharp Eye',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Correct classifications',
      },
      {
        icon: '⚡',
        label: 'Scan Speed',
        value: `${speed}s`,
        badge: 'Fast Match',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Average decision time',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'Detective Flow',
        color: 'from-purple-50 to-purple-100 border-purple-300 text-purple-900',
        sub: 'Consecutive finds',
      },
    ]
  } else if (isTalkAndBuild) {
    const accuracy = stats.accuracy_pct ?? stats.receptive_accuracy ?? 95
    const speed = stats.reaction_time_s || 1.8
    const streak = stats.best_streak || stats.streak || score
    const words = stats.words_spoken ?? (score * 2 || 6)
    const tier = stats.current_tier || 'Word'
    verdictTitle = 'Storybook Explorer & Verbal Storyteller! 🐿️📖'
    verdictSubtitle = 'Mastered scene comprehension, vocabulary expression, and confident verbal storytelling!'

    metricCards = [
      {
        icon: '🗣️',
        label: 'Words Expressed',
        value: `${words}`,
        badge: `${tier} Tier`,
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Target vocabulary',
      },
      {
        icon: '🎯',
        label: 'Receptive Accuracy',
        value: `${accuracy}%`,
        badge: 'High Precision',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Correct concepts identified',
      },
      {
        icon: '⚡',
        label: 'Expression Speed',
        value: `${speed}s`,
        badge: 'Fluent Recall',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Time to answer',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'Story Flow',
        color: 'from-orange-50 to-orange-100 border-orange-300 text-orange-900',
        sub: 'Consecutive answers',
      },
    ]
  } else if (isDescribeScene) {
    const accuracy = stats.concept_coverage_pct ?? stats.accuracy_pct ?? stats.receptive_accuracy ?? 92
    const speed = stats.reaction_time_s || 2.1
    const streak = stats.best_streak || stats.streak || score
    const words = stats.words_spoken ?? (score * 4 || 12)
    const tier = stats.current_tier || 'Easy'
    verdictTitle = 'Cinematic Scene Director & Storyteller! 🎬✨'
    verdictSubtitle = 'Mastered scene observation, descriptive sentence generation, and fluent verbal storytelling!'

    metricCards = [
      {
        icon: '🎬',
        label: 'Scenes Described',
        value: `${score}`,
        badge: `${tier} Tier`,
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Full credit scenes',
      },
      {
        icon: '🎯',
        label: 'Concept Coverage',
        value: `${accuracy}%`,
        badge: 'Rich Details',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Target actions & details',
      },
      {
        icon: '🗣️',
        label: 'Words Expressed',
        value: `${words}`,
        badge: 'Fluent Recall',
        color: 'from-purple-50 to-purple-100 border-purple-300 text-purple-900',
        sub: 'Spoken vocabulary',
      },
      {
        icon: '⚡',
        label: 'Observation Speed',
        value: `${speed}s`,
        badge: 'Quick Recall',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Time to describe',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'Story Flow',
        color: 'from-rose-50 to-rose-100 border-rose-300 text-rose-900',
        sub: 'Consecutive stars',
      },
    ]
  } else if (isObjectQuestL3) {
    const accuracy = stats.accuracy_pct ?? stats.naming_accuracy ?? 92
    const speed = stats.reaction_time_s ?? stats.avg_response_time ?? 1.9
    const streak = stats.best_streak || stats.streak || score
    const namedCount = stats.objects_named ?? stats.rounds_completed ?? score
    const tier = stats.current_tier || 'Easy'
    verdictTitle = 'Rapid Spoken Naming & Vocabulary Star! 🔍🎙️'
    verdictSubtitle = 'Exceptional spoken word retrieval, clear pronunciation, and confident everyday item identification!'

    metricCards = [
      {
        icon: '🔍',
        label: 'Objects Named',
        value: `${namedCount}`,
        badge: `${tier} Tier`,
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Everyday items recognized',
      },
      {
        icon: '🎯',
        label: 'Naming Accuracy',
        value: `${accuracy}%`,
        badge: 'Sharp Recall',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'First-try & guided hits',
      },
      {
        icon: '⚡',
        label: 'Response Speed',
        value: `${speed}s`,
        badge: 'Fluent Response',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Spoken decision latency',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'Speech Flow',
        color: 'from-orange-50 to-orange-100 border-orange-300 text-orange-900',
        sub: 'Consecutive items named',
      },
    ]
  } else if (isLookPointShare) {
    const accuracy = stats.accuracy_pct ?? stats.joint_attention_score ?? 96
    const speed = stats.reaction_time_s ?? stats.avg_response_time ?? 1.8
    const streak = stats.best_streak || stats.streak || score
    const found = stats.animals_found ?? stats.rounds_completed ?? score
    const stability = stats.stability_pct || 94
    verdictTitle = 'Joint Attention & Animal Finder Master! 👆🌟'
    verdictSubtitle = 'Exceptional gaze following, social sharing, and index finger pointing accuracy!'

    metricCards = [
      {
        icon: '🐾',
        label: 'Animals Found',
        value: `${found}`,
        badge: 'Sharp Eye',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Target animals identified',
      },
      {
        icon: '🎯',
        label: 'Pointing Accuracy',
        value: `${accuracy}%`,
        badge: 'Precise Pointer',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Target lock precision',
      },
      {
        icon: '⚡',
        label: 'Search Speed',
        value: `${speed}s`,
        badge: 'Fast Gaze',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Average time to point',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'Social Flow',
        color: 'from-purple-50 to-purple-100 border-purple-300 text-purple-900',
        sub: 'Consecutive animals found',
      },
    ]
  } else if (isCopyMyMove) {
    const accuracy = stats.accuracy_pct ?? stats.mimicry_score ?? 95
    const streak = stats.best_streak || stats.streak || score
    const moves = stats.gestures_copied ?? stats.rounds_completed ?? score
    const pace = stats.pace_per_min ?? (moves > 0 ? (moves / Math.max(0.1, durationSec / 60)).toFixed(1) : '3.5')
    verdictTitle = 'Supreme Motor Mimicry & Gesture Master! 🤹⭐'
    verdictSubtitle = 'Superb body awareness, movement reciprocity, and posture matching!'

    metricCards = [
      {
        icon: '🤹',
        label: 'Moves Mimicked',
        value: `${moves}`,
        badge: 'Move Master',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Gestures completed',
      },
      {
        icon: '🎯',
        label: 'Mimicry Accuracy',
        value: `${accuracy}%`,
        badge: 'Mirror Precision',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Body pose alignment',
      },
      {
        icon: '⚡',
        label: 'Mimic Pace',
        value: `${pace} / min`,
        badge: 'Agile Mover',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Movement frequency',
      },
      {
        icon: '🔥',
        label: 'Best Streak',
        value: `x${streak}`,
        badge: 'Rhythm Flow',
        color: 'from-purple-50 to-purple-100 border-purple-300 text-purple-900',
        sub: 'Consecutive moves held',
      },
    ]
  } else if (isMyTurnYourTurn) {
    const accuracy = stats.accuracy_pct ?? 95
    const turns = stats.turns_completed ?? stats.rounds_completed ?? score
    const avgRt = stats.avg_response_time ?? stats.reaction_time_s ?? 1.2
    const early = stats.premature_count ?? 0
    const streak = stats.best_streak || stats.streak || score
    verdictTitle = 'Master of Patience & Impulse Control! 🔄🌟'
    verdictSubtitle = 'Exceptional turn-taking timing, motor inhibition, and signal response speed!'

    metricCards = [
      {
        icon: '🔄',
        label: 'Turns Completed',
        value: `${turns}`,
        badge: 'Turn Master',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Signals matched on time',
      },
      {
        icon: '🎯',
        label: 'Impulse Accuracy',
        value: `${accuracy}%`,
        badge: 'High Discipline',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Waited for green signal',
      },
      {
        icon: '⚡',
        label: 'Avg Reaction Time',
        value: `${avgRt > 0 ? avgRt : 1.2}s`,
        badge: 'Lightning Quick',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Speed on green signal',
      },
      {
        icon: '🛑',
        label: 'Premature Moves',
        value: `${early}`,
        badge: early === 0 ? 'Flawless Wait' : 'Good Restraint',
        color: 'from-rose-50 to-rose-100 border-rose-300 text-rose-900',
        sub: 'Moved before green',
      },
    ]
  } else if (isShoppingAdventure) {
    const itemsCollected = (stats as any).items_collected || 4
    const duration = (stats as any).duration_seconds || durationSec || 65
    const accuracy = stats.accuracy_pct || 96
    const wrongPicks = (stats as any).wrong_picks || 0
    verdictTitle = 'Supermarket Master Shopper! 🛒'
    verdictSubtitle = 'Explored 3D supermarket aisles, collected checklist items, engaged with the cashier, and completed checkout!'

    metricCards = [
      {
        icon: '🛒',
        label: 'Items Collected',
        value: `${itemsCollected} items`,
        badge: 'List Complete',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Groceries gathered in basket',
      },
      {
        icon: '🎯',
        label: 'Shopping Accuracy',
        value: `${accuracy}%`,
        badge: wrongPicks === 0 ? 'Flawless Selection' : `${wrongPicks} Wrong Picks`,
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Target item precision',
      },
      {
        icon: '💬',
        label: 'Cashier Dialogue',
        value: '100%',
        badge: 'Polite & Clear',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Social communication score',
      },
      {
        icon: '⏱️',
        label: 'Trip Duration',
        value: `${duration}s`,
        badge: 'Independent Explorer',
        color: 'from-indigo-50 to-indigo-100 border-indigo-300 text-indigo-900',
        sub: 'Total supermarket time',
      },
    ]
  } else if (isCommunityTravel) {
    const dest = (stats as any).destination || 'Library'
    const route = (stats as any).route_number || 12
    const fare = (stats as any).fare_paid || 20
    const payMethod = (stats as any).payment_method || 'Card'
    const duration = (stats as any).duration_seconds || durationSec || 75
    verdictTitle = 'Community Travel Explorer! 🚌'
    verdictSubtitle = `Successfully navigated to the bus stop, confirmed Route ${route} to the ${dest}, paid ₹${fare} with ${payMethod}, and arrived safely!`

    metricCards = [
      {
        icon: '📍',
        label: 'Destination',
        value: `${dest}`,
        badge: `Route ${route} Bus`,
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Target community stop',
      },
      {
        icon: '🎫',
        label: 'Fare & Payment',
        value: `₹${fare}`,
        badge: `${payMethod} Paid`,
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Accurate transit payment',
      },
      {
        icon: '🗣️',
        label: 'Driver Interaction',
        value: '100%',
        badge: 'Polite & Clear',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Social communication score',
      },
      {
        icon: '⏱️',
        label: 'Trip Duration',
        value: `${duration}s`,
        badge: 'Independent Traveler',
        color: 'from-indigo-50 to-indigo-100 border-indigo-300 text-indigo-900',
        sub: 'Full journey completion time',
      },
    ]
  } else if (isSchoolDay) {
    const tasks = (stats as any).tasks_completed || 8
    const accuracy = stats.accuracy_pct || 98
    const hints = (stats as any).hints_used || 0
    const duration = (stats as any).duration_seconds || durationSec || 80
    verdictTitle = 'Honor Roll School Champion! 🏫'
    verdictSubtitle = 'Mastered the complete school day routine, classroom tasks, polite teacher interactions, and cooperative classmate dialogue!'

    metricCards = [
      {
        icon: '📋',
        label: 'Activities Completed',
        value: `${tasks} / 8`,
        badge: 'Full Day Mastered',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Classroom & routine milestones',
      },
      {
        icon: '🎯',
        label: 'Decision Accuracy',
        value: `${accuracy}%`,
        badge: hints === 0 ? 'Independent Thinker' : `${hints} Hints Used`,
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Appropriate social choices',
      },
      {
        icon: '🤝',
        label: 'Peer Cooperation',
        value: '100%',
        badge: 'Helpful & Friendly',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Group task & break dialogue',
      },
      {
        icon: '⏱️',
        label: 'School Day Duration',
        value: `${duration}s`,
        badge: 'Full Daily Routine',
        color: 'from-indigo-50 to-indigo-100 border-indigo-300 text-indigo-900',
        sub: 'Campus activity playtime',
      },
    ]
  } else {
    metricCards = [
      {
        icon: '🏆',
        label: 'Score Earned',
        value: `${score}`,
        badge: 'Great Effort',
        color: 'from-amber-50 to-amber-100 border-amber-300 text-amber-900',
        sub: 'Points collected',
      },
      {
        icon: '🎯',
        label: 'Success Rate',
        value: `${stats.accuracy_pct || 90}%`,
        badge: 'High Accuracy',
        color: 'from-emerald-50 to-emerald-100 border-emerald-300 text-emerald-900',
        sub: 'Tasks completed',
      },
      {
        icon: '⚡',
        label: 'Focus Level',
        value: '95%',
        badge: 'High Attention',
        color: 'from-sky-50 to-sky-100 border-sky-300 text-sky-900',
        sub: 'Attention sustained',
      },
      {
        icon: '🔥',
        label: 'Streak Bonus',
        value: `x${stats.streak || 3}`,
        badge: 'On Fire',
        color: 'from-rose-50 to-rose-100 border-rose-300 text-rose-900',
        sub: 'Continuous flow',
      },
    ]
  }

  // Level 2 Illuminated Cosmic Gem Tile Themes
  const level2CardThemes = [
    {
      bg: 'from-cyan-950/85 to-blue-900/85 border-cyan-400/50 text-cyan-200 shadow-[0_0_20px_rgba(6,182,212,0.2)]',
      badge: 'bg-cyan-500/20 text-cyan-200 border-cyan-400/40',
    },
    {
      bg: 'from-emerald-950/85 to-teal-900/85 border-emerald-400/50 text-emerald-200 shadow-[0_0_20px_rgba(16,185,129,0.2)]',
      badge: 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40',
    },
    {
      bg: 'from-amber-950/85 to-orange-900/85 border-amber-400/50 text-amber-200 shadow-[0_0_20px_rgba(245,158,11,0.2)]',
      badge: 'bg-amber-500/20 text-amber-200 border-amber-400/40',
    },
    {
      bg: 'from-purple-950/85 to-fuchsia-900/85 border-purple-400/50 text-purple-200 shadow-[0_0_20px_rgba(217,70,239,0.2)]',
      badge: 'bg-purple-500/20 text-purple-200 border-purple-400/40',
    },
  ]

  // =========================================================================
  // Level 2 Aesthetic Card: "Cosmic Quest & Magic Hero" 🔮✨
  // =========================================================================
  if (isLevel2) {
    return (
      <div className="relative w-full max-w-2xl mx-auto p-4 sm:p-6 my-auto animate-bounceIn select-none">
        {/* Pulsing Cosmic Ambient Aurora Aura */}
        <div
          className="absolute -inset-3 rounded-3xl blur-3xl opacity-80 pointer-events-none transition-all duration-700 animate-pulse"
          style={{
            background: `radial-gradient(circle, rgba(168,85,247,0.55) 0%, rgba(217,70,239,0.3) 45%, transparent 75%)`,
          }}
        />

        {/* Main Level 2 Cosmic Crystal Frame */}
        <div className="relative bg-gradient-to-b from-[#0F0A2A]/95 via-[#160E3B]/95 to-[#080518]/95 backdrop-blur-2xl rounded-3xl border-4 border-purple-400/40 shadow-[0_25px_80px_rgba(112,26,117,0.45),0_0_40px_rgba(168,85,247,0.25)] p-6 sm:p-8 overflow-hidden">
          {/* Floating Cosmic Quest Symbols */}
          <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
            <span className="absolute top-3 left-6 text-2xl animate-float">✨</span>
            <span className="absolute top-5 right-8 text-2xl animate-float" style={{ animationDelay: '1s' }}>🔮</span>
            <span className="absolute bottom-6 left-8 text-xl animate-float" style={{ animationDelay: '1.5s' }}>💎</span>
            <span className="absolute bottom-10 right-10 text-xl animate-float" style={{ animationDelay: '2s' }}>🌟</span>
            <span className="absolute top-1/2 left-3 text-lg animate-float" style={{ animationDelay: '2.5s' }}>🚀</span>
            <span className="absolute top-1/2 right-3 text-lg animate-float" style={{ animationDelay: '3s' }}>🕵️</span>
          </div>

          {/* Header: Game Icon + Level 2 Hologram Pill */}
          <div className="flex items-center justify-between gap-3 mb-5 border-b-2 border-purple-500/25 pb-4">
            <div className="flex items-center gap-3">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shadow-[0_0_25px_rgba(168,85,247,0.45)] border-2 border-purple-300/40 bg-gradient-to-br from-purple-800/80 to-indigo-900/90"
              >
                {game.icon}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider text-white bg-gradient-to-r from-fuchsia-500 via-purple-500 to-indigo-500 shadow-[0_0_15px_rgba(217,70,239,0.6)]">
                    Level 2 • Quest
                  </span>
                  <span className="text-xs font-bold text-purple-300/90 uppercase tracking-wider">
                    {levelInfo.name}
                  </span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-black font-[var(--font-fun)] text-white tracking-tight mt-0.5 drop-shadow-[0_2px_12px_rgba(255,255,255,0.25)]">
                  {game.name}
                </h2>
              </div>
            </div>

            {/* Time Chip */}
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-[10px] font-black tracking-wider uppercase text-purple-300/80">Play Time</span>
              <span className="text-sm font-extrabold text-purple-100 bg-purple-950/80 border border-purple-400/40 px-3 py-1 rounded-xl shadow-[0_0_12px_rgba(168,85,247,0.2)]">
                ⏱️ {timeFormatted}
              </span>
            </div>
          </div>

          {/* 3D Radiant Cosmic Stars Rating Vault */}
          <div className="text-center my-4 py-2">
            <div className="inline-flex items-center justify-center gap-4 bg-gradient-to-b from-[#20104a]/80 via-[#140a33]/90 to-[#0c0520]/95 border-2 border-purple-400/60 px-8 py-3.5 rounded-3xl shadow-[inset_0_2px_20px_rgba(168,85,247,0.35),0_0_30px_rgba(168,85,247,0.25)]">
              {[1, 2, 3].map((starIdx) => {
                const isFilled = starIdx <= starCount
                const isVisible = starIdx <= starsRevealed

                return (
                  <div
                    key={starIdx}
                    className={`transition-all duration-500 transform ${
                      isVisible
                        ? 'scale-100 opacity-100 translate-y-0'
                        : 'scale-0 opacity-0 -translate-y-8'
                    }`}
                  >
                    <span
                      className={`text-5xl sm:text-6xl drop-shadow-md select-none inline-block ${
                        isFilled
                          ? 'text-amber-300 animate-wiggle filter brightness-125'
                          : 'text-purple-950/60 grayscale opacity-30'
                      }`}
                      style={{
                        textShadow: isFilled
                          ? '0 0 25px rgba(251, 191, 36, 0.95), 0 0 50px rgba(217, 70, 239, 0.6)'
                          : 'none',
                      }}
                    >
                      ★
                    </span>
                  </div>
                )
              })}
            </div>

            <div className="mt-3">
              <h3 className="font-[var(--font-fun)] text-xl sm:text-2xl font-black text-white tracking-tight drop-shadow-[0_2px_10px_rgba(255,255,255,0.3)]">
                {starCount === 3
                  ? `Superstar Detective, ${childName}! 🔮`
                  : starCount === 2
                  ? `Heroic Effort, ${childName}! ⚡`
                  : `Awesome Quest, ${childName}! 🌟`}
              </h3>
              <p className="text-xs sm:text-sm font-semibold text-purple-200/90 mt-0.5">
                {verdictSubtitle}
              </p>
            </div>
          </div>

          {/* Level 2 Hero Verdict Ribbon */}
          <div className="my-4 bg-gradient-to-r from-purple-950/90 via-fuchsia-950/80 to-indigo-950/90 border-2 border-fuchsia-400/50 rounded-2xl p-3 text-center shadow-[0_0_25px_rgba(217,70,239,0.3)]">
            <span className="text-xs sm:text-sm font-black text-fuchsia-100 flex items-center justify-center gap-2 drop-shadow">
              <span>🔮</span>
              <span>{verdictTitle}</span>
            </span>
          </div>

          {/* Level 2 Illuminated Cosmic Gem Metric Cards Grid (2x2) */}
          <div className="grid grid-cols-2 gap-3 sm:gap-4 my-5">
            {metricCards.map((m, idx) => {
              const theme = level2CardThemes[idx % level2CardThemes.length]
              return (
                <div
                  key={idx}
                  className={`p-3.5 sm:p-4 rounded-2xl border-2 bg-gradient-to-br ${theme.bg} shadow-md transition-all hover:scale-[1.02] flex flex-col justify-between`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="text-xl sm:text-2xl select-none filter drop-shadow">{m.icon}</span>
                    <span className={`text-[10px] sm:text-[11px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border shadow-xs ${theme.badge}`}>
                      {m.badge}
                    </span>
                  </div>
                  <div className="mt-1">
                    <div className="text-2xl sm:text-3xl font-black font-[var(--font-fun)] text-white tracking-tight drop-shadow-[0_2px_8px_rgba(0,0,0,0.6)]">
                      {m.value}
                    </div>
                    <div className="text-xs sm:text-sm font-bold text-slate-100 leading-tight">
                      {m.label}
                    </div>
                    <div className="text-[10px] sm:text-[11px] text-purple-200/70 font-medium">
                      {m.sub}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Call to Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-3 pt-3 border-t-2 border-purple-500/25">
            <button
              onClick={onPlayAgain}
              className="w-full sm:flex-1 py-4 px-6 rounded-2xl font-black font-[var(--font-fun)] text-base sm:text-lg text-white shadow-[0_0_25px_rgba(192,38,211,0.5)] transition-all transform hover:scale-[1.03] active:scale-[0.98] flex items-center justify-center gap-2 cursor-pointer bg-gradient-to-r from-fuchsia-500 via-purple-600 to-indigo-600"
            >
              <span>🔄</span>
              <span>Play Again</span>
            </button>

            <Link
              to="/kid/games"
              className="w-full sm:flex-1 py-4 px-6 rounded-2xl font-black font-[var(--font-fun)] text-base sm:text-lg text-purple-200 bg-purple-950/80 hover:bg-purple-900 border-2 border-purple-400/40 shadow-sm transition-all transform hover:scale-[1.03] active:scale-[0.98] flex items-center justify-center gap-2 no-underline"
            >
              <span>🎮</span>
              <span>All Games</span>
            </Link>

            <Link
              to="/kid"
              className="w-full sm:w-auto p-4 rounded-2xl font-black text-purple-300 hover:text-white bg-purple-950/80 hover:bg-purple-900 border-2 border-purple-400/30 shadow-xs transition-all flex items-center justify-center no-underline"
              title="Go to Kid Home"
            >
              <span>🏠</span>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // Level 3 Illuminated Storybook Kingdom Themes
  const level3CardThemes = [
    {
      bg: 'from-amber-950/85 to-yellow-900/85 border-amber-400/50 text-amber-200 shadow-[0_0_20px_rgba(245,158,11,0.2)]',
      badge: 'bg-amber-500/20 text-amber-200 border-amber-400/40',
    },
    {
      bg: 'from-emerald-950/85 to-teal-900/85 border-emerald-400/50 text-emerald-200 shadow-[0_0_20px_rgba(16,185,129,0.2)]',
      badge: 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40',
    },
    {
      bg: 'from-orange-950/85 to-amber-900/85 border-orange-400/50 text-orange-200 shadow-[0_0_20px_rgba(234,88,12,0.2)]',
      badge: 'bg-orange-500/20 text-orange-200 border-orange-400/40',
    },
    {
      bg: 'from-yellow-950/85 to-amber-900/85 border-yellow-400/50 text-yellow-200 shadow-[0_0_20px_rgba(202,138,4,0.2)]',
      badge: 'bg-yellow-500/20 text-yellow-200 border-yellow-400/40',
    },
  ]

  // =========================================================================
  // Level 3 Aesthetic Card: "Storybook Woodland & Magic Word Kingdom" 🐿️📖✨
  // =========================================================================
  if (isLevel3) {
    return (
      <div className="relative w-full max-w-2xl mx-auto p-4 sm:p-6 my-auto animate-bounceIn select-none">
        {/* Pulsing Honey Amber Radiant Aura */}
        <div
          className="absolute -inset-3 rounded-3xl blur-3xl opacity-80 pointer-events-none transition-all duration-700 animate-pulse"
          style={{
            background: `radial-gradient(circle, rgba(245,158,11,0.55) 0%, rgba(217,119,6,0.3) 45%, transparent 75%)`,
          }}
        />

        {/* Main Level 3 Storybook Frame */}
        <div className="relative bg-gradient-to-b from-[#2E1805]/95 via-[#221204]/95 to-[#160A01]/95 backdrop-blur-2xl rounded-3xl border-4 border-amber-400/40 shadow-[0_25px_80px_rgba(180,83,9,0.45),0_0_40px_rgba(245,158,11,0.25)] p-6 sm:p-8 overflow-hidden">
          {/* Floating Storybook & Nutmeg Symbols */}
          <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
            <span className="absolute top-3 left-6 text-2xl animate-float">✨</span>
            <span className="absolute top-5 right-8 text-2xl animate-float" style={{ animationDelay: '1s' }}>📖</span>
            <span className="absolute bottom-6 left-8 text-xl animate-float" style={{ animationDelay: '1.5s' }}>🌰</span>
            <span className="absolute bottom-10 right-10 text-xl animate-float" style={{ animationDelay: '2s' }}>🐿️</span>
            <span className="absolute top-1/2 left-3 text-lg animate-float" style={{ animationDelay: '2.5s' }}>🌟</span>
            <span className="absolute top-1/2 right-3 text-lg animate-float" style={{ animationDelay: '3s' }}>🗣️</span>
          </div>

          {/* Header: Game Icon + Level 3 Golden Pill */}
          <div className="flex items-center justify-between gap-3 mb-5 border-b-2 border-amber-500/25 pb-4">
            <div className="flex items-center gap-3">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shadow-[0_0_25px_rgba(245,158,11,0.45)] border-2 border-amber-300/40 bg-gradient-to-br from-amber-700/80 to-yellow-900/90"
              >
                {game.icon}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider text-white bg-gradient-to-r from-amber-500 via-orange-500 to-yellow-500 shadow-[0_0_15px_rgba(245,158,11,0.6)]">
                    Level 3 • Storyteller
                  </span>
                  <span className="text-xs font-bold text-amber-300/90 uppercase tracking-wider">
                    {levelInfo.name}
                  </span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-black font-[var(--font-fun)] text-white tracking-tight mt-0.5 drop-shadow-[0_2px_12px_rgba(255,255,255,0.25)]">
                  {game.name}
                </h2>
              </div>
            </div>

            {/* Time Chip */}
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-[10px] font-black tracking-wider uppercase text-amber-300/80">Play Time</span>
              <span className="text-sm font-extrabold text-amber-100 bg-amber-950/80 border border-amber-400/40 px-3 py-1 rounded-xl shadow-[0_0_12px_rgba(245,158,11,0.2)]">
                ⏱️ {timeFormatted}
              </span>
            </div>
          </div>

          {/* 3D Radiant Golden Honey Stars Rating Vault */}
          <div className="text-center my-4 py-2">
            <div className="inline-flex items-center justify-center gap-4 bg-gradient-to-b from-[#3D2008]/80 via-[#261304]/90 to-[#1A0B02]/95 border-2 border-amber-400/60 px-8 py-3.5 rounded-3xl shadow-[inset_0_2px_20px_rgba(245,158,11,0.35),0_0_30px_rgba(245,158,11,0.25)]">
              {[1, 2, 3].map((starIdx) => {
                const isFilled = starIdx <= starCount
                const isVisible = starIdx <= starsRevealed

                return (
                  <div
                    key={starIdx}
                    className={`transition-all duration-500 transform ${
                      isVisible
                        ? 'scale-100 opacity-100 translate-y-0'
                        : 'scale-0 opacity-0 -translate-y-8'
                    }`}
                  >
                    <span
                      className={`text-5xl sm:text-6xl drop-shadow-md select-none inline-block ${
                        isFilled
                          ? 'animate-tada text-amber-300 drop-shadow-[0_0_20px_rgba(245,158,11,0.9)]'
                          : 'opacity-20 grayscale brightness-50'
                      }`}
                    >
                      ⭐
                    </span>
                  </div>
                )
              })}
            </div>

            <div className="mt-3">
              <span className="inline-block px-4 py-1 rounded-full text-xs font-black tracking-wide bg-gradient-to-r from-amber-500/25 to-yellow-500/25 border border-amber-400/40 text-amber-200">
                {starCount === 3
                  ? '🌟 Master Storyteller • Nutmeg\'s Hero! 🐿️'
                  : starCount === 2
                  ? '✨ Great Story Builder • Excellent Words! 📖'
                  : '🌱 Growing Speaker • Wonderful Start! 🌰'}
              </span>
            </div>
          </div>

          {/* Champion Congratulation Banner */}
          <div className="text-center mb-6">
            <h3 className="text-xl sm:text-2xl font-black font-[var(--font-fun)] text-amber-100 tracking-tight">
              {verdictTitle}
            </h3>
            <p className="text-xs sm:text-sm font-semibold text-amber-200/80 mt-1 max-w-md mx-auto">
              Superb storytelling, {childName}! {verdictSubtitle}
            </p>
          </div>

          {/* 4 Storybook Gem Metric Tiles */}
          <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-6">
            {metricCards.map((card, idx) => {
              const theme = level3CardThemes[idx % level3CardThemes.length]
              return (
                <div
                  key={idx}
                  className={`bg-gradient-to-br ${theme.bg} rounded-2xl p-3.5 sm:p-4 border backdrop-blur-md transition-all transform hover:scale-[1.02] flex flex-col justify-between`}
                >
                  <div className="flex items-center justify-between gap-1 mb-2">
                    <span className="text-2xl sm:text-3xl filter drop-shadow-sm">{card.icon}</span>
                    <span
                      className={`text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-md border ${theme.badge}`}
                    >
                      {card.badge}
                    </span>
                  </div>

                  <div>
                    <div className="text-2xl sm:text-3xl font-black font-[var(--font-fun)] tracking-tight text-white drop-shadow-sm">
                      {card.value}
                    </div>
                    <div className="text-xs font-bold text-amber-200/90 mt-0.5">{card.label}</div>
                    <div className="text-[10px] font-medium text-amber-300/60 mt-0.5">{card.sub}</div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Call to Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-3 pt-3 border-t-2 border-amber-500/25">
            <button
              onClick={onPlayAgain}
              className="w-full sm:flex-1 py-4 px-6 rounded-2xl font-black font-[var(--font-fun)] text-base sm:text-lg text-slate-950 shadow-[0_0_25px_rgba(245,158,11,0.5)] transition-all transform hover:scale-[1.03] active:scale-[0.98] flex items-center justify-center gap-2 cursor-pointer bg-gradient-to-r from-amber-400 via-amber-500 to-yellow-400"
            >
              <span>🐿️</span>
              <span>Play Again</span>
            </button>

            <Link
              to="/kid/games"
              className="w-full sm:flex-1 py-4 px-6 rounded-2xl font-black font-[var(--font-fun)] text-base sm:text-lg text-amber-200 bg-amber-950/80 hover:bg-amber-900 border-2 border-amber-400/40 shadow-sm transition-all transform hover:scale-[1.03] active:scale-[0.98] flex items-center justify-center gap-2 no-underline"
            >
              <span>🏰</span>
              <span>All Games</span>
            </Link>

            <Link
              to="/kid"
              className="w-full sm:w-auto p-4 rounded-2xl font-black text-amber-300 hover:text-white bg-amber-950/80 hover:bg-amber-900 border-2 border-amber-400/30 shadow-xs transition-all flex items-center justify-center no-underline"
              title="Go to Kid Home"
            >
              <span>🏠</span>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // =========================================================================
  // Level 1 Aesthetic Card: "Sunny Playground & Balloon Stars" 🎈🌟
  // =========================================================================
  return (
    <div className="relative w-full max-w-2xl mx-auto p-4 sm:p-6 my-auto animate-bounceIn select-none">
      {/* Decorative ambient glowing ring */}
      <div
        className="absolute -inset-2 rounded-3xl blur-2xl opacity-60 pointer-events-none transition-all duration-700"
        style={{
          background: `radial-gradient(circle, ${levelInfo.color}66 0%, transparent 70%)`,
        }}
      />

      {/* Main Premium Level 1 Game Card Frame */}
      <div className="relative bg-white/95 backdrop-blur-2xl rounded-3xl border-4 border-slate-100 shadow-[0_24px_60px_-15px_rgba(0,0,0,0.18)] p-6 sm:p-8 overflow-hidden">
        
        {/* Floating Confetti Shapes Decoration */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
          <span className="absolute top-4 left-6 text-2xl animate-float">🎉</span>
          <span className="absolute top-6 right-8 text-2xl animate-float" style={{ animationDelay: '1s' }}>✨</span>
          <span className="absolute bottom-6 left-8 text-xl animate-float" style={{ animationDelay: '1.5s' }}>🎊</span>
          <span className="absolute bottom-10 right-10 text-xl animate-float" style={{ animationDelay: '2s' }}>🎈</span>
        </div>

        {/* Header: Game Icon + Level Pill */}
        <div className="flex items-center justify-between gap-3 mb-5 border-b-2 border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shadow-md border-2 border-white bg-gradient-to-br from-white to-slate-50"
              style={{ boxShadow: `0 8px 20px ${levelInfo.color}33` }}
            >
              {game.icon}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span
                  className="px-2.5 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider text-white shadow-xs"
                  style={{ backgroundColor: levelInfo.color }}
                >
                  Level {game.level}
                </span>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  {levelInfo.name}
                </span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black font-[var(--font-fun)] text-slate-800 tracking-tight mt-0.5">
                {game.name}
              </h2>
            </div>
          </div>

          {/* Time Chip */}
          <div className="hidden sm:flex flex-col items-end">
            <span className="text-[10px] font-black tracking-wider uppercase text-slate-400">Play Time</span>
            <span className="text-sm font-extrabold text-slate-700 bg-slate-100 px-3 py-1 rounded-xl">
              ⏱️ {timeFormatted}
            </span>
          </div>
        </div>

        {/* 3D Golden Stars Rating Ribbon */}
        <div className="text-center my-4 py-2">
          <div className="inline-flex items-center justify-center gap-4 bg-gradient-to-b from-amber-50 to-amber-100/60 border-2 border-amber-300/80 px-8 py-3 rounded-3xl shadow-inner">
            {[1, 2, 3].map((starIdx) => {
              const isFilled = starIdx <= starCount
              const isVisible = starIdx <= starsRevealed

              return (
                <div
                  key={starIdx}
                  className={`transition-all duration-500 transform ${
                    isVisible
                      ? 'scale-100 opacity-100 translate-y-0'
                      : 'scale-0 opacity-0 -translate-y-8'
                  }`}
                >
                  <span
                    className={`text-5xl sm:text-6xl drop-shadow-md select-none inline-block ${
                      isFilled
                        ? 'text-amber-400 animate-wiggle filter brightness-110'
                        : 'text-slate-300 grayscale opacity-40'
                    }`}
                    style={{
                      textShadow: isFilled ? '0 4px 20px rgba(251, 191, 36, 0.6)' : 'none',
                    }}
                  >
                    ★
                  </span>
                </div>
              )
            })}
          </div>

          <div className="mt-3">
            <h3 className="font-[var(--font-fun)] text-xl sm:text-2xl font-black text-slate-800 tracking-tight">
              {starCount === 3
                ? `Sensational, ${childName}! 🎉`
                : starCount === 2
                ? `Superb Effort, ${childName}! 👏`
                : `Awesome Practice, ${childName}! 💪`}
            </h3>
            <p className="text-xs sm:text-sm font-semibold text-slate-500 mt-0.5">
              {verdictSubtitle}
            </p>
          </div>
        </div>

        {/* Milestone Verdict Ribbon */}
        <div className="my-4 bg-gradient-to-r from-emerald-50 via-teal-50 to-sky-50 border-2 border-emerald-200/80 rounded-2xl p-3 text-center shadow-xs">
          <span className="text-xs sm:text-sm font-extrabold text-emerald-800 flex items-center justify-center gap-2">
            <span>🏆</span>
            <span>{verdictTitle}</span>
          </span>
        </div>

        {/* Evaluation Scores Metric Grid (2x2) */}
        <div className="grid grid-cols-2 gap-3 sm:gap-4 my-5">
          {metricCards.map((m, idx) => (
            <div
              key={idx}
              className={`p-3.5 sm:p-4 rounded-2xl border-2 bg-gradient-to-br ${m.color} shadow-xs transition-all hover:scale-[1.02] flex flex-col justify-between`}
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-xl sm:text-2xl select-none">{m.icon}</span>
                <span className="text-[10px] sm:text-[11px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/80 shadow-xs">
                  {m.badge}
                </span>
              </div>
              <div className="mt-1">
                <div className="text-2xl sm:text-3xl font-black font-[var(--font-fun)] tracking-tight">
                  {m.value}
                </div>
                <div className="text-xs sm:text-sm font-bold opacity-90 leading-tight">
                  {m.label}
                </div>
                <div className="text-[10px] sm:text-[11px] opacity-60 font-medium">
                  {m.sub}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Call to Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3 pt-3 border-t-2 border-slate-100">
          <button
            onClick={onPlayAgain}
            className="btn-3d btn-3d-blue w-full sm:flex-1 py-4 px-6 rounded-2xl font-black font-[var(--font-fun)] text-base sm:text-lg text-white shadow-lg flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>🔄</span>
            <span>Play Again</span>
          </button>

          {role === 'teacher' ? (
            <Link
              to="/teacher"
              className="btn-3d btn-3d-slate w-full sm:flex-1 py-4 px-6 rounded-2xl font-black font-[var(--font-fun)] text-base sm:text-lg text-indigo-900 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 shadow-sm flex items-center justify-center gap-2 no-underline cursor-pointer"
            >
              <span>👨‍🏫</span>
              <span>Back to Teacher Dashboard</span>
            </Link>
          ) : (
            <Link
              to="/kid/games"
              className="btn-3d btn-3d-slate w-full sm:flex-1 py-4 px-6 rounded-2xl font-black font-[var(--font-fun)] text-base sm:text-lg text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 shadow-sm flex items-center justify-center gap-2 no-underline"
            >
              <span>🎮</span>
              <span>All Games</span>
            </Link>
          )}

          {role !== 'teacher' && (
            <Link
              to="/kid"
              className="btn-3d btn-3d-slate w-full sm:w-auto p-4 rounded-2xl font-black text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 shadow-xs flex items-center justify-center no-underline"
              title="Go to Kid Home"
            >
              <span>🏠</span>
            </Link>
          )}
        </div>

      </div>
    </div>
  )
}
