"""
Demonstração da Abordagem Híbrida do Proxygenesis AI
Mostra a diferença entre coleta passiva e descoberta ativa
"""

import asyncio
import logging
from hybrid_collector import HybridCollector
from checker import ProxyChecker
from trainer import ProxyTrainer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_hybrid_approach():
    """Demonstração da abordagem híbrida"""
    print("🚀 DEMONSTRAÇÃO DA ABORDAGEM HÍBRIDA")
    print("Proxygenesis AI - Descoberta Ativa vs Coleta Passiva")
    print("=" * 70)
    
    # Criar coletor híbrido
    collector = HybridCollector(shodan_api_key=None)  # Sem Shodan para demonstração
    
    print("\n📊 COMPARAÇÃO DE MÉTODOS DE DESCOBERTA")
    print("-" * 50)
    
    # Método 1: Apenas Coleta Passiva (método original)
    print("\n1️⃣ COLETA PASSIVA (Método Original)")
    print("   - Listas públicas de proxies")
    print("   - Fóruns e sites especializados")
    print("   - GitHub repositories")
    
    # Simular coleta passiva
    collector.enable_port_scanning = False
    collector.enable_search_dorking = False
    collector.enable_public_lists = True
    
    passive_results = await collector.collect_all_sources()
    passive_count = sum(len(proxies) for proxies in passive_results.values())
    
    print(f"   ✅ Resultado: {passive_count} proxies encontrados")
    
    # Método 2: Descoberta Ativa
    print("\n2️⃣ DESCOBERTA ATIVA (Método Avançado)")
    print("   - Varredura de portas (masscan)")
    print("   - Google Dorks")
    print("   - Shodan API")
    print("   - Pastebin mining")
    
    # Habilitar todos os métodos
    collector.enable_port_scanning = True
    collector.enable_search_dorking = True
    collector.enable_public_lists = True
    
    active_results = await collector.collect_all_sources()
    active_count = sum(len(proxies) for proxies in active_results.values())
    
    print(f"   ✅ Resultado: {active_count} proxies encontrados")
    
    # Comparação
    print(f"\n📈 COMPARAÇÃO:")
    print(f"   Coleta Passiva: {passive_count} proxies")
    print(f"   Descoberta Ativa: {active_count} proxies")
    print(f"   Melhoria: {((active_count - passive_count) / max(passive_count, 1) * 100):.1f}%")
    
    # Análise de Qualidade
    print(f"\n🔍 ANÁLISE DE QUALIDADE")
    print("-" * 30)
    
    # Consolidar candidatos
    candidates = collector.consolidate_candidates(active_results)
    
    # Análise por fonte
    source_analysis = {}
    for candidate in candidates:
        source = candidate['source']
        if source not in source_analysis:
            source_analysis[source] = {
                'count': 0,
                'avg_quality': 0,
                'total_quality': 0
            }
        
        source_analysis[source]['count'] += 1
        source_analysis[source]['total_quality'] += candidate['quality_score']
    
    # Calcular médias
    for source, data in source_analysis.items():
        data['avg_quality'] = data['total_quality'] / data['count']
    
    print("Qualidade por fonte:")
    for source, data in sorted(source_analysis.items(), key=lambda x: x[1]['avg_quality'], reverse=True):
        print(f"   {source:15}: {data['count']:4d} proxies, qualidade média: {data['avg_quality']:.3f}")
    
    # Análise por método de descoberta
    method_analysis = {}
    for candidate in candidates:
        method = candidate['discovery_method']
        if method not in method_analysis:
            method_analysis[method] = {
                'count': 0,
                'avg_quality': 0,
                'total_quality': 0
            }
        
        method_analysis[method]['count'] += 1
        method_analysis[method]['total_quality'] += candidate['quality_score']
    
    # Calcular médias
    for method, data in method_analysis.items():
        data['avg_quality'] = data['total_quality'] / data['count']
    
    print("\nQualidade por método de descoberta:")
    for method, data in sorted(method_analysis.items(), key=lambda x: x[1]['avg_quality'], reverse=True):
        print(f"   {method:20}: {data['count']:4d} proxies, qualidade média: {data['avg_quality']:.3f}")
    
    # Priorização Inteligente
    print(f"\n🎯 PRIORIZAÇÃO INTELIGENTE")
    print("-" * 30)
    
    # Priorizar candidatos
    prioritized = collector.prioritize_candidates(candidates, max_candidates=20)
    
    print("Top 10 candidatos priorizados:")
    for i, candidate in enumerate(prioritized[:10], 1):
        print(f"   {i:2d}. {candidate['proxy']:20} "
              f"(fonte: {candidate['source']:12}, "
              f"qualidade: {candidate['quality_score']:.3f})")
    
    # Validação de Amostra
    print(f"\n🔧 VALIDAÇÃO DE AMOSTRA")
    print("-" * 30)
    
    # Testar apenas os top 5 para demonstração
    test_candidates = [candidate['proxy'] for candidate in prioritized[:5]]
    
    checker = ProxyChecker()
    validation_results = await checker.validate_proxies(test_candidates)
    
    active_proxies = [r for r in validation_results if r['is_active']]
    
    print(f"Testados: {len(validation_results)} proxies")
    print(f"Ativos: {len(active_proxies)} proxies")
    print(f"Taxa de sucesso: {(len(active_proxies) / len(validation_results) * 100):.1f}%")
    
    if active_proxies:
        print("\nProxies ativos encontrados:")
        for proxy in active_proxies:
            print(f"   ✓ {proxy['proxy']} ({proxy['response_time_ms']}ms)")
    
    # Machine Learning com Features Avançadas
    print(f"\n🧠 MACHINE LEARNING AVANÇADO")
    print("-" * 30)
    
    if len(validation_results) >= 10:
        trainer = ProxyTrainer()
        
        # Adicionar metadados aos resultados
        for result in validation_results:
            proxy = result['proxy']
            # Encontrar metadados do candidato
            for candidate in candidates:
                if candidate['proxy'] == proxy:
                    result.update({
                        'source': candidate['source'],
                        'discovery_method': candidate['discovery_method'],
                        'quality_score': candidate['quality_score']
                    })
                    break
        
        # Criar features
        df = trainer.create_features(validation_results)
        print(f"Features criadas: {df.shape[1]-1} atributos")
        
        # Treinar modelo
        metrics = trainer.train_model(df)
        
        if 'error' not in metrics:
            print(f"Modelo treinado com sucesso!")
            print(f"   Acurácia: {metrics['accuracy']:.3f}")
            print(f"   Precisão: {metrics['precision']:.3f}")
            print(f"   Recall: {metrics['recall']:.3f}")
            
            # Mostrar features mais importantes
            importance = trainer.get_feature_importance()
            top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
            print(f"\nTop 10 features mais importantes:")
            for feature, imp in top_features:
                print(f"   {feature:25}: {imp:.3f}")
        else:
            print(f"Erro no treinamento: {metrics['error']}")
    else:
        print("Dados insuficientes para treinamento de ML")
    
    # Conclusões
    print(f"\n🎉 CONCLUSÕES")
    print("=" * 50)
    print("✅ A abordagem híbrida combina:")
    print("   • Coleta passiva (listas públicas)")
    print("   • Descoberta ativa (varredura de portas)")
    print("   • Busca avançada (Google Dorks, Shodan)")
    print("   • Priorização inteligente baseada em qualidade")
    print("   • Machine Learning com features avançadas")
    print("\n🚀 Resultado: Sistema muito mais eficiente e inteligente!")

async def main():
    """Função principal"""
    try:
        await demo_hybrid_approach()
    except Exception as e:
        logger.error(f"Erro na demonstração: {e}")
        print(f"\n❌ Erro na demonstração: {e}")

if __name__ == "__main__":
    asyncio.run(main())