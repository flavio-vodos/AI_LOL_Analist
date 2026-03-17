<script lang="ts">
  import type { ObjectiveCorrelations } from '$lib/types/analytics';

  interface Props {
    data: ObjectiveCorrelations;
  }

  let { data }: Props = $props();

  const conditions = $derived([
    { label: 'Primeiro Barão', value: data.fbaron_wr, icon: '👑', color: '#a78bfa', desc: 'Conquista do 1º Barão' },
    { label: 'Primeira Soul (4 Drags)', value: data.soul_wr, icon: '🔥', color: '#f97316', desc: 'Acúmulo de 4 Dragões' },
    { label: 'Vantagem Ouro (2k @15m)', value: data.large_lead_wr, icon: '💰', color: '#eab308', desc: 'Lead > 2k gold aos 15 min' },
    { label: 'Primeiro Arauto', value: data.fherald_wr, icon: '👾', color: '#c084fc', desc: 'Conquista do 1º Arauto' },
    { label: 'Primeiro Dragão', value: data.fd_wr, icon: '🐉', color: '#fb923c', desc: 'Conquista do 1º Dragão' },
    { label: 'First Blood', value: data.fb_wr, icon: '🩸', color: '#f87171', desc: 'Primeiro Abate da Partida' },
  ]);
</script>

<div class="section-card">
  <h3 class="section-title">📊 Probabilidade de Vitória (Win Conditions Globais)</h3>
  <p class="subtitle">Quanto cada objetivo aumenta a chance de vitória (Base: Dataset Global)</p>

  <div class="grid">
    {#each conditions as item}
      <div class="condition-card" style:--color={item.color}>
        <div class="icon">{item.icon}</div>
        <div class="info">
          <div class="label">{item.label}</div>
          <div class="desc">{item.desc}</div>
        </div>
        <div class="percentage">
          <span class="value">{item.value.toFixed(1)}%</span>
          <div class="bar-track">
            <div class="bar" style:width="{item.value}%"></div>
          </div>
        </div>
      </div>
    {/each}
  </div>

  <div class="footer-note">
    💡 <strong>Insights para Apostas:</strong> Foque em times com alto <strong>FBN%</strong> (Barão) e <strong>Gold@15</strong>. O First Blood é o objetivo menos correlacionado com a vitória final.
  </div>
</div>

<style>
  .section-card {
    background: #1e293b;
    border-radius: 1rem;
    padding: 1.5rem;
    border: 1px solid #334155;
    width: 100%;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
  }

  .section-title {
    color: #f1f5f9;
    font-size: 1.125rem;
    font-weight: 800;
    margin: 0 0 0.25rem 0;
  }

  .subtitle {
    font-size: 0.8125rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
  }

  .condition-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(255, 255, 255, 0.03);
    padding: 1rem;
    border-radius: 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.2s ease;
  }

  .condition-card:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--color);
    transform: translateY(-2px);
  }

  .icon {
    font-size: 1.5rem;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
  }

  .info {
    flex: 1;
  }

  .label {
    font-size: 0.875rem;
    font-weight: 700;
    color: #e2e8f0;
  }

  .desc {
    font-size: 0.6875rem;
    color: #64748b;
  }

  .percentage {
    text-align: right;
    width: 80px;
  }

  .value {
    font-size: 1rem;
    font-weight: 800;
    color: var(--color);
  }

  .bar-track {
    width: 100%;
    height: 4px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 2px;
    margin-top: 4px;
    overflow: hidden;
  }

  .bar {
    height: 100%;
    background: var(--color);
    border-radius: 2px;
  }

  .footer-note {
    margin-top: 1.5rem;
    padding: 1rem;
    background: rgba(59, 130, 246, 0.1);
    border-radius: 0.5rem;
    border-left: 4px solid #3b82f6;
    font-size: 0.8125rem;
    color: #94a3b8;
    line-height: 1.5;
  }

  .footer-note strong {
    color: #60a5fa;
  }
</style>
