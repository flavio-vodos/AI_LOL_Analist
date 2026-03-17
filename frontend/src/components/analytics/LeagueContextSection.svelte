<script lang="ts">
  import type { LeagueContextSection } from '$lib/types/analytics';

  interface Props {
    data: LeagueContextSection;
  }

  let { data }: Props = $props();
</script>

<div class="section-card">
  <div class="header">
    <h3 class="section-title">🌍 Contexto da Liga: {data.league}</h3>
    <span class="sample-badge">Amostra: {data.total_games_analyzed} jogos</span>
  </div>

  <div class="baseline-stats">
    <div class="baseline-item">
        <span class="label">Média Abates:</span>
        <span class="value">{data.avg_total_kills.toFixed(1)}</span>
    </div>
    <div class="baseline-item">
        <span class="label">Side Bias (Blue WR):</span>
        <span class="value">{data.blue_win_rate.toFixed(1)}%</span>
    </div>
    <div class="baseline-item">
        <span class="label">Duração Média:</span>
        <span class="value">{data.avg_duration.toFixed(0)}m</span>
    </div>
  </div>

  <div class="insights-list">
    {#each data.insights as insight}
        <div class="insight-item">
            {@html insight}
        </div>
    {/each}
  </div>
</div>

<style>
  .section-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-radius: 0.75rem;
    padding: 1.25rem;
    border: 1px solid #1e40af; /* Azul para contexto global */
    width: 100%;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .section-title {
    color: #60a5fa;
    font-size: 0.9375rem;
    font-weight: 800;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }

  .sample-badge {
    background: rgba(96, 165, 250, 0.1);
    color: #60a5fa;
    font-size: 0.625rem;
    padding: 0.125rem 0.5rem;
    border-radius: 9999px;
    border: 1px solid rgba(96, 165, 250, 0.2);
  }

  .baseline-stats {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  }

  .baseline-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .label {
    font-size: 0.6875rem;
    color: #64748b;
    font-weight: 600;
  }

  .value {
    font-size: 1rem;
    font-weight: 700;
    color: #e2e8f0;
  }

  .insights-list {
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
  }

  .insight-item {
    font-size: 0.8125rem;
    color: #cbd5e1;
    line-height: 1.4;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 0.375rem;
  }
</style>
