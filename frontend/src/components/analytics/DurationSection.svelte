<script lang="ts">
  import type { DistributionSection } from '$lib/types/analytics';
  import HistogramChart from './HistogramChart.svelte';
  import StatsBadge from './StatsBadge.svelte';
  import ExplainBox from './ExplainBox.svelte';
  import DataCommentBox from './DataCommentBox.svelte';

  interface Props {
    data: DistributionSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  const accentColor = '#06b6d4';

  const statsBadges = [
    { label: 'μ', key: 'avg' as const, tooltip: 'Média aritmética da duração das partidas' },
    { label: 'Med', key: 'med' as const, tooltip: 'Duração mediana das partidas' },
    { label: 'σ', key: 'std' as const, tooltip: 'Desvio padrão — dispersão da duração' },
    { label: 'Min', key: 'min' as const, tooltip: 'Duração mínima observada' },
    { label: 'Max', key: 'max' as const, tooltip: 'Duração máxima observada' },
    { label: 'Moda', key: 'mode' as const, tooltip: 'Duração mais frequente' },
    { label: 'P25', key: 'p25' as const, tooltip: 'Percentil 25 — 25% das partidas terminam antes deste valor' },
    { label: 'P75', key: 'p75' as const, tooltip: 'Percentil 75 — 75% das partidas terminam antes deste valor' },
  ];

  const overUnderLines = [25.5, 27.5, 30.5, 32.5, 35.5, 37.5];
</script>

<div class="section-wrapper">
  <h2 class="section-heading">⏱️ Duração da Partida</h2>

  <div class="chart-card">
    <h3 class="card-title">Distribuição de Duração (minutos)</h3>

    <HistogramChart rawData={data.histogram_data} color={accentColor} meanLine={true} label="Duração (min)" />

    <div class="badges-row">
      {#each statsBadges as b}
        <StatsBadge
          label={b.label}
          value={data.stats[b.key].toFixed(1)}
          tooltip={b.tooltip}
          color={accentColor}
        />
      {/each}
    </div>

    <div class="lines-row">
      <span class="lines-label">Linhas Over/Under:</span>
      {#each overUnderLines as line}
        <span class="line-badge">{line}</span>
      {/each}
    </div>

    {#if data.draft_projection}
      <div class="draft-banner">
        ✨ <strong>Projeção do Draft ativa</strong> — valores ajustados pelo multiplicador de campeões
      </div>
    {/if}


    <ExplainBox text={data.explain_text} />
    <DataCommentBox comments={data.comments} />
  </div>
</div>

<style>
  .section-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .section-heading {
    color: #22d3ee;
    font-size: 1.125rem;
    font-weight: 700;
    margin: 0;
  }

  .chart-card {
    background: #1e293b;
    border-radius: 0.75rem;
    padding: 1.25rem;
    border: 1px solid #334155;
    border-left: 3px solid #06b6d4;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    width: 100%;
  }

  .chart-card:hover {
    transform: translateY(-4px);
    border-color: #22d3ee;
    box-shadow: 0 0 16px rgba(6, 182, 212, 0.2);
  }

  .card-title {
    color: #67e8f9;
    font-size: 0.9375rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .badges-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 0.75rem 0;
  }

  .lines-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin: 0.5rem 0 0.75rem 0;
  }

  .lines-label {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 600;
    margin-right: 2px;
  }

  .line-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    background-color: rgba(6, 182, 212, 0.1);
    color: #22d3ee;
    border: 1px solid rgba(6, 182, 212, 0.3);
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

</style>
