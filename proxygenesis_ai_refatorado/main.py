#!/usr/bin/env python3
"""
Script Principal do Proxygenesis AI Refatorado

Demonstra o uso da nova estrutura simplificada com menos módulos e mais inteligência.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from proxygenesis_ai_refatorado import ProxygenesisAI, Config


async def main():
    """Função principal de demonstração"""
    print("=" * 60)
    print("🚀 PROXYGENESIS AI - VERSÃO RE FATORADA")
    print("=" * 60)
    print()
    print("✨ Melhorias da nova versão:")
    print("  • Menos módulos (de 15+ para 3 principais)")
    print("  • Código mais coeso e fácil de manter")
    print("  • Mesma funcionalidade completa")
    print("  • Configurações unificadas em dataclass")
    print("  • Tipagem moderna com dataclasses e type hints")
    print()
    print("=" * 60)
    
    # Criar configuração personalizada (opcional)
    config = Config(
        max_candidates_per_cycle=5000,
        top_candidates_to_test=1000,
        retrain_frequency=3,
        min_training_samples=500,
    )
    
    # Criar instância do sistema
    print("\n📦 Inicializando sistema...")
    system = ProxygenesisAI(config=config)
    
    # Mostrar estatísticas iniciais
    initial_stats = system.get_stats()
    print(f"✅ Sistema inicializado!")
    print(f"   Modelo treinado: {'Sim' if initial_stats.get('trained', False) else 'Não'}")
    print()
    
    # Executar ciclo de demonstração
    print("🔄 Executando ciclo de demonstração...")
    print("-" * 60)
    
    try:
        # Executar apenas 1 ciclo para demonstração
        cycle_stats = await system.run_cycle()
        
        print()
        print("=" * 60)
        print("📊 RESULTADOS DO CICLO")
        print("=" * 60)
        print(f"Ciclo: {cycle_stats['cycle']}")
        print(f"Duração: {cycle_stats.get('duration', 0):.1f}s")
        print(f"Candidatos coletados: {cycle_stats.get('collected', 0)}")
        print(f"Candidatos testados: {cycle_stats.get('tested', 0)}")
        print(f"Proxies ativos encontrados: {cycle_stats.get('active', 0)}")
        print(f"Taxa de sucesso: {cycle_stats.get('rate', 0):.1f}%")
        if cycle_stats.get('retrained'):
            print("Modelo retreinado: ✓")
        print("=" * 60)
        
        # Mostrar estatísticas finais
        final_stats = system.get_stats()
        print()
        print("📈 ESTATÍSTICAS GERAIS")
        print("=" * 60)
        print(f"Ciclos completados: {final_stats.get('cycles', 0)}")
        print(f"Total de candidatos: {final_stats.get('found', 0)}")
        print(f"Total validados: {final_stats.get('validated', 0)}")
        print(f"Total ativos: {final_stats.get('active', 0)}")
        print(f"Sucesso geral: {final_stats.get('rate', 0):.1f}%")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro na execução: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print()
    print("✨ Demonstração concluída com sucesso!")
    print()
    print("📚 Para usar em produção:")
    print("   from proxygenesis_ai_refatorado import ProxygenesisAI, Config")
    print()
    print("   config = Config()")
    print("   system = ProxygenesisAI(config)")
    print("   await system.run_continuous(max_cycles=10)")
    print()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
