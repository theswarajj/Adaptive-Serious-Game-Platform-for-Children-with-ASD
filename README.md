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

---

### Level 1: Attention & Motor Control (Sensory-Motor Foundation)

#### 1. Bubble Hunt (`bubble_hunt.py`)
* **Clinical Target:** Fine motor precision, bilateral finger isolation, hand-eye coordination, and visual tracking.
* **Computer Vision Pipeline:** Leverages **MediaPipe Hands** to identify 21 3D hand landmarks in real time. The distance between Landmark 4 (Thumb Tip) and Landmark 8 (Index Tip) is continuously tracked in Euclidean normalized coordinate space:
  $$	ext{Dist}_{	ext{pinch}} = \sqrt{(x_8 - x_4)^2 + (y_8 - y_4)^2 + (z_8 - z_4)^2}$$
* **Interactive Mechanics:** Color-coded floating bubbles spawn across randomized vectors. When the child performs a pinch gesture ($	ext{Dist}_{	ext{pinch}} < 	heta_{	ext{threshold}}$) or taps over a bubble, the system triggers a dynamic particle explosion, plays a physical pop frequency through the Web Audio synthesizer, and increments the motor stability score.
* **Metrics Recorded:** Average reaction time (ms), pinch precision error, total bubbles popped, and bilateral hand usage ratio.

#### 2. Follow the Star (`follow_the_star.py`)
* **Clinical Target:** Vestibular stability, sustained ocular fixation, and smooth cervical head-tracking.
* **Computer Vision Pipeline:** Utilizes **MediaPipe Face Mesh** with 468 3D facial landmarks. Extracts Landmark 1 (Nasal Tip), Landmark 33 (Left Eye), and Landmark 263 (Right Eye) to calculate real-time head pose yaw, pitch, and roll:
  $$	ext{Yaw} = rctan2(x_{	ext{nose}} - x_{	ext{mid\_eyes}}, z_{	ext{nose}} - z_{	ext{mid\_eyes}})$$
* **Interactive Mechanics:** A celestial gold star drifts along smooth parametric paths. The child must steer their nose and head into the star's glowing orbital ring. A sustained 2-second hold within the bounding radius triggers a star capture animation and positive reinforcement audio.
* **Metrics Recorded:** Continuous gaze-on-target percentage, average angular tracking deviation, hold stability percentage, and cervical rotation range.

#### 3. Pattern Trail (`pattern_trail.py`)
* **Clinical Target:** Dynamic motor planning, trajectory tracing precision, and velocity regulation.
* **Computer Vision Pipeline:** Tracks Landmark 8 (Index Finger Tip) of the dominant hand, maintaining a temporal moving-average smoothing filter to eliminate physiological tremor:
  $$\mathbf{p}_{	ext{filtered}}^{(t)} = lpha \mathbf{p}_{	ext{raw}}^{(t)} + (1 - lpha) \mathbf{p}_{	ext{filtered}}^{(t-1)}$$
* **Interactive Mechanics:** Displays geometric ribbons (circles, infinity loops, zig-zags, and numerals). The child traces the glowing trajectory within a dynamic spatial tolerance window. Deviation off the trail dampens audio feedback, guiding the child back gently without negative penalization.
* **Metrics Recorded:** Mean path deviation (pixels), trajectory smoothness index, completion time, and velocity uniformity.

---

### Level 2: Emotion Understanding & Visual Processing (Affective Cognition)

#### 4. Emotion Mirror (`emotion_mirror.py`)
* **Clinical Target:** Facial emotion recognition, affective empathy, and facial action unit (AU) mimicry.
* **Computer Vision Pipeline:** Real-time geometric analysis of facial landmarks:
  - **Lip Corner Puller (AU12 - Joy):** Ratio between mouth corner distance (Landmarks 61, 291) and inter-ocular distance.
  - **Mouth Stretch / Jaw Drop (AU26 - Surprise):** Vertical distance between upper and lower inner lips (Landmarks 13, 14).
  - **Brow Lowerer / Furrow (AU4 - Frustration / Focus):** Distance between medial eyebrow points (Landmarks 55, 285).
* **Interactive Mechanics:** Displays an expressive animated character prompt (e.g., Happy, Surprised, Calm). The child mirrors the expression into their webcam. An affective matching gauge fills in real time; upon reaching 80% congruence, celebratory confetti sparkles burst across the viewport.
* **Metrics Recorded:** Emotion classification latency, mimicry accuracy index, facial symmetry score, and held duration.

