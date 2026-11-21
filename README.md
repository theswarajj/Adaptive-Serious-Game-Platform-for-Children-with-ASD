# Adaptive Serious-Game Platform for Children with Autism Spectrum Disorder (ASD)

> **An Intelligent, Multimodal Pediatric Neurodevelopmental System Powered by Computer Vision, Real-Time Speech Processing, and Reinforcement Learning**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-7.0-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.3-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.3-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.10%2B-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Google_AI-00758F.svg)](https://developers.google.com/mediapipe)
[![Reinforcement Learning](https://img.shields.io/badge/RL-Q--Learning%20%26%20Contextual%20Bandits-FF6F00.svg)](https://en.wikipedia.org/wiki/Q-learning)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Executive Overview

Children diagnosed with **Autism Spectrum Disorder (ASD)** frequently navigate unique neurodevelopmental challenges across social interaction, reciprocal communication, sensory modulation, fine/gross motor coordination, and executive functioning. Conventional clinical interventions (such as Applied Behavior Analysis, occupational therapy, and speech-language therapy) face persistent real-world obstacles, including severe therapist shortages, high recurring costs, geographic disparities, and difficulty sustaining intrinsic motivation in pediatric subjects.

To address these challenges, I designed and developed the **Adaptive Serious-Game Platform for Children with ASD**, an enterprise-grade, multimodal therapeutic computing platform that bridges advanced artificial intelligence with clinical child psychology. 

The platform features **15 clinically structured serious games across five developmental tiers**. Utilizing non-invasive commodity hardware—a standard webcam and microphone—the system captures real-time biometric and behavioral signals (skeletal posture, hand articulation, ocular/facial landmarks, and acoustic phonemes). These signals feed into an **adaptive Q-Learning reinforcement engine** and **Contextual Multi-Armed Bandit model**, which personalize game difficulty, deliver real-time visual and auditory scaffolding, detect attention lapses, and curate customized IEP (Individualized Education Program) progress tracks for educators and parents.

---

## 👨‍💻 Author Profile & Academic Credentials

* **Author:** **Swaraj Krishna P P**
* **Academic Background:** Graduate in Computer Science & Engineering (B.Tech CSE), Class of 2026
* **Institution:** **APJ Abdul Kalam Technological University (KTU)**, Kerala, India
* **Specialization & Focus Areas:** Artificial Intelligence, Machine Learning, Real-Time Computer Vision, Reinforcement Learning, Assistive HealthTech & Serious Games for Neurodevelopmental Intervention
* **Engineering Philosophy:** Building high-impact, clinically grounded assistive technologies that translate theoretical machine learning into accessible, dignified, and transformative real-world applications.

---

## 🏗️ Repository Architecture & Directory Hierarchy

The repository is structured to maintain a clean separation between the production-ready full-stack application and standalone prototype research modules.

```
Adaptive Serious-Game Platform for Children with ASD/
├── FINAL_PROJECT/                       # 🌟 PRIMARY PRODUCTION DEPLOYMENT PLATFORM
│   ├── backend/                         # FastAPI core server & AI engines
│   │   ├── app.py                       # 🚀 Main backend application entry point
│   │   ├── api_platform.py              # REST API routing for clinical & auth operations
│   │   ├── game_streamer.py             # Low-latency OpenCV video streamer & CV orchestrator
│   │   ├── adaptation_engine.py         # Dynamic difficulty adjustment & prompt scaffolding
│   │   ├── profiler_recommender.py      # Contextual Bandit RL policy recommendation engine
│   │   ├── student_model.py             # Multi-domain skill mastery state tracking (Q-Learning)
│   │   ├── db_schema.py                 # SQLite database schema, seeding, & IEP tables
│   │   ├── game_launcher.py             # Process lifecycle manager for embedded activities
│   │   ├── platform.db                  # Local relational database storing clinical records
│   │   └── requirements.txt             # Backend Python dependencies
│   ├── frontend/                        # React 19 + TypeScript + Vite frontend
│   │   ├── src/
│   │   │   ├── pages/                   # Primary portal interfaces
│   │   │   │   ├── KidHome.tsx          # Child portal (Duolingo-style winding quest path)
│   │   │   │   ├── GameLaunch.tsx       # Live 16:9 HUD stream viewer with TEACCH schedule
│   │   │   │   ├── GameLibrary.tsx      # Comprehensive catalogue filtered by developmental level
│   │   │   │   ├── TeacherDashboard.tsx # Educator console, 360° radar, curriculum, & IEP report
│   │   │   │   ├── ParentDashboard.tsx  # Parent portal, home observations, & transfer tips
│   │   │   │   ├── LoginPage.tsx        # Multi-role authentication & instant demo selectors
│   │   │   │   └── LandingPage.tsx      # Public introduction & visual platform overview
│   │   │   ├── components/              # Reusable UI & therapeutic components
│   │   │   │   ├── SkeletonLoader.tsx   # Shimmer skeleton loading components
│   │   │   │   ├── EvaluationGameCard.tsx# Post-session milestone celebration & metrics card
│   │   │   │   └── GameIntroOutro.tsx   # Interactive countdowns & balloon-popping celebrations
│   │   │   ├── store/                   # Zustand state management (Auth, Role, Session)
│   │   │   ├── data/games.ts            # Clinical game catalog metadata & level taxonomies
│   │   │   └── index.css                # Tactile 3D button design tokens & luxury glassmorphism
│   │   ├── package.json                 # Frontend dependencies & build scripts
│   │   └── vite.config.ts               # Vite bundler configuration
│   └── start_platform.bat               # Unified single-click startup script (Backend + Frontend)
│
├── LEVEL_1/                             # Standalone prototypes: Attention & Motor Control
├── LEVEL_2/                             # Standalone prototypes: Emotion & Visual Processing
├── LEVEL_3/                             # Standalone prototypes: Speech & Verbal Communication
├── LEVEL4/                              # Standalone prototypes: Social Interaction & Turn-Taking
├── LEVEL5/                              # Standalone prototypes: Real-Life Adaptive Simulations
├── .gitignore                           # Production Git exclusion configuration
└── README.md                            # Comprehensive technical documentation
```

### 📍 Where is the Core Code?
1. **Backend Server (`FINAL_PROJECT/backend/app.py`):** Starts the high-performance FastAPI server on `http://localhost:8000`. It initializes database schemas, sets up CORS headers, exposes real-time video streaming routes (`/api/stream/{game_id}`), and runs the Q-Learning and Contextual Bandit inference loops.
2. **Frontend Client (`FINAL_PROJECT/frontend/`):** React 19 single-page application on `http://localhost:5173`. Houses all three role-based portals (Kid, Teacher, Parent) with full tactile feedback and sensory controls.
3. **One-Click Automated Launcher (`FINAL_PROJECT/start_platform.bat`):** Batch script that validates Python 3.10 and Node environments, launches the FastAPI server in one window, and launches the Vite frontend development server in a second window.

---

## 🎮 The 15 Serious Games: Deep Technical & Clinical Analysis

The curriculum is structured into five progressive levels mapped directly to established neurodevelopmental diagnostic domains:

```
Level 1: Attention & Motor Control (Sensory Grounding)
   └── Level 2: Emotion Understanding & Visual Processing (Affective Decoding)
         └── Level 3: Speech & Communication (Expressive Language)
               └── Level 4: Social Interaction & Joint Attention (Reciprocal Socialization)
                     └── Level 5: Real-Life Simulations (Adaptive Independence)
```

Every game in the platform operates as an active clinical observation sensor and therapeutic intervention tool. Below is an exhaustive breakdown of all 15 serious games, detailing their clinical purpose, perception AI pipeline, interactive mechanics, adaptive difficulty scaling, and diagnostic metrics.

---

### Level 1: Attention & Motor Control (Sensory-Motor Foundation)

#### 1. Bubble Hunt (`bubble_hunt.py` / `BubbleHuntStreamSession`)
* **Clinical Target:** Fine motor precision, bilateral finger isolation, hand-eye coordination, and spatial visual tracking.
* **Clinical Rationale:** Children with ASD frequently exhibit dyspraxia, hypotonia, and difficulties with isolated finger movement. Bubble Hunt trains rapid finger-thumb apposition (pincer grasp) and visual-spatial targeting without sensory overstimulation.
* **Perception AI Pipeline:**
  * Model: **MediaPipe Hands** executing in multi-threaded asynchronous mode at 30+ FPS.
  * Landmarks Tracked: 21 3D coordinates. Specifically monitors Landmark 4 (Thumb Tip) and Landmark 8 (Index Finger Tip).
  * Mathematical Formula: Calculates normalized Euclidean distance in screen space:
    $$\text{Dist}_{\text{pinch}} = \sqrt{(x_8 - x_4)^2 + (y_8 - y_4)^2 + (z_8 - z_4)^2}$$
    A pinch gesture is registered when $\text{Dist}_{\text{pinch}} \le \theta_{\text{threshold}}$, where $\theta_{\text{threshold}} \in [0.035, 0.065]$ dynamically adapts to the child's hand span.
* **Interactive Mechanics:**
  * Color-coded buoyant bubbles spawn across randomized vectors with gentle sinusoidal bobbing:
    $$y(t) = y_0 - v_y \cdot t + A \cdot \sin(\omega t + \phi)$$
  * Pinching or tapping directly inside a bubble's radius triggers a multi-colored 12-particle dynamic explosion with alpha decay.
  * Audio feedback: Generates an instantaneous synthetic sine-wave pop frequency (800 Hz down to 140 Hz over 80 ms) using the Web Audio API.
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Large bubble radius ($r = 65\text{ px}$), slow vertical drift ($v_y = 1.2\text{ px/frame}$), generous pinch threshold ($\theta = 0.065$), maximum 3 simultaneous bubbles.
  * **Medium:** Medium radius ($r = 48\text{ px}$), standard drift ($v_y = 2.4\text{ px/frame}$), tighter pinch threshold ($\theta = 0.050$), maximum 5 simultaneous bubbles.
  * **Hard:** Small radius ($r = 34\text{ px}$), accelerated drift ($v_y = 4.0\text{ px/frame}$), dual-handed simultaneous spawning, randomized speed bursts.
* **Clinical Assessment Metrics Logged:**
  * Mean reaction latency (ms from bubble spawn to pop).
  * Pincer grasp accuracy index (deviation from bubble center).
  * Bilateral hand utilization ratio (left vs. right hand preference).
  * Total bubbles popped, streak counter, and motor stability score.

---

#### 2. Follow the Star (`follow_the_star.py` / `FollowTheStarStreamSession`)
* **Clinical Target:** Vestibular-cervical head stability, sustained ocular fixation, continuous attention endurance, and anti-saccadic control.
* **Clinical Rationale:** Gaze instability and poor vestibular-ocular reflex (VOR) suppression are common in ASD. This activity develops the child's ability to maintain sustained cervical alignment and focused gaze on a continuously moving reference point.
* **Perception AI Pipeline:**
  * Model: **MediaPipe Face Mesh** analyzing 468 3D facial landmarks in real time.
  * Landmarks Tracked: Landmark 1 (Nasal Tip), Landmark 33 (Left Eye Outer Corner), Landmark 263 (Right Eye Outer Corner), and Landmark 168 (Mid-Forehead).
  * Mathematical Formula: Calculates real-time 3D head pose orientation (Yaw, Pitch, Roll) and tracks the 2D projection of the nose tip relative to the target reticle:
    $$\Delta_{\text{reticle}} = \sqrt{(x_{\text{nose}} - x_{\text{star}})^2 + (y_{\text{nose}} - y_{\text{star}})^2}$$
    $$\text{Yaw} = \arctan2(x_{\text{nose}} - x_{\text{mid\_eyes}}, z_{\text{nose}} - z_{\text{mid\_eyes}})$$
* **Interactive Mechanics:**
  * A glowing celestial star glides smoothly along parametric Bézier and Lissajous curves across the screen.
  * The child maneuvers their head and nose into the star's glowing orbital reticle.
  * Entering the reticle activates a dynamic charging ring that fills clockwise over a 2.0-second dwell period.
  * Continuous hold triggers a star-capture explosion with floating sparkle particles and a pleasant celestial arpeggio chime (C5-E5-G5-C6).
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Broad capture radius ($r = 75\text{ px}$), slow star velocity ($v = 1.0\text{ px/frame}$), shortened dwell time (1.5 seconds), simple horizontal sweep.
  * **Medium:** Standard capture radius ($r = 50\text{ px}$), Lissajous figure-eight trajectories, 2.0-second dwell time.
  * **Hard:** Narrow capture radius ($r = 35\text{ px}$), rapid multi-directional Bézier curves, 2.5-second dwell time with velocity pulses.
* **Clinical Assessment Metrics Logged:**
  * Continuous gaze-on-target percentage ($\% \text{ time } \Delta_{\text{reticle}} < r$).
  * Average angular cervical deviation (degrees).
  * Longest sustained fixation duration without departure (seconds).
  * Attentional lapse count (number of exits from the active zone).

---

#### 3. Pattern Trail (`pattern_trail.py` / `PatternTrailStreamSession`)
* **Clinical Target:** Dynamic motor planning, continuous velocity regulation, trajectory tracing precision, and visual-spatial integration.
* **Clinical Rationale:** Fine-motor trajectory tracking requires predictive motor planning and real-time sensory feedback integration, areas where neurodivergent children frequently experience coordination friction.
* **Perception AI Pipeline:**
  * Model: **MediaPipe Hands** isolating Landmark 8 (Index Finger Tip).
  * Tremor Dampening: Applies a real-time Exponential Moving Average (EMA) filter to remove physiological hand tremor:
    $$\mathbf{p}_{\text{filtered}}^{(t)} = \alpha \mathbf{p}_{\text{raw}}^{(t)} + (1 - \alpha) \mathbf{p}_{\text{filtered}}^{(t-1)}, \quad \alpha = 0.35$$
* **Interactive Mechanics:**
  * The canvas renders glowing geometric spline paths (circles, wavy ribbons, figure-eights, spirals, and basic numerals).
  * A pulsing guidance orb leads the way along the path. The child traces the trail from start to finish with their extended index finger.
  * Touching the trail illuminates it in radiant neon green. Deviating beyond the boundary turns the trail amber and softens the audio, gently redirecting the child back without frustrating failure screens.
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Generous tolerance corridor (width $= 45\text{ px}$), simple straight and circular lines, slow-moving guidance orb.
  * **Medium:** Moderate corridor (width $= 28\text{ px}$), wave and zig-zag patterns, moderate speed.
  * **Hard:** Precision corridor (width $= 18\text{ px}$), complex recursive loops and numeral shapes, variable-speed guidance runner requiring active acceleration and deceleration.
* **Clinical Assessment Metrics Logged:**
  * Mean path deviation error ($\text{RMSE}$ in pixels from path center).
  * Trajectory smoothness index (derivative of acceleration / jerk profile).
  * Tracing velocity uniformity and completion time (seconds).
  * Off-track deviation count and recovery latency (ms).

---

### Level 2: Emotion Understanding & Visual Processing (Affective Cognition)

#### 4. Emotion Mirror (`emotion_mirror.py` / `EmotionMirrorStreamSession`)
* **Clinical Target:** Facial emotion recognition, affective empathy, voluntary facial Action Unit (AU) activation, and socio-emotional reciprocity.
* **Clinical Rationale:** Individuals with ASD often process facial expressions differently and may struggle with voluntary facial mimicry. Emotion Mirror provides non-judgmental, immediate mirror-biofeedback to develop facial motor awareness.
* **Perception AI Pipeline:**
  * Model: **MediaPipe Face Mesh** analyzing 468 landmark vectors.
  * Action Unit (AU) Geometric Extractors:
    * **AU12 (Zygomaticus Major - Smile/Joy):** Ratio of lip corner width (Landmarks 61, 291) to inter-ocular distance.
    * **AU26/27 (Jaw Drop/Mouth Stretch - Surprise):** Vertical aperture between inner lip margins (Landmarks 13, 14).
    * **AU4 (Corrugator Supercilii - Brow Furrow / Focus):** Euclidean distance between medial eyebrow points (Landmarks 55, 285).
    * **Neutral/Calm:** Baseline resting distance calibration computed during game initialization.
* **Interactive Mechanics:**
  * The screen presents an expressive animated peer avatar demonstrating an emotional state (Happy, Surprised, Calm).
  * The child mirrors the expression into their webcam. A circular affective matching meter fills dynamically around the camera viewport.
  * Reaching 80% congruence for 1.2 continuous seconds triggers victory confetti, audio praise, and unlocks the next affective trial.
  * Features an on-screen mute/unmute toggle for vocal prompts to accommodate auditory-sensitive children.
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Primary emotions (Happy, Calm), broad matching tolerance ($\pm 25\%$), visual animated mimicry guides shown continuously.
  * **Medium:** Adds Surprise and Focused, tighter angular thresholds ($\pm 15\%$), prompt fading after 3 seconds.
  * **Hard:** Complex sequence matching (e.g., Happy $\rightarrow$ Surprised $\rightarrow$ Calm in 10 seconds), rapid expression switching without on-screen visual guides.
* **Clinical Assessment Metrics Logged:**
  * Emotion identification and mimicry onset latency (ms).
  * Facial expression congruence percentage (0–100%).
  * Facial Action Unit symmetry index (left vs. right hemiface activation).
  * Sustained expression hold duration (seconds).

---

#### 5. Body Says It (`body_says_it.py` / `BodySaysItStreamSession`)
* **Clinical Target:** Gross motor posture interpretation, non-verbal body language decoding, and somatic social perception.
* **Clinical Rationale:** Understanding non-verbal social intent through whole-body posture is a critical real-world social skill. Body Says It trains children to recognize how emotions manifest across body language.
* **Perception AI Pipeline:**
  * Model: **MediaPipe Pose** (33 full-body landmarks) tracking bilateral shoulder angles (11, 12), elbows (13, 14), wrists (15, 16), and torso inclination.
  * Gesture Response Mode: Uses **MediaPipe Hands** to allow the child to answer by raising 1 to 4 fingers, or by tapping on-screen tactile cards.
* **Interactive Mechanics:**
  * Presents lively 3D scenarios where a character communicates emotion exclusively through posture (e.g., open upright posture for excitement, crossed slumped arms for defensive/upset, hands on hips for determination).
  * The child interprets the posture and selects the matching emotion using finger-gesture counting or tactile card clicks.
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Distinct high-contrast postures (Happy Waving vs. Sad Slumping), 2 answer choices, audio hints enabled.
  * **Medium:** Subtle postural cues (Curious Lean vs. Reluctant Hesitation), 4 answer choices.
  * **Hard:** Context-dependent social postures with peer group interactions, timed non-verbal response challenges.
* **Clinical Assessment Metrics Logged:**
  * Postural interpretation accuracy rate (%).
  * Response formulation time (ms).
  * Finger-count gesture classification reliability.
  * Non-verbal affective deduction score.

---

#### 6. Object Quest: Visual Scan (`objectquest.py` / `ObjectQuestStreamSession`)
* **Clinical Target:** Environmental visual scanning, physical object discrimination, spatial figure-ground perception, and real-world tactile engagement.
* **Clinical Rationale:** Grounding digital gameplay in physical reality helps prevent screen detachment and encourages children to interact with objects in their physical room.
* **Perception AI Pipeline:**
  * Model: **YOLOv8 nano** deep learning object detection model running locally alongside MediaPipe Hand tracking.
  * Object Categorization & Bounding Box Logic:
    * Electronics: phone, remote, laptop, mouse.
    * Everyday Essentials: cup, bottle, book, scissors, backpack.
  * Hand-Object Association: Evaluates Intersection over Union ($\text{IoU}$) between the child's hand bounding box and the detected object bounding box:
    $$\text{IoU} = \frac{\text{Area}(\mathbf{B}_{\text{hand}} \cap \mathbf{B}_{\text{object}})}{\text{Area}(\mathbf{B}_{\text{hand}} \cup \mathbf{B}_{\text{object}})} > 0.35$$
* **Interactive Mechanics:**
  * The system displays a real-world quest challenge: *"Show me a cup!"* or *"Find your book!"*.
  * The child searches their physical environment, picks up the item, and holds it before the camera.
  * When YOLOv8 detects the target object in the child's grasp with confidence $> 0.65$ for 1.5 continuous seconds, an emerald bounding frame locks on, triggering a fanfare celebration.
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Common items (cup, bottle, phone), generous 20-second retrieval window, photographic visual clue.
  * **Medium:** Less common items (book, scissors, backpack), 15-second window, outline clue.
  * **Hard:** Sequential multi-item retrieval challenges (e.g., *"Find a bottle, then show a book"*), tighter 10-second windows.
* **Clinical Assessment Metrics Logged:**
  * Environmental search and retrieval latency (seconds).
  * Real-world object recognition accuracy.
  * Detection confidence index and hold stability.
  * Object vocabulary breadth score.

---

### Level 3: Speech Processing & Expressive Communication (Verbal Expression)

#### 7. Talk & Build (`talk_and_build.py` / `TalkAndBuildStreamSession`)
* **Clinical Target:** Receptive scene comprehension, spoken sentence generation, descriptive vocabulary expansion, and joint conversational turn-taking.
* **Clinical Rationale:** Speech delays and echolalia are prevalent in ASD. Talk & Build combines an engaging animated conversational mascot with dual input (voice + AAC buttons) to scaffold spoken sentence formulation.
* **Speech Processing & Perception Pipeline:**
  * Audio Capture: High-precision circular buffer streaming through `sounddevice` at 16 kHz mono.
  * Speech Recognition: On-device **faster-whisper** acoustic model running with custom phonetic token matching.
  * Fuzzy Semantic Matching: Evaluates phonetic distance against target answer concepts:
    $$\text{Sim}_{\text{Levenshtein}}(\text{Transcript}, \text{Target}) \ge 0.70$$
  * Fallback / AAC Mode: Real-time on-screen candy buttons for non-verbal or selectively mute children.
* **Interactive Mechanics:**
  * **Nutmeg the Squirrel** introduces an illustrated, lively story scene (e.g., children playing with a red ball in a sunny park).
  * Nutmeg asks: *"Where are the children playing?"*.
  * The child speaks into their microphone (*"In the park!"*) or taps a candy option.
  * Live speech recognition displays the recognized words in the Magic Mic banner alongside animated live equalizer bars. Nutmeg responds with cheerful speech bubbles and adds a new visual element to build the story!
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Single-word target answers, prominent visual pictorial clues, 2 candy buttons.
  * **Medium:** 2–3 word descriptive phrases, 4 candy buttons.
  * **Hard:** Full grammatical sentences (Subject + Verb + Object), inferential questions, open-ended storytelling without AAC button prompts.
* **Clinical Assessment Metrics Logged:**
  * Spoken response latency (ms from question to speech onset).
  * Mean Length of Utterance (MLU) in words.
  * Phonological clarity and phonetic congruence score.
  * Spoken voice vs. AAC button reliance ratio.

---

#### 8. Describe the Scene (`describe_the_scene.py` / `DescribeTheSceneStreamSession`)
* **Clinical Target:** Expressive narrative language, spontaneous descriptive fluency, syntactic elaboration, and detail observation.
* **Clinical Rationale:** Moving from single-word labeling to multi-word narrative description is a major therapeutic hurdle in ASD. This game encourages children to observe scenes and express descriptive observations in their own words.
* **Speech Processing & Perception Pipeline:**
  * Pipeline: Voice Activity Detection (VAD) coupled with keyword semantic tokenization.
  * Semantic Classifier: Compares spoken transcripts against a multi-tier ontological dictionary of scene entities, colors, actions, and environmental features.
* **Interactive Mechanics:**
  * A colorful animated or live video vignette plays (e.g., a ginger cat relaxing on a wooden chair, children assembling building blocks).
  * The prompt displays: *"What is happening in the picture? Tell me one thing!"*.
  * The child speaks into the Magic Mic. The system parses spoken predicates (*"cat sitting"*, *"cat on chair"*, *"cat resting"*) and awards 1 to 3 stars based on descriptive richness.
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Simple subject-action identification, 2 pictorial prompt cards.
  * **Medium:** Descriptive phrases incorporating attributes (color, position, state), 4 prompt cards.
  * **Hard:** Complex compound sentences describing relational actions between multiple subjects without prompt cards.
* **Clinical Assessment Metrics Logged:**
  * Descriptive vocabulary diversity index.
  * Utterance formation speed (seconds).
  * Semantic alignment accuracy score (0–100%).
  * Syntactic complexity rating.

---

#### 9. Object Quest: See & Say (`object_quest.py` / `ObjectQuestSeeSayStreamSession`)
* **Clinical Target:** Rapid confrontation naming, phonological retrieval fluency, speech volume modulation, and verbal confidence.
* **Clinical Rationale:** Rapid naming exercises strengthen semantic-phonological neural pathways and reduce verbal retrieval hesitations during everyday social interactions.
* **Speech Processing & Perception Pipeline:**
  * Acoustic Capture: Real-time RMS volume energy monitoring:
    $$\text{RMS} = \sqrt{\frac{1}{N}\sum_{i=1}^N x_i^2}$$
  * Phonetic Whisper ASR matcher with phoneme onset latency tracking.
* **Interactive Mechanics:**
  * Everyday objects (fruits, animals, household tools) flash onto the screen.
  * The child names each object clearly into their microphone.
  * The Magic Mic banner glows radiant green upon detecting vocal onset. If the child hesitates for longer than 4 seconds, Nutmeg gently models the first phoneme as a verbal scaffold (*"It starts with 'Buh'..."*).
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Monosyllabic, familiar objects (cup, dog, car, ball), 6-second timeout before hint modeling.
  * **Medium:** Bisyllabic objects (apple, guitar, rabbit, table), 4-second timeout.
  * **Hard:** Multisyllabic, lower-frequency objects (helicopter, binoculars, strawberry), rapid 3-second confrontation naming sprints.
* **Clinical Assessment Metrics Logged:**
  * Phoneme onset latency (ms from image appearance to vocal sound).
  * Naming accuracy percentage (first-attempt correct).
  * Vocal volume stability (RMS decibel envelope).
  * Scaffolding hint dependency rate.

---

### Level 4: Social Interaction & Joint Attention (Reciprocal Socialization)

#### 10. Look, Point, and Share (`look_point_and_share.py` / `LookPointShareStreamSession`)
* **Clinical Target:** Responding to Joint Attention (RJA), initiating joint attention (IJA), referential gaze following, and 3D index-finger pointing.
* **Clinical Rationale:** Deficits in joint attention—the shared focus of two individuals on an object—are one of the earliest and most profound behavioral hallmarks of autism. This activity systematically trains gaze-following and deictic pointing.
* **Perception AI Pipeline:**
  * Dual-Tracker Orchestration: Executes **MediaPipe Face Mesh** and **MediaPipe Hands** concurrently.
  * Gaze & Pointing Ray Intersection: Calculates the pointing ray extending from Landmark 5 (Index MCP) through Landmark 8 (Index Tip) in 3D projective space:
    $$\vec{\mathbf{v}}_{\text{point}} = \frac{\mathbf{p}_8 - \mathbf{p}_5}{\|\mathbf{p}_8 - \mathbf{p}_5\|}$$
    $$\Delta_{\text{target}} = \min_t \|\mathbf{p}_5 + t \vec{\mathbf{v}}_{\text{point}} - \mathbf{p}_{\text{target}}\|$$
* **Interactive Mechanics:**
  * A virtual peer appears on screen, turns its head, looks towards a specific animated animal in the upper corner, and says: *"Look at that!"*.
  * The child must follow the peer's gaze, locate the referenced item, and physically point at it with their index finger or direct their sustained gaze at it.
  * Successful target intersection illuminates the target with starbursts and triggers a warm social affirmation (*"You found it together!"*).
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Peer looks and points simultaneously with glowing target border.
  * **Medium:** Peer looks without pointing; target has subtle breathing animation.
  * **Hard:** Peer glances briefly with head turn only; multiple distractor objects in the room; rapid target switching.
* **Clinical Assessment Metrics Logged:**
  * Joint attention response latency (ms).
  * Deictic pointing trajectory accuracy (angular deviation).
  * Social referencing gaze frequency (checking back with peer).
  * Referential target acquisition rate.

---

#### 11. My Turn, Your Turn (`my_turn_your_turn.py` / `MyTurnYourTurnStreamSession`)
* **Clinical Target:** Reciprocal social turn-taking, inhibitory motor control, response inhibition, impulse regulation, and waiting endurance.
* **Clinical Rationale:** Impulsive responding and difficulty with reciprocal waiting disrupt classroom participation and peer play. This game provides visual and auditory structure to practice waiting turns calmly.
* **Perception AI Pipeline:**
  * Interaction Zone State Machine: Monitors hand presence and tap events within an active interactive bounding box.
  * Synchronization Engine: Manages transitions between `MY_TURN`, `PEER_TURN`, and `WAIT_INTERVAL`.
* **Interactive Mechanics:**
  * The game is played cooperatively alongside a virtual peer.
  * **Green Light ("Your Turn"):** The child interacts freely to pop or place their game piece.
  * **Red Light ("Friend's Turn / Wait"):** The virtual peer takes their turn. The child must keep their hands resting quietly outside the interactive zone.
  * Moving hands into the active zone during a red light gently displays a friendly waiting countdown without punitive score resets.
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Short 2-second waiting periods, clear audio cues (*"Your turn!"* / *"Wait patiently"*), high error tolerance.
  * **Medium:** 4-second waiting periods, visual cues only (traffic light indicator).
  * **Hard:** Variable randomized waiting intervals (4 to 8 seconds), subtle turn-shift cues, distractor animations during the waiting phase.
* **Clinical Assessment Metrics Logged:**
  * Response inhibition success rate (% of clean wait intervals).
  * Premature response count during forbidden windows.
  * Maximum sustained waiting endurance (seconds).
  * Reciprocal transition latency (ms to act when green light appears).

---

#### 12. Copy My Move (`copymymove.py` / `CopyMyMoveStreamSession`)
* **Clinical Target:** Bilateral motor imitation, kinesthetic proprioception, gross motor coordination, and body schema awareness.
* **Clinical Rationale:** Motor imitation is a core developmental building block for social learning and empathy. Copy My Move trains children to observe, map, and execute full-body physical postures.
* **Perception AI Pipeline:**
  * Model: **MediaPipe Pose** tracking 33 3D skeletal keypoints.
  * Joint Angle Trigonometric Calculations: Evaluates 6 primary joint angle pairs (left/right shoulder abduction, left/right elbow flexion, left/right knee angles):
    $$\theta = \arccos\left(\frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}\right)$$
  * Normalized Anatomical Scale: Normalizes coordinates against the child's torso height and biacromial shoulder breadth.
* **Interactive Mechanics:**
  * A friendly character demonstrates engaging yoga and superhero postures (e.g., Airplane Arms, Tree Pose, Superhero Stretch).
  * The child stands before their camera and mirrors the posture.
  * A neon skeletal overlay reflects the child's body in real time, shifting from sky-blue to radiant gold as their joint angles align within $\pm 15^\circ$ of the target pose.
  * Holding the pose for 2.0 seconds completes the trial with celebratory fanfare.
* **Adaptive Dynamic Difficulty Adjustment (DDA):**
  * **Easy:** Symmetric upper-body poses (both arms raised, T-pose), wide $\pm 25^\circ$ angular tolerance, 1.5-second hold.
  * **Medium:** Asymmetric poses (one arm up, one arm on hip), tighter $\pm 18^\circ$ tolerance, 2.0-second hold.
  * **Hard:** Full-body balancing postures requiring single-leg balance and dual-arm coordination, $\pm 12^\circ$ tolerance, 3.0-second hold.
* **Clinical Assessment Metrics Logged:**
  * Angular imitation congruence score (0–100%).
  * Pose acquisition and stabilization time (seconds).
  * Bilateral postural symmetry index.
  * Proprioceptive balance hold endurance.

---

### Level 5: Real-Life Adaptive Life-Skills Simulations (Functional Independence)

#### 13. School Day Routine Simulator (`school_day_simulator.py` / `.html`)
* **Clinical Target:** Classroom navigation, morning routine sequencing, desk organization, polite help-seeking, and sensory transition coping.
* **Clinical Rationale:** The unpredictable social and sensory demands of school environments can cause severe anxiety in children with ASD. This 3D simulation provides a safe, repeatable sandbox to master daily school routines.
* **Interactive Simulation Engine:**
  * Architecture: 3D interactive WebGL environment integrated via bidirectional event listeners (`postMessage`) with the platform.
  * Decision Tree Branches: Simulates arrival at the front gate, hanging backpacks in cubbies, walking to assigned desks, following the visual schedule, and asking the teacher for help politely when stuck.
* **Adaptive Gameplay Scenarios:**
  * **Morning Routine:** Sequential step execution (Unpack bag $\rightarrow$ Place binder $\rightarrow$ Sit at desk).
  * **Help-Seeking Challenge:** The child encounters a challenging math worksheet. Options include: Crumple paper, Stay silent, or Raise hand and say *"Excuse me, can you help me please?"*.
  * **Sensory Fire Drill Simulation:** An unexpected bell rings. The child practices choosing their self-regulation tool (putting on noise-cancelling headphones, taking deep breaths, and walking calmly in line).
* **Clinical Assessment Metrics Logged:**
  * Routine sequential decision accuracy (% optimal choices).
  * Polite self-advocacy and help-seeking selection rate.
  * Sensory regulation coping resilience score.
  * Scenario completion time and independence index.

---

#### 14. Community Travel Simulator (`community_travel_simulator.py` / `.html`)
* **Clinical Target:** Pedestrian crosswalk safety, transit navigation, bus boarding etiquette, fare payment, and community wayfinding.
* **Clinical Rationale:** Community mobility and safe street navigation are foundational requirements for adolescent independence and community integration.
* **Interactive Simulation Engine:**
  * Architecture: Realistic 3D simulated streetscape with active traffic lights, pedestrian crossing signals, bus stop shelters, and arriving transit buses.
* **Adaptive Gameplay Scenarios:**
  * **Pedestrian Crosswalk:** The child approaches an intersection. Must check left, right, and left again, wait for the green walk signal, and cross safely.
  * **Bus Stop & Route Identification:** The child inspects the route timetable, identifies their assigned bus route number, and boards the bus calmly.
  * **Transit Social Exchange:** The child greets the driver (*"Good morning!"*), taps their transit card on the scanner, takes an available seat, and pulls the stop cord when approaching their destination.
* **Clinical Assessment Metrics Logged:**
  * Crosswalk safety compliance score (checking traffic + signal waiting).
  * Route and transit number discrimination accuracy.
  * Social communication exchange score with transit personnel.
  * Environmental hazard awareness rating.

---

#### 15. Supermarket Shopping Adventure (`supermarket_adventure.py` / `.html`)
* **Clinical Target:** Visual list scanning, item categorization, budget adherence, executive functioning, and cashier checkout communication.
* **Clinical Rationale:** Grocery shopping integrates multiple executive functions: maintaining working memory of a list, spatial aisle navigation, impulse control against unlisted items, and social interaction during checkout.
* **Interactive Simulation Engine:**
  * Architecture: Detailed 3D retail supermarket environment featuring dynamic grocery aisles (Produce, Bakery, Dairy, Pantry), an interactive shopping cart, budget calculators, and a checkout counter.
* **Adaptive Gameplay Scenarios:**
  * **List Management:** The child is given a pictorial and text shopping list of 3 to 5 items with a fixed budget (e.g., $10.00).
  * **Aisle Wayfinding:** The child navigates through aisles, locates the target items, verifies prices, and adds them to their cart while avoiding tempting unlisted snack items.
  * **Checkout & Payment:** At the counter, the child places items on the conveyor belt, greets the cashier (*"Hello!"*), pays with exact bills/coins, collects their receipt, and says *"Thank you!"*.
* **Clinical Assessment Metrics Logged:**
  * Shopping list item completion percentage.
  * Budget adherence accuracy (total spend $\le$ budget).
  * Impulse control index (ratio of listed to unlisted items picked).
  * Social checkout communication etiquette score.

---

## 🧠 Machine Learning, Q-Learning & Adaptive Intelligence

The platform rejects rigid, one-size-fits-all game progression. Instead, it deploys a dual-tier adaptive artificial intelligence architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Multimodal Sensor Streaming Pipeline                 │
│        Webcam Frame (OpenCV/MediaPipe)  +  Audio Signal (ASR/VAD)      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│              Student Behavioral & Clinical State Tracker               │
│   Motor Precision • Gaze Fixation • Emotion Mimicry • Verbal Clarity   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│            Reinforcement Learning Engine (Q-Learning & Bandits)        │
│    Dynamic Difficulty (Easy/Med/Hard)  •  Scaffolding Prompt Fading    │
│    Attention Recovery Trigger          •  IEP Sequential Progression   │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. Mathematical Formulation of Q-Learning Adaptation
The student's developmental learning state is modeled as a Markov Decision Process (MDP) tuple $(S, A, P, R, \gamma)$:

* **State Space ($S \in \mathbb{R}^d$):**
  $$s_t = \left( 	ext{SkillDomainMastery}, 	ext{CurrentStreak}, 	ext{AttentionScore}, 	ext{ErrorRate}, 	ext{ReactionLatency} 
ight)$$
* **Action Space ($A$):**
  $$a \in \{ 	ext{IncreaseDifficulty}, 	ext{DecreaseDifficulty}, 	ext{InjectVisualHint}, 	ext{TriggerRefocusingCue}, 	ext{PromoteLevel} \}$$
* **Reward Function ($R(s, a)$):**
  Balances challenge and emotional comfort to prevent frustration or boredom:
  $$R(s_t, a_t) = w_1 \cdot 	ext{Accuracy} + w_2 \cdot 	ext{AttentionRetention} - w_3 \cdot 	ext{FrustrationSignal} - w_4 \cdot 	ext{Latency}$$
* **Bellman Update Equation:**
  $$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + lpha \left[ R(s_t, a_t) + \gamma \max_{a'} Q(s_{t+1}, a') - Q(s_t, a_t) 
ight]$$
  Where learning rate $lpha = 0.15$ and discount factor $\gamma = 0.90$.

### 2. Contextual Multi-Armed Bandit for Activity Recommendation
When an educator requests an AI-curated curriculum recommendation, the platform evaluates historical student interactions using a **Contextual Bandit with Upper Confidence Bound (UCB)** exploration:
$$\hat{\mu}_i(t) + \sqrt{rac{2 \ln t}{N_i(t)}}$$
This balances assigning proven mastery activities with introducing novel cognitive challenges.

### 3. Real-Time Attention Lapse Detection & Refocusing Loop
Children with ASD frequently experience spontaneous attentional divergence. The system calculates continuous ocular and nasal orientation. If the gaze deviates from the display bounds for longer than 3.5 seconds:
1. The game physics automatically pause.
2. An animated, friendly mascot cue floats into view.
3. A gentle xylophone chime plays to redirect focus back to the center of the display.
4. The activity resumes seamlessly upon re-establishing ocular alignment.

---

## 🎨 Accessible, Sensory-Friendly Design System

I engineered a proprietary, accessible design system tailored for pediatric and neurodivergent accessibility:

* **Tactile 3D Button Physics:** Custom CSS tokens (`.btn-3d`, `.btn-3d-green`, `.btn-3d-blue`, `.btn-3d-amber`) provide physical 4px bottom socket depth. Clicking triggers an instant `translateY(4px)` physical depression with socket collapse, offering immediate sensory feedback.
* **Duolingo-Style Winding Adventure Path:** The child's curriculum renders as an engaging serpentine stepping-stone path with dashed track connectors, glowing pulsing rings (`.duo-pulse-ring`) on active missions, and gold crown trophies on mastered nodes.
* **TEACCH Visual Schedule Strip:** Embedded directly within the gameplay HUD, displaying three predictable phases:
  $$	ext{[ 1. Warm-Up & Mic Ready ✓ ]} \longrightarrow 	ext{[ 2. Active Quest Play 🎯 ]} \longrightarrow 	ext{[ 3. Star Celebration ⭐ ]}$$
  This structure significantly reduces task transition anxiety.
* **Sensory Calm Mode:** A 1-click header toggle that swaps high-saturation palettes for soft pastel sage and lavender hues, turns off rapid floating animations, and lowers audio frequencies.
* **Interactive Mascot Companion:** Nutmeg the Squirrel floats unobtrusively in the corner with animated speech bubbles that cycle evidence-based encouraging affirmations, accompanied by pleasant Web Audio synthesizer chirps.
* **Collectible Sticker Album:** Children unlock achievement stickers (e.g., *Bubble Popping Ace*, *Turn-Taking Champion*) stored in an interactive trophy showcase.

---

## 📊 Comprehensive Three-Tier Clinical Ecosystem

### 1. Student / Child Portal (`KidHome.tsx`)
* Curated stepping-stone quest path linked directly to teacher assignments.
* Daily streak counter (🔥 3-Day Streak), star tally, and energy crystals.
* Instant 1-click launch into active game streams with zero configuration required.

### 2. Teacher & Clinician Console (`TeacherDashboard.tsx`)
* **Multi-Student Classroom Overview:** Real-time visibility across all enrolled students.
* **Sequential Curriculum Manager:** Full drag-and-drop / 1-click reordering of all 15 games, custom difficulty overrides (Easy / Medium / Hard), and multi-student batch assignment.
* **Student 360° Profile:** Comprehensive 6-domain developmental radar (Motor Skills, Visual Attention, Emotion Recognition, Spoken Communication, Social Turn-Taking, and Daily Living).
* **1-Click IEP Clinical Summary Generator:** Formats student progress into an official, ready-to-print **Individualized Education Program (IEP) Report** with diagnostic goals, sensory accommodation checklists, radar scores, and clinician signature blocks.

### 3. Parent & Caregiver Portal (`ParentDashboard.tsx`)
* **Home-School Synchronization:** Parents can view exactly what their child practiced at school on any given day.
* **Home Transfer Tip of the Day:** Evidence-based 2-minute co-regulation routines for parents (e.g., practicing reciprocal waiting at dinner).
* **Home Observation Log:** Enables parents to log routine transitions, vocalization attempts, and sensory sensitivities.
* **Secure Communications:** Direct real-time chat with the lead special educator.
* **Credential Management:** Allows parents to update student login PINs and account passwords from home.

---

## ⚡ Installation & Execution Guide

### Prerequisites
* **Operating System:** Windows 10/11, macOS (12+), or Ubuntu Linux (20.04+)
* **Python:** Python 3.10 or 3.11 installed and added to system `PATH`
* **Node.js:** Node.js v18.0.0 or higher with `npm`
* **Hardware:** Standard USB/built-in 720p/1080p Webcam and Microphone

---

### Option A: Automated One-Click Launch (Recommended for Windows)

Navigate to the `FINAL_PROJECT` folder and double-click `start_platform.bat`:
```cmd
cd FINAL_PROJECT
start_platform.bat
```
This batch script will automatically:
1. Start the FastAPI backend server on `http://localhost:8000`.
2. Start the Vite React development server on `http://localhost:5173`.
3. Open your browser directly to the application.

---

### Option B: Manual Setup & Execution

#### Step 1: Clone Repository
```bash
git clone https://github.com/<your-username>/adaptive-serious-games-asd.git
cd adaptive-serious-games-asd
```

#### Step 2: Backend Setup
```bash
# Navigate to the backend directory
cd FINAL_PROJECT/backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install opencv-python mediapipe ultralytics faster-whisper sounddevice

# Start the FastAPI server
python app.py
```
*The backend server will start on `http://localhost:8000` with interactive Swagger API docs at `http://localhost:8000/docs`.*

#### Step 3: Frontend Setup
Open a new terminal window:
```bash
# Navigate to the frontend directory
cd FINAL_PROJECT/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
*The frontend application will be live at `http://localhost:5173`.*

---

## 🔑 Demo Credentials for Testing

The platform comes pre-seeded with sample clinical and student records:

| Role | Username | Password / PIN | Description |
| :--- | :--- | :--- | :--- |
| **Student** | `alex` | `1234` | Alex Miller (Age 7, Level 3 Adventurer, Assigned 5 Quests) |
| **Student** | `maya` | `1234` | Maya Lin (Age 6, Level 2 Explorer) |
| **Teacher** | `teacher` | `teacher123` | Ms. Sarah Wilson (Lead Educator, Sunflower Classroom) |
| **Parent** | `parent` | `parent123` | Elena Miller (Mother & Primary Caregiver of Alex) |

*The login screen includes **1-Click Instant Demo Login Buttons** for rapid evaluation.*

---

## 🔬 Scientific & Technical References

1. **Google MediaPipe:** Lugaresi, C., et al. (2019). *MediaPipe: A Framework for Building Perception Pipelines.* arXiv:1906.08172.
2. **OpenCV:** Bradski, G. (2000). *The OpenCV Library.* Dr. Dobb's Journal of Software Tools.
3. **Reinforcement Learning:** Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction.* MIT Press.
4. **TEACCH Autism Program:** Mesibov, G. B., Shea, V., & Schopler, E. (2004). *The TEACCH Approach to Autism Spectrum Disorders.* Springer Science & Business Media.
5. **Facial Action Coding System (FACS):** Ekman, P., & Friesen, W. V. (1978). *Facial Action Coding System: A Technique for the Measurement of Facial Movement.* Consulting Psychologists Press.
6. **YOLOv8 Architecture:** Jocher, G., Chaurasia, A., & Qiu, J. (2023). *Ultralytics YOLOv8.* GitHub: https://github.com/ultralytics/ultralytics.
7. **FastAPI Framework:** Ramírez, S. (2018). *FastAPI: Modern, Fast Web Framework for Python.* https://fastapi.tiangolo.com/.

---

## 📜 Ethical Considerations & Clinical Disclaimer

> **Clinical Disclaimer:** This serious-game computing platform is designed as an assistive, supplemental educational and developmental practice tool for children with Autism Spectrum Disorder. It is engineered to complement, not replace, certified professional clinical therapy, speech-language pathology, or medical diagnoses. Always consult licensed pediatric developmental specialists for clinical diagnostic evaluations.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for full details.

---

<p align="center">
  <b>Designed and Engineered by Swaraj Krishna P P</b><br>
  <i>Computer Science & Engineering • APJ Abdul Kalam Technological University (KTU) • Class of 2026</i>
</p>
