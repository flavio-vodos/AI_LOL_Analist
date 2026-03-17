<script lang="ts">
  import { onMount } from 'svelte';
  import gsap from 'gsap';

  interface Props {
    rawData: number[];
    color: string;
    meanLine?: boolean;
    label: string;
  }

  let { rawData, color, meanLine = false, label }: Props = $props();

  let bars: SVGRectElement[] = [];
  let meanLineEl = $state<SVGLineElement | null>(null);
  let tooltip = $state<{ visible: boolean; x: number; y: number; freq: number; range: string }>({
    visible: false, x: 0, y: 0, freq: 0, range: ''
  });

  const width = 600;
  const height = 200;
  const padding = { top: 24, right: 20, bottom: 40, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const bins = 15;
  const minVal = $derived(Math.min(...rawData, 0));
  const maxVal = $derived(Math.max(...rawData, 1));
  const binWidth = $derived((maxVal - minVal) / bins || 1);

  const histogram = $derived.by(() => {
    const h = Array(bins).fill(0);
    rawData.forEach(val => {
      const idx = Math.min(Math.floor((val - minVal) / binWidth), bins - 1);
      h[idx]++;
    });
    return h;
  });

  const maxFreq = $derived(Math.max(...histogram, 1));
  const barWidthPx = $derived(chartWidth / bins);
  const mean = $derived(rawData.length > 0 ? rawData.reduce((a, b) => a + b, 0) / rawData.length : 0);
  const meanX = $derived(padding.left + ((mean - minVal) / (maxVal - minVal || 1)) * chartWidth);

  function showTooltip(e: MouseEvent, i: number) {
    const svg = (e.target as SVGElement).closest('svg')!.getBoundingClientRect();
    const rect = (e.target as SVGElement).getBoundingClientRect();
    tooltip = {
      visible: true,
      x: rect.left - svg.left + barWidthPx / 2,
      y: rect.top - svg.top,
      freq: histogram[i],
      range: `${(minVal + i * binWidth).toFixed(1)} – ${(minVal + (i + 1) * binWidth).toFixed(1)}`
    };
  }

  function hideTooltip() { tooltip = { ...tooltip, visible: false }; }

  $effect(() => {
    if (rawData.length === 0) return;

    // Filter out any potential nulls from the bind:this array
    const validBars = bars.filter(b => b !== null);

    gsap.fromTo(validBars,
      { attr: { height: 0, y: padding.top + chartHeight } },
      {
        attr: {
          height: (i) => (histogram[i] / maxFreq) * chartHeight,
          y: (i) => padding.top + chartHeight - (histogram[i] / maxFreq) * chartHeight
        },
        duration: 1,
        ease: 'power2.out',
        stagger: 0.03
      }
    );
    if (meanLine && meanLineEl) {
      gsap.fromTo(meanLineEl,
        { attr: { strokeDashoffset: 300 } },
        { attr: { strokeDashoffset: 0 }, duration: 1.5, delay: 0.5, ease: 'power2.out' }
      );
    }
  });
</script>

<div class="relative w-full">
  <svg {width} {height} viewBox="0 0 {width} {height}" class="w-full h-auto">
    <line x1={padding.left} y1={padding.top} x2={padding.left} y2={padding.top + chartHeight}
      stroke="#475569" stroke-width="2" />
    <line x1={padding.left} y1={padding.top + chartHeight} x2={padding.left + chartWidth} y2={padding.top + chartHeight}
      stroke="#475569" stroke-width="2" />

    {#each histogram as freq, i}
      <rect bind:this={bars[i]}
        x={padding.left + i * barWidthPx + 1}
        y={padding.top + chartHeight}
        width={barWidthPx - 2}
        height="0"
        fill={color}
        opacity="0.8"
        role="img" aria-label="Frequency for range {(minVal + i * binWidth).toFixed(1)} to {(minVal + (i + 1) * binWidth).toFixed(1)}: {freq} games"
        style="cursor: pointer; filter: drop-shadow(0 0 3px {color})"
        onmouseenter={(e) => showTooltip(e, i)}
        onmouseleave={hideTooltip}
      />
    {/each}

    {#if meanLine}
      <line bind:this={meanLineEl}
        x1={meanX} y1={padding.top} x2={meanX} y2={padding.top + chartHeight}
        stroke="#fbbf24" stroke-width="2" stroke-dasharray="6 4" stroke-dashoffset="300"
        style="filter: drop-shadow(0 0 4px rgba(251,191,36,0.6))" />
      <text x={meanX} y={padding.top - 5} text-anchor="middle" font-size="11" font-weight="600" fill="#fbbf24">
        μ = {mean.toFixed(1)}
      </text>
    {/if}

    <text x={padding.left} y={padding.top + chartHeight + 25} font-size="10" fill="#94a3b8" 
      transform="rotate(45, {padding.left}, {padding.top + chartHeight + 25})">{minVal.toFixed(0)}</text>
    <text x={padding.left + chartWidth} y={padding.top + chartHeight + 25} text-anchor="start" font-size="10" fill="#94a3b8"
      transform="rotate(45, {padding.left + chartWidth}, {padding.top + chartHeight + 25})">{maxVal.toFixed(0)}</text>
    
    <text x={padding.left + chartWidth / 2} y={padding.top + chartHeight + 35} text-anchor="middle" font-size="11" font-weight="600" fill="#94a3b8">{label}</text>
    
    <text x={padding.left - 40} y={padding.top + chartHeight / 2} text-anchor="middle" font-size="10" fill="#94a3b8"
      transform="rotate(-90, {padding.left - 40}, {padding.top + chartHeight / 2})">Frequência</text>
  </svg>

  {#if tooltip.visible}
    <div class="absolute pointer-events-none z-10 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-xs shadow-xl"
      style="left: {tooltip.x}px; top: {tooltip.y}px; transform: translate(-50%, -110%)">
      <div class="text-slate-400 mb-0.5">{tooltip.range}</div>
      <div class="font-bold" style="color: {color}">{tooltip.freq} jogos</div>
    </div>
  {/if}
</div>
