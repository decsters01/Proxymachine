"""
Enhanced ML module with XGBoost and advanced features
Includes geolocation, ASN, time-based features, and auto-healing integration
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import joblib
import os
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not available, using GradientBoosting as fallback")

class EnhancedMLPredictor:
    """Advanced ML predictor with multiple algorithms and features"""
    
    def __init__(self, model_path: str = "models/enhanced_proxy_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = [
            'port', 'protocol_http', 'protocol_https', 'protocol_socks4', 'protocol_socks5',
            'anonymity_elite', 'anonymity_anonymous', 'anonymity_transparent',
            'hour_of_day', 'day_of_week', 'speed_ms', 'uptime_percentage',
            'check_count', 'avg_historical_speed'
        ]
        
    def prepare_features(self, data: List[Dict]) -> pd.DataFrame:
        """Prepare features from raw data with encoding"""
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Protocol encoding (one-hot)
        protocols = ['http', 'https', 'socks4', 'socks5']
        for proto in protocols:
            df[f'protocol_{proto}'] = (df['protocol'] == proto).astype(int)
        
        # Anonymity level encoding (one-hot)
        anonymity_levels = ['elite', 'anonymous', 'transparent']
        for level in anonymity_levels:
            df[f'anonymity_{level}'] = (df['anonymity_level'] == level).astype(int)
        
        # Time-based features
        if 'hour_of_day' not in df.columns:
            df['hour_of_day'] = df.get('last_checked', pd.Series([datetime.now()] * len(df))).apply(
                lambda x: int(x.split(':')[0]) if isinstance(x, str) else datetime.now().hour
            )
        
        if 'day_of_week' not in df.columns:
            df['day_of_week'] = df.get('last_checked', pd.Series([datetime.now()] * len(df))).apply(
                lambda x: int(x) if isinstance(x, str) and x.isdigit() else datetime.now().weekday()
            )
        
        # Encode categorical variables
        for col in ['country_code', 'asn', 'city']:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col] = df[col].fillna('Unknown')
                    self.label_encoders[col].fit(df[col].astype(str))
                
                df[f'{col}_encoded'] = df[col].apply(
                    lambda x: self.label_encoders[col].transform([x])[0] 
                    if x in self.label_encoders[col].classes_ else -1
                )
        
        # Ensure all feature columns exist
        for col in self.feature_columns:
            if col not in df.columns:
                if 'protocol_' in col or 'anonymity_' in col:
                    df[col] = 0
                else:
                    df[col] = 0
        
        # Fill missing values
        df = df.fillna(0)
        
        return df
    
    def train(self, training_data: List[Dict], target_column: str = 'uptime_percentage'):
        """Train the model with enhanced features"""
        if not training_data:
            print("❌ No training data available")
            return False
        
        df = self.prepare_features(training_data)
        
        if df.empty:
            print("❌ Failed to prepare features")
            return False
        
        # Create target variable (binary: good/bad proxy)
        if target_column in df.columns:
            y = (df[target_column] > 70).astype(int)  # Threshold for "good" proxy
        else:
            print(f"❌ Target column {target_column} not found")
            return False
        
        # Prepare feature matrix
        X = df[self.feature_columns].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Choose best available model
        if XGBOOST_AVAILABLE:
            print("🧠 Training XGBoost model...")
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
        else:
            print("🧠 Training GradientBoosting model (XGBoost not available)...")
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Evaluate
        y_pred = self.model.predict(X_scaled)
        accuracy = accuracy_score(y, y_pred)
        print(f"✅ Model trained with accuracy: {accuracy:.2%}")
        print("\nClassification Report:")
        print(classification_report(y, y_pred, target_names=['Bad Proxy', 'Good Proxy']))
        
        # Save model
        self.save_model()
        
        return True
    
    def predict(self, proxy_data: Dict) -> Tuple[float, Dict]:
        """Predict proxy quality score"""
        if self.model is None:
            self.load_model()
        
        if self.model is None:
            return 0.5, {"error": "No model available"}
        
        # Prepare single sample
        df = self.prepare_features([proxy_data])
        
        if df.empty:
            return 0.5, {"error": "Failed to prepare features"}
        
        X = df[self.feature_columns].values
        X_scaled = self.scaler.transform(X)
        
        # Predict probability
        proba = self.model.predict_proba(X_scaled)[0]
        score = proba[1] if len(proba) > 1 else proba[0]
        
        # Feature importance
        importance = {}
        if hasattr(self.model, 'feature_importances_'):
            for i, feat in enumerate(self.feature_columns):
                importance[feat] = float(self.model.feature_importances_[i])
        
        return score, importance
    
    def predict_batch(self, proxies: List[Dict]) -> List[Tuple[int, float]]:
        """Predict scores for multiple proxies"""
        if self.model is None:
            self.load_model()
        
        if self.model is None or not proxies:
            return []
        
        df = self.prepare_features(proxies)
        
        if df.empty:
            return []
        
        X = df[self.feature_columns].values
        X_scaled = self.scaler.transform(X)
        
        # Predict probabilities
        probas = self.model.predict_proba(X_scaled)
        scores = [proba[1] if len(proba) > 1 else proba[0] for proba in probas]
        
        # Return proxy IDs with scores
        results = []
        for i, proxy in enumerate(proxies):
            proxy_id = proxy.get('id', i)
            results.append((proxy_id, float(scores[i])))
        
        return results
    
    def save_model(self):
        """Save model and encoders to disk"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns
        }
        
        joblib.dump(model_data, self.model_path)
        print(f"💾 Model saved to {self.model_path}")
    
    def load_model(self):
        """Load model from disk"""
        if os.path.exists(self.model_path):
            try:
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.label_encoders = model_data['label_encoders']
                self.feature_columns = model_data['feature_columns']
                print(f"📦 Model loaded from {self.model_path}")
                return True
            except Exception as e:
                print(f"❌ Error loading model: {e}")
                return False
        else:
            print(f"⚠️  No model found at {self.model_path}")
            return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if self.model is None:
            self.load_model()
        
        if self.model is None or not hasattr(self.model, 'feature_importances_'):
            return {}
        
        importance = {}
        for i, feat in enumerate(self.feature_columns):
            importance[feat] = float(self.model.feature_importances_[i])
        
        # Sort by importance
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        return importance
    
    def retrain_with_new_data(self, db_manager, threshold_samples: int = 100):
        """Retrain model with new data from database"""
        print("🔄 Checking if retraining is needed...")
        
        training_data = db_manager.get_ml_training_data(limit=10000)
        
        if len(training_data) < threshold_samples:
            print(f"⚠️  Insufficient data for retraining ({len(training_data)} < {threshold_samples})")
            return False
        
        print(f"📊 Retraining with {len(training_data)} samples...")
        success = self.train(training_data)
        
        if success:
            print("✅ Model retrained successfully")
        else:
            print("❌ Model retraining failed")
        
        return success


def train_initial_model(db_manager):
    """Train initial model if none exists"""
    predictor = EnhancedMLPredictor()
    
    if not predictor.load_model():
        print("🎯 No existing model found, training new one...")
        training_data = db_manager.get_ml_training_data(limit=5000)
        
        if training_data:
            predictor.train(training_data)
        else:
            print("⚠️  No training data available yet")
    
    return predictor


if __name__ == "__main__":
    # Test the enhanced ML module
    from database.db_manager import DatabaseManager
    
    db = DatabaseManager()
    predictor = EnhancedMLPredictor()
    
    # Load or train model
    if not predictor.load_model():
        data = db.get_ml_training_data(limit=1000)
        if data:
            predictor.train(data)
    
    # Test prediction
    test_proxy = {
        'ip': '192.168.1.1',
        'port': 8080,
        'protocol': 'http',
        'country_code': 'US',
        'anonymity_level': 'elite',
        'speed_ms': 150.0,
        'uptime_percentage': 85.0
    }
    
    score, importance = predictor.predict(test_proxy)
    print(f"\n🎯 Prediction Score: {score:.2%}")
    print(f"📊 Top Features: {dict(list(importance.items())[:5])}")
