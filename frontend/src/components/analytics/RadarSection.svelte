<script lang="ts">
  import type { RadarSection } from '$lib/types/analytics';
  import RadarChart from '../analytics/RadarChart.svelte';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';

  interface Props {
    data: RadarSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();
</script>

<div class="section-card">
  <h3 class="section-title">🕸️ Identidade Tática (Team DNA)</h3>

  <div class="chart-wrapper">
    <RadarChart
      labels={data.labels}
      t1Values={data.t1_values}
      t2Values={data.t2_values}
      {team1}
      {team2}
    />
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
    border-left: 3px solid #3b82f6;
    width: 100%;
  }

  .section-title {
    color: #60a5fa;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .chart-wrapper {
    width: 100%;
    max-width: 550px;
    margin: 0 auto 1rem auto;
  }
</style>
