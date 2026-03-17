<script lang="ts">
  import type { MLRSection } from '$lib/types/analytics';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';

  interface Props {
    data: MLRSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();
</script>

<div class="section-card">
  <h3 class="section-title">🏰 MLR Proxy — Mid/Late Rating</h3>

  <div class="table-wrapper">
    <table class="mlr-table">
      <thead>
        <tr>
          <th class="metric-col">Métrica</th>
          <th class="t1-col">{team1}</th>
          <th class="t2-col">{team2}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="metric-name">FBN% (First Baron)</td>
          <td class="t1-val">{data.t1.fbaron_rate.toFixed(1)}%</td>
          <td class="t2-val">{data.t2.fbaron_rate.toFixed(1)}%</td>
        </tr>
        <tr>
          <td class="metric-name">Barões AVG</td>
          <td class="t1-val">{data.t1.avg_barons.toFixed(2)}</td>
          <td class="t2-val">{data.t2.avg_barons.toFixed(2)}</td>
        </tr>
        <tr>
          <td class="metric-name">Inibidores AVG</td>
          <td class="t1-val">{data.t1.avg_inhibitors.toFixed(2)}</td>
          <td class="t2-val">{data.t2.avg_inhibitors.toFixed(2)}</td>
        </tr>
        <tr>
          <td class="metric-name">Torres AVG</td>
          <td class="t1-val">{data.t1.avg_towers.toFixed(2)}</td>
          <td class="t2-val">{data.t2.avg_towers.toFixed(2)}</td>
        </tr>
      </tbody>
    </table>
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

  .table-wrapper {
    overflow-x: auto;
    margin-bottom: 1rem;
  }

  .mlr-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  .mlr-table th {
    padding: 0.5rem 0.75rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 1px solid #334155;
    font-size: 0.8125rem;
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

  .mlr-table td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  }

  .metric-name {
    color: #94a3b8;
  }

  .t1-val {
    color: #93c5fd;
    font-weight: 600;
  }

  .t2-val {
    color: #fca5a5;
    font-weight: 600;
  }

  .mlr-table tbody tr:hover {
    background: rgba(255, 255, 255, 0.03);
  }
</style>
