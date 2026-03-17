<script lang="ts">
  import type { WinRateSection } from '$lib/types/analytics';
  import GaugeChart from './GaugeChart.svelte';
  import ExplainBox from './ExplainBox.svelte';
  import DataCommentBox from './DataCommentBox.svelte';

  interface Props {
    data: WinRateSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();
</script>

<div class="section-card">
  <h3 class="section-title">🏆 Win Rate</h3>

  <div class="gauges-row">
    <div class="gauge-container">
      <GaugeChart winRate={data.t1_win_rate} teamColor="#3b82f6" teamName={team1} />
      <div class="gauge-meta">
        <span class="wins-label t1">{data.t1_wins}V / {data.t1_total - data.t1_wins}D</span>
        <span class="games-label">{data.t1_total} jogos</span>
      </div>
    </div>
    <div class="gauge-container">
      <GaugeChart winRate={data.t2_win_rate} teamColor="#ef4444" teamName={team2} />
      <div class="gauge-meta">
        <span class="wins-label t2">{data.t2_wins}V / {data.t2_total - data.t2_wins}D</span>
        <span class="games-label">{data.t2_total} jogos</span>
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
    border-left: 3px solid #3b82f6;
    width: 100%;
  }

  .section-title {
    color: #93c5fd;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .gauges-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-bottom: 1rem;
  }

  .gauge-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .gauge-meta {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.125rem;
  }

  .wins-label {
    font-size: 0.8125rem;
    font-weight: 600;
  }

  .wins-label.t1 {
    color: #60a5fa;
  }

  .wins-label.t2 {
    color: #f87171;
  }

  .games-label {
    font-size: 0.75rem;
    color: #64748b;
  }
</style>
