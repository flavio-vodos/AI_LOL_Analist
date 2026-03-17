<script lang="ts">
  import { onMount, tick } from 'svelte';
  import gsap from 'gsap';
  import type { AnalyticsResponse } from '$lib/types/analytics';
  import ResultsHeader from '../../components/analytics/ResultsHeader.svelte';
  import EducationalSection from '../../components/analytics/EducationalSection.svelte';
  import EGRSection from '../../components/analytics/EGRSection.svelte';
  import MLRSection from '../../components/analytics/MLRSection.svelte';
  import RadarSection from '../../components/analytics/RadarSection.svelte';
  import TimelineSection from '../../components/analytics/TimelineSection.svelte';
  import EconomySection from '../../components/analytics/EconomySection.svelte';
  import PaceSection from '../../components/analytics/PaceSection.svelte';
  import WinRateSection from '../../components/analytics/WinRateSection.svelte';
  import RecentFormSection from '../../components/analytics/RecentFormSection.svelte';
  import KillsSection from '../../components/analytics/KillsSection.svelte';
  import ObjectivesSection from '../../components/analytics/ObjectivesSection.svelte';
  import DurationSection from '../../components/analytics/DurationSection.svelte';
  import SeriesSection from '../../components/analytics/SeriesSection.svelte';
  import SidePerformanceSection from '../../components/analytics/SidePerformanceSection.svelte';
  import LeagueContextSection from '../../components/analytics/LeagueContextSection.svelte';
  import WinConditionsSection from '../../components/analytics/WinConditionsSection.svelte';
  import EVFinderSection from '../../components/analytics/EVFinderSection.svelte';

  let teams: string[] = $state([]);
  let patches: string[] = $state([]);
  let champions: string[] = $state([]);

  let time1 = $state('');
  let time2 = $state('');
  let selectedPatches: string[] = $state([]);

  type Role = 'top' | 'jg' | 'mid' | 'adc' | 'sup';
  const roles: Role[] = ['top', 'jg', 'mid', 'adc', 'sup'];

  let t1_champs = $state<Record<Role, string>>({ top: '', jg: '', mid: '', adc: '', sup: '' });
  let t2_champs = $state<Record<Role, string>>({ top: '', jg: '', mid: '', adc: '', sup: '' });

  let t1_logo = $state("");
  let t2_logo = $state("");

  let analyticsData: AnalyticsResponse | null = $state(null);
  let loading = $state(false);
  let errorMsg = $state('');

  // Search/Dropdown state
  let q1 = $state('');
  let q2 = $state('');
  let showList1 = $state(false);
  let showList2 = $state(false);

  let filtered1 = $derived(teams.filter(t => t.toLowerCase().includes(q1.toLowerCase())));
  let filtered2 = $derived(teams.filter(t => t.toLowerCase().includes(q2.toLowerCase())));

  function selectTeam1(t: string) {
    time1 = t;
    q1 = t;
    showList1 = false;
  }

  function selectTeam2(t: string) {
    time2 = t;
    q2 = t;
    showList2 = false;
  }

  onMount(async () => {
    gsap.from('.stagger-fade', { opacity: 0, y: 15, duration: 0.5, stagger: 0.1 });
    
    try {
        const [tRes, pRes, cRes] = await Promise.all([
        fetch('http://localhost:8000/api/analytics/teams').then(r => r.json()),
        fetch('http://localhost:8000/api/analytics/patches').then(r => r.json()),
        fetch('http://localhost:8000/api/analytics/champions').then(r => r.json())
        ]);

        teams = tRes.teams || [];
        patches = pRes.patches || [];
        champions = cRes.champions || [];

        if (patches.length > 0) {
          // Filtrar "Todos" da seleção padrão (Last 4 patches reais)
          selectedPatches = patches.filter(p => p !== "Todos").slice(0, 4);
        }
    } catch (e) {
        console.error("Erro ao carregar options:", e);
    }
  });

  function togglePatch(p: string) {
    if (selectedPatches.includes(p)) {
      selectedPatches = selectedPatches.filter(patch => patch !== p);
    } else {
      selectedPatches = [...selectedPatches, p];
    }
  }

  // Fetch logos when teams change
  $effect(() => {
    if (time1 && time1 !== "Rode o Pipeline Primeiro" && time1 !== "Erro ao carregar times") {
      fetch(`http://localhost:8000/api/analytics/team_logo/${encodeURIComponent(time1)}`)
        .then(r => r.json())
        .then(data => t1_logo = data.url ? `http://localhost:8000${data.url}` : "");
    } else {
      t1_logo = "";
    }
  });

  $effect(() => {
    if (time2 && time2 !== "Rode o Pipeline Primeiro" && time2 !== "Erro ao carregar times") {
      fetch(`http://localhost:8000/api/analytics/team_logo/${encodeURIComponent(time2)}`)
        .then(r => r.json())
        .then(data => t2_logo = data.url ? `http://localhost:8000${data.url}` : "");
    } else {
      t2_logo = "";
    }
  });

  async function generateInsights() {
    errorMsg = '';
    analyticsData = null;
    
    // Auto-resolve typed teams if not explicitly selected
    if (!time1 && q1 && teams.includes(q1)) time1 = q1;
    if (!time2 && q2 && teams.includes(q2)) time2 = q2;

    if (!time1 || !time2) {
      errorMsg = 'Selecione dois times válidos na lista de busca.';
      return;
    }
    if (time1 === time2) {
      errorMsg = 'Selecione times diferentes.';
      return;
    }

    loading = true;
    try {
      const payload = {
        time1: time1,
        time2: time2,
        patches: selectedPatches.length > 0 ? selectedPatches : ["Todos"],
        t1_top: t1_champs.top,
        t1_jg: t1_champs.jg,
        t1_mid: t1_champs.mid,
        t1_adc: t1_champs.adc,
        t1_sup: t1_champs.sup,
        t2_top: t2_champs.top,
        t2_jg: t2_champs.jg,
        t2_mid: t2_champs.mid,
        t2_adc: t2_champs.adc,
        t2_sup: t2_champs.sup
      };

      const res = await fetch('http://localhost:8000/api/analytics/insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Erro ao gerar insights HTTP Error');
      }

      analyticsData = await res.json() as AnalyticsResponse;

      // Animate result sections after data loads
      await tick();
      gsap.from('.analytics-section', { opacity: 0, y: 20, duration: 0.6, stagger: 0.08, ease: 'power2.out' });
      
    } catch (e: any) {
      errorMsg = e.message;
    } finally {
      loading = false;
    }
  }
