<script lang="ts">
  import type { PaceSection } from '$lib/types/analytics';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';

  interface Props {
    data: PaceSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  function barWidth(value: number, t1: number, t2: number): string {
    const max = Math.max(t1, t2, 1);
    return `${(value / max) * 100}%`;
  }
</script>

<div class="section-card">
  <h3 class="section-title">💥 Pace Context</h3>

  <div class="metrics">
    <!-- CKPM -->
    <div class="metric-block">
      <div class="metric-header">CKPM <span class="metric-sub">(Combined Kills Per Minute)</span></div>
      <div class="bar-group">
        <span class="team-name t1">{team1}</span>
        <div class="bar-track">
          <div class="bar t1-bar" style:width={barWidth(data.ckpm.t1, data.ckpm.t1, data.ckpm.t2)}></div>
        </div>
        <span class="bar-value">{data.ckpm.t1.toFixed(2)}</span>
      </div>
      <div class="bar-group">
        <span class="team-name t2">{team2}</span>
        <div class="bar-track">
          <div class="bar t2-bar" style:width={barWidth(data.ckpm.t2, data.ckpm.t1, data.ckpm.t2)}></div>
        </div>
        <span class="bar-value">{data.ckpm.t2.toFixed(2)}</span>
      </div>
    </div>

    <!-- KPM -->
    <div class="metric-block">
      <div class="metric-header">KPM <span class="metric-sub">(Kills Per Minute)</span></div>
      <div class="bar-group">
        <span class="team-name t1">{team1}</span>
        <div class="bar-track">
          <div class="bar t1-bar" style:width={barWidth(data.kpm.t1, data.kpm.t1, data.kpm.t2)}></div>
        </div>
        <span class="bar-value">{data.kpm.t1.toFixed(2)}</span>
      </div>
      <div class="bar-group">
        <span class="team-name t2">{team2}</span>
        <div class="bar-track">
          <div class="bar t2-bar" style:width={barWidth(data.kpm.t2, data.kpm.t1, data.kpm.t2)}></div>
        </div>
        <span class="bar-value">{data.kpm.t2.toFixed(2)}</span>
      </div>
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

  .metrics {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .metric-block {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .metric-header {
    color: #cbd5e1;
    font-size: 0.8125rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
  }

  .metric-sub {
    color: #64748b;
    font-weight: 400;
    font-size: 0.75rem;
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
    width: 48px;
    flex-shrink: 0;
  }
</style>