#### 5. Body Says It (`body_says_it.py`)
* **Clinical Target:** Gross motor posture interpretation, non-verbal body language decoding, and somatic awareness.
* **Computer Vision Pipeline:** Uses **MediaPipe Pose** with 33 full-body skeletal keypoints. Tracks bilateral shoulder slopes (Landmarks 11, 12), elbow angles (13, 14), and wrist elevations (15, 16) to classify macro-postures (e.g., confident upright, defensive crossed arms, excited waving).
* **Interactive Mechanics:** Presents animated 3D scenarios where a character communicates purely through posture. The child identifies the character's internal affective state by raising corresponding fingers (1–4) detected via MediaPipe, or tapping on-screen tactile cards.
* **Metrics Recorded:** Postural classification accuracy, non-verbal deduction speed, and response confidence.

#### 6. Object Quest: Visual Scan (`objectquest.py`)
* **Clinical Target:** Environmental visual scanning, object discrimination, and spatial perceptual processing.
* **Computer Vision Pipeline:** Employs an optimized **YOLOv8 nano** deep learning object detection model running locally alongside MediaPipe hand bounding boxes:
  $$\hat{y} = 	ext{YOLOv8}(\mathbf{I}_{	ext{webcam}}), \quad 	ext{IoU}(\mathbf{B}_{	ext{hand}}, \mathbf{B}_{	ext{object}}) > 0.4$$
* **Interactive Mechanics:** The system presents a challenge (e.g., *"Show me a cup!"* or *"Find a book!"*). The child holds the requested physical item up to their camera. The YOLOv8 inference pipeline validates the object class with high confidence ($> 0.65$) within the child's grasp, rewarding physical real-world interaction.
* **Metrics Recorded:** Real-world object retrieval latency, detection accuracy, scanning persistence, and object vocabulary depth.

---

### Level 3: Speech Processing & Expressive Communication (Verbal Expression)

#### 7. Talk & Build (`talk_and_build.py`)
* **Clinical Target:** Verbal sentence construction, narrative comprehension, and expressive vocabulary formation.
* **Speech Processing Pipeline:** Captures live microphone audio buffers via `sounddevice`, processed through a real-time local automatic speech recognition (ASR) pipeline powered by **faster-whisper** with custom phonetic grammar matching:
  $$	ext{Sim}_{	ext{Levenshtein}}(	ext{Transcript}, 	ext{Expected\_Tokens}) \ge 0.70$$
* **Interactive Mechanics:** Features **Nutmeg the Squirrel**, an animated companion who asks engaging questions about illustrated scenes (e.g., *"Where are the children playing?"*). The child can speak their answer aloud into the Magic Mic or tap tactile candy option buttons. Live speech recognition displays immediate phonetic text feedback with animated equalizers.
* **Metrics Recorded:** Utterance response latency, sentence completeness score, phoneme clarity, and voluntary verbalization percentage.

#### 8. Describe the Scene (`describe_the_scene.py`)
* **Clinical Target:** Spoken descriptive fluency, contextual visual storytelling, and syntactic elaboration.
* **Speech Processing Pipeline:** Multimodal pipeline correlating computer vision scene descriptors with acoustic speech transcripts using keyword semantic matching.
* **Interactive Mechanics:** Shows lively video scenarios (e.g., a playful kitten in a sunlit room, children sharing toys at school). The child speaks aloud one or more descriptive sentences explaining the scene. Speech analysis extracts semantic predicates and visual descriptors to award 1 to 3 gold stars.
* **Metrics Recorded:** Descriptive word count, semantic breadth index, response formulation speed, and narrative coherence.

#### 9. Object Quest: See & Say (`object_quest.py` - Level 3)
* **Clinical Target:** Rapid verbal naming, phonological retrieval, and speech articulation.
* **Speech Processing Pipeline:** Voice activity detection (VAD) coupled with phonetic phrase alignment.
* **Interactive Mechanics:** Everyday physical items appear on screen. The child names the item clearly into their microphone. The system confirms pronunciation, provides supportive phonetic audio modeling if the child hesitates, and advances the questline.
* **Metrics Recorded:** Articulation accuracy, phoneme onset latency, vocal volume stability, and naming stamina.

---

### Level 4: Social Interaction & Joint Attention (Reciprocal Engagement)

#### 10. Look, Point, and Share (`look_point_and_share.py`)
* **Clinical Target:** Responding to joint attention (RJA), initiating joint attention (IJA), and referential index pointing.
* **Computer Vision Pipeline:** Simultaneous dual-model orchestration: MediaPipe Face Mesh calculates 3D gaze vector $ec{\mathbf{v}}_{	ext{gaze}}$, while MediaPipe Hands calculates the directional ray extending from Landmark 5 (Index MCP) through Landmark 8 (Index Tip) $ec{\mathbf{v}}_{	ext{point}}$. Target intersection is evaluated in 3D projective geometry:
  $$\Delta_{	ext{target}} = \min_t \|\mathbf{p}_{	ext{finger}} + t ec{\mathbf{v}}_{	ext{point}} - \mathbf{p}_{	ext{target}}\|$$
