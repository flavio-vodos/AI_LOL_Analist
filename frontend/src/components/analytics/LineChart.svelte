<script lang="ts">
  import { onMount } from 'svelte';
  import gsap from 'gsap';
  import type { TimelineSection } from '$lib/types/analytics';

  interface Props {
    timelineData: TimelineSection;
    team1: string;
    team2: string;
  }

  let { timelineData, team1, team2 }: Props = $props();

  let goldPath1: SVGPathElement, goldPath2: SVGPathElement;
  let csPath1: SVGPathElement, csPath2: SVGPathElement;
  let xpPath1: SVGPathElement, xpPath2: SVGPathElement;
  let draftPaths: SVGPathElement[] = [];

  let tooltip = $state<{ visible: boolean; x: number; y: number; min: number; metric: string; t1: number; t2: number; unit: string }>({
    visible: false, x: 0, y: 0, min: 0, metric: '', t1: 0, t2: 0, unit: ''
  });

  const width = 800;
  const height = 600;
  const pad = { top: 40, right: 80, bottom: 60, left: 70 };
  const chartW = width - pad.left - pad.right;
  const secH = (height - pad.top - pad.bottom) / 3;

  const allGold = $derived([...timelineData.gold_diff_t1, ...timelineData.gold_diff_t2]);
  const allCs = $derived([...timelineData.cs_diff_t1, ...timelineData.cs_diff_t2]);
  const allXp = $derived([...timelineData.xp_diff_t1, ...timelineData.xp_diff_t2]);
  const maxGold = $derived(Math.max(...allGold.map(Math.abs), 1) * 1.2);
  const maxCs = $derived(Math.max(...allCs.map(Math.abs), 1) * 1.2);
  const maxXp = $derived(Math.max(...allXp.map(Math.abs), 1) * 1.2);

  const goldY = pad.top;
  const csY = pad.top + secH;
  const xpY = pad.top + secH * 2;

  function ptX(i: number) {
    return pad.left + (i / (timelineData.minutes.length - 1)) * chartW;
  }
  function ptY(val: number, yOffset: number, maxVal: number) {
    return yOffset + secH / 2 - (val / maxVal) * (secH / 2.5);
  }
  function makePath(data: number[], yOffset: number, maxVal: number) {
    return 'M ' + data.map((v, i) => `${ptX(i)},${ptY(v, yOffset, maxVal)}`).join(' L ');
  }

  function showTip(e: MouseEvent, i: number, metric: string, t1: number, t2: number, unit: string) {
    const svg = (e.target as SVGElement).closest('svg')!.getBoundingClientRect();
    const el = e.target as SVGElement;
    const r = el.getBoundingClientRect();
    tooltip = { visible: true, x: r.left - svg.left, y: r.top - svg.top, min: timelineData.minutes[i], metric, t1, t2, unit };
  }
  function hideTip() { tooltip = { ...tooltip, visible: false }; }

  onMount(() => {
    [goldPath1, goldPath2, csPath1, csPath2, xpPath1, xpPath2].forEach((p, i) => {
      if (!p) return;
      const len = p.getTotalLength();
      gsap.fromTo(p,
        { strokeDasharray: len, strokeDashoffset: len },
        { strokeDashoffset: 0, duration: 1.5, delay: i * 0.15, ease: 'power2.out' }
      );
    });
    draftPaths.forEach((p, i) => {
      if (!p) return;
      const len = p.getTotalLength();
      gsap.fromTo(p,
        { strokeDasharray: len, strokeDashoffset: len, opacity: 0 },
        { strokeDashoffset: 0, opacity: 0.6, duration: 1.2, delay: 1.5 + i * 0.1, ease: 'power2.out' }
      );
    });
  });
</script>

