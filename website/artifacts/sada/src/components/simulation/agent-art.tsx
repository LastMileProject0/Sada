const C = 'hsl(182 90% 60%)', V = 'hsl(270 80% 70%)';

export function AgentArt({ index, className = '' }: { index: number; className?: string }) {
  const id = `ag${index}`;
  return (
    <svg viewBox="0 0 80 80" className={className} aria-hidden fill="none" strokeLinecap="round" strokeLinejoin="round">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor={C} /><stop offset="1" stopColor={V} /></linearGradient>
        <radialGradient id={`${id}g`}><stop offset="0" stopColor={index % 2 ? V : C} stopOpacity=".35" /><stop offset="1" stopColor={C} stopOpacity="0" /></radialGradient>
      </defs>
      <circle cx="40" cy="40" r="38" fill={`url(#${id}g)`} />
      <circle cx="40" cy="40" r="30" stroke={`url(#${id})`} strokeOpacity=".35" strokeDasharray="2 5" className="sim-orbit" />
      {index === 0 && <g stroke={`url(#${id})`} strokeWidth="2">
        <path d="M40 46 V22" /><circle cx="40" cy="20" r="3" fill={C} />
        <path d="M30 30 a14 14 0 0 1 20 0" /><path d="M24 24 a22 22 0 0 1 32 0" opacity=".6" />
        <path d="M32 58 L40 46 L48 58 Z" /><path d="M14 62 h52" opacity=".4" />
        {[18, 30, 50, 62].map((x, i) => <rect key={x} x={x - 2} y="60" width="4" height="4" rx="1" fill={['hsl(160 80% 55%)', 'hsl(42 95% 60%)', 'hsl(352 85% 62%)', 'hsl(220 15% 55%)'][i]} stroke="none" />)}
      </g>}
      {index === 1 && <g stroke={`url(#${id})`} strokeWidth="2">
        <path d="M40 16 L64 58 H16 Z" /><path d="M40 32 V44" /><circle cx="40" cy="50" r="1.6" fill={V} />
        <path d="M10 40 h8 l4 -8 l5 14 l4 -6 h4" opacity=".5" /><path d="M52 64 h18" opacity=".4" />
      </g>}
      {index === 2 && <g stroke={`url(#${id})`} strokeWidth="2">
        <path d="M40 14 L60 22 V38 C60 52 50 60 40 66 C30 60 20 52 20 38 V22 Z" />
        <circle cx="40" cy="32" r="3.5" /><path d="M32 40 h16 M40 40 v10 M34 54 l6 -4 l6 4" />
      </g>}
      {index === 3 && <g stroke={`url(#${id})`} strokeWidth="2">
        <path d="M58 30 A20 20 0 1 0 60 44" /><path d="M58 20 v10 h-10" />
        <circle cx="40" cy="40" r="4" fill={C} stroke="none" />
        {[[40, 40, 52, 30], [40, 40, 28, 30], [40, 40, 34, 54]].map(([a, b, c, d], i) => <g key={i}><path d={`M${a} ${b} L${c} ${d}`} opacity=".55" /><circle cx={c} cy={d} r="2.6" fill={i === 0 ? V : 'none'} /></g>)}
      </g>}
    </svg>
  );
}
