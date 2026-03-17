<script lang="ts">
  import type { SeriesSection } from '$lib/types/analytics';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';

  interface Props {
    data: SeriesSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  // Combina os dados para facilitar a renderização lado a lado
  const maxGames = $derived(Math.max(
    ...data.t1_series.map(s => s.game),
    ...data.t2_series.map(s => s.game),
    0
  ));

  const gameNumbers = $derived(Array.from({ length: maxGames }, (_, i) => i + 1));

  function getStat(series: any[], game: number) {
    return series.find(s => s.game === game);
  }
</script>

<div class="section-card">
  <h3 class="section-title">📊 Series Performance (Insights por Mapa)</h3>

  <div class="table-container">
    <table class="series-table">
      <thead>
        <tr>
          <th class="map-col">Mapa</th>
          <th class="team-col t1">{team1}</th>
          <th class="team-col t2">{team2}</th>
        </tr>
      </thead>
      <tbody>
        {#each gameNumbers as game}
          {@const s1 = getStat(data.t1_series, game)}
          {@const s2 = getStat(data.t2_series, game)}
          <tr class="game-row">
            <td class="map-num">Game {game}</td>
            <td class="stat-cell t1">
              {#if s1}
                <div class="main-stat">{s1.win_rate.toFixed(0)}% WR</div>
                <div class="sub-stat">{s1.avg_kills.toFixed(1)} Kills | {s1.avg_duration_min.toFixed(0)}m</div>
                <div class="meta-stat">{s1.matches} jogos</div>
              {:else}
                <span class="no-data">-</span>
              {/if}
            </td>
            <td class="stat-cell t2">
              {#if s2}
                <div class="main-stat">{s2.win_rate.toFixed(0)}% WR</div>
                <div class="sub-stat">{s2.avg_kills.toFixed(1)} Kills | {s2.avg_duration_min.toFixed(0)}m</div>
                <div class="meta-stat">{s2.matches} jogos</div>
              {:else}
                <span class="no-data">-</span>
              {/if}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <p class="section-note">
    Dica: Mapas decisivos (como o Jogo 5) frequentemente mostram variações drásticas em agressividade e tempo de jogo.
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
    border-left: 3px solid #8b5cf6; /* Roxo para Séries */
    width: 100%;
  }

  .section-title {
    color: #a78bfa;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .table-container {
    overflow-x: auto;
    margin-bottom: 1rem;
    background: rgba(139, 92, 246, 0.05);
    border-radius: 0.5rem;
    border: 1px solid rgba(139, 92, 246, 0.1);
  }

  .series-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    color: #e2e8f0;
  }

  .series-table th {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #334155;
    font-weight: 600;
  }

  .map-col {
    width: 80px;
    color: #94a3b8;
  }

  .team-col.t1 {
    color: #60a5fa;
  }

  .team-col.t2 {
    color: #f87171;
  }

  .series-table td {
    padding: 0.75rem;
    vertical-align: top;
    border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  }

  .map-num {
    font-weight: 700;
    color: #64748b;
  }

  .stat-cell {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .main-stat {
    font-size: 0.9375rem;
    font-weight: 700;
  }

  .t1 .main-stat { color: #93c5fd; }
  .t2 .main-stat { color: #fca5a5; }

  .sub-stat {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .meta-stat {
    font-size: 0.6875rem;
    color: #64748b;
    font-style: italic;
  }

  .no-data {
    color: #475569;
  }

  .section-note {
    font-size: 0.75rem;
    color: #64748b;
    margin-bottom: 1rem;
    font-style: italic;
  }
</style>