<div class="relative w-full">
  <svg {width} {height} viewBox="0 0 {width} {height}" class="w-full h-auto overflow-visible">

    <!-- ── GOLD DIFF ── -->
    <text x={pad.left - 8} y={goldY + 12} text-anchor="end" font-size="12" font-weight="700" fill="#fbbf24">💰 Gold</text>
    <line x1={pad.left} y1={goldY + secH / 2} x2={pad.left + chartW} y2={goldY + secH / 2}
      stroke="#475569" stroke-width="1" stroke-dasharray="4 2" />
    <path bind:this={goldPath1} d={makePath(timelineData.gold_diff_t1, goldY, maxGold)}
      fill="none" stroke="#3b82f6" stroke-width="3" style="filter:drop-shadow(0 0 4px rgba(59,130,246,.6))" />
    <path bind:this={goldPath2} d={makePath(timelineData.gold_diff_t2, goldY, maxGold)}
      fill="none" stroke="#ef4444" stroke-width="3" style="filter:drop-shadow(0 0 4px rgba(239,68,68,.6))" />
    {#if timelineData.draft_projection_active && timelineData.draft_gold_diff_t1}
      <path bind:this={draftPaths[0]} d={makePath(timelineData.draft_gold_diff_t1, goldY, maxGold)}
        fill="none" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="6 3" opacity="0" />
    {/if}
    <!-- Gold hover dots -->
    {#each timelineData.minutes as _, i}
      <circle cx={ptX(i)} cy={ptY(timelineData.gold_diff_t1[i], goldY, maxGold)} r="6"
        fill="#3b82f6" opacity="0" style="cursor:pointer"
        role="img" aria-label="Gold Diff at {timelineData.minutes[i]}min"
        onmouseenter={(e) => showTip(e, i, 'Gold Diff', timelineData.gold_diff_t1[i], timelineData.gold_diff_t2[i], 'g')}
        onmouseleave={hideTip}
        class="hover:opacity-100 transition-opacity" />
    {/each}

    <!-- ── CS DIFF ── -->
    <text x={pad.left - 8} y={csY + 12} text-anchor="end" font-size="12" font-weight="700" fill="#10b981">🌾 CS</text>
    <line x1={pad.left} y1={csY + secH / 2} x2={pad.left + chartW} y2={csY + secH / 2}
      stroke="#475569" stroke-width="1" stroke-dasharray="4 2" />
    <path bind:this={csPath1} d={makePath(timelineData.cs_diff_t1, csY, maxCs)}
      fill="none" stroke="#3b82f6" stroke-width="3" style="filter:drop-shadow(0 0 4px rgba(59,130,246,.6))" />
    <path bind:this={csPath2} d={makePath(timelineData.cs_diff_t2, csY, maxCs)}
      fill="none" stroke="#ef4444" stroke-width="3" style="filter:drop-shadow(0 0 4px rgba(239,68,68,.6))" />
    {#if timelineData.draft_projection_active && timelineData.draft_cs_diff_t1}
      <path bind:this={draftPaths[1]} d={makePath(timelineData.draft_cs_diff_t1, csY, maxCs)}
        fill="none" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="6 3" opacity="0" />
    {/if}
    {#each timelineData.minutes as _, i}
      <circle cx={ptX(i)} cy={ptY(timelineData.cs_diff_t1[i], csY, maxCs)} r="6"
        fill="#3b82f6" opacity="0" style="cursor:pointer"
        role="img" aria-label="CS Diff at {timelineData.minutes[i]}min"
        onmouseenter={(e) => showTip(e, i, 'CS Diff', timelineData.cs_diff_t1[i], timelineData.cs_diff_t2[i], 'cs')}
        onmouseleave={hideTip}
        class="hover:opacity-100 transition-opacity" />
    {/each}

    <!-- ── XP DIFF ── -->
    <text x={pad.left - 8} y={xpY + 12} text-anchor="end" font-size="12" font-weight="700" fill="#a78bfa">⚡ XP</text>
    <line x1={pad.left} y1={xpY + secH / 2} x2={pad.left + chartW} y2={xpY + secH / 2}
      stroke="#475569" stroke-width="1" stroke-dasharray="4 2" />
    <path bind:this={xpPath1} d={makePath(timelineData.xp_diff_t1, xpY, maxXp)}
      fill="none" stroke="#3b82f6" stroke-width="3" style="filter:drop-shadow(0 0 4px rgba(59,130,246,.6))" />
    <path bind:this={xpPath2} d={makePath(timelineData.xp_diff_t2, xpY, maxXp)}
      fill="none" stroke="#ef4444" stroke-width="3" style="filter:drop-shadow(0 0 4px rgba(239,68,68,.6))" />
    {#if timelineData.draft_projection_active && timelineData.draft_xp_diff_t1}
      <path bind:this={draftPaths[2]} d={makePath(timelineData.draft_xp_diff_t1, xpY, maxXp)}
        fill="none" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="6 3" opacity="0" />
    {/if}
    {#each timelineData.minutes as _, i}
      <circle cx={ptX(i)} cy={ptY(timelineData.xp_diff_t1[i], xpY, maxXp)} r="6"
        fill="#3b82f6" opacity="0" style="cursor:pointer"
        role="img" aria-label="XP Diff at {timelineData.minutes[i]}min"
        onmouseenter={(e) => showTip(e, i, 'XP Diff', timelineData.xp_diff_t1[i], timelineData.xp_diff_t2[i], 'xp')}
        onmouseleave={hideTip}
        class="hover:opacity-100 transition-opacity" />
    {/each}

    <!-- X-axis labels -->
    {#each timelineData.minutes as min, i}
      <text x={ptX(i)} y={height - pad.bottom + 20} text-anchor="middle" font-size="12" fill="#94a3b8">
        {min}min
      </text>
    {/each}

    <!-- Legend -->
    <g transform="translate({width - pad.right + 10}, {pad.top + 10})">
      <line x1="0" y1="0" x2="20" y2="0" stroke="#3b82f6" stroke-width="3" />
      <text x="26" y="4" font-size="12" font-weight="600" fill="#60a5fa">{team1}</text>
      <line x1="0" y1="22" x2="20" y2="22" stroke="#ef4444" stroke-width="3" />
      <text x="26" y="26" font-size="12" font-weight="600" fill="#fca5a5">{team2}</text>
      {#if timelineData.draft_projection_active}
        <line x1="0" y1="44" x2="20" y2="44" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="6 3" />
        <text x="26" y="48" font-size="11" fill="#c4b5fd">✨ Draft</text>
      {/if}
    </g>
  </svg>

  {#if tooltip.visible}
    <div class="absolute pointer-events-none z-10 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-xs shadow-xl min-w-[140px]"
      style="left: {tooltip.x}px; top: {tooltip.y}px; transform: translate(-50%, -115%)">
      <div class="font-semibold text-slate-300 mb-1">{tooltip.metric} — {tooltip.min}min</div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-blue-500 inline-block"></span>
        <span class="text-slate-400">{team1}:</span>
        <span class="text-blue-400 font-bold">{tooltip.t1 > 0 ? '+' : ''}{tooltip.t1.toFixed(0)}{tooltip.unit}</span>
      </div>
      <div class="flex items-center gap-2 mt-0.5">
        <span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span>
        <span class="text-slate-400">{team2}:</span>
        <span class="text-red-400 font-bold">{tooltip.t2 > 0 ? '+' : ''}{tooltip.t2.toFixed(0)}{tooltip.unit}</span>
      </div>
    </div>
  {/if}
</div>
