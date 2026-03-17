<script lang="ts">
  import type { BetEntryData } from '$lib/types/analytics';

  const { entry } = $props<{ entry: BetEntryData }>();
</script>

<details class="bet-entry bet-{entry.risk_tier}">
  <summary>
    {entry.team} — {entry.market} {entry.line} @ <b>{entry.odd.toFixed(2)}x</b>
    ({entry.probability.toFixed(0)}%) [{entry.risk_label}]
    {#if entry.has_draft_projection}<span class="draft-badge">✨ Draft</span>{/if}
  </summary>

  <div class="bet-detail">
    <div class="bet-detail-row"><span class="detail-label">Mercado:</span> {entry.market}</div>
    <div class="bet-detail-row"><span class="detail-label">Time:</span> {entry.team}</div>
    <div class="bet-detail-row"><span class="detail-label">Probabilidade Empírica:</span> {entry.probability.toFixed(1)}%</div>
    <div class="bet-detail-row">
      <span class="detail-label">Odd Justa:</span>
      <span class="odd-badge">{entry.odd.toFixed(2)}x</span>
    </div>
    <div class="bet-detail-row"><span class="detail-label">Classificação:</span> {entry.risk_label}</div>

    {#if entry.has_draft_projection && entry.draft_multiplier != null}
      <div class="bet-detail-row">
        <span class="detail-label">Conselho do Draft:</span>
        Multiplicador {entry.draft_multiplier.toFixed(2)}x aplicado
      </div>
    {/if}

    <div class="bet-formula">
      Odd = 100 / Prob% = 100 / {entry.probability.toFixed(1)}% = {entry.odd.toFixed(2)}x
    </div>

    <div class="bet-explanation">{entry.explanation}</div>
  </div>
</details>

<style>
  .bet-entry {
    border-radius: 6px;
    margin-bottom: 8px;
    border-left: 4px solid #64748b;
    background-color: rgba(15, 23, 42, 0.6);
    transition: transform 0.2s ease, border-color 0.2s ease;
    overflow: hidden;
  }

  .bet-entry:hover {
    transform: translateX(4px);
  }

  /* Risk tier border colors */
  .bet-entry.bet-low {
    border-left-color: #22c55e;
  }

  .bet-entry.bet-med {
    border-left-color: #eab308;
  }

  .bet-entry.bet-high {
    border-left-color: #ef4444;
  }

  .bet-entry.bet-low:hover {
    border-left-color: #16a34a;
  }

  .bet-entry.bet-med:hover {
    border-left-color: #ca8a04;
  }

  .bet-entry.bet-high:hover {
    border-left-color: #dc2626;
  }

  summary {
    padding: 10px 14px;
    cursor: pointer;
    font-size: 0.85rem;
    color: #cbd5e1;
    list-style: none;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    user-select: none;
  }

  summary::-webkit-details-marker {
    display: none;
  }

  summary::before {
    content: '▶';
    font-size: 0.6rem;
    margin-right: 6px;
    color: #64748b;
    transition: transform 0.2s ease;
    flex-shrink: 0;
  }

  details[open] summary::before {
    transform: rotate(90deg);
  }

  summary b {
    color: #f1f5f9;
  }

  .draft-badge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    background-color: rgba(234, 179, 8, 0.15);
    color: #eab308;
    border: 1px solid rgba(234, 179, 8, 0.35);
    margin-left: 4px;
  }

  .bet-detail {
    padding: 10px 14px 14px 14px;
    border-top: 1px solid rgba(100, 116, 139, 0.2);
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .bet-detail-row {
    font-size: 0.8rem;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .detail-label {
    font-weight: 600;
    color: #cbd5e1;
    min-width: 160px;
  }

  .odd-badge {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 700;
    background-color: rgba(234, 179, 8, 0.15);
    color: #eab308;
    border: 1px solid rgba(234, 179, 8, 0.3);
  }

  .bet-formula {
    margin-top: 4px;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 0.78rem;
    font-family: 'Courier New', monospace;
    color: #a3e635;
    background-color: rgba(163, 230, 53, 0.07);
    border: 1px solid rgba(163, 230, 53, 0.15);
  }

  .bet-explanation {
    margin-top: 4px;
    font-size: 0.8rem;
    color: #94a3b8;
    line-height: 1.5;
  }
</style>
