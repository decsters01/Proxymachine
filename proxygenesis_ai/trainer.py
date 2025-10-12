"""
Módulo de Machine Learning para Classificação de Proxies
Implementa a Fase 3 do Proxygenesis AI
"""

import pandas as pd
import numpy as np
import joblib
import logging
from typing import List, Dict, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler
import ipaddress
import re
from settings import ML_CONFIG, COMMON_PORTS, PATHS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyTrainer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_trained = False
        
    def create_features(self, proxy_data: List[Dict]) -> pd.DataFrame:
        """
        Cria features (atributos) para treinamento do modelo
        
        Args:
            proxy_data: Lista de dicionários com dados dos proxies
            
        Returns:
            DataFrame com features e target
        """
        logger.info(f"Criando features para {len(proxy_data)} proxies")
        
        features_list = []
        
        for data in proxy_data:
            proxy = data.get('proxy', '')
            is_active = data.get('is_active', False)
            response_time = data.get('response_time_ms', 0)
            anonymity = data.get('anonymity', 'unknown')
            source = data.get('source', 'unknown')
            
            # Extrair IP e porta
            if ':' in proxy:
                ip, port = proxy.split(':', 1)
            else:
                continue
            
            # Features básicas do IP
            ip_features = self._extract_ip_features(ip)
            
            # Features da porta
            port_features = self._extract_port_features(port)
            
            # Features de performance
            performance_features = self._extract_performance_features(response_time, is_active)
            
            # Features de anonimato
            anonymity_features = self._extract_anonymity_features(anonymity)
            
            # Features da fonte
            source_features = self._extract_source_features(source)
            
            # Combinar todas as features
            feature_dict = {
                **ip_features,
                **port_features,
                **performance_features,
                **anonymity_features,
                **source_features,
                'is_active': 1 if is_active else 0
            }
            
            features_list.append(feature_dict)
        
        df = pd.DataFrame(features_list)
        
        # Garantir que todas as colunas numéricas existam
        self._ensure_numeric_columns(df)
        
        logger.info(f"Features criadas: {df.shape[1]-1} features + target")
        return df
    
    def _extract_ip_features(self, ip: str) -> Dict:
        """Extrai features do endereço IP"""
        features = {}
        
        try:
            # Octetos do IP
            octets = ip.split('.')
            for i, octet in enumerate(octets, 1):
                features[f'octet_{i}'] = int(octet)
            
            # Soma dos octetos
            features['ip_sum'] = sum(int(octet) for octet in octets)
            
            # Média dos octetos
            features['ip_mean'] = np.mean([int(octet) for octet in octets])
            
            # Desvio padrão dos octetos
            features['ip_std'] = np.std([int(octet) for octet in octets])
            
            # IP é privado?
            try:
                ip_obj = ipaddress.ip_address(ip)
                features['is_private_ip'] = 1 if ip_obj.is_private else 0
                features['is_loopback'] = 1 if ip_obj.is_loopback else 0
                features['is_multicast'] = 1 if ip_obj.is_multicast else 0
            except:
                features['is_private_ip'] = 0
                features['is_loopback'] = 0
                features['is_multicast'] = 0
            
            # Padrões no IP
            features['has_repeated_octets'] = 1 if len(set(octets)) < len(octets) else 0
            features['has_sequential_octets'] = 1 if self._has_sequential_octets(octets) else 0
            
        except Exception as e:
            logger.warning(f"Erro ao extrair features do IP {ip}: {e}")
            # Valores padrão
            for i in range(1, 5):
                features[f'octet_{i}'] = 0
            features.update({
                'ip_sum': 0, 'ip_mean': 0, 'ip_std': 0,
                'is_private_ip': 0, 'is_loopback': 0, 'is_multicast': 0,
                'has_repeated_octets': 0, 'has_sequential_octets': 0
            })
        
        return features
    
    def _extract_port_features(self, port: str) -> Dict:
        """Extrai features da porta"""
        features = {}
        
        try:
            port_num = int(port)
            features['port'] = port_num
            
            # Porta é comum?
            features['is_common_port'] = 1 if port_num in COMMON_PORTS else 0
            
            # Categorias de porta
            features['is_http_port'] = 1 if port_num in [80, 8080, 8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010] else 0
            features['is_https_port'] = 1 if port_num in [443, 8443] else 0
            features['is_socks_port'] = 1 if port_num in [1080, 1081] else 0
            features['is_squid_port'] = 1 if port_num in [3128, 3129] else 0
            
            # Faixas de porta
            features['is_well_known'] = 1 if 1 <= port_num <= 1023 else 0
            features['is_registered'] = 1 if 1024 <= port_num <= 49151 else 0
            features['is_dynamic'] = 1 if 49152 <= port_num <= 65535 else 0
            
            # Características numéricas
            features['port_is_even'] = 1 if port_num % 2 == 0 else 0
            features['port_ends_in_zero'] = 1 if port_num % 10 == 0 else 0
            features['port_has_repeated_digits'] = 1 if self._has_repeated_digits(str(port_num)) else 0
            
        except Exception as e:
            logger.warning(f"Erro ao extrair features da porta {port}: {e}")
            features = {
                'port': 0, 'is_common_port': 0, 'is_http_port': 0, 'is_https_port': 0,
                'is_socks_port': 0, 'is_squid_port': 0, 'is_well_known': 0,
                'is_registered': 0, 'is_dynamic': 0, 'port_is_even': 0,
                'port_ends_in_zero': 0, 'port_has_repeated_digits': 0
            }
        
        return features
    
    def _extract_performance_features(self, response_time: int, is_active: bool) -> Dict:
        """Extrai features de performance"""
        return {
            'response_time_ms': response_time,
            'is_fast_response': 1 if response_time < 1000 else 0,  # < 1s
            'is_medium_response': 1 if 1000 <= response_time < 5000 else 0,  # 1-5s
            'is_slow_response': 1 if response_time >= 5000 else 0,  # >= 5s
            'has_response_time': 1 if response_time > 0 else 0
        }
    
    def _extract_anonymity_features(self, anonymity: str) -> Dict:
        """Extrai features de anonimato"""
        anonymity_map = {
            'elite': 3,
            'anonymous': 2,
            'transparent': 1,
            'unknown': 0
        }
        
        return {
            'anonymity_level': anonymity_map.get(anonymity, 0),
            'is_elite': 1 if anonymity == 'elite' else 0,
            'is_anonymous': 1 if anonymity == 'anonymous' else 0,
            'is_transparent': 1 if anonymity == 'transparent' else 0,
            'is_unknown_anonymity': 1 if anonymity == 'unknown' else 0
        }
    
    def _extract_source_features(self, source: str) -> Dict:
        """Extrai features da fonte do proxy"""
        # Features baseadas no domínio da fonte
        features = {
            'source_has_github': 1 if 'github' in source.lower() else 0,
            'source_has_raw': 1 if 'raw' in source.lower() else 0,
            'source_has_proxy': 1 if 'proxy' in source.lower() else 0,
            'source_has_list': 1 if 'list' in source.lower() else 0,
            'source_length': len(source)
        }
        
        return features
    
    def _has_sequential_octets(self, octets: List[str]) -> bool:
        """Verifica se os octetos são sequenciais"""
        try:
            nums = [int(octet) for octet in octets]
            return all(nums[i] == nums[i-1] + 1 for i in range(1, len(nums)))
        except:
            return False
    
    def _has_repeated_digits(self, text: str) -> bool:
        """Verifica se há dígitos repetidos"""
        return len(set(text)) < len(text)
    
    def _ensure_numeric_columns(self, df: pd.DataFrame):
        """Garante que todas as colunas sejam numéricas"""
        for col in df.columns:
            if col != 'is_active' and df[col].dtype == 'object':
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    def train_model(self, dataframe: pd.DataFrame) -> Dict:
        """
        Treina o modelo de classificação
        
        Args:
            dataframe: DataFrame com features e target
            
        Returns:
            Dicionário com métricas de performance
        """
        logger.info("Iniciando treinamento do modelo")
        
        if len(dataframe) < 10:  # Mínimo de 10 amostras para teste
            logger.warning(f"Dados insuficientes para treinamento: {len(dataframe)} < 10")
            return {'error': 'Dados insuficientes'}
        
        # Separar features e target
        X = dataframe.drop('is_active', axis=1)
        y = dataframe['is_active']
        
        # Salvar nomes das colunas
        self.feature_columns = X.columns.tolist()
        
        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=ML_CONFIG['test_size'], 
            random_state=ML_CONFIG['random_state'],
            stratify=y
        )
        
        # Normalizar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Criar e treinar modelo
        self.model = RandomForestClassifier(
            n_estimators=ML_CONFIG['n_estimators'],
            max_depth=ML_CONFIG['max_depth'],
            min_samples_split=ML_CONFIG['min_samples_split'],
            min_samples_leaf=ML_CONFIG['min_samples_leaf'],
            random_state=ML_CONFIG['random_state']
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Fazer previsões
        y_pred = self.model.predict(X_test_scaled)
        
        # Verificar se há múltiplas classes
        proba = self.model.predict_proba(X_test_scaled)
        if proba.shape[1] > 1:
            y_pred_proba = proba[:, 1]
        else:
            y_pred_proba = proba[:, 0]
        
        # Calcular métricas
        accuracy = accuracy_score(y_test, y_pred)
        
        # Relatório de classificação
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Matriz de confusão
        cm = confusion_matrix(y_test, y_pred)
        
        self.is_trained = True
        
        # Verificar se há classe '1' no relatório
        if '1' in report:
            precision = report['1']['precision']
            recall = report['1']['recall']
            f1_score = report['1']['f1-score']
        else:
            # Se não há classe '1', usar valores da classe '0' ou 0
            if '0' in report:
                precision = report['0']['precision']
                recall = report['0']['recall']
                f1_score = report['0']['f1-score']
            else:
                precision = 0.0
                recall = 0.0
                f1_score = 0.0
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'confusion_matrix': cm.tolist(),
            'feature_importance': dict(zip(self.feature_columns, self.model.feature_importances_)),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        logger.info(f"Modelo treinado com sucesso. Acurácia: {accuracy:.3f}")
        return metrics
    
    def predict_proxy_probability(self, proxy_data: List[Dict]) -> List[float]:
        """
        Prediz a probabilidade de proxies serem ativos
        
        Args:
            proxy_data: Lista de dados dos proxies
            
        Returns:
            Lista de probabilidades
        """
        if not self.is_trained:
            logger.error("Modelo não foi treinado ainda")
            return [0.0] * len(proxy_data)
        
        # Criar features
        df = self.create_features(proxy_data)
        
        # Remover target se existir
        if 'is_active' in df.columns:
            X = df.drop('is_active', axis=1)
        else:
            X = df
        
        # Garantir que as colunas estejam na mesma ordem
        X = X.reindex(columns=self.feature_columns, fill_value=0)
        
        # Normalizar
        X_scaled = self.scaler.transform(X)
        
        # Fazer previsões
        proba = self.model.predict_proba(X_scaled)
        if proba.shape[1] > 1:
            probabilities = proba[:, 1]
        else:
            probabilities = proba[:, 0]
        
        return probabilities.tolist()
    
    def save_model(self, filepath: str = None):
        """Salva o modelo treinado"""
        if not self.is_trained:
            logger.error("Nenhum modelo treinado para salvar")
            return
        
        if filepath is None:
            filepath = PATHS['model_file']
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Modelo salvo em: {filepath}")
    
    def load_model(self, filepath: str = None):
        """Carrega um modelo treinado"""
        if filepath is None:
            filepath = PATHS['model_file']
        
        try:
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Modelo carregado de: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return False
    
    def get_feature_importance(self) -> Dict:
        """Retorna a importância das features"""
        if not self.is_trained:
            return {}
        
        return dict(zip(self.feature_columns, self.model.feature_importances_))

def main():
    """Função principal para teste do trainer"""
    trainer = ProxyTrainer()
    
    # Dados de exemplo
    sample_data = [
        {'proxy': '192.168.1.1:8080', 'is_active': True, 'response_time_ms': 500, 'anonymity': 'elite', 'source': 'github.com'},
        {'proxy': '10.0.0.1:3128', 'is_active': False, 'response_time_ms': 0, 'anonymity': 'unknown', 'source': 'proxy-list.com'},
        {'proxy': '8.8.8.8:80', 'is_active': True, 'response_time_ms': 200, 'anonymity': 'transparent', 'source': 'raw.githubusercontent.com'},
        {'proxy': '1.1.1.1:443', 'is_active': True, 'response_time_ms': 300, 'anonymity': 'anonymous', 'source': 'free-proxy-list.net'}
    ]
    
    print("Testando criação de features...")
    df = trainer.create_features(sample_data)
    print(f"DataFrame criado: {df.shape}")
    print(f"Colunas: {list(df.columns)}")
    
    print("\nTestando treinamento...")
    metrics = trainer.train_model(df)
    print(f"Métricas: {metrics}")
    
    print("\nTestando previsão...")
    probabilities = trainer.predict_proxy_probability(sample_data)
    for i, prob in enumerate(probabilities):
        print(f"{sample_data[i]['proxy']}: {prob:.3f}")

if __name__ == "__main__":
    main()