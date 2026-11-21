import { Link } from 'react-router-dom'
import { LEVEL_INFO, GAME_CATALOGUE } from '../data/games'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-playground overflow-hidden">
      {/* ── Fun Floating Decorations ─────────────────────── */}
      <div className="fixed pointer-events-none z-0">
        <div className="absolute top-20 left-10 text-5xl animate-float opacity-30" style={{animationDelay:'0s'}}>🌈</div>
        <div className="absolute top-40 right-20 text-4xl animate-float opacity-25" style={{animationDelay:'0.5s'}}>⭐</div>
        <div className="absolute top-72 left-1/4 text-3xl animate-float opacity-20" style={{animationDelay:'1s'}}>🎈</div>
        <div className="absolute bottom-40 right-1/3 text-4xl animate-float opacity-25" style={{animationDelay:'1.5s'}}>🦋</div>
        <div className="absolute bottom-20 left-20 text-3xl animate-float opacity-20" style={{animationDelay:'2s'}}>🌻</div>
      </div>

      {/* ── Nav ───────────────────────────────────────────── */}
      <nav className="relative z-10 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-rainbow rounded-2xl flex items-center justify-center text-2xl shadow-lg animate-wiggle">
              ✨
            </div>
            <span className="font-[var(--font-fun)] font-extrabold text-2xl text-[var(--color-text)]">
              Skill<span className="text-[var(--color-sky-dark)]">Spark</span>
            </span>
          </div>
          <Link to="/login" className="btn-3d btn-3d-purple no-underline text-white font-black px-5 py-2.5 rounded-2xl text-sm shadow-md flex items-center gap-1.5">
            🚀 Let's Go!
          </Link>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="relative z-10 px-6 pt-10 pb-16">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-white/80 backdrop-blur-sm border-3 border-[var(--color-sunshine)] rounded-full px-5 py-2.5 mb-8 animate-bounceIn">
            <span className="text-xl">🎮</span>
            <span className="font-[var(--font-fun)] font-bold text-sm text-[var(--color-text)]">Learn Through Play!</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold mb-6 font-[var(--font-fun)] animate-fadeInUp leading-tight">
            <span className="text-[var(--color-sky-dark)]">Learn</span>{' '}
            <span className="text-[var(--color-lavender-dark)]">Social Skills</span>
            <br />
            <span className="text-[var(--color-sunshine-dark)]">Through</span>{' '}
            <span className="text-[var(--color-coral-dark)]">Fun Games!</span>{' '}
            <span className="text-4xl md:text-5xl animate-wiggle inline-block">🎉</span>
          </h1>

          <p className="text-lg md:text-xl text-[var(--color-text-light)] max-w-2xl mx-auto mb-10 animate-fadeInUp" style={{animationDelay:'0.15s'}}>
            Play colorful games, earn stars, and level up! Each game helps you learn new skills at your own pace. No rush — just fun! 🌟
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fadeInUp" style={{animationDelay:'0.25s'}}>
            <Link to="/login" className="btn-3d btn-3d-blue no-underline text-white font-black text-base px-7 py-3.5 rounded-2xl shadow-lg flex items-center gap-2">
              🎮 Start Playing!
            </Link>
            <a href="#levels" className="btn-3d btn-3d-slate no-underline text-slate-800 bg-white font-black text-base px-7 py-3.5 rounded-2xl shadow-md border-2 border-slate-200 flex items-center gap-2">
              👀 See the Games
            </a>
          </div>
        </div>
      </section>

      {/* ── Who Is It For? ────────────────────────────────── */}
      <section className="relative z-10 px-6 py-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-extrabold text-center mb-10 font-[var(--font-fun)]">
            Something for Everyone! 🌈
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { emoji: '👦', role: 'For Kids', desc: 'Play fun games, pop bubbles, explore a 3D supermarket, and earn stars as you learn new skills!', bg: 'bg-ocean', shadow: 'shadow-blue-200' },
              { emoji: '👨‍👩‍👧', role: 'For Parents', desc: 'See your child\'s progress, set goals, manage game settings, and track their learning journey.', bg: 'bg-sunny', shadow: 'shadow-yellow-200' },
              { emoji: '👩‍🏫', role: 'For Teachers', desc: 'Monitor multiple students, create lesson plans, review performance data, and assign activities.', bg: 'bg-forest', shadow: 'shadow-green-200' },
            ].map((item, i) => (
              <div key={i} className="fun-card p-8 text-center animate-fadeInUp" style={{animationDelay:`${i*0.1}s`}}>
                <div className={`w-20 h-20 ${item.bg} rounded-3xl flex items-center justify-center text-4xl mx-auto mb-5 shadow-lg ${item.shadow}`}>
                  {item.emoji}
                </div>
                <h3 className="font-[var(--font-fun)] font-bold text-xl mb-3">{item.role}</h3>
                <p className="text-[var(--color-text-light)] text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Five Levels ───────────────────────────────────── */}
      <section className="relative z-10 px-6 py-16" id="levels">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-extrabold text-center mb-4 font-[var(--font-fun)]">
            5 Levels of Adventure! 🏆
          </h2>
          <p className="text-center text-[var(--color-text-light)] mb-10 text-lg">
            Complete each level to unlock the next one. Keep going! 💪
          </p>
          <div className="grid gap-5">
            {Object.entries(LEVEL_INFO).map(([num, info]) => {
              const games = GAME_CATALOGUE.filter(g => g.level === Number(num))
              return (
                <div key={num} className="fun-card overflow-hidden animate-fadeInUp" style={{animationDelay:`${Number(num)*0.08}s`}}>
                  <div className="flex flex-col md:flex-row">
                    <div className="md:w-56 p-6 flex items-center gap-4" style={{background: `linear-gradient(135deg, ${info.color}30, ${info.color}15)`}}>
                      <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-white font-extrabold text-2xl font-[var(--font-fun)] shadow-lg shrink-0" style={{backgroundColor: info.color}}>
                        {num}
                      </div>
                      <div>
                        <h3 className="font-[var(--font-fun)] font-bold text-base">{info.name}</h3>
                        <p className="text-xs text-[var(--color-text-light)] mt-0.5">{info.description}</p>
                      </div>
                    </div>
                    <div className="flex-1 p-5 flex items-center gap-3 flex-wrap">
                      {games.map(g => (
                        <div key={g.id} className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-sm font-bold border-2 ${
                          g.status === 'available'
                            ? 'bg-green-50 border-green-300 text-green-800'
                            : 'bg-gray-50 border-gray-200 text-gray-400 border-dashed'
                        }`}>
                          <span className="text-lg">{g.icon}</span>
                          <span>{g.name}</span>
                          {g.status === 'planned' && <span className="text-[10px] opacity-60">🔜</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────── */}
      <section className="relative z-10 px-6 py-16">
        <div className="max-w-3xl mx-auto text-center">
          <div className="text-6xl mb-6 animate-bounceIn">🚀</div>
          <h2 className="text-3xl md:text-4xl font-extrabold mb-4 font-[var(--font-fun)]">
            Ready for an Adventure?
          </h2>
          <p className="text-[var(--color-text-light)] text-lg mb-8">
            Pick your role and start exploring today!
          </p>
          <Link to="/login" className="btn-fun btn-fun-lg bg-rainbow text-white shadow-xl">
            🎮 Let's Go!
          </Link>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────── */}
      <footer className="relative z-10 py-8 px-6 border-t-3 border-[var(--color-border)] bg-white/60">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xl">✨</span>
            <span className="font-[var(--font-fun)] font-bold text-sm">SkillSpark</span>
          </div>
          <p className="text-xs text-[var(--color-text-light)]">
            A fun learning platform for building social skills through play. Not a diagnostic or assessment tool.
          </p>
        </div>
      </footer>
    </div>
  )
}
