<script lang="ts">
  import type { DistributionSection, KillsPerTeamSection, HandicapSection, BetEntryData } from '$lib/types/analytics';
  import HistogramChart from './HistogramChart.svelte';
  import StatsBadge from './StatsBadge.svelte';
  import ExplainBox from './ExplainBox.svelte';
  import DataCommentBox from './DataCommentBox.svelte';

  interface Props {
    killsTotal: DistributionSection;
    killsPerTeam: KillsPerTeamSection;
    handicap: HandicapSection;
    team1: string;
    team2: string;
  }

  let { killsTotal, killsPerTeam, handicap, team1, team2 }: Props = $props();

  const statsBadges = [
    { label: 'μ', key: 'avg' as const, tooltip: 'Média aritmética dos valores históricos' },
    { label: 'Med', key: 'med' as const, tooltip: 'Valor central da distribuição' },
    { label: 'σ', key: 'std' as const, tooltip: 'Desvio padrão — dispersão dos dados' },
    { label: 'Min', key: 'min' as const, tooltip: 'Valores mínimo e máximo observados' },
    { label: 'Max', key: 'max' as const, tooltip: 'Valores mínimo e máximo observados' },
    { label: 'Moda', key: 'mode' as const, tooltip: 'Valor mais frequente na distribuição' },
    { label: 'P25', key: 'p25' as const, tooltip: 'Percentis 25 e 75 — intervalo interquartil' },
    { label: 'P75', key: 'p75' as const, tooltip: 'Percentis 25 e 75 — intervalo interquartil' },
  ];

  function groupByRisk(entries: BetEntryData[]) {
    return {
      low: entries.filter(e => e.risk_tier === 'low'),
      med: entries.filter(e => e.risk_tier === 'med'),
      high: entries.filter(e => e.risk_tier === 'high'),
    };
  }
</script>

<div class="section-wrapper">
  <h2 class="section-heading">⚔️ Distribuições de Abates (Combate Extremo)</h2>

  <!-- Total Kills Card -->
  <div class="chart-card">
    <h3 class="card-title">Total de Abates na Partida</h3>
    <HistogramChart rawData={killsTotal.histogram_data} color="#8b5cf6" meanLine={true} label="Total Kills" />

    <div class="badges-row">
      {#each statsBadges as b}
        <StatsBadge label={b.label} value={killsTotal.stats[b.key].toFixed(1)} tooltip={b.tooltip} color="#8b5cf6" />
      {/each}
    </div>

    {#if killsTotal.draft_projection}
      <div class="draft-banner">
        ✨ <strong>Projeção do Draft ativa</strong> — valores ajustados pelo multiplicador de campeões
      </div>
    {/if}


    <ExplainBox text={killsTotal.explain_text} />
    <DataCommentBox comments={killsTotal.comments} />
  </div>

  <!-- Kills Per Team Card -->
  <div class="chart-card">
    <h3 class="card-title">Kills por Time</h3>
    <div class="dual-histograms">
      <div class="histogram-col">
        <div class="histogram-label t1">{team1}</div>
        <HistogramChart rawData={killsPerTeam.t1_histogram} color="#3b82f6" meanLine={true} label={team1} />
        <div class="badges-row">
          {#each statsBadges as b}
            {#if killsPerTeam.t1_stats}
              <StatsBadge label={b.label} value={killsPerTeam.t1_stats[b.key].toFixed(1)} tooltip={b.tooltip} color="#3b82f6" />
            {/if}
          {/each}
        </div>
      </div>
      <div class="histogram-col">
        <div class="histogram-label t2">{team2}</div>
        <HistogramChart rawData={killsPerTeam.t2_histogram} color="#ef4444" meanLine={true} label={team2} />
        <div class="badges-row">
          {#each statsBadges as b}
            {#if killsPerTeam.t2_stats}
              <StatsBadge label={b.label} value={killsPerTeam.t2_stats[b.key].toFixed(1)} tooltip={b.tooltip} color="#ef4444" />
            {/if}
          {/each}
        </div>
      </div>
    </div>

    {#if killsPerTeam.draft_projection}
      <div class="draft-banner">
        ✨ <strong>Projeção do Draft ativa</strong> — valores ajustados pelo multiplicador de campeões
      </div>
    {/if}


    <ExplainBox text={killsPerTeam.explain_text} />
    <DataCommentBox comments={killsPerTeam.comments} />
  </div>

  <!-- Handicap Card -->
  <div class="chart-card">
    <h3 class="card-title">Handicap de Kills ({team1} − {team2})</h3>

    <div class="handicap-note">
      <p>
        O <strong>Handicap de Kills</strong> representa a diferença de abates entre os dois times em cada partida.
        Um valor positivo indica que {team1} terminou com mais kills; negativo indica que {team2} dominou o combate.
      </p>
      <p>
        <strong>Exemplo:</strong> Se FURIA fez 18 kills e Sentinels fez 12, o handicap é <code>+6</code> para FURIA.
        Apostas de handicap permitem apostar se um time vai "vencer" o combate por uma margem específica.
      </p>
    </div>

    <HistogramChart rawData={handicap.t1_histogram} color="#8b5cf6" meanLine={true} label="Kill Diff" />

    <div class="badges-row">
      {#each statsBadges as b}
        {#if handicap.t1_stats}
          <StatsBadge label={b.label} value={handicap.t1_stats[b.key].toFixed(1)} tooltip={b.tooltip} color="#8b5cf6" />
        {/if}
      {/each}
    </div>

    {#if handicap.draft_projection}
      <div class="draft-banner">
        ✨ <strong>Projeção do Draft ativa</strong> — valores ajustados pelo multiplicador de campeões
      </div>
    {/if}


    <ExplainBox text={handicap.explain_text} />
    <DataCommentBox comments={handicap.comments} />
  </div>
</div>

<style>
  .section-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .section-heading {
    color: #a78bfa;
    font-size: 1.125rem;
    font-weight: 700;
    margin: 0;
  }

  .chart-card {
    background: #1e293b;
    border-radius: 0.75rem;
    padding: 1.25rem;
    border: 1px solid #334155;
    border-left: 3px solid #8b5cf6;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    width: 100%;
  }

  .chart-card:hover {
    transform: translateY(-4px);
    border-color: #a78bfa;
    box-shadow: 0 0 16px rgba(139, 92, 246, 0.2);
  }

  .card-title {
    color: #c4b5fd;
    font-size: 0.9375rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .dual-histograms {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .histogram-col {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .histogram-label {
    font-size: 0.8125rem;
    font-weight: 700;
    text-align: center;
  }

  .histogram-label.t1 {
    color: #60a5fa;
  }

  .histogram-label.t2 {
    color: #f87171;
  }

  .badges-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 0.75rem 0;
  }

  .draft-banner {
    background: rgba(234, 179, 8, 0.1);
    border: 1px solid rgba(234, 179, 8, 0.3);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.8125rem;
    color: #fbbf24;
    margin-bottom: 0.75rem;
  }


  .handicap-note {
    background: rgba(139, 92, 246, 0.07);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
    font-size: 0.8125rem;
    color: #94a3b8;
    line-height: 1.6;
  }

  .handicap-note p {
    margin: 0 0 0.5rem 0;
  }

  .handicap-note p:last-child {
    margin-bottom: 0;
  }

  .handicap-note strong {
    color: #c4b5fd;
  }

  .handicap-note code {
    background: rgba(139, 92, 246, 0.15);
    color: #a78bfa;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
  }
</style>
