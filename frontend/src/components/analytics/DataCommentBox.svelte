<script lang="ts">
  const { comments }: { comments: string[] } = $props();
</script>

{#if comments && comments.length > 0}
  <div class="data-comment-box">
    <div class="data-comment-box-inner">
      <div class="comment-title"><span class="pulse-dot"></span>💡 Comentário Baseado em Dados</div>
      {#each comments as comment}
        <div class="insight-item">{@html comment}</div>
      {/each}
    </div>
  </div>
{/if}

<style>
  .data-comment-box {
    position: relative;
    padding: 2px;
    border-radius: 0.5rem;
    background: conic-gradient(
      from var(--angle, 0deg),
      #3b82f6,
      #10b981,
      #8b5cf6,
      #3b82f6
    );
    animation: led-rotate 4s linear infinite;
    margin: 0.5rem 0;
  }

  .data-comment-box-inner {
    background: #1e293b;
    border-radius: calc(0.5rem - 2px);
    padding: 0.875rem 1rem;
  }

  .comment-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: #a7f3d0;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  .pulse-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #10b981;
    animation: pulse-emerald 2s infinite;
    flex-shrink: 0;
  }

  .insight-item {
    color: #cbd5e1;
    font-size: 0.875rem;
    line-height: 1.6;
    padding: 0.25rem 0;
  }

  .insight-item + .insight-item {
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    margin-top: 0.25rem;
  }

  @property --angle {
    syntax: '<angle>';
    initial-value: 0deg;
    inherits: false;
  }

  @keyframes led-rotate {
    to {
      --angle: 360deg;
    }
  }

  @keyframes pulse-emerald {
    0%, 100% {
      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
    }
    50% {
      box-shadow: 0 0 10px 4px rgba(16, 185, 129, 0);
    }
  }
</style>
