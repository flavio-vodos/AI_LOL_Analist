<script lang="ts">
  import type { EconomySection } from '$lib/types/analytics';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';

  interface Props {
    data: EconomySection;
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
  <h3 class="section-title">💰 Economy Context</h3>

  <div class="metrics">
    <!-- EGPM -->
    <div class="metric-block">
      <div class="metric-header">EGPM <span class="metric-sub">(Earned Gold Per Minute)</span></div>
      <div class="bar-group">
        <span class="team-name t1">{team1}</span>
        <div class="bar-track">
          <div class="bar t1-bar" style:width={barWidth(data.egpm.t1, data.egpm.t1, data.egpm.t2)}></div>
        </div>
        <span class="bar-value">{data.egpm.t1.toFixed(0)}</span>
      </div>
      <div class="bar-group">
        <span class="team-name t2">{team2}</span>
        <div class="bar-track">
          <div class="bar t2-bar" style:width={barWidth(data.egpm.t2, data.egpm.t1, data.egpm.t2)}></div>
        </div>
        <span class="bar-value">{data.egpm.t2.toFixed(0)}</span>
      </div>
    </div>

    <!-- DPM -->
    <div class="metric-block">
      <div class="metric-header">DPM <span class="metric-sub">(Damage Per Minute)</span></div>
      <div class="bar-group">
        <span class="team-name t1">{team1}</span>
        <div class="bar-track">
          <div class="bar t1-bar" style:width={barWidth(data.dpm.t1, data.dpm.t1, data.dpm.t2)}></div>
        </div>
        <span class="bar-value">{data.dpm.t1.toFixed(0)}</span>
      </div>
      <div class="bar-group">
        <span class="team-name t2">{team2}</span>
        <div class="bar-track">
          <div class="bar t2-bar" style:width={barWidth(data.dpm.t2, data.dpm.t1, data.dpm.t2)}></div>
        </div>
        <span class="bar-value">{data.dpm.t2.toFixed(0)}</span>
      </div>
    </div>
  </div>

  {#if data.gold_layer}
    <div class="gold-layer">
      <div class="gold-layer-title">🥇 Gold Layer</div>
      <table class="gold-table">
        <thead>
          <tr>
            <th class="metric-col">Métrica</th>
            <th class="t1-col">{team1}</th>
            <th class="t2-col">{team2}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>EGDI</td>
            <td class="t1-val">{(data.gold_layer.t1.egdi ?? 0).toFixed(2)}</td>
            <td class="t2-val">{(data.gold_layer.t2.egdi ?? 0).toFixed(2)}</td>
          </tr>
          <tr>
            <td>Throw Rate</td>
            <td class="t1-val">{(data.gold_layer.t1.throw_rate ?? 0).toFixed(1)}%</td>
            <td class="t2-val">{(data.gold_layer.t2.throw_rate ?? 0).toFixed(1)}%</td>
          </tr>
          <tr>
            <td>Comeback Rate</td>
            <td class="t1-val">{(data.gold_layer.t1.comeback_rate ?? 0).toFixed(1)}%</td>
            <td class="t2-val">{(data.gold_layer.t2.comeback_rate ?? 0).toFixed(1)}%</td>
          </tr>
        </tbody>
      </table>
    </div>
  {/if}

  <p class="advanced-stats-note">
    Baseado no artigo <em>'LoL's Advanced Stats Problem'</em> — EGPM e DPM são as métricas mais confiáveis para medir eficiência econômica e de combate.
  </p>

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

  .gold-layer {
    margin-bottom: 1rem;
    background: rgba(234, 179, 8, 0.07);
    border: 1px solid rgba(234, 179, 8, 0.2);
    border-radius: 0.5rem;
    padding: 0.75rem;
  }

  .gold-layer-title {
    color: #fbbf24;
    font-size: 0.875rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
  }

  .gold-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8125rem;
  }

  .gold-table th {
    padding: 0.375rem 0.5rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 1px solid rgba(51, 65, 85, 0.6);
  }

  .metric-col {
    color: #94a3b8;
  }

  .t1-col {
    color: #60a5fa;
  }

  .t2-col {
    color: #f87171;
  }

  .gold-table td {
    padding: 0.375rem 0.5rem;
    color: #94a3b8;
    border-bottom: 1px solid rgba(51, 65, 85, 0.3);
  }

  .t1-val {
    color: #93c5fd;
    font-weight: 600;
  }

  .t2-val {
    color: #fca5a5;
    font-weight: 600;
  }

  .advanced-stats-note {
    color: #64748b;
    font-size: 0.75rem;
    line-height: 1.5;
    margin: 0 0 0.75rem 0;
    font-style: italic;
  }

  .advanced-stats-note em {
    color: #94a3b8;
    font-style: normal;
    font-weight: 600;
  }
</style>
