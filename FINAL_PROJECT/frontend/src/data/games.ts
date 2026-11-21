import type { GameDefinition, LevelInfo } from '../types/game'

export const LEVEL_INFO: Record<number, LevelInfo> = {
  1: { name: 'Attention & Motor', color: '#3B82F6', description: 'Build focus and hand-eye coordination' },
  2: { name: 'Emotion & Visual', color: '#8B5CF6', description: 'Understand expressions and visual cues' },
  3: { name: 'Communication', color: '#F59E0B', description: 'Practice speaking and describing' },
  4: { name: 'Social Interaction', color: '#10B981', description: 'Learn turn-taking and sharing attention' },
  5: { name: 'Social Reasoning', color: '#EF4444', description: 'Navigate real-world social situations' },
}

export const GAME_CATALOGUE: GameDefinition[] = [
  {
    id: 'bubble-hunt', level: 1, name: 'Bubble Hunt',
    description: 'Pop colorful bubbles by pinching with your fingers. Practice your hand-eye coordination and attention skills.',
    runtime: 'python-launched', inputModes: ['camera-hand', 'pointer'],
    needs: { camera: true, microphone: false },
    difficultyScale: ['standard'], status: 'available',
    sourcePath: 'LEVEL_1/bubble_hunt.py', version: '1.0.0', icon: '🫧',
  },
  {
    id: 'follow-the-star', level: 1, name: 'Follow the Star',
    description: 'Move your head to follow a friendly face target on screen. Practice visual tracking and motor control.',
    runtime: 'python-launched', inputModes: ['camera-face', 'pointer'],
    needs: { camera: true, microphone: false },
    difficultyScale: ['standard'], status: 'available',
    sourcePath: 'LEVEL_1/follow_the_star.py', version: '1.0.0', icon: '⭐',
  },
  {
    id: 'pattern-trail', level: 1, name: 'Pattern Trail',
    description: 'Trace letters and numbers with your fingertip. Practice path tracking and motor precision.',
    runtime: 'python-launched', inputModes: ['camera-hand', 'pointer'],
    needs: { camera: true, microphone: false },
    difficultyScale: ['see', 'follow', 'control'], status: 'available',
    sourcePath: 'LEVEL_1/pattern_trail.py', version: '1.0.0', icon: '✏️',
  },
  {
    id: 'emotion-mirror', level: 2, name: 'Emotion Mirror',
    description: 'Match facial expressions shown on screen. Practice recognizing and imitating emotions.',
    runtime: 'python-launched', inputModes: ['camera-face', 'choice-select'],
    needs: { camera: true, microphone: false },
    difficultyScale: ['standard'], status: 'available',
    sourcePath: 'LEVEL_2/emotion_mirror.py', version: '1.0.0', icon: '🪞',
  },
  {
    id: 'body-says-it', level: 2, name: 'Body Says It',
    description: 'Watch animated characters show body language and identify the emotion they express.',
    runtime: 'python-launched', inputModes: ['camera-hand', 'choice-select'],
    needs: { camera: true, microphone: false },
    difficultyScale: ['standard'], status: 'available',
    sourcePath: 'LEVEL_2/body_says_it.py', version: '1.0.0', icon: '🧍',
  },
  {
    id: 'object-quest', level: 2, name: 'Object Quest',
    description: 'Hold everyday objects up to the camera, let the AI scan them, and guess what they are!',
    runtime: 'python-launched', inputModes: ['camera-face', 'pointer', 'choice-select'],
    needs: { camera: true, microphone: false },
    difficultyScale: ['standard'], status: 'available',
    sourcePath: 'LEVEL_2/objectquest.py', version: '1.0.0', icon: '🔍',
  },
  {
    id: 'talk-and-build', level: 3, name: 'Talk & Build',
    description: 'Answer questions about scenes using your voice or tap candy buttons. Practice forming answers and building sentences.',
    runtime: 'python-launched', inputModes: ['speech', 'pointer', 'choice-select'],
    needs: { camera: true, microphone: true },
    difficultyScale: ['word', 'phrase', 'sentence'], status: 'available',
    sourcePath: 'LEVEL_3/talk_and_build.py', version: '1.0.0', icon: '🐿️',
  },
  {
    id: 'describe-the-scene', level: 3, name: 'Describe the Scene',
    description: 'Watch video scenes and describe what is happening in your own words. Practice expressive storytelling and vocabulary.',
    runtime: 'python-launched', inputModes: ['speech', 'pointer', 'choice-select'],
    needs: { camera: true, microphone: true },
    difficultyScale: ['easy', 'medium', 'hard'], status: 'available',
    sourcePath: 'LEVEL_3/describe_the_scene.py', version: '1.0.0', icon: '🎬',
  },
  {
    id: 'object-quest-see-say', level: 3, name: 'Object Quest: See & Say',
    description: 'Watch everyday objects in high definition and say what they are. Practice rapid naming and vocabulary retrieval.',
    runtime: 'python-launched', inputModes: ['speech', 'pointer', 'choice-select'],
    needs: { camera: true, microphone: true },
    difficultyScale: ['easy', 'medium', 'hard'], status: 'available',
    sourcePath: 'LEVEL_3/object_quest.py', version: '1.0.0', icon: '🔍',
  },
  {
    id: 'look-point-share', level: 4, name: 'Look–Point–Share',
    description: 'Point to the animal that matches the instruction. Practice pointing and sharing attention.',
    runtime: 'python-launched', inputModes: ['camera-hand', 'pointer', 'touch'],
    needs: { camera: true, microphone: false },
    difficultyScale: ['standard'], status: 'available',
    sourcePath: 'LEVEL4/look_point_and_share.py', version: '1.0.0', icon: '👆',
  },
  {
    id: 'my-turn-your-turn', level: 4, name: 'My Turn / Your Turn',
    description: 'Wait for your turn! Keep still on red and raise your hand when green appears.',
    runtime: 'python-launched', inputModes: ['camera-pose', 'keyboard'],
    needs: { camera: true, microphone: false },
    difficultyScale: ['standard'], status: 'available',
    sourcePath: 'LEVEL4/my_turn_your_turn.py', version: '1.0.0', icon: '🔄',
  },
  {
    id: 'copy-my-move', level: 4, name: 'Copy My Move',
    description: 'Watch the stick figure and hand gestures, then mirror and hold the pose!',
    runtime: 'python-launched', inputModes: ['camera-pose', 'camera-hand', 'choice-select'],
    needs: { camera: true, microphone: false },
    difficultyScale: ['standard'], status: 'available',
    sourcePath: 'LEVEL4/copymymove.py', version: '1.0.0', icon: '🤹',
  },
  {
    id: 'school-day-simulator', level: 5, name: 'School Day Simulator',
    description: 'Navigate a realistic school day routine, interact with teachers and classmates, ask for help, and participate in classroom activities.',
    runtime: 'web-embedded', inputModes: ['keyboard', 'pointer', 'touch'],
    needs: { camera: false, microphone: false, webgl: true },
    difficultyScale: ['easy', 'medium', 'hard'], status: 'available',
    sourcePath: 'LEVEL5/School Day Simulator.html', version: '1.0.0', icon: '🏫',
  },
  {
    id: 'community-travel-simulator', level: 5, name: 'Community Travel Simulator',
    description: 'Navigate public transport, read route boards, interact politely with the driver, pay bus fare, and travel safely to community destinations.',
    runtime: 'web-embedded', inputModes: ['keyboard', 'pointer', 'touch'],
    needs: { camera: false, microphone: false, webgl: true },
    difficultyScale: ['easy', 'medium', 'hard'], status: 'available',
    sourcePath: 'LEVEL5/Community Travel Simulator.html', version: '1.0.0', icon: '🚌',
  },
  {
    id: 'shopping-adventure', level: 5, name: 'Shopping Adventure',
    description: 'Explore a 3D supermarket (Supermarket Adventure), collect items from your shopping list, chat with the cashier, and pay for your groceries.',
    runtime: 'web-embedded', inputModes: ['keyboard', 'pointer', 'touch'],
    needs: { camera: false, microphone: false, webgl: true },
    difficultyScale: ['easy', 'medium', 'hard'], status: 'available',
    sourcePath: 'LEVEL5/Shopping Adventure.html', version: '1.0.0', icon: '🛒',
  },
]

export function getGamesByLevel(level: number): GameDefinition[] {
  return GAME_CATALOGUE.filter(g => g.level === level)
}

export function getGameById(id: string): GameDefinition | undefined {
  return GAME_CATALOGUE.find(g => g.id === id)
}

export function getPrimaryGameForLevel(level: number): GameDefinition | undefined {
  const games = getGamesByLevel(level)
  return games.find(g => g.status === 'available') || games[0]
}
