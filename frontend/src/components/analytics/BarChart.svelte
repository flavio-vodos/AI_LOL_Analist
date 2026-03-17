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

  let bars: SVGRectElement[] = [];
  let tooltip = $state<{ visible: boolean; x: number; y: number; label: string; team: string; value: number; color: string }>({
    visible: false, x: 0, y: 0, label: '', team: '', value: 0, color: ''
  });

  const width = 600;
  const height = 300;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const maxValue = $derived(Math.max(...t1Values, ...t2Values, 1) * 1.15);
  const groupSpacing = $derived(chartWidth / (labels.length || 1));
  const barW = $derived(groupSpacing * 0.35);

  function getBarHeight(val: number) { return (val / maxValue) * chartHeight; }
  function getBarY(val: number) { return padding.top + chartHeight - getBarHeight(val); }

  function showTooltip(e: MouseEvent, label: string, team: string, value: number, color: string) {
    const svg = (e.target as SVGElement).closest('svg')!.getBoundingClientRect();
    const rect = (e.target as SVGElement).getBoundingClientRect();
    tooltip = { visible: true, x: rect.left - svg.left + barW / 2, y: rect.top - svg.top, label, team, value, color };
  }
  function hideTooltip() { tooltip = { ...tooltip, visible: false }; }

  $effect(() => {
    if (t1Values.length === 0) return;
    
    // Filter out any potential nulls from the bind:this array
    const validBars = bars.filter(b => b !== null);
    
    gsap.fromTo(validBars,
      { attr: { height: 0, y: padding.top + chartHeight } },
      {
        attr: {
          height: (i) => {
            const isT1 = i % 2 === 0;
            const vi = Math.floor(i / 2);
            return getBarHeight(isT1 ? t1Values[vi] : t2Values[vi]);
          },
          y: (i) => {
            const isT1 = i % 2 === 0;
            const vi = Math.floor(i / 2);
            return getBarY(isT1 ? t1Values[vi] : t2Values[vi]);
          }
        },
        duration: 1.2,
        ease: 'power3.out',
        stagger: 0.05
      }
    );
  });
</script>

<div class="relative w-full">
  <svg {width} {height} viewBox="0 0 {width} {height}" class="w-full h-auto">
    <line x1={padding.left} y1={padding.top} x2={padding.left} y2={padding.top + chartHeight} stroke="#475569" stroke-width="2" />
    <line x1={padding.left} y1={padding.top + chartHeight} x2={padding.left + chartWidth} y2={padding.top + chartHeight} stroke="#475569" stroke-width="2" />

    {#each labels as lbl, i}
      {@const gx = padding.left + i * groupSpacing + groupSpacing * 0.15}

      <!-- T1 bar -->
      <rect bind:this={bars[i * 2]}
        x={gx} y={padding.top + chartHeight} width={barW} height="0"
        fill="#3b82f6" rx="2"
        role="img" aria-label="{team1} {lbl}: {t1Values[i]}"
        style="cursor:pointer; filter: drop-shadow(0 0 5px rgba(59,130,246,0.5))"
        onmouseenter={(e) => showTooltip(e, lbl, team1, t1Values[i], '#3b82f6')}
        onmouseleave={hideTooltip} />

      <!-- T2 bar -->
      <rect bind:this={bars[i * 2 + 1]}
        x={gx + barW + 4} y={padding.top + chartHeight} width={barW} height="0"
        fill="#ef4444" rx="2"
        role="img" aria-label="{team2} {lbl}: {t2Values[i]}"
        style="cursor:pointer; filter: drop-shadow(0 0 5px rgba(239,68,68,0.5))"
        onmouseenter={(e) => showTooltip(e, lbl, team2, t2Values[i], '#ef4444')}
        onmouseleave={hideTooltip} />

      <!-- Value labels above bars -->
      <text x={gx + barW / 2} y={getBarY(t1Values[i]) - 5} text-anchor="middle" font-size="10" fill="#60a5fa">
        {t1Values[i].toFixed(1)}
      </text>
      <text x={gx + barW + 4 + barW / 2} y={getBarY(t2Values[i]) - 5} text-anchor="middle" font-size="10" fill="#fca5a5">
        {t2Values[i].toFixed(1)}
      </text>

      <!-- X label -->
      <text x={gx + barW + 2} y={padding.top + chartHeight + 20} text-anchor="middle" font-size="11" fill="#94a3b8">
        {lbl}
      </text>
    {/each}

    <!-- Legend top-right -->
    <g transform="translate({width - padding.right - 10}, {padding.top - 20})">
      <rect x="-120" y="-8" width="14" height="14" fill="#3b82f6" rx="2" />
      <text x="-102" y="4" font-size="12" fill="#94a3b8">{team1}</text>
      <rect x="-40" y="-8" width="14" height="14" fill="#ef4444" rx="2" />
      <text x="-22" y="4" font-size="12" fill="#94a3b8">{team2}</text>
    </g>
  </svg>

  {#if tooltip.visible}
    <div class="absolute pointer-events-none z-10 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-xs shadow-xl"
      style="left: {tooltip.x}px; top: {tooltip.y}px; transform: translate(-50%, -110%)">
      <div class="text-slate-400 mb-0.5">{tooltip.label}</div>
      <div class="font-bold" style="color: {tooltip.color}">{tooltip.team}: {tooltip.value.toFixed(2)}</div>
    </div>
  {/if}
</div>
