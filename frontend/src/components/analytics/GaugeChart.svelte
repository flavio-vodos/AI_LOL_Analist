<script lang="ts">
  import { onMount } from 'svelte';
  import gsap from 'gsap';

  interface Props {
    winRate: number;
    teamColor: string;
    teamName: string;
  }

  let { winRate, teamColor, teamName }: Props = $props();

  let arcEl: SVGPathElement;
  let countEl: SVGTextElement;
  let svgEl: SVGSVGElement;

  const cx = 120, cy = 130, r = 85, sw = 12;

  function polar(cx: number, cy: number, r: number, deg: number) {
    // Start at -180deg (Left) and sweep clockwise
    const rad = ((deg - 180) * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  }

  function arc(pct: number) {
    const angle = (pct / 100) * 180;
    const start = polar(cx, cy, r, 0); // 9 o'clock
    const end = polar(cx, cy, r, angle);
    const large = angle > 180 ? 1 : 0;
    // Sweep-flag 1 for standard top-arc (clockwise from left)
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`;
  }

  const bgPath = arc(100);

  onMount(() => {
    const proxy = { pct: 0 };
    gsap.to(proxy, {
      pct: winRate,
      duration: 1.8,
      ease: 'power4.out',
      onUpdate() {
        if (arcEl) arcEl.setAttribute('d', arc(proxy.pct));
        if (countEl) countEl.textContent = Math.round(proxy.pct).toString();
      }
    });

    // Elegant Glow pulse
    gsap.to(arcEl, {
      filter: `drop-shadow(0 0 18px ${teamColor})`,
      duration: 2,
      delay: 1.8,
      ease: 'sine.inOut',
      repeat: -1,
      yoyo: true
    });
  });
</script>

<svg bind:this={svgEl} width="240" height="170" viewBox="0 0 240 170" class="w-full h-auto overflow-visible">
  <!-- Background arc -->
  <path d={bgPath} fill="none" stroke="#1e293b" stroke-width={sw + 6} stroke-linecap="round" opacity="0.4" />
  <path d={bgPath} fill="none" stroke="#2d3748" stroke-width={sw} stroke-linecap="round" />

  <!-- Animated fill arc -->
  <path bind:this={arcEl} d={arc(0)} fill="none" stroke={teamColor} stroke-width={sw} stroke-linecap="round"
    style="filter: drop-shadow(0 0 10px {teamColor})" />

  <!-- Percentage core -->
  <text x={cx} y={cy - 22} text-anchor="middle" dominant-baseline="central">
    <tspan bind:this={countEl} font-size="48" font-weight="900" fill="#f8fafc" style="filter: drop-shadow(0 0 10px rgba(0,0,0,0.5))">0</tspan>
    <tspan font-size="16" font-weight="700" fill="#64748b" dx="4" dy="-14">%</tspan>
  </text>

  <!-- Team name as a subtle label below -->
  <text x={cx} y={cy + 24} text-anchor="middle" font-size="11" font-weight="800" fill={teamColor} style="text-transform: uppercase; letter-spacing: 3px; opacity: 0.9">
    {teamName}
  </text>

  <!-- Min/Max (0/100) labels inside the base -->
  <text x={cx - r} y={cy + 15} text-anchor="middle" font-size="9" font-weight="700" fill="#4a5568">0%</text>
  <text x={cx + r} y={cy + 15} text-anchor="middle" font-size="9" font-weight="700" fill="#4a5568">100%</text>
</svg>
