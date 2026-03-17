<script lang="ts">
  import type { TimelineSection } from '$lib/types/analytics';
  import LineChart from '../analytics/LineChart.svelte';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';

  interface Props {
    data: TimelineSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();
</script>

<div class="section-card">
  <h3 class="section-title">📈 Timeline de Vantagens (10 a 25 min)</h3>

  {#if data.draft_projection_active}
    <div class="draft-banner">
      <span class="draft-icon">✨</span>
      <span class="draft-label">Projeção de Snowball (Draft)</span>
      {#if data.mult_t1 != null}
        <span class="mult t1-mult">{team1}: ×{data.mult_t1.toFixed(2)}</span>
      {/if}
      {#if data.mult_t2 != null}
        <span class="mult t2-mult">{team2}: ×{data.mult_t2.toFixed(2)}</span>
      {/if}
    </div>
  {/if}

  <div class="chart-wrapper">
    <LineChart timelineData={data} {team1} {team2} />
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
  }

  .section-title {
    color: #fbbf24;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .draft-banner {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.4);
    border-radius: 0.5rem;
    padding: 0.625rem 1rem;
    margin-bottom: 1rem;
    font-size: 0.875rem;
  }

  .draft-icon {
    font-size: 1rem;
  }

  .draft-label {
    color: #c4b5fd;
    font-weight: 600;
  }

  .mult {
    font-weight: 700;
    padding: 0.125rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.8125rem;
  }

  .t1-mult {
    background: rgba(59, 130, 246, 0.2);
    color: #93c5fd;
  }

  .t2-mult {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
  }

  .chart-wrapper {
    margin-bottom: 1rem;
  }
</style>
