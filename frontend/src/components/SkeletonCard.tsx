export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded-xl bg-gray-50 border border-gray-100 p-5 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="h-4 bg-gray-200 rounded w-24" />
        <div className="w-9 h-9 bg-gray-200 rounded-lg" />
      </div>
      <div className="h-8 bg-gray-200 rounded w-16 mb-2" />
      <div className="h-3 bg-gray-100 rounded w-32" />
    </div>
  )
}

export function SkeletonRow() {
  return (
    <div className="animate-pulse flex items-center gap-4 py-3 border-b border-gray-50">
      <div className="h-4 bg-gray-200 rounded w-1/4" />
      <div className="h-4 bg-gray-100 rounded w-1/3" />
      <div className="h-6 bg-gray-200 rounded-full w-16 ml-auto" />
    </div>
  )
}
