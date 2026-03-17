<script lang="ts">
  const { label, value, tooltip, color = '#3b82f6' } = $props<{
    label: string;
    value: string | number;
    tooltip: string;
    color?: string;
  }>();
</script>

<span class="stats-badge" data-tip={tooltip} style:--badge-color={color}>
  {label}={value}
</span>

<style>
  .stats-badge {
    position: relative;
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: default;
    background-color: color-mix(in srgb, var(--badge-color) 15%, transparent);
    color: var(--badge-color);
    border: 1px solid color-mix(in srgb, var(--badge-color) 40%, transparent);
  }

  .stats-badge::after {
    content: attr(data-tip);
    position: absolute;
    bottom: calc(100% + 6px);
    left: 50%;
    transform: translateX(-50%);
    white-space: nowrap;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 400;
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s ease;
    z-index: 10;
  }

  .stats-badge:hover::after {
    opacity: 1;
  }
</style>
