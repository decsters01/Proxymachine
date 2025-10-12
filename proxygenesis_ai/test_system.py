"""
Script de Teste para o Proxygenesis AI
Demonstra o funcionamento de cada módulo individualmente
"""

import asyncio
import logging
from scraper import ProxyScraper
from checker import ProxyChecker
from trainer import ProxyTrainer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scraper():
    """Testa o módulo de scraping"""
    print("🔍 Testando Scraper...")
    print("=" * 50)
    
    scraper = ProxyScraper()
    
    # Testar coleta assíncrona
    print("Coletando proxies de fontes online...")
    proxies = await scraper.collect_all_proxies_async()
    
    print(f"Proxies encontrados: {len(proxies)}")
    
    if proxies:
        print("\nPrimeiros 10 proxies encontrados:")
        for i, proxy in enumerate(proxies[:10], 1):
            print(f"  {i:2d}. {proxy}")
    
    return proxies

async def test_checker(proxies):
    """Testa o módulo de validação"""
    print("\n🔧 Testando Checker...")
    print("=" * 50)
    
    if not proxies:
        print("Nenhum proxy para testar!")
        return []
    
    checker = ProxyChecker()
    
    # Testar apenas os primeiros 5 proxies para não demorar muito
    test_proxies = proxies[:5]
    print(f"Testando {len(test_proxies)} proxies...")
    
    results = await checker.validate_proxies(test_proxies)
    
    print("\nResultados da validação:")
    for result in results:
        status = "✅ ATIVO" if result['is_active'] else "❌ INATIVO"
        print(f"  {result['proxy']}: {status}")
        if result['is_active']:
            print(f"    Tempo: {result['response_time_ms']}ms")
            print(f"    Anonimato: {result['anonymity']}")
        elif result['error']:
            print(f"    Erro: {result['error']}")
    
    # Estatísticas
    stats = checker.get_proxy_stats(results)
    print(f"\nEstatísticas:")
    print(f"  Total testado: {stats['total_tested']}")
    print(f"  Ativos: {stats['active_count']}")
    print(f"  Taxa de sucesso: {stats['success_rate']:.1f}%")
    
    return results

def test_trainer(validation_results):
    """Testa o módulo de machine learning"""
    print("\n🧠 Testando Trainer...")
    print("=" * 50)
    
    if not validation_results:
        print("Nenhum resultado de validação para treinar!")
        return
    
    trainer = ProxyTrainer()
    
    # Criar features
    print("Criando features...")
    df = trainer.create_features(validation_results)
    print(f"DataFrame criado: {df.shape}")
    print(f"Colunas: {list(df.columns)}")
    
    # Treinar modelo
    print("\nTreinando modelo...")
    metrics = trainer.train_model(df)
    
    if 'error' in metrics:
        print(f"Erro no treinamento: {metrics['error']}")
        return
    
    print(f"Modelo treinado com sucesso!")
    print(f"  Acurácia: {metrics['accuracy']:.3f}")
    print(f"  Precisão: {metrics['precision']:.3f}")
    print(f"  Recall: {metrics['recall']:.3f}")
    print(f"  F1-Score: {metrics['f1_score']:.3f}")
    
    # Mostrar importância das features
    print(f"\nTop 10 features mais importantes:")
    feature_importance = trainer.get_feature_importance()
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    for feature, importance in sorted_features[:10]:
        print(f"  {feature}: {importance:.3f}")
    
    # Testar predição
    print(f"\nTestando predição...")
    probabilities = trainer.predict_proxy_probability(validation_results)
    
    print("Probabilidades de ativação:")
    for i, (result, prob) in enumerate(zip(validation_results, probabilities)):
        print(f"  {result['proxy']}: {prob:.3f}")
    
    # Salvar modelo
    trainer.save_model()
    print(f"\nModelo salvo em: models/proxy_classifier.pkl")

async def main():
    """Função principal de teste"""
    print("🚀 Iniciando Testes do Proxygenesis AI")
    print("Sistema Inteligente de Geração e Validação de Proxies")
    print("=" * 60)
    
    try:
        # Teste 1: Scraper
        proxies = await test_scraper()
        
        # Teste 2: Checker
        validation_results = await test_checker(proxies)
        
        # Teste 3: Trainer
        test_trainer(validation_results)
        
        print("\n✅ Todos os testes concluídos com sucesso!")
        print("\nPara executar o sistema completo, use:")
        print("  python main.py")
        
    except Exception as e:
        logger.error(f"Erro durante os testes: {e}")
        print(f"\n❌ Erro durante os testes: {e}")

if __name__ == "__main__":
    asyncio.run(main())