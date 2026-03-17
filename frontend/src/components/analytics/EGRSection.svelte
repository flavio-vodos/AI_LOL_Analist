<script lang="ts">
  import type { EGRSection } from '$lib/types/analytics';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';

  interface Props {
    data: EGRSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  const metrics = $derived([
    { label: 'First Blood%', t1: data.t1_values.fb, t2: data.t2_values.fb },
    { label: 'First Dragon%', t1: data.t1_values.fd, t2: data.t2_values.fd },
    { label: 'First Herald%', t1: data.t1_values.fh, t2: data.t2_values.fh },
  ]);

  function barWidth(value: number, t1: number, t2: number): string {
    const max = Math.max(t1, t2, 1);
    return `${(value / max) * 100}%`;
  }
</script>

<div class="section-card">
  <h3 class="section-title">🧠 EGR Proxy — Early-Game Rating</h3>

  <div class="metrics">
    {#each metrics as metric}
      <div class="metric-row">
        <div class="metric-label">{metric.label}</div>
        <div class="bars">
          <div class="bar-group">
            <span class="team-name t1">{team1}</span>
            <div class="bar-track">
              <div
                class="bar t1-bar"
                style:width={barWidth(metric.t1, metric.t1, metric.t2)}
              ></div>
            </div>
            <span class="bar-value">{metric.t1.toFixed(1)}%</span>
          </div>
          <div class="bar-group">
            <span class="team-name t2">{team2}</span>
            <div class="bar-track">
              <div
                class="bar t2-bar"
                style:width={barWidth(metric.t2, metric.t1, metric.t2)}
              ></div>
            </div>
            <span class="bar-value">{metric.t2.toFixed(1)}%</span>
          </div>
        </div>
      </div>
    {/each}
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

  .metrics {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .metric-row {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .metric-label {
    color: #94a3b8;
    font-size: 0.8125rem;
    font-weight: 600;
  }

  .bars {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .bar-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .team-name {
    font-size: 0.75rem;
    font-weight: 600;
    width: 80px;
    flex-shrink: 0;
    text-align: right;
  }

  .team-name.t1 {
    color: #60a5fa;
  }

  .team-name.t2 {
    color: #f87171;
  }

  .bar-track {
    flex: 1;
    height: 14px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    overflow: hidden;
  }

  .bar {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
  }

  .t1-bar {
    background: #3b82f6;
  }

  .t2-bar {
    background: #ef4444;
  }

  .bar-value {
    font-size: 0.75rem;
    color: #cbd5e1;
    width: 40px;
    flex-shrink: 0;
  }
</style>
