import sys
import subprocess
import os
import time
from pipeline.controller import executar_pipeline_completo

def run_servers():
    """Lança o backend (FastAPI) e o frontend (SvelteKit) em subprocessos e os mantém rodando."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"\n🌐 Iniciando os servidores da Aplicação em {project_root}...")
    
    # 1. Inicia o Backend Python (FastAPI via Uvicorn)
    api_path = os.path.join(project_root, "api.py")
    backend_process = subprocess.Popen(
        [sys.executable, api_path],
        cwd=project_root,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Dá um tempo pro backend subir
    time.sleep(2)
    
    # 2. Inicia o Frontend SvelteKit (via npm)
    frontend_dir = os.path.join(project_root, "frontend")

    if not os.path.exists(frontend_dir):
        print(f"❌ Erro: Diretório frontend não encontrado em {frontend_dir}")
        backend_process.terminate()
        return

    # Garante que o diretório do Node.js está no PATH do processo filho
    node_dir = r"C:\Program Files\nodejs"
    env = os.environ.copy()
    if os.name == "nt" and node_dir not in env.get("PATH", ""):
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")

    if os.name == "nt":
        # Tentamos encontrar o npm.cmd automaticamente ou usar o caminho padrão
        npm_cmd = "npm.cmd run dev"
    else:
        npm_cmd = "npm run dev"

    frontend_process = subprocess.Popen(
        npm_cmd,
        cwd=frontend_dir,
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True,
        env=env
    )
    
    print("\n✅ Aplicação rodando!")
    print("👉 Acesse o Frontend em: http://localhost:5173")
    print("👉 A API está rodando em: http://localhost:8000")
    print("\nPressione Ctrl+C para encerrar todos os servidores.")
    
    try:
        # Aguarda infinitamente até que os processos sejam interrompidos ou encerrem
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando servidores...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("Servidores encerrados com sucesso.")

if __name__ == "__main__":
    # Impede a criação de arquivos __pycache__ e .pyc
    sys.dont_write_bytecode = True
    
    # Garante que estamos rodando a partir da pasta raiz do projeto
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    print("🚀 Iniciando Pipeline Automático de Processamento de Dados...")
    resultado_pipeline = executar_pipeline_completo()
    print(resultado_pipeline)
    
    # Inicia os servidores Web e de API simultaneamente
    run_servers()
