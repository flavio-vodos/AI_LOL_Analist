<script lang="ts">
  const {
    team1,
    team2,
    patchLabel,
    gamesT1,
    gamesT2
  }: {
    team1: string;
    team2: string;
    patchLabel: string;
    gamesT1: number;
    gamesT2: number;
  } = $props();
</script>

<div class="results-header">
  <div class="header-content">
    <h1 class="header-title">📊 Advanced Analytics — Powered by Oracle's Elixir</h1>
    <div class="matchup-badge">
      <span class="team-blue">{team1}</span>
      <span class="vs-separator">VS</span>
      <span class="team-red">{team2}</span>
    </div>
    <div class="header-meta">
      <span class="meta-item">🗂️ Patch: <strong>{patchLabel}</strong></span>
      <span class="meta-separator">·</span>
      <span class="meta-item">
        <span class="team-blue-text">{team1}</span>: <strong>{gamesT1} jogos</strong>
      </span>
      <span class="meta-separator">·</span>
      <span class="meta-item">
        <span class="team-red-text">{team2}</span>: <strong>{gamesT2} jogos</strong>
      </span>
    </div>
  </div>
</div>

<style>
  .results-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    border-bottom: 1px solid rgba(59, 130, 246, 0.2);
    padding: 2rem 1.5rem;
    text-align: center;
  }

  .header-content {
    max-width: 800px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .header-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0;
    letter-spacing: 0.01em;
  }

  .matchup-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 9999px;
    padding: 0.5rem 1.5rem;
    font-size: 1.125rem;
    font-weight: 700;
  }

  .team-blue {
    color: #60a5fa;
  }

  .vs-separator {
    color: #94a3b8;
    font-size: 0.875rem;
    font-weight: 600;
    letter-spacing: 0.1em;
  }

  .team-red {
    color: #f87171;
  }

  .header-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: #94a3b8;
  }

  .meta-item {
    color: #94a3b8;
  }

  .meta-item strong {
    color: #cbd5e1;
  }

  .meta-separator {
    color: #475569;
  }

  .team-blue-text {
    color: #60a5fa;
  }

  .team-red-text {
    color: #f87171;
  }
</style>
