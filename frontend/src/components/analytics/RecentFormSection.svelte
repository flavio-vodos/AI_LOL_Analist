<script lang="ts">
  import type { RecentFormSection } from '$lib/types/analytics';
  import DataCommentBox from './DataCommentBox.svelte';

  interface Props {
    data: RecentFormSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();
</script>

<div class="section-card">
  <h3 class="section-title">📊 Forma Recente</h3>

  <div class="form-section">
    <div class="team-form">
      <div class="team-header">
        <span class="team-name t1">{team1}</span>
        <span class="recent-wr t1">WR recente: {data.t1_recent_wr.toFixed(1)}%</span>
      </div>
      <div class="blocks-row">
        {#each data.t1_results as result}
          <div class="wl-block {result === '1' ? 'win' : 'loss'}" title={result === '1' ? 'Vitória' : 'Derrota'}>
            {result === '1' ? 'W' : 'L'}
          </div>
        {/each}
      </div>
    </div>

    <div class="team-form">
      <div class="team-header">
        <span class="team-name t2">{team2}</span>
        <span class="recent-wr t2">WR recente: {data.t2_recent_wr.toFixed(1)}%</span>
      </div>
      <div class="blocks-row">
        {#each data.t2_results as result}
          <div class="wl-block {result === '1' ? 'win' : 'loss'}" title={result === '1' ? 'Vitória' : 'Derrota'}>
            {result === '1' ? 'W' : 'L'}
          </div>
        {/each}
      </div>
    </div>
  </div>

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

  .form-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .team-form {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .team-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .team-name {
    font-size: 0.875rem;
    font-weight: 700;
  }

  .team-name.t1 {
    color: #60a5fa;
  }

  .team-name.t2 {
    color: #f87171;
  }

  .recent-wr {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .recent-wr.t1 {
    background: rgba(59, 130, 246, 0.15);
    color: #93c5fd;
    border: 1px solid rgba(59, 130, 246, 0.3);
  }

  .recent-wr.t2 {
    background: rgba(239, 68, 68, 0.15);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .blocks-row {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .wl-block {
    width: 34px;
    height: 34px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    cursor: default;
    user-select: none;
  }

  .wl-block.win {
    background: rgba(34, 197, 94, 0.25);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.4);
  }

  .wl-block.loss {
    background: rgba(239, 68, 68, 0.25);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
  }
</style>