</script>

<div class="p-8 pb-32 max-w-7xl mx-auto">
  <div class="mb-10 text-center stagger-fade">
    <h1 class="text-3xl font-extrabold text-[#90CDF4] tracking-tight">📊 Advanced Analytics</h1>
    <p class="text-slate-400 mt-2">Cruzamento nativo The Oracle's Elixir x Riot Games</p>
  </div>

  <div class="bg-[#1e293b] p-6 rounded-2xl border border-[#334155] mb-8 stagger-fade shadow-xl">
    
    <!-- Teams Selection -->
      <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
        <!-- Time 1 Selection -->
        <div class="flex flex-col gap-2 relative">
          <label for="team1-input" class="flex items-center gap-2 text-sm font-semibold text-[#90CDF4]">
            <span class="h-3 w-3 rounded-sm bg-blue-500"></span>
            Time 1 (Blue Side)
          </label>
          <div class="flex items-center gap-3">
             <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-slate-700 bg-[#1E293B] p-1 shadow-inner">
              {#if t1_logo}
                <img src={t1_logo} alt="Logo T1" class="h-10 w-10 object-contain" />
              {:else}
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Blue</span>
              {/if}
            </div>
            <div class="relative w-full">
              <input 
                id="team1-input"
                type="text"
                placeholder="Busque o time (ex: love)..."
                bind:value={q1}
                onfocus={() => showList1 = true}
                onblur={() => setTimeout(() => showList1 = false, 200)}
                class="h-12 w-full rounded-lg border border-slate-700 bg-[#0f172a] px-4 text-white focus:border-blue-500 focus:outline-none transition-colors"
              />
              {#if showList1 && filtered1.length > 0}
                <div class="absolute z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-lg border border-slate-700 bg-[#1e293b] shadow-2xl scrollbar-thin scrollbar-thumb-slate-600">
                  {#each filtered1 as t}
                    <button 
                      type="button"
                      class="w-full px-4 py-2.5 text-left text-sm text-slate-200 hover:bg-blue-600 hover:text-white transition-colors border-b border-slate-800 last:border-0"
                      onclick={() => selectTeam1(t)}
                    >
                      {t}
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        </div>

        <!-- Time 2 Selection -->
        <div class="flex flex-col gap-2 relative">
          <label for="team2-input" class="flex items-center gap-2 text-sm font-semibold text-[#F56565]">
            <span class="h-3 w-3 rounded-sm bg-red-500"></span>
            Time 2 (Red Side)
          </label>
          <div class="flex items-center gap-3">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-slate-700 bg-[#1E293B] p-1 shadow-inner">
              {#if t2_logo}
                <img src={t2_logo} alt="Logo T2" class="h-10 w-10 object-contain" />
              {:else}
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Red</span>
              {/if}
            </div>
            <div class="relative w-full">
              <input 
                id="team2-input"
                type="text"
                placeholder="Busque o time (ex: T1)..."
                bind:value={q2}
                onfocus={() => showList2 = true}
                onblur={() => setTimeout(() => showList2 = false, 200)}
                class="h-12 w-full rounded-lg border border-slate-700 bg-[#0f172a] px-4 text-white focus:border-red-500 focus:outline-none transition-colors"
              />
              {#if showList2 && filtered2.length > 0}
                <div class="absolute z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-lg border border-slate-700 bg-[#1e293b] shadow-2xl scrollbar-thin scrollbar-thumb-slate-600">
                  {#each filtered2 as t}
                    <button 
                      type="button"
                      class="w-full px-4 py-2.5 text-left text-sm text-slate-200 hover:bg-red-600 hover:text-white transition-colors border-b border-slate-800 last:border-0"
                      onclick={() => selectTeam2(t)}
                    >
                      {t}
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        </div>
      </div>

    <div class="mb-6">
      <span class="block text-sm font-semibold text-slate-300 mb-2">📅 Versões Filtradas (Por Padrão: Últimos 4)</span>
      <div class="flex flex-wrap gap-2">
        {#each patches as p}
          <button 
            class="px-3 py-1.5 rounded-full text-sm font-medium border transition-colors {selectedPatches.includes(p) ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_10px_rgba(59,130,246,0.5)]' : 'bg-[#0f172a] border-[#334155] text-slate-400 hover:text-slate-200 hover:border-slate-500'}"
            onclick={() => togglePatch(p)}
          >
            {p}
          </button>
        {/each}
      </div>
    </div>

    <!-- Advanced Champions -->
    <details class="mb-8 border border-[#334155] rounded-lg overflow-hidden group">
      <summary class="bg-[#0f172a] p-4 font-semibold text-slate-300 cursor-pointer hover:bg-[#152033] transition-colors select-none">
        ⚔️ Adicionar Predição Específica de Draft de Campeões (Opcional)
      </summary>
      <div class="p-6 bg-[#172132] space-y-8 border-t border-[#334155]">
        <div>
           <h3 class="text-blue-400 font-bold mb-4 uppercase text-sm tracking-wider flex items-center gap-2">
              <span class="w-3 h-3 bg-blue-500 rounded-full inline-block"></span> 🟦 Blue Side Draft
           </h3>
           <div class="grid grid-cols-2 lg:grid-cols-5 gap-6">
             {#each roles as role}
               <div class="flex flex-col items-center bg-[#0a101a] p-3 rounded-xl border border-[#1e40af] border-opacity-30">
                 <span class="block text-xs font-bold text-blue-300 uppercase tracking-widest mb-3">{role}</span>
                 <!-- Image Preview -->
                 <div class="w-16 h-16 bg-[#0f172a] border border-[#1e293b] rounded-lg overflow-hidden flex items-center justify-center mb-3 shadow-inner">
                   {#if t1_champs[role]}
                     <img src={`http://localhost:8000/champs/${t1_champs[role]}.png`} alt={t1_champs[role]} class="w-full h-full object-cover" />
                   {:else}
                     <span class="text-xl text-slate-700 font-bold opacity-50">?</span>
                   {/if}
                 </div>
                 <select bind:value={t1_champs[role]} aria-label="Blue side {role}" class="w-full bg-[#1e293b] text-xs border border-[#334155] rounded p-2 text-white outline-none focus:ring-1 focus:ring-blue-500 transition-colors">
                   <option value="">Nenhum</option>
                   {#each champions as c} 
                     {#if c} <option value={c}>{c}</option> {/if}
                   {/each}
                 </select>
               </div>
             {/each}
           </div>
        </div>
        <div>
           <h3 class="text-red-400 font-bold mb-4 uppercase text-sm tracking-wider flex items-center gap-2">
             <span class="w-3 h-3 bg-red-500 rounded-full inline-block"></span> 🟥 Red Side Draft
           </h3>
           <div class="grid grid-cols-2 lg:grid-cols-5 gap-6">
             {#each roles as role}
               <div class="flex flex-col items-center bg-[#0a101a] p-3 rounded-xl border border-[#991b1b] border-opacity-30">
                 <span class="block text-xs font-bold text-red-300 uppercase tracking-widest mb-3">{role}</span>
                 <!-- Image Preview -->
                 <div class="w-16 h-16 bg-[#0f172a] border border-[#1e293b] rounded-lg overflow-hidden flex items-center justify-center mb-3 shadow-inner">
                   {#if t2_champs[role]}
                     <img src={`http://localhost:8000/champs/${t2_champs[role]}.png`} alt={t2_champs[role]} class="w-full h-full object-cover" />
                   {:else}
                     <span class="text-xl text-slate-700 font-bold opacity-50">?</span>
                   {/if}
                 </div>
                 <select bind:value={t2_champs[role]} aria-label="Red side {role}" class="w-full bg-[#1e293b] text-xs border border-[#334155] rounded p-2 text-white outline-none focus:ring-1 focus:ring-red-500 transition-colors">
                   <option value="">Nenhum</option>
                   {#each champions as c} 
                     {#if c} <option value={c}>{c}</option> {/if}
                   {/each}
                 </select>
               </div>
             {/each}
           </div>
        </div>
      </div>
    </details>

    <div class="text-center">
      {#if errorMsg}
        <p class="text-red-400 mb-4 font-medium animate-pulse">{errorMsg}</p>
      {/if}
      <button 
        onclick={generateInsights} 
        disabled={loading}
        class="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:shadow-none text-white font-bold py-3 px-10 rounded-xl transition-all shadow-lg shadow-blue-900/50 hover:-translate-y-1 active:scale-95"
      >
        {loading ? '🔮 Processando Modelos Neurais...' : '📊 Gerar Insights de Apostas e Predição'}
      </button>
    </div>
  </div>

  {#if analyticsData}
    <div class="results-panel flex flex-col gap-6 mt-6 w-full">
      
      <!-- Seções de Largura Total -->
      <div class="analytics-section">
        <ResultsHeader
          team1={analyticsData.meta.team1}
          team2={analyticsData.meta.team2}
          patchLabel={analyticsData.meta.patch_label}
          gamesT1={analyticsData.meta.games_t1}
          gamesT2={analyticsData.meta.games_t2}
        />
      </div>

      <div class="analytics-section">
        <EducationalSection />
      </div>

      {#if analyticsData.league_context}
        <div class="analytics-section">
          <LeagueContextSection data={analyticsData.league_context} />
        </div>
      {/if}

      {#if analyticsData.objective_correlations}
        <div class="analytics-section">
          <WinConditionsSection data={analyticsData.objective_correlations} />
        </div>
      {/if}

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <!-- Coluna Esquerda: Stack de métricas e distribuições -->
        <div class="flex flex-col gap-6 h-full">
          <div class="analytics-section"><EGRSection data={analyticsData.egr} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          <div class="analytics-section"><RadarSection data={analyticsData.radar} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          {#if analyticsData.side_performance}
            <div class="analytics-section"><SidePerformanceSection data={analyticsData.side_performance} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          {/if}
          <div class="analytics-section"><PaceSection data={analyticsData.pace} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          <div class="analytics-section"><RecentFormSection data={analyticsData.recent_form} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          
          {#if analyticsData.dragons && analyticsData.towers && analyticsData.barons}
            <div class="analytics-section">
              <ObjectivesSection
                dragons={analyticsData.dragons}
                towers={analyticsData.towers}
                barons={analyticsData.barons}
                team1={analyticsData.meta.team1}
                team2={analyticsData.meta.team2}
              />
            </div>
          {/if}
        </div>

        <!-- Coluna Direita: Stack de métricas e distribuições -->
        <div class="flex flex-col gap-6 h-full">
          <div class="analytics-section"><MLRSection data={analyticsData.mlr} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          <div class="analytics-section"><TimelineSection data={analyticsData.timeline} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          <div class="analytics-section"><EconomySection data={analyticsData.economy} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          <div class="analytics-section"><WinRateSection data={analyticsData.winrate} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          
          {#if analyticsData.kills_total && analyticsData.kills_per_team && analyticsData.handicap}
            <div class="analytics-section">
              <KillsSection
                killsTotal={analyticsData.kills_total}
                killsPerTeam={analyticsData.kills_per_team}
                handicap={analyticsData.handicap}
                team1={analyticsData.meta.team1}
                team2={analyticsData.meta.team2}
              />
            </div>
          {/if}
          {#if analyticsData.duration}
            <div class="analytics-section"><DurationSection data={analyticsData.duration} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} /></div>
          {/if}
        </div>
      </div>

      <!-- Series Performance -->
      {#if analyticsData.series}
        <div class="analytics-section">
          <SeriesSection data={analyticsData.series} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} />
        </div>
      {/if}

      <!-- EV Finder (Largura Total) -->
      {#if analyticsData.ev_finder}
        <div class="analytics-section">
          <EVFinderSection data={analyticsData.ev_finder} team1={analyticsData.meta.team1} team2={analyticsData.meta.team2} />
        </div>
      {/if}

      <footer class="text-center text-slate-500 text-sm py-8 border-t border-slate-800 mt-4">
        Camada Silver Analytics | Desenvolvido com Metodologia do Oracle's Elixir
      </footer>
    </div>
  {/if}
</div>