* **Interactive Mechanics:** A virtual peer turns its head and looks toward an animated object in the corner of the room. The child must follow the peer's gaze, identify the referenced target, and physically point at it with their index finger or gaze steadily at it.
* **Metrics Recorded:** Gaze-following reaction time (ms), pointing angle accuracy, referential joint attention score, and social referencing rate.

#### 11. My Turn, Your Turn (`my_turn_your_turn.py`)
* **Clinical Target:** Reciprocal turn-taking, inhibitory motor control, and impulse regulation.
* **Computer Vision Pipeline:** Tracks hand presence within an active tactile interaction zone, synchronized with a state-machine controlling interactive permissions.
* **Interactive Mechanics:** A cooperative game played alongside a virtual peer or therapist. When the signal indicates **"My Turn" (Green Light)**, the child interacts freely. When the signal shifts to **"Wait / Friend's Turn" (Red Light)**, the child must withhold motor responses. Premature clicks or movement in the active zone trigger gentle visual cues to encourage waiting.
* **Metrics Recorded:** Response inhibition success rate, premature response count, waiting interval endurance (seconds), and reciprocal latency.

#### 12. Copy My Move (`copymymove.py`)
* **Clinical Target:** Bilateral motor imitation, kinesthetic proprioception, and motor execution.
* **Computer Vision Pipeline:** Extracts 33 skeletal landmarks via MediaPipe Pose, calculating relative joint angles (shoulder abduction, elbow flexion, knee angle) normalized against anatomical body dimensions:
  $$	heta = rccos\left(rac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}ight)$$
* **Interactive Mechanics:** An animated avatar demonstrates engaging, therapeutic poses (e.g., Airplane Arms, Tree Pose, Superhero Stretch). The child mirrors the pose. Visual skeletal overlays glow gold when anatomical angles align within an adaptive angular error threshold ($\pm 15^\circ$).
* **Metrics Recorded:** Angular pose matching congruence (%), motor imitation latency, balance hold time, and bilateral symmetry.

---

### Level 5: Real-Life Adaptive Life-Skills Simulations (Functional Independence)

#### 13. School Day Routine Simulator (`school_day_simulator.py`)
* **Clinical Target:** Navigating school environments, classroom morning routines, desk organization, and asking for educator assistance.
* **Interactive Simulation:** An interactive visual simulation where the child navigates real-world school dilemmas: hanging their backpack, following the visual schedule, coping with unexpected fire alarm bells (sensory regulation), and raising their hand when stuck.
* **Metrics Recorded:** Routine decision-making accuracy, social problem-solving score, and sensory coping selection.

#### 14. Community Travel Simulator (`community_travel_simulator.py`)
* **Clinical Target:** Community pedestrian safety, crosswalk signal comprehension, bus boarding, and ticket payment.
* **Interactive Simulation:** A realistic street-crossing and public transit simulation. The child checks traffic in both directions, waits for pedestrian walk signals, identifies the correct bus number, and practices interacting with the bus driver.
* **Metrics Recorded:** Street safety compliance index, transit sequential comprehension, and environmental hazard awareness.

#### 15. Supermarket Shopping Adventure (`supermarket_adventure.py`)
* **Clinical Target:** Visual list scanning, item categorization, currency management, and cashier social communication.
* **Interactive Simulation:** The child is given a pictorial and text shopping list. They navigate store aisles, select corresponding groceries, calculate total cost within a set budget, and practice conversational exchange with the cashier (*"Hello!", "Thank you!"*).
* **Metrics Recorded:** List item completion percentage, budget adherence accuracy, conversational etiquette score, and scanning efficiency.

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
  $$s_t = \left( 	ext{SkillDomainMastery}, 	ext{CurrentStreak}, 	ext{AttentionScore}, 	ext{ErrorRate}, 	ext{ReactionLatency} ight)$$
* **Action Space ($A$):**
  $$a \in \{ 	ext{IncreaseDifficulty}, 	ext{DecreaseDifficulty}, 	ext{InjectVisualHint}, 	ext{TriggerRefocusingCue}, 	ext{PromoteLevel} \}$$
* **Reward Function ($R(s, a)$):**
  Balances challenge and emotional comfort to prevent frustration or boredom:
  $$R(s_t, a_t) = w_1 \cdot 	ext{Accuracy} + w_2 \cdot 	ext{AttentionRetention} - w_3 \cdot 	ext{FrustrationSignal} - w_4 \cdot 	ext{Latency}$$
* **Bellman Update Equation:**
  $$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + lpha \left[ R(s_t, a_t) + \gamma \max_{a'} Q(s_{t+1}, a') - Q(s_t, a_t) ight]$$
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
