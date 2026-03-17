<script lang="ts">
  import { onMount } from "svelte";
  import gsap from "gsap";

  let { match, isLive = false }: { match: any; isLive?: boolean } = $props();

  let cardElement: HTMLElement;

  onMount(() => {
    // A simple fade in and slight move up animation on mount
    gsap.from(cardElement, {
      opacity: 0,
      y: 20,
      duration: 0.5,
      ease: "power2.out",
      clearProps: "all",
    });
  });

  const league = $derived(match.league || "Unknown League");
  const matchId = $derived(match.match_id || match.game_id);
</script>

<a
  href={`/match/${matchId}`}
  bind:this={cardElement}
  class="match-card group relative flex cursor-pointer flex-col items-center rounded-xl bg-[#181A20] p-4 border transition-all duration-300 hover:bg-[#1A202C] hover:-translate-y-1 hover:shadow-lg {isLive ? 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.15)]' : 'border-slate-800'}"
>
  <!-- Live Indicator (Red Dot + Text) -->
  {#if isLive}
    <div 
      class="absolute flex items-center gap-1.5 z-20 pointer-events-none"
      style="top: 12px; left: 16px; transform: none; right: auto; bottom: auto; position: absolute;"
    >
      <div class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
      </div>
      <span class="text-[10px] font-bold text-white uppercase tracking-widest leading-none">Live</span>
    </div>
  {/if}

  <!-- League Name -->
  <div
    class="mb-4 text-[13px] font-semibold text-[#90CDF4] uppercase tracking-wide"
  >
    {league}
  </div>

  <!-- Teams and VS -->
  <div class="mb-3 flex w-full items-center justify-center gap-6">
    <!-- Blue Team Logo -->
    <div
      class="flex h-10 w-10 overflow-hidden rounded-md bg-[#1E222D] items-center justify-center shadow-inner"
    >
      {#if match.team_blue?.image}
        <img
          src={match.team_blue.image}
          alt={match.team_blue.name || match.team_blue.code}
          class="h-[34px] w-[34px] object-contain"
        />
      {:else}
        <span class="text-xs font-bold text-gray-500"
          >{match.team_blue?.code || "?"}</span
        >
      {/if}
    </div>

    <!-- VS Text -->
    <div class="text-xl font-bold text-slate-400">VS</div>

    <!-- Red Team Logo -->
    <div
      class="flex h-10 w-10 overflow-hidden rounded-md bg-[#1E222D] items-center justify-center shadow-inner"
    >
      {#if match.team_red?.image}
        <img
          src={match.team_red.image}
          alt={match.team_red.name || match.team_red.code}
          class="h-[34px] w-[34px] object-contain"
        />
      {:else}
        <span class="text-xs font-bold text-gray-500"
          >{match.team_red?.code || "?"}</span
        >
      {/if}
    </div>
  </div>

  <!-- Team Names -->
  <div class="mt-1 flex w-full justify-between gap-2 px-1">
    <div class="flex-1 truncate text-center text-xs font-medium text-[#90CDF4]">
      {match.team_blue?.name || match.team_blue?.code || "Team 1"}
    </div>
    <div class="flex-1 truncate text-center text-xs font-medium text-[#90CDF4]">
      {match.team_red?.name || match.team_red?.code || "Team 2"}
    </div>
  </div>
</a>
