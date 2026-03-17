<script lang="ts">
  import type { DistributionSection, BetEntryData } from '$lib/types/analytics';
  import HistogramChart from './HistogramChart.svelte';
  import StatsBadge from './StatsBadge.svelte';
  import ExplainBox from './ExplainBox.svelte';
  import DataCommentBox from './DataCommentBox.svelte';

  interface Props {
    dragons: DistributionSection;
    towers: DistributionSection;
    barons: DistributionSection;
    team1: string;
    team2: string;
  }

  let { dragons, towers, barons, team1, team2 }: Props = $props();

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

  interface ObjectiveCard {
    data: DistributionSection;
    title: string;
    color: string;
    icon: string;
  }

  const cards: ObjectiveCard[] = $derived([
    { data: dragons, title: 'Dragões', color: '#f97316', icon: '🐉' },
    { data: towers, title: 'Torres', color: '#f97316', icon: '🏰' },
    { data: barons, title: 'Barões', color: '#f97316', icon: '👑' },
  ]);
</script>

<div class="section-wrapper">
  <h2 class="section-heading">🐉 Distribuições de Objetivos (Dragões, Torres, Barões)</h2>

  {#each cards as card}
    <div class="chart-card" style:--accent={card.color}>
      <h3 class="card-title">{card.icon} {card.title}</h3>

      <HistogramChart rawData={card.data.histogram_data} color={card.color} meanLine={true} label={card.title} />

      <div class="badges-row">
        {#each statsBadges as b}
          <StatsBadge
            label={b.label}
            value={card.data.stats[b.key].toFixed(1)}
            tooltip={b.tooltip}
            color={card.color}
          />
        {/each}
      </div>

      {#if card.data.draft_projection}
        <div class="draft-banner">
          ✨ <strong>Projeção do Draft ativa</strong> — valores ajustados pelo multiplicador de campeões
        </div>
      {/if}


      <ExplainBox text={card.data.explain_text} />
      <DataCommentBox comments={card.data.comments} />
    </div>
  {/each}
</div>

<style>
  .section-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .section-heading {
    color: #fb923c;
    font-size: 1.125rem;
    font-weight: 700;
    margin: 0;
  }

  .chart-card {
    background: #1e293b;
    border-radius: 0.75rem;
    padding: 1.25rem;
    border: 1px solid #334155;
    border-left: 3px solid var(--accent, #f97316);
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    width: 100%;
  }

  .chart-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 0 16px rgba(249, 115, 22, 0.2);
  }

  .card-title {
    color: #fdba74;
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
