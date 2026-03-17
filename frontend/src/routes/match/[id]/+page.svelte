<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import gsap from 'gsap';

  let matchId = $page.params.id;
  let matchData: any = $state(null);
  let loading = $state(true);

  const CHAMPIONS_URL = "https://ddragon.leagueoflegends.com/cdn/16.5.1/img/champion/";
  const ITEMS_URL     = "https://ddragon.leagueoflegends.com/cdn/16.5.1/img/item/";

  async function fetchDetails() {
    try {
      const res = await fetch(`http://localhost:8000/api/live/match/${matchId}`);
      if (res.ok) {
        matchData = await res.json();
      } else {
        const gamesRes = await fetch(`http://localhost:8000/api/live/games`);
        const games = await gamesRes.json();
        matchData = games.find((g: any) => g.game_id === matchId || g.match_id === matchId) ?? null;
      }
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchDetails();
    gsap.from('.fade-in', { opacity: 0, y: 15, duration: 0.6, stagger: 0.1 });
    
    const interval = setInterval(() => {
      if (matchData?.state === 'completed') return;
      fetchDetails();
    }, 500);
    return () => clearInterval(interval);
  });

  function fmtGold(val: number) {
    if (!val) return "0";
    return val.toLocaleString('pt-BR');
  }

  function getGoldPct(blue: number, red: number) {
    const total = (blue || 0) + (red || 0);
    if (total === 0) return { blue: 50, red: 50 };
    return {
      blue: (blue / total) * 100,
      red: (red / total) * 100
    };
  }

  const DRAGON_ICONS: Record<string, string> = {
    ocean: "/images/dragon-ocean.svg", 
    infernal: "/images/dragon-infernal.svg", 
    mountain: "/images/dragon-mountain.svg",
    cloud: "/images/dragon-cloud.svg", 
    elder: "/images/dragon-elder.svg", 
    chemtech: "/images/dragon-chemtech.svg", 
    hextech: "/images/dragon-hextech.svg"
  };

  const DRAGON_NAMES: Record<string, string> = {
    ocean: "Oceano", infernal: "Infernal", mountain: "Montanha",
    cloud: "Nuvens", elder: "Ancião", chemtech: "Quimtec", hextech: "Hextec"
  };

  const CHAMP_MAPPING: Record<string, string> = {
    "Dr. Mundo": "DrMundo",
    "Kha'Zix": "Khazix",
    "Lee Sin": "LeeSin",
    "Wukong": "MonkeyKing",
    "LeBlanc": "Leblanc",
    "Nunu & Willump": "Nunu",
    "Renata Glasc": "Renata",
    "Bel'Veth": "Belveth",
    "Vel'Koz": "Velkoz",
    "Cho'Gath": "Chogath",
    "Kai'Sa": "Kaisa",
    "Le Sin": "LeeSin"
  };

  function getChampImg(id: string) {
    if (!id) return "https://ddragon.leagueoflegends.com/cdn/16.5.1/img/profileicon/29.png";
    const mapped = CHAMP_MAPPING[id] || id;
    const sanitized = mapped.replace(/'| |\.|\&/g, '');
    return `${CHAMPIONS_URL}${sanitized}.png`;
  }

  function handleImageError(e: Event) {
    const target = e.currentTarget as HTMLImageElement;
    if (!target) return;
    if (target.src.includes('/champion/')) {
      target.onerror = null;
      target.src = "https://ddragon.leagueoflegends.com/cdn/16.5.1/img/profileicon/29.png";
    } else {
      target.style.display = 'none';
    }
  }

  import { tweened } from 'svelte/motion';
  import { sineOut } from 'svelte/easing';

  const bGold = tweened(0, { duration: 500, easing: sineOut });
  const rGold = tweened(0, { duration: 500, easing: sineOut });
  const bKills = tweened(0, { duration: 300, easing: sineOut });
  const rKills = tweened(0, { duration: 300, easing: sineOut });

  $effect(() => {
    if (matchData) {
      bGold.set(matchData.blue_gold || 0);
      rGold.set(matchData.red_gold || 0);
      bKills.set(matchData.blue_kills || 0);
      rKills.set(matchData.red_kills || 0);
    }
  });

  let pcts = $derived(matchData ? getGoldPct(matchData.blue_gold ?? 0, matchData.red_gold ?? 0) : { blue: 50, red: 50 });
</script>

<div class="p-4 md:p-8 font-sans bg-[#0f172a] min-h-screen text-slate-200 fade-in">
  <!-- Top Nav -->
  <div class="max-w-7xl mx-auto mb-6 flex justify-between items-center">
    <a href="/" class="text-blue-400 hover:text-blue-300 inline-flex items-center gap-2 border border-blue-900/50 px-4 py-2 rounded-xl transition-all bg-[#1e293b] hover:bg-[#2d3748] shadow-lg">
      <span class="text-lg">←</span> Voltar ao Dashboard
    </a>
    
    {#if matchData}
    <div class="flex gap-2">
       <div class="px-4 py-2 rounded-xl bg-[#1e293b] border border-slate-700 text-xs font-bold text-slate-400 uppercase tracking-widest">
         API: <span class="text-green-400">ONLINE</span>
       </div>
    </div>
    {/if}
  </div>

  {#if loading}
    <div class="h-96 flex flex-col items-center justify-center gap-4">
      <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <div class="animate-pulse text-slate-500 font-medium uppercase tracking-widest text-sm">Sincronizando Telemetria...</div>
    </div>
  {:else if !matchData}
    <div class="max-w-2xl mx-auto bg-[#1e293b] p-12 rounded-2xl border border-red-900/30 text-center shadow-2xl fade-in">
      <div class="text-6xl mb-6">⚠️</div>
      <h2 class="text-2xl font-bold text-red-200 mb-2">Partida Não Encontrada</h2>
      <p class="text-slate-400">Os dados da Riot API ainda não estão disponíveis para este ID ou a partida expirou.</p>
      <button onclick={fetchDetails} class="mt-8 px-6 py-2 bg-red-900/20 hover:bg-red-900/40 border border-red-900/50 rounded-lg text-red-400 transition-colors">Tentar Novamente</button>
    </div>
  {:else}
    <div class="max-w-7xl mx-auto space-y-6">
      
      <!-- HEADER AUREOM STYLE -->
      <div class="bg-[#111827] rounded-2xl border border-[#1f2937] overflow-hidden shadow-2xl">
        <!-- League & Match State -->
        <div class="text-center py-4 bg-[#0a0f1a] border-b border-[#1f2937]">
            <span class="text-xs font-black text-slate-500 uppercase tracking-[0.2em]">{matchData.league}</span>
        </div>

        <div class="p-6 md:p-8">
            <!-- VS Section -->
            <div class="flex flex-col md:flex-row items-center justify-between gap-8 mb-8">
                <!-- Blue Team -->
                <div class="flex flex-1 items-center justify-end gap-6 w-full md:w-auto">
                    <div class="text-right">
                        <h2 class="text-2xl md:text-3xl font-black text-blue-400 tracking-tight leading-none">
                            {matchData.team_blue?.code || 'BLUE'}
                        </h2>
                        <span class="text-xs text-slate-500 font-bold uppercase hidden md:block">{matchData.team_blue?.name || ''}</span>
                    </div>
                    <div class="w-16 h-16 md:w-20 md:h-20 bg-[#1e293b] rounded-2xl p-2 border border-blue-900/30 shadow-inner flex items-center justify-center">
                        <img src={matchData.team_blue?.image || ''} class="max-w-full max-h-full object-contain" alt="Logo Blue" onerror={handleImageError}>
                    </div>
                </div>

                <!-- Center VS -->
                <div class="flex flex-col items-center min-w-[140px]">
                    <div class="text-5xl font-black text-slate-700 italic">VS</div>
                    <div class="mt-2 px-6 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg flex items-center
                        {matchData.state === 'inProgress' ? 'bg-red-500/10 border border-red-500/50 text-red-500' : 'bg-slate-700 text-slate-300'}">
                        {#if matchData.state === 'inProgress'}
                            <span class="w-2 h-2 bg-red-500 rounded-full mr-2 shadow-[0_0_10px_rgba(239,68,68,0.6)] animate-pulse"></span>
                        {/if}
                        {matchData.state === 'inProgress' ? 'AO VIVO' : matchData.state}
                    </div>
                </div>

                <!-- Red Team -->
                <div class="flex flex-1 items-center justify-start gap-6 w-full md:w-auto">
                    <div class="w-16 h-16 md:w-20 md:h-20 bg-[#1e293b] rounded-2xl p-2 border border-red-900/30 shadow-inner flex items-center justify-center">
                        <img src={matchData.team_red?.image || ''} class="max-w-full max-h-full object-contain" alt="Logo Red" onerror={handleImageError}>
                    </div>
                    <div class="text-left">
                        <h2 class="text-2xl md:text-3xl font-black text-red-400 tracking-tight leading-none">
                            {matchData.team_red?.code || 'RED'}
                        </h2>
                        <span class="text-xs text-slate-500 font-bold uppercase hidden md:block">{matchData.team_red?.name || ''}</span>
                    </div>
                </div>
            </div>

            <!-- Team Stats Icons -->
            <div class="grid grid-cols-2 gap-4 mb-6">
                <!-- Blue Stats -->
                <div class="flex flex-wrap items-center justify-end gap-4 md:gap-7 pr-2 md:pr-4 border-r border-slate-800">
                    <div class="flex flex-col items-center group cursor-help" title="Dragões">
                        <img src="/images/dragon-infernal.svg" alt="Dragão" class="w-6 h-6 md:w-7 md:h-7 opacity-80 group-hover:opacity-100 transition-opacity" />
                        <span class="text-sm font-black text-blue-100">{matchData.blue_dragons?.length || 0}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Barões">
                        <img src="/images/baron.svg" alt="Barão" class="w-6 h-6 md:w-7 md:h-7 opacity-80 group-hover:opacity-100 transition-opacity" />
                        <span class="text-sm font-black text-blue-100">{matchData.blue_barons || 0}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Arautos">
                        <img src="/images/herald.png" alt="Arauto" class="w-6 h-6 md:w-7 md:h-7 opacity-80 group-hover:opacity-100 transition-opacity" />
                        <span class="text-sm font-black text-blue-100">{matchData.blue_heralds || 0}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Torres">
                        <img src="/images/tower.svg" alt="Torre" class="w-6 h-6 md:w-7 md:h-7 opacity-80 group-hover:opacity-100 transition-opacity" />
                        <span class="text-sm font-black text-blue-100">{matchData.blue_towers || 0}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Ouro Total">
                        <img src="/images/gold.svg" alt="Ouro" class="w-6 h-6 md:w-7 md:h-7" />
                        <span class="text-xs md:text-sm font-black text-blue-100">{fmtGold(Math.round($bGold))}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Abates">
                        <img src="/images/kill.svg" alt="Abates" class="w-6 h-6 md:w-7 md:h-7" />
                        <span class="text-sm md:text-xl font-black text-blue-400">{Math.round($bKills)}</span>
                    </div>
                </div>

                <!-- Red Stats -->
                <div class="flex flex-wrap items-center justify-start gap-4 md:gap-7 pl-2 md:pl-4">
                    <div class="flex flex-col items-center group cursor-help" title="Abates">
                        <img src="/images/kill.svg" alt="Abates" class="w-6 h-6 md:w-7 md:h-7" />
                        <span class="text-sm md:text-xl font-black text-red-400">{Math.round($rKills)}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Ouro Total">
                        <img src="/images/gold.svg" alt="Ouro" class="w-6 h-6 md:w-7 md:h-7" />
                        <span class="text-xs md:text-sm font-black text-red-100">{fmtGold(Math.round($rGold))}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Torres">
                        <img src="/images/tower.svg" alt="Torre" class="w-6 h-6 md:w-7 md:h-7 opacity-80 group-hover:opacity-100 transition-opacity" />
                        <span class="text-sm font-black text-red-100">{matchData.red_towers || 0}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Arautos">
                        <img src="/images/herald.png" alt="Arauto" class="w-6 h-6 md:w-7 md:h-7 opacity-80 group-hover:opacity-100 transition-opacity" />
                        <span class="text-sm font-black text-red-100">{matchData.red_heralds || 0}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Barões">
                        <img src="/images/baron.svg" alt="Barão" class="w-6 h-6 md:w-7 md:h-7 opacity-80 group-hover:opacity-100 transition-opacity" />
                        <span class="text-sm font-black text-red-100">{matchData.red_barons || 0}</span>
                    </div>
                    <div class="flex flex-col items-center group cursor-help" title="Dragões">
                        <img src="/images/dragon-infernal.svg" alt="Dragão" class="w-6 h-6 md:w-7 md:h-7 opacity-80 group-hover:opacity-100 transition-opacity" />
                        <span class="text-sm font-black text-red-100">{matchData.red_dragons?.length || 0}</span>
                    </div>
                </div>
            </div>

            <!-- Gold Percentage Bar -->
            <div class="w-full h-3 bg-slate-800 rounded-full overflow-hidden flex shadow-inner mb-2">
                <div class="h-full bg-gradient-to-r from-blue-700 to-blue-400 transition-all duration-500" style="width: {pcts.blue}%"></div>
                <div class="h-full bg-gradient-to-l from-red-700 to-red-400 transition-all duration-500" style="width: {pcts.red}%"></div>
            </div>
            <div class="flex justify-between text-[10px] font-black text-slate-500 uppercase tracking-tighter px-1">
                <span>{pcts.blue.toFixed(1)}%</span>
                <span>Distribuição de Ouro</span>
                <span>{pcts.red.toFixed(1)}%</span>
            </div>

            <!-- Individual Dragons -->
            <div class="flex justify-between items-center mt-6 px-2">
                <div class="flex gap-1.5 h-8 items-center">
                    {#each (matchData.blue_dragons || []) as drag}
                        <img src={DRAGON_ICONS[drag.toLowerCase()] || "/images/dragon-infernal.svg"} 
                             class="w-8 h-8 filter drop-shadow-md hover:scale-125 transition-transform cursor-help" 
                             alt={drag}
                             title={DRAGON_NAMES[drag.toLowerCase()] || drag} />
                    {/each}
                </div>
                <div class="flex gap-1.5 h-8 flex-row-reverse items-center">
                    {#each (matchData.red_dragons || []) as drag}
                        <img src={DRAGON_ICONS[drag.toLowerCase()] || "/images/dragon-infernal.svg"} 
                             class="w-8 h-8 filter drop-shadow-md hover:scale-125 transition-transform cursor-help" 
                             alt={drag}
                             title={DRAGON_NAMES[drag.toLowerCase()] || drag} />
                    {/each}
                </div>
            </div>
        </div>
      </div>

      <!-- PLAYER TABLES (AUREOM STYLE) -->
      <div class="grid grid-cols-1 gap-6">
        
        <!-- BLUE TEAM TABLE -->
        <div class="bg-[#111827] rounded-2xl border border-[#1f2937] overflow-hidden shadow-xl">
            <div class="bg-blue-900/20 px-6 py-3 border-b border-[#1f2937] flex justify-between items-center">
                <h3 class="text-sm font-black text-blue-400 uppercase tracking-widest">{matchData.team_blue?.name || 'Equipe Azul'}</h3>
                <span class="text-[10px] text-slate-500 font-bold uppercase">Telemetria em Tempo Real</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-[#1f2937] bg-[#0d121d]">
                            <th class="px-6 py-4">Campeão / Time</th>
                            <th class="px-4 py-4 min-w-[140px]">Vida</th>
                            <th class="px-4 py-4 min-w-[200px]">Itens</th>
                            <th class="px-3 py-4 text-center">CS</th>
                            <th class="px-2 py-4 text-center">K</th>
                            <th class="px-2 py-4 text-center">D</th>
                            <th class="px-2 py-4 text-center">A</th>
                            <th class="px-4 py-4 text-center">Ouro</th>
                            <th class="px-6 py-4 text-center">+/-</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-[#1f2937]">
                        {#each (matchData.blue_champs || []) as p}
                        {@const hpPct = (p.currentHealth / p.maxHealth) * 100}
                        <tr class="hover:bg-white/[0.02] transition-colors">
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-4">
                                    <div class="relative flex-shrink-0">
                                        <img src="{getChampImg(p.champion)}" onerror={handleImageError} class="w-12 h-12 rounded-xl border border-slate-700 shadow-lg" alt={p.champion}>
                                        <span class="absolute -bottom-1 -right-1 bg-slate-900 text-[10px] font-black w-5 h-5 flex items-center justify-center rounded-lg border border-slate-700 text-slate-400">
                                            {p.level}
                                        </span>
                                    </div>
                                    <div class="min-w-0">
                                        <div class="font-black text-sm text-slate-100 truncate">{p.champion}</div>
                                        <div class="text-[10px] font-bold text-slate-500 uppercase tracking-tighter truncate">{p.summonerName}</div>
                                    </div>
                                </div>
                            </td>
                            <td class="px-4 py-4">
                                <div class="w-full h-4 bg-slate-800 rounded-md overflow-hidden relative border border-slate-700/50">
                                    <div class="h-full transition-all duration-300 rounded-r-sm" 
                                         style="width: {hpPct}%; background: {hpPct > 60 ? '#10b981' : (hpPct > 30 ? '#f59e0b' : '#ef4444')}"></div>
                                    <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black text-white drop-shadow-md">
                                        {p.currentHealth} / {p.maxHealth}
                                    </span>
                                </div>
                            </td>
                            <td class="px-4 py-4">
                                <div class="flex flex-wrap gap-1">
                                    {#each (p.items || []) as item}
                                        <div class="w-7 h-7 bg-slate-800 rounded-md border border-slate-700 flex-shrink-0">
                                            {#if item && item !== 0}
                                                <img src="{ITEMS_URL}{item}.png" class="w-full h-full rounded-md" alt="item" onerror={handleImageError}>
                                            {/if}
                                        </div>
                                    {/each}
                                </div>
                            </td>
                            <td class="px-3 py-4 text-center text-sm font-bold text-slate-300">{p.cs}</td>
                            <td class="px-2 py-4 text-center text-sm font-black text-green-400">{p.kills}</td>
                            <td class="px-2 py-4 text-center text-sm font-black text-red-400">{p.deaths}</td>
                            <td class="px-2 py-4 text-center text-sm font-black text-blue-400">{p.assists}</td>
                            <td class="px-4 py-4 text-center text-sm font-bold text-slate-300">{fmtGold(p.gold)}</td>
                            <td class="px-6 py-4 text-center">
                                <div class="inline-block px-2 py-1 rounded text-[10px] font-black {p.goldDiff >= 0 ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}">
                                    {p.goldDiff >= 0 ? '+' : ''}{fmtGold(p.goldDiff)}
                                </div>
                            </td>
                        </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
            {#if !(matchData.blue_champs?.length)}
                <div class="py-20 text-center text-slate-600 font-black uppercase tracking-widest text-sm">Escalação ainda não detectada</div>
            {/if}
        </div>

        <!-- RED TEAM TABLE -->
        <div class="bg-[#111827] rounded-2xl border border-[#1f2937] overflow-hidden shadow-xl">
            <div class="bg-red-900/20 px-6 py-3 border-b border-[#1f2937] flex justify-between items-center">
                <h3 class="text-sm font-black text-red-400 uppercase tracking-widest">{matchData.team_red?.name || 'Equipe Vermelha'}</h3>
                <span class="text-[10px] text-slate-500 font-bold uppercase">Telemetria em Tempo Real</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-[#1f2937] bg-[#0d121d]">
                            <th class="px-6 py-4">Campeão / Time</th>
                            <th class="px-4 py-4 min-w-[140px]">Vida</th>
                            <th class="px-4 py-4 min-w-[200px]">Itens</th>
                            <th class="px-3 py-4 text-center">CS</th>
                            <th class="px-2 py-4 text-center">K</th>
                            <th class="px-2 py-4 text-center">D</th>
                            <th class="px-2 py-4 text-center">A</th>
                            <th class="px-4 py-4 text-center">Ouro</th>
                            <th class="px-6 py-4 text-center">+/-</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-[#1f2937]">
                        {#each (matchData.red_champs || []) as p}
                        {@const hpPct = (p.currentHealth / p.maxHealth) * 100}
                        <tr class="hover:bg-white/[0.02] transition-colors">
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-4">
                                    <div class="relative flex-shrink-0">
                                        <img src="{getChampImg(p.champion)}" onerror={handleImageError} class="w-12 h-12 rounded-xl border border-slate-700 shadow-lg" alt={p.champion}>
                                        <span class="absolute -bottom-1 -right-1 bg-slate-900 text-[10px] font-black w-5 h-5 flex items-center justify-center rounded-lg border border-slate-700 text-slate-400">
                                            {p.level}
                                        </span>
                                    </div>
                                    <div class="min-w-0">
                                        <div class="font-black text-sm text-slate-100 truncate">{p.champion}</div>
                                        <div class="text-[10px] font-bold text-slate-500 uppercase tracking-tighter truncate">{p.summonerName}</div>
                                    </div>
                                </div>
                            </td>
                            <td class="px-4 py-4">
                                <div class="w-full h-4 bg-slate-800 rounded-md overflow-hidden relative border border-slate-700/50">
                                    <div class="h-full transition-all duration-300 rounded-r-sm" 
                                         style="width: {hpPct}%; background: {hpPct > 60 ? '#10b981' : (hpPct > 30 ? '#f59e0b' : '#ef4444')}"></div>
                                    <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black text-white drop-shadow-md">
                                        {p.currentHealth} / {p.maxHealth}
                                    </span>
                                </div>
                            </td>
                            <td class="px-4 py-4">
                                <div class="flex flex-wrap gap-1">
                                    {#each (p.items || []) as item}
                                        <div class="w-7 h-7 bg-slate-800 rounded-md border border-slate-700 flex-shrink-0">
                                            {#if item && item !== 0}
                                                <img src="{ITEMS_URL}{item}.png" class="w-full h-full rounded-md" alt="item" onerror={handleImageError}>
                                            {/if}
                                        </div>
                                    {/each}
                                </div>
                            </td>
                            <td class="px-3 py-4 text-center text-sm font-bold text-slate-300">{p.cs}</td>
                            <td class="px-2 py-4 text-center text-sm font-black text-green-400">{p.kills}</td>
                            <td class="px-2 py-4 text-center text-sm font-black text-red-400">{p.deaths}</td>
                            <td class="px-2 py-4 text-center text-sm font-black text-blue-400">{p.assists}</td>
                            <td class="px-4 py-4 text-center text-sm font-bold text-slate-300">{fmtGold(p.gold)}</td>
                            <td class="px-6 py-4 text-center">
                                <div class="inline-block px-2 py-1 rounded text-[10px] font-black {p.goldDiff >= 0 ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}">
                                    {p.goldDiff >= 0 ? '+' : ''}{fmtGold(p.goldDiff)}
                                </div>
                            </td>
                        </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
            {#if !(matchData.red_champs?.length)}
                <div class="py-20 text-center text-slate-600 font-black uppercase tracking-widest text-sm">Escalação ainda não detectada</div>
            {/if}
        </div>

      </div>

      <footer class="pt-12 pb-20 text-center space-y-2">
        <div class="text-[10px] font-black text-slate-600 uppercase tracking-[0.4em]">Aureom Predictor Pro</div>
        <div class="text-[9px] text-slate-700 font-medium">Sincronizado com Riot Games Live Telemetry Engine</div>
      </footer>

    </div>
  {/if}
</div>

<style>
  :global(body) {
    background-color: #0d121d !important;
  }
  
  /* Custom Scrollbar for better internal table sizing */
  .overflow-x-auto::-webkit-scrollbar {
    height: 6px;
  }
  .overflow-x-auto::-webkit-scrollbar-track {
    background: #111827;
  }
  .overflow-x-auto::-webkit-scrollbar-thumb {
    background: #1f2937;
    border-radius: 3px;
  }
</style>
