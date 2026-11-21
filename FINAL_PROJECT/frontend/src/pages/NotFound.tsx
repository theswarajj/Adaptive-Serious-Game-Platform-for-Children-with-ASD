import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-playground flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-20 left-10 text-5xl animate-float opacity-20">🌈</div>
      <div className="absolute bottom-20 right-10 text-4xl animate-float opacity-15" style={{animationDelay:'1s'}}>⭐</div>

      <div className="fun-card-flat p-12 text-center max-w-md animate-bounceIn relative z-10">
        <div className="text-7xl mb-6 animate-wiggle">🗺️</div>
        <h1 className="text-5xl font-extrabold font-[var(--font-fun)] mb-3 text-[var(--color-sky-dark)]">Oops!</h1>
        <p className="text-[var(--color-text-light)] text-lg mb-8">
          This page doesn't exist! Let's go somewhere fun instead! 🚀
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link to="/" className="btn-fun btn-fun-md bg-ocean text-white shadow-lg no-underline">
            🏠 Go Home
          </Link>
          <Link to="/login" className="btn-fun btn-fun-md bg-white text-[var(--color-text)] border-3 border-[var(--color-border)] shadow-md no-underline">
            🎮 Play Games
          </Link>
        </div>
      </div>
    </div>
  )
}
