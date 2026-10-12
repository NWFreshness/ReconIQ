export function StatStrip({ stats }: { stats: { label: string; value: string | number }[] }) {
  return (
    <dl className="grid grid-cols-2 sm:grid-cols-4 border-y border-foreground mb-8">
      {stats.map((stat) => (
        <div key={stat.label} className="flex flex-col-reverse py-3 pr-4">
          <dt className="text-xs text-muted">{stat.label}</dt>
          <dd className="font-display text-3xl font-semibold tabular-nums">{stat.value}</dd>
        </div>
      ))}
    </dl>
  );
}
