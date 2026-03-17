<script lang="ts">
  const { text }: { text: string } = $props();
</script>

<div class="explain-box">📖 <b>Como ler:</b> {@html text}</div>

<style>
  .explain-box {
    border-left: 3px solid #3b82f6;
    background: #1e293b;
    color: #cbd5e1;
    padding: 0.75rem 1rem;
    border-radius: 0 0.375rem 0.375rem 0;
    font-size: 0.875rem;
    line-height: 1.6;
    margin: 0.5rem 0;
  }

  .explain-box b {
    color: #93c5fd;
  }
</style>
