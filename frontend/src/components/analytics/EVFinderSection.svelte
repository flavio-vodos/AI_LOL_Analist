<script lang="ts">
  import type { EVFinderSection, EVFinderTeamCard, BetEntryData } from '$lib/types/analytics';
  import BetEntry from './BetEntry.svelte';

  interface Props {
    data: EVFinderSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  const riskTiers = [
    { key: 'low' as const, label: '🟢 Baixo Risco' },
    { key: 'med' as const, label: '🟡 Risco Médio' },
    { key: 'high' as const, label: '🔴 Alto Risco' },
  ];

  function entriesByRisk(entries: BetEntryData[], tier: 'low' | 'med' | 'high'): BetEntryData[] {
    return entries.filter(e => e.risk_tier === tier);
  }

  function hasAnyEntries(markets: Record<string, BetEntryData[]>): boolean {
    return Object.values(markets).some(entries => entries.length > 0);
  }
</script>

<div class="section-wrapper">
  <!-- Green gradient header -->
  <div class="ev-header">
    <h2 class="ev-title">🎯 Expected Value Finder (Odd Mining)</h2>
    <p class="ev-subtitle">
      Algoritmo de varredura buscando Edges Estatísticos baseados nos Modelos do Elixir
    </p>
  </div>

  <div class="cards-grid">
    <!-- T1 Card -->
    <div class="team-card t1-card">
      <div class="team-card-header t1-header">
        <span class="team-card-title">{team1}</span>
      </div>
      <div class="team-card-body">
        {#if hasAnyEntries(data.t1_card.markets)}
          {#each Object.entries(data.t1_card.markets) as [market, entries]}
            {#if entries.length > 0}
              <div class="market-group">
                <div class="market-title">{market}</div>
                {#each riskTiers as tier}
                  {#if entriesByRisk(entries, tier.key).length > 0}
                    <div class="risk-tier-section">
                      <div class="risk-tier-header">{tier.label}</div>
                      <div class="entries-row">
                        {#each entriesByRisk(entries, tier.key) as entry}
                          <BetEntry {entry} />
                        {/each}
                      </div>
                    </div>
                  {/if}
                {/each}
              </div>
            {/if}
          {/each}
        {:else}
          <p class="no-entries">Nenhuma entrada encontrada para este time.</p>
        {/if}
      </div>
    </div>

    <!-- T2 Card -->
    <div class="team-card t2-card">
      <div class="team-card-header t2-header">
        <span class="team-card-title">{team2}</span>
      </div>
      <div class="team-card-body">
        {#if hasAnyEntries(data.t2_card.markets)}
          {#each Object.entries(data.t2_card.markets) as [market, entries]}
            {#if entries.length > 0}
              <div class="market-group">
                <div class="market-title">{market}</div>
                {#each riskTiers as tier}
                  {#if entriesByRisk(entries, tier.key).length > 0}
                    <div class="risk-tier-section">
                      <div class="risk-tier-header">{tier.label}</div>
                      <div class="entries-row">
                        {#each entriesByRisk(entries, tier.key) as entry}
                          <BetEntry {entry} />
                        {/each}
                      </div>
                    </div>
                  {/if}
                {/each}
              </div>
            {/if}
          {/each}
        {:else}
          <p class="no-entries">Nenhuma entrada encontrada para este time.</p>
        {/if}
      </div>
    </div>

    <!-- Joint Card -->
    <div class="team-card joint-card">
      <div class="team-card-header joint-header">
        <span class="team-card-title">Análise Confronto (Versus)</span>
      </div>
      <div class="team-card-body">
        {#if hasAnyEntries(data.joint_card.markets)}
          {#each Object.entries(data.joint_card.markets) as [market, entries]}
            {#if entries.length > 0}
              <div class="market-group">
                <div class="market-title">{market}</div>
                {#each riskTiers as tier}
                  {#if entriesByRisk(entries, tier.key).length > 0}
                    <div class="risk-tier-section">
                      <div class="risk-tier-header">{tier.label}</div>
                      <div class="entries-row">
                        {#each entriesByRisk(entries, tier.key) as entry}
                          <BetEntry {entry} />
                        {/each}
                      </div>
                    </div>
                  {/if}
                {/each}
              </div>
            {/if}
          {/each}
        {:else}
          <p class="no-entries">Nenhuma entrada combinada encontrada.</p>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  .section-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    width: 100%;
  }

  .ev-header {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 1rem;
    padding: 1.5rem 2rem;
    position: relative;
    overflow: hidden;
  }

  .ev-header::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 200px;
    height: 100%;
    background: radial-gradient(circle at center, rgba(16, 185, 129, 0.1) 0%, transparent 70%);
  }

  .ev-title {
    color: #10b981;
    font-size: 1.25rem;
    font-weight: 800;
    margin: 0 0 0.5rem 0;
    text-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
  }

  .ev-subtitle {
    color: #a7f3d0;
    font-size: 0.875rem;
    margin: 0;
    opacity: 0.8;
  }

  .cards-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  @media (min-width: 1024px) {
    .cards-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  .team-card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(12px);
    border-radius: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.05);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .team-card:hover {
    transform: translateY(-4px);
    border-color: rgba(255, 255, 255, 0.1);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
  }

  .team-card-header {
    padding: 1.25rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .t1-header {
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
    border-bottom: 2px solid rgba(59, 130, 246, 0.3);
  }

  .t2-header {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, transparent 100%);
    border-bottom: 2px solid rgba(239, 68, 68, 0.3);
  }

  .joint-header {
    background: linear-gradient(90deg, rgba(168, 85, 247, 0.1) 0%, transparent 100%);
    border-bottom: 2px solid rgba(168, 85, 247, 0.3);
  }

  .team-card-title {
    font-size: 1.125rem;
    font-weight: 800;
    letter-spacing: -0.025em;
  }

  .t1-card .team-card-title { color: #60a5fa; }
  .t2-card .team-card-title { color: #f87171; }
  .joint-card .team-card-title { color: #c084fc; }

  .team-card-body {
    padding: 1.25rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .market-group {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .market-title {
    font-size: 0.8125rem;
    font-weight: 800;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .market-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(51, 65, 85, 0.8), transparent);
  }

  .risk-tier-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .risk-tier-header {
    font-size: 0.75rem;
    font-weight: 700;
    color: #94a3b8;
    background: rgba(255, 255, 255, 0.03);
    padding: 0.25rem 0.625rem;
    border-radius: 1rem;
    width: fit-content;
  }

  .entries-row {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  /* Force horizontal expansion for entries in row */
  .entries-row :global(.bet-entry) {
    flex: 1 1 280px;
    margin-bottom: 0 !important;
  }

  .no-entries {
    color: #475569;
    font-size: 0.8125rem;
    font-style: italic;
    text-align: center;
    padding: 1rem;
  }
</style>
