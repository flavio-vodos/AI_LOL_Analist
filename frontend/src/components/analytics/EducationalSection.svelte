<script lang="ts">
  // Static component — no props
</script>

<div class="educational-card">
  <h3 class="card-title">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
    </svg>
    📚 Oracle's Elixir: Glossário &amp; Conceitos Essenciais
  </h3>

  <div class="grid">
    <!-- Column 1: Odds Modeling + Draft Projection -->
    <div class="col">
      <h4 class="col-title">Modelagem de Probabilidades (Odds)</h4>
      <p class="col-text">
        Segundo o artigo <em>"What Are the Odds?"</em>, prever estatísticas não é sobre "certezas", mas sobre identificar valor.
        A <strong>Odd Ideal</strong> é calculada matematicamente como
        <code>1 / (Probabilidade% / 100)</code> baseada no histórico.<br /><br />
        Se a odd for <strong>1.50</strong> (66% chance) e a casa oferecer <strong>1.80</strong>, há uma discrepância estatística (+EV).
      </p>

      <h4 class="col-title draft-title">✨ Projeção do Draft</h4>
      <p class="col-text">
        É um multiplicador dinâmico calculado ao isolar o desempenho histórico do Campeão escolhido (Platinum Layer)
        frente à média global de todos os campeões naquela função. Por exemplo, se um time pega <em>Draven</em>, o algoritmo
        percebe que o <strong class="highlight-purple">Multiplicador de First Blood</strong> dele é <em>1.40x</em>. As projeções empurram
        as odds/quantidades originais para refletir a nova agressividade da composição.
      </p>
    </div>

    <!-- Column 2: EGR & MLR -->
    <div class="col">
      <h4 class="col-title">EGR (Early-Game Rating) &amp; MLR (Mid/Late Rating)</h4>
      <p class="col-text">
        <em>EGR</em> estima a probabilidade de um time vencer aos 15 minutos, baseado no controle de primeiros objetivos
        (<strong class="highlight-red">FB%</strong>, <strong class="highlight-yellow">FD%</strong>, <strong class="highlight-purple">HLD%</strong>)
        e vantagem de ouro.<br /><br />
        <em>MLR</em> mede se um time destrói estruturas (Torres, <strong class="highlight-gold">FBN%</strong>, Inibidores) ou perde jogos
        que estava ganhando. Um time com bons Barões mas longa duração sofre para fechar o mapa.
      </p>
    </div>

    <!-- Column 3: Glossary -->
    <div class="col">
      <h4 class="col-title">Glossário de Terminologias</h4>
      <ul class="glossary-list">
        <li><span class="glossary-term">CKPM</span>: Combined Kills Per Minute (Dita a "sangria" ou velocidade do jogo).</li>
        <li><span class="glossary-term">FB% / FD%</span>: First Blood / First Dragon Rate (Controle inicial).</li>
        <li><span class="glossary-term">FBN%</span>: First Baron Rate (Controle de mapa mid-late).</li>
        <li><span class="glossary-term">EGPM</span>: Earned Gold Per Minute (Mede eficiência na fazenda/abates).</li>
        <li><span class="glossary-term">DPM</span>: Damage Per Minute (O dano real trocado com campeões).</li>
      </ul>
    </div>
  </div>
</div>

<style>
  .educational-card {
    background: #1e293b;
    border-radius: 0.75rem;
    padding: 1.5rem;
    border: 1px solid #334155;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }

  .card-title {
    color: #6366f1;
    margin: 0 0 1rem 0;
    font-size: 1.125rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .card-title svg {
    flex-shrink: 0;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.25rem;
  }

  .col {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .col-title {
    color: #cbd5e1;
    margin: 0 0 0.5rem 0;
    font-size: 0.9375rem;
    font-weight: 600;
  }

  .draft-title {
    color: #c4b5fd;
    margin-top: 1rem;
  }

  .col-text {
    color: #94a3b8;
    font-size: 0.85rem;
    line-height: 1.6;
    margin: 0;
  }

  code {
    background: rgba(255, 255, 255, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.8rem;
  }

  .highlight-red {
    color: #ef4444;
  }

  .highlight-yellow {
    color: #fbbf24;
  }

  .highlight-purple {
    color: #c4b5fd;
  }

  .highlight-gold {
    color: #eab308;
  }

  .glossary-list {
    color: #94a3b8;
    font-size: 0.8rem;
    line-height: 1.7;
    margin: 0;
    padding-left: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .glossary-term {
    color: #a5b4fc;
    font-weight: 600;
  }
</style>
