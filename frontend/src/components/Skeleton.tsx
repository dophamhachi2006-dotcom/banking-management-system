export function Skeleton({ className = "h-6 w-full" }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-primary/10 ${className}`} />;
}
export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => <Skeleton key={i} className="h-10 w-full"/>)}
    </div>
  );
}
