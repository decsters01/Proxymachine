"""
Demonstração Rápida do Proxygenesis AI
Executa um ciclo completo com poucos proxies para demonstração
"""

import asyncio
import logging
from scraper import ProxyScraper
from checker import ProxyChecker
from trainer import ProxyTrainer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo():
    """Demonstração rápida do sistema"""
    print("🚀 DEMONSTRAÇÃO DO PROXYGENESIS AI")
    print("Sistema Inteligente de Geração e Validação de Proxies")
    print("=" * 60)
    
    # Fase 1: Coleta
    print("\n📥 FASE 1: COLETA DE PROXIES")
    print("-" * 40)
    
    scraper = ProxyScraper()
    proxies = await scraper.collect_all_proxies_async()
    
    print(f"✅ Coletados {len(proxies)} proxies candidatos")
    
    if proxies:
        print("\nPrimeiros 5 proxies encontrados:")
        for i, proxy in enumerate(proxies[:5], 1):
            print(f"  {i}. {proxy}")
    
    # Limitar para demonstração
    test_proxies = proxies[:20] if len(proxies) > 20 else proxies
    print(f"\n🔍 Testando {len(test_proxies)} proxies para demonstração...")
    
    # Fase 2: Validação
    print("\n🔧 FASE 2: VALIDAÇÃO DE PROXIES")
    print("-" * 40)
    
    checker = ProxyChecker()
    results = await checker.validate_proxies(test_proxies)
    
    active_proxies = [r for r in results if r['is_active']]
    print(f"✅ Validação concluída: {len(active_proxies)}/{len(results)} proxies ativos")
    
    if active_proxies:
        print("\nProxies ativos encontrados:")
        for proxy in active_proxies:
            print(f"  ✓ {proxy['proxy']} ({proxy['response_time_ms']}ms)")
    
    # Fase 3: Machine Learning
    print("\n🧠 FASE 3: MACHINE LEARNING")
    print("-" * 40)
    
    trainer = ProxyTrainer()
    
    # Adicionar fonte aos dados para o ML
    for result in results:
        result['source'] = 'demo'
    
    # Criar features
    df = trainer.create_features(results)
    print(f"✅ Features criadas: {df.shape[1]-1} atributos")
    
    # Treinar modelo (se tiver dados suficientes)
    if len(df) >= 10:
        print("📊 Treinando modelo de classificação...")
        metrics = trainer.train_model(df)
        
        if 'error' not in metrics:
            print(f"✅ Modelo treinado com sucesso!")
            print(f"   Acurácia: {metrics['accuracy']:.3f}")
            print(f"   Precisão: {metrics['precision']:.3f}")
            print(f"   Recall: {metrics['recall']:.3f}")
            
            # Mostrar features mais importantes
            importance = trainer.get_feature_importance()
            top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"\nTop 5 features mais importantes:")
            for feature, imp in top_features:
                print(f"   {feature}: {imp:.3f}")
        else:
            print(f"⚠️  Erro no treinamento: {metrics['error']}")
    else:
        print(f"⚠️  Dados insuficientes para treinamento ({len(df)} < 10)")
    
    # Estatísticas finais
    print("\n📊 ESTATÍSTICAS FINAIS")
    print("-" * 40)
    
    stats = checker.get_proxy_stats(results)
    print(f"Total de candidatos: {len(proxies)}")
    print(f"Total testados: {stats['total_tested']}")
    print(f"Proxies ativos: {stats['active_count']}")
    print(f"Taxa de sucesso: {stats['success_rate']:.1f}%")
    
    if stats['active_count'] > 0:
        print(f"Tempo médio de resposta: {stats['avg_response_time_ms']:.1f}ms")
        print(f"Distribuição de anonimato: {stats['anonymity_distribution']}")
    
    print("\n🎉 Demonstração concluída!")
    print("\nPara executar o sistema completo com mais proxies:")
    print("  python3 main.py")

if __name__ == "__main__":
    asyncio.run(demo())