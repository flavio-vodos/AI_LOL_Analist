<script lang="ts">
  import type { SideStatEntry } from '$lib/types/analytics';

  interface Props {
    data: Record<string, SideStatEntry[]>;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  const t1_blue = $derived(data.t1.find(s => s.side.toLowerCase() === 'blue'));
  const t1_red = $derived(data.t1.find(s => s.side.toLowerCase() === 'red'));
  const t2_blue = $derived(data.t2.find(s => s.side.toLowerCase() === 'blue'));
  const t2_red = $derived(data.t2.find(s => s.side.toLowerCase() === 'red'));
</script>

<div class="section-card">
    <h3 class="section-title">⚖️ Performance por Lado (Side Bias)</h3>

    <div class="side-grid">
        <!-- Blue Side Column -->
        <div class="side-column blue">
            <div class="side-header blue-text">🟦 BLUE SIDE</div>
            <div class="team-stats">
                <div class="team-stat">
                    <span class="team-name">{team1}</span>
                    {#if t1_blue}
                        <span class="wr-value">{t1_blue.win_rate.toFixed(0)}%</span>
                        <span class="games-count">({t1_blue.wins}/{t1_blue.games})</span>
                    {:else}
                        <span class="no-data">-</span>
                    {/if}
                </div>
                <div class="team-stat">
                    <span class="team-name">{team2}</span>
                    {#if t2_blue}
                        <span class="wr-value">{t2_blue.win_rate.toFixed(0)}%</span>
                        <span class="games-count">({t2_blue.wins}/{t2_blue.games})</span>
                    {:else}
                        <span class="no-data">-</span>
                    {/if}
                </div>
            </div>
        </div>

        <!-- Red Side Column -->
        <div class="side-column red">
            <div class="side-header red-text">🟥 RED SIDE</div>
            <div class="team-stats">
                <div class="team-stat">
                    <span class="team-name">{team1}</span>
                    {#if t1_red}
                        <span class="wr-value">{t1_red.win_rate.toFixed(0)}%</span>
                        <span class="games-count">({t1_red.wins}/{t1_red.games})</span>
                    {:else}
                        <span class="no-data">-</span>
                    {/if}
                </div>
                <div class="team-stat">
                    <span class="team-name">{team2}</span>
                    {#if t2_red}
                        <span class="wr-value">{t2_red.win_rate.toFixed(0)}%</span>
                        <span class="games-count">({t2_red.wins}/{t2_red.games})</span>
                    {:else}
                        <span class="no-data">-</span>
                    {/if}
                </div>
            </div>
        </div>
    </div>

    <p class="section-note">
        Nota: Alguns times possuem escolhas estratégicas que funcionam muito melhor no Red Side (como o counter-pick no Top).
    </p>
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

  .side-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .side-column {
    background: rgba(15, 23, 42, 0.4);
    border-radius: 0.5rem;
    padding: 0.75rem;
    border: 1px solid #334155;
  }

  .side-header {
    font-size: 0.75rem;
    font-weight: 800;
    margin-bottom: 0.75rem;
    text-align: center;
    letter-spacing: 0.05em;
  }

  .blue-text { color: #60a5fa; }
  .red-text { color: #f87171; }

  .team-stats {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .team-stat {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 0.8125rem;
  }

  .team-name {
    color: #94a3b8;
    max-width: 60px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .wr-value {
    font-weight: 700;
    color: #f1f5f9;
  }

  .games-count {
    color: #64748b;
    font-size: 0.6875rem;
  }

  .no-data {
    color: #475569;
  }

  .section-note {
    font-size: 0.75rem;
    color: #64748b;
    font-style: italic;
  }
</style>
