import React from 'react'

export function SkeletonCard({ count = 1 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="p-5 rounded-3xl bg-white/90 border-2 border-slate-100 shadow-sm overflow-hidden relative space-y-4"
        >
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl skeleton-shimmer shrink-0" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-3/4 rounded-lg skeleton-shimmer" />
              <div className="h-3 w-1/2 rounded-md skeleton-shimmer" />
            </div>
          </div>
          <div className="space-y-2 pt-1">
            <div className="h-3 w-full rounded-md skeleton-shimmer" />
            <div className="h-3 w-5/6 rounded-md skeleton-shimmer" />
          </div>
          <div className="flex items-center justify-between pt-2">
            <div className="h-6 w-20 rounded-full skeleton-shimmer" />
            <div className="h-9 w-28 rounded-2xl skeleton-shimmer" />
          </div>
        </div>
      ))}
    </>
  )
}

export function SkeletonStatsGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 mb-6">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="p-4 rounded-2xl bg-white border border-slate-100 shadow-xs space-y-2.5"
        >
          <div className="flex items-center justify-between">
            <div className="h-3 w-16 rounded skeleton-shimmer" />
            <div className="w-6 h-6 rounded-full skeleton-shimmer" />
          </div>
          <div className="h-7 w-12 rounded-lg skeleton-shimmer" />
          <div className="h-2.5 w-20 rounded skeleton-shimmer" />
        </div>
      ))}
    </div>
  )
}

export function SkeletonCurriculum({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 p-4 rounded-2xl bg-white border border-slate-100 shadow-xs"
        >
          <div className="w-9 h-9 rounded-xl skeleton-shimmer shrink-0" />
          <div className="w-12 h-12 rounded-2xl skeleton-shimmer shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-44 rounded-lg skeleton-shimmer" />
            <div className="h-3 w-72 rounded-md skeleton-shimmer" />
          </div>
          <div className="h-8 w-24 rounded-xl skeleton-shimmer shrink-0" />
        </div>
      ))}
    </div>
  )
}

export function SkeletonProfile360() {
  return (
    <div className="space-y-6">
      <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex items-center gap-6">
        <div className="w-20 h-20 rounded-full skeleton-shimmer shrink-0" />
        <div className="flex-1 space-y-3">
          <div className="h-6 w-48 rounded-lg skeleton-shimmer" />
          <div className="h-4 w-72 rounded-md skeleton-shimmer" />
          <div className="flex gap-2">
            <div className="h-6 w-24 rounded-full skeleton-shimmer" />
            <div className="h-6 w-28 rounded-full skeleton-shimmer" />
          </div>
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-6">
        <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm h-72 skeleton-shimmer" />
        <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm space-y-4">
          <div className="h-5 w-36 rounded skeleton-shimmer" />
          <div className="h-4 w-full rounded skeleton-shimmer" />
          <div className="h-4 w-5/6 rounded skeleton-shimmer" />
          <div className="h-4 w-4/6 rounded skeleton-shimmer" />
        </div>
      </div>
    </div>
  )
}
