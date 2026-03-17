<script lang="ts">
  import { onMount } from 'svelte';
  import gsap from 'gsap';

  interface Props {
    labels: string[];
    t1Values: number[];
    t2Values: number[];
    team1: string;
    team2: string;
  }

  let { labels, t1Values, t2Values, team1, team2 }: Props = $props();

  let t1Polygon: SVGPolygonElement;
  let t2Polygon: SVGPolygonElement;
  let dotEls: SVGCircleElement[] = [];

  // Tooltip state
  let tooltip = $state<{ visible: boolean; x: number; y: number; label: string; t1: number; t2: number }>({
    visible: false, x: 0, y: 0, label: '', t1: 0, t2: 0
  });

  const width = 480;
  const height = 400;
  const centerX = width / 2;
  const centerY = (height - 50) / 2 + 20; // shift up to leave room for legend at bottom
  const radius = 120;
  const levels = 5;
  const angleStep = $derived(360 / labels.length);

  function polarToCartesian(angle: number, distance: number) {
    const rad = (angle - 90) * (Math.PI / 180);
    return { x: centerX + distance * Math.cos(rad), y: centerY + distance * Math.sin(rad) };
  }

  const t1Points = $derived.by(() => {
    return t1Values.map((val, i) => {
      const pt = polarToCartesian(angleStep * i, (val / 100) * radius);
      return `${pt.x},${pt.y}`;
    }).join(' ');
  });

  const t2Points = $derived.by(() => {
    return t2Values.map((val, i) => {
      const pt = polarToCartesian(angleStep * i, (val / 100) * radius);
      return `${pt.x},${pt.y}`;
    }).join(' ');
  });

  function showTooltip(e: MouseEvent, i: number) {
    const svg = (e.target as SVGElement).closest('svg')!.getBoundingClientRect();
    const el = e.target as SVGElement;
    const rect = el.getBoundingClientRect();
    tooltip = {
      visible: true,
      x: rect.left - svg.left + 10,
      y: rect.top - svg.top - 10,
      label: labels[i],
      t1: t1Values[i],
      t2: t2Values[i]
    };
  }

  function hideTooltip() {
    tooltip = { ...tooltip, visible: false };
  }

  $effect(() => {
    if (t1Values.length === 0) return;

    gsap.fromTo(
      [t1Polygon, t2Polygon],
      { scale: 0, transformOrigin: `${centerX}px ${centerY}px`, opacity: 0 },
      { scale: 1, opacity: 1, duration: 1.2, ease: 'back.out(1.2)', stagger: 0.2 }
    );
    
    const validDots = dotEls.filter(d => d !== null);
    gsap.fromTo(
      validDots,
      { scale: 0, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.6, delay: 1, stagger: 0.05, ease: 'back.out(2)' }
    );
  });
</script>

<div class="relative w-full">
  <svg {width} {height} viewBox="0 0 {width} {height}" class="w-full h-auto overflow-visible">
    <!-- Background level rings -->
    {#each Array(levels) as _, i}
      <circle cx={centerX} cy={centerY} r={radius * ((i + 1) / levels)}
        fill="none" stroke="#334155" stroke-width="1" opacity="0.4" />
    {/each}

    <!-- Axis lines -->
    {#each labels as _, i}
      {@const pt = polarToCartesian(angleStep * i, radius)}
      <line x1={centerX} y1={centerY} x2={pt.x} y2={pt.y}
        stroke="#475569" stroke-width="1" opacity="0.5" />
    {/each}

    <!-- Team 2 polygon -->
    <polygon bind:this={t2Polygon}
      points={t2Points}
      fill="#ef4444" fill-opacity="0.15"
      stroke="#ef4444" stroke-width="2"
      style="filter: drop-shadow(0 0 8px rgba(239,68,68,0.4))" />

    <!-- Team 1 polygon -->
    <polygon bind:this={t1Polygon}
      points={t1Points}
      fill="#3b82f6" fill-opacity="0.15"
      stroke="#3b82f6" stroke-width="2"
      style="filter: drop-shadow(0 0 8px rgba(59,130,246,0.4))" />

    <!-- Axis labels -->
    {#each labels as label, i}
      {@const pt = polarToCartesian(angleStep * i, radius + 28)}
      <text x={pt.x} y={pt.y} text-anchor="middle" dominant-baseline="middle"
        font-size="11" fill="#94a3b8">{label}</text>
    {/each}

    <!-- T1 dots with hover -->
    {#each t1Values as val, i}
      {@const pt = polarToCartesian(angleStep * i, (val / 100) * radius)}
      <circle bind:this={dotEls[i]}
        cx={pt.x} cy={pt.y} r="5" fill="#3b82f6"
        role="img"
        aria-label="{labels[i]} indicator for {team1}"
        style="filter: drop-shadow(0 0 4px rgba(59,130,246,0.9)); cursor: pointer"
        onmouseenter={(e) => showTooltip(e, i)}
        onmouseleave={hideTooltip} />
    {/each}

    <!-- T2 dots with hover -->
    {#each t2Values as val, i}
      {@const pt = polarToCartesian(angleStep * i, (val / 100) * radius)}
      <circle bind:this={dotEls[labels.length + i]}
        cx={pt.x} cy={pt.y} r="5" fill="#ef4444"
        role="img"
        aria-label="{labels[i]} indicator for {team2}"
        style="filter: drop-shadow(0 0 4px rgba(239,68,68,0.9)); cursor: pointer"
        onmouseenter={(e) => showTooltip(e, i)}
        onmouseleave={hideTooltip} />
    {/each}

    <!-- Legend — bottom center, well below chart -->
    <g transform="translate({centerX}, {height - 18})">
      <circle cx="-90" cy="0" r="5" fill="#3b82f6" />
      <text x="-80" y="4" font-size="12" font-weight="600" fill="#60a5fa">{team1}</text>
      <circle cx="30" cy="0" r="5" fill="#ef4444" />
      <text x="40" y="4" font-size="12" font-weight="600" fill="#fca5a5">{team2}</text>
    </g>
  </svg>

  <!-- Tooltip -->
  {#if tooltip.visible}
    <div
      class="absolute pointer-events-none z-10 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-xs shadow-xl"
      style="left: {tooltip.x}px; top: {tooltip.y}px; transform: translateY(-100%)"
    >
      <div class="font-semibold text-slate-200 mb-1">{tooltip.label}</div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-blue-500 inline-block"></span>
        <span class="text-slate-400">{team1}:</span>
        <span class="text-blue-400 font-bold">{tooltip.t1.toFixed(1)}%</span>
      </div>
      <div class="flex items-center gap-2 mt-0.5">
        <span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span>
        <span class="text-slate-400">{team2}:</span>
        <span class="text-red-400 font-bold">{tooltip.t2.toFixed(1)}%</span>
      </div>
    </div>
  {/if}
</div>
