<script lang="ts">
  import type { VisionSection } from '$lib/types/analytics';
  import BarChart from '../analytics/BarChart.svelte';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';

  interface Props {
    data: VisionSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  const chartLabels = ['Wards Colocadas', 'Wards Destruídas', 'Control Wards'];
  const t1Values = $derived([
    data.wards_placed.t1,
    data.wards_killed.t1,
    data.control_wards.t1,
  ]);
  const t2Values = $derived([
    data.wards_placed.t2,
    data.wards_killed.t2,
    data.control_wards.t2,
  ]);
</script>

<div class="section-card">
  <h3 class="section-title">👁️ Visão &amp; Controle de Mapa</h3>

  <div class="chart-wrapper">
    <BarChart
      labels={chartLabels}
      {t1Values}
      {t2Values}
      {team1}
      {team2}
    />
  </div>

  <div class="vision-score-row">
    <div class="vs-item t1">
      <span class="vs-label">{team1} — Vision Score Total</span>
      <span class="vs-value">{data.vision_score.t1.toFixed(1)}</span>
    </div>
    <div class="vs-item t2">
      <span class="vs-label">{team2} — Vision Score Total</span>
      <span class="vs-value">{data.vision_score.t2.toFixed(1)}</span>
    </div>
  </div>

  <ExplainBox text={data.explain_text} />
  <DataCommentBox comments={data.comments} />
</div>

<style>
  .section-card {
    background: #1e293b;
    border-radius: 0.75rem;
    padding: 1.25rem;
    border: 1px solid #334155;
    border-left: 3px solid #eab308;
    width: 100%;
  }

  .section-title {
    color: #fbbf24;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .chart-wrapper {
    margin-bottom: 1rem;
  }

  .vision-score-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }

  .vs-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(255, 255, 255, 0.04);
    border-radius: 0.375rem;
    padding: 0.5rem 0.75rem;
    flex: 1;
    min-width: 180px;
  }

  .vs-label {
    color: #94a3b8;
    font-size: 0.8125rem;
  }

  .vs-value {
    font-size: 1rem;
    font-weight: 700;
    margin-left: auto;
  }

  .vs-item.t1 .vs-value {
    color: #60a5fa;
  }

  .vs-item.t2 .vs-value {
    color: #f87171;
  }
</style>
