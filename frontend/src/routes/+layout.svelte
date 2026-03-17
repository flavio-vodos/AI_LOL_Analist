<script lang="ts">
  import { page } from '$app/stores';
  import '../app.css';
  let { children } = $props();
</script>

<div class="flex h-screen bg-[#0f172a] text-white overflow-hidden font-sans">
  
  <!-- Sidebar -->
  <aside class="w-64 bg-[#1e293b] flex flex-col border-r border-[#334155] p-6 shrink-0 z-50 shadow-xl">
    <div class="text-xl font-black text-blue-400 mb-8 tracking-wide uppercase">⚡ Predictor AI</div>
    
    <nav class="flex-1 space-y-2">
      <a 
        href="/analytics" 
        class="block px-4 py-3 rounded-lg transition-colors text-sm font-bold tracking-wide { $page.url.pathname === '/analytics' ? 'bg-[#2563eb] bg-opacity-20 text-blue-400 border-l-4 border-blue-500' : 'text-slate-400 hover:bg-[#334155] hover:text-white' }"
      >
        📊 Advanced Analytics
      </a>
      <a 
        href="/" 
        class="block px-4 py-3 rounded-lg transition-colors text-sm font-bold tracking-wide { $page.url.pathname === '/' || $page.url.pathname.includes('/match') ? 'bg-[#2563eb] bg-opacity-20 text-blue-400 border-l-4 border-blue-500' : 'text-slate-400 hover:bg-[#334155] hover:text-white' }"
      >
        🔴 Jogos Ao Vivo
      </a>
    </nav>
    <div class="text-xs text-slate-500 mt-auto opacity-60">Engine: Python & SvelteKit 5</div>
  </aside>

  <!-- Main Viewport -->
  <main class="flex-1 relative overflow-y-auto">
    {@render children()}
  </main>
</div>
