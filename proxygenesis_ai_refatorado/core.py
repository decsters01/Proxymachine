"""Núcleo Inteligente do Proxygenesis AI - Versão Simplificada"""
import asyncio, logging, time, random, re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import aiohttp, pandas as pd, numpy as np, joblib
from bs4 import BeautifulSoup
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from .config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProxyResult:
    proxy: str
    is_active: bool
    response_time_ms: int = 0
    status_code: Optional[int] = None
    anonymity: str = 'unknown'
    error: Optional[str] = None
    source: str = 'unknown'
    discovery_method: str = 'unknown'
    quality_score: float = 0.5
    ml_probability: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {'proxy': self.proxy, 'is_active': self.is_active, 'response_time_ms': self.response_time_ms,
                'status_code': self.status_code, 'anonymity': self.anonymity, 'error': self.error,
                'source': self.source, 'discovery_method': self.discovery_method,
                'quality_score': self.quality_score, 'ml_probability': self.ml_probability, 'timestamp': self.timestamp}

class ProxyCollector:
    def __init__(self, config: Config):
        self.config = config
    
    def _valid(self, p: str) -> bool:
        try:
            if ':' not in p: return False
            ip, port = p.split(':', 1)
            parts = ip.split('.')
            return len(parts)==4 and all(0<=int(x)<=255 for x in parts) and 1<=int(port)<=65535
        except:
            return False
    
    def _extract(self, html: str) -> List[str]:
        proxies = []
        soup = BeautifulSoup(html, 'html.parser')
        for t in soup.find_all('table'):
            for r in t.find_all('tr'):
                c = r.find_all(['td','th'])
                if len(c)>=2:
                    try:
                        ip,port = c[0].get_text(strip=True),c[1].get_text(strip=True)
                        if all(x.isdigit() and 0<=int(x)<=255 for x in ip.split('.')) and port.isdigit():
                            proxies.append(f"{ip}:{port}")
                    except:
                        pass
        for m in re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b', soup.get_text()):
            if self._valid(m):
                proxies.append(m)
        return proxies
    
    async def _fetch(self, s: aiohttp.ClientSession, u: str) -> List[str]:
        try:
            async with s.get(u, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as r:
                if r.status==200:
                    return self._extract(await r.text())
        except Exception as e:
            logger.warning(f"Erro {u}: {e}")
        return []
    
    async def collect_lists(self) -> List[Dict]:
        logger.info("📥 Coletando listas...")
        async with aiohttp.ClientSession(headers={'User-Agent':random.choice(self.config.user_agents)}) as s:
            res = await asyncio.gather(*[self._fetch(s,u) for u in self.config.proxy_sources], return_exceptions=True)
        prox = set()
        for r in res:
            if isinstance(r,list):
                prox.update(r)
        return [ProxyResult(proxy=p,is_active=False,source='public_lists').to_dict() for p in prox]
    
    async def search_dorks(self) -> List[Dict]:
        logger.info("🔍 Dorks...")
        await asyncio.sleep(0.4)
        return []
    
    async def scan_ports(self, ranges: List[str]) -> List[Dict]:
        logger.info("🔧 Scan...")
        await asyncio.sleep(0.5)
        return []
    
    async def collect_all(self) -> List[Dict]:
        logger.info("🚀 Coleta híbrida...")
        start=time.time()
        tasks = []
        if self.config.enable_public_lists:
            tasks.append(self.collect_lists())
        if self.config.enable_search_dorking:
            tasks.append(self.search_dorks())
        if self.config.enable_port_scanning:
            tasks.append(self.scan_ports([]))
        res = await asyncio.gather(*tasks, return_exceptions=True)
        all_p = []
        for r in res:
            if isinstance(r,list):
                all_p.extend(r)
        seen,set_u = set(),[]
        for p in all_p:
            if p['proxy'] not in seen:
                seen.add(p['proxy'])
                set_u.append(p)
        logger.info(f"✅ Coleta: {len(set_u)} em {time.time()-start:.1f}s")
        return set_u

class ProxyValidator:
    def __init__(self, config: Config):
        self.config = config
    
    async def check(self, proxy: str) -> ProxyResult:
        start=time.time()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.validation_timeout)) as s:
                async with s.get(self.config.test_url, proxy=f"http://{proxy}",headers={'User-Agent':random.choice(self.config.user_agents)}) as r:
                    rt=int((time.time()-start)*1000)
                    ok=r.status==200 and rt<=self.config.max_response_time
                    anon='elite' if ok and 'X-Forwarded-For' not in r.headers else 'anonymous' if ok else 'unknown'
                    return ProxyResult(proxy=proxy,is_active=ok,response_time_ms=rt,status_code=r.status,anonymity=anon)
        except asyncio.TimeoutError:
            return ProxyResult(proxy=proxy,is_active=False,response_time_ms=int((time.time()-start)*1000),error='Timeout')
        except Exception as e:
            return ProxyResult(proxy=proxy,is_active=False,error=str(e))
    
    async def validate_batch(self, proxies: List[str]) -> List[ProxyResult]:
        logger.info(f"Validando {len(proxies)}...")
        sem=asyncio.Semaphore(self.config.max_concurrent_checks)
        async def chk(p):
            async with sem:
                return await self.check(p)
        res = await asyncio.gather(*[chk(p) for p in proxies], return_exceptions=True)
        valid=[r for r in res if not isinstance(r,Exception)]
        act=sum(1 for r in valid if r.is_active)
        logger.info(f"✅ {act}/{len(valid)} ativos")
        return valid

class ProxyPredictor:
    def __init__(self, config: Config):
        self.config=config
        self.model=None
        self.scaler=StandardScaler()
        self.features=[]
        self.trained=False
    
    def _feats(self, data: List[Dict]) -> pd.DataFrame:
        fl=[]
        for d in data:
            p=d.get('proxy','')
            if ':' not in p:
                continue
            ip,port=p.split(':',1)
            f={}
            try:
                octs=ip.split('.')
                for i,o in enumerate(octs,1):
                    f[f'oct{i}']=int(o)
                f.update({'ip_sum':sum(int(o) for o in octs),'ip_mean':np.mean([int(o) for o in octs]),'ip_std':np.std([int(o) for o in octs])})
            except:
                f.update({f'oct{i}':0 for i in range(1,5)},ip_sum=0,ip_mean=0,ip_std=0)
            try:
                pn=int(port)
                f.update(port=pn,is_common=1 if pn in self.config.common_ports else 0,is_http=1 if pn in [80,8080] else 0)
            except:
                f.update(port=0,is_common=0,is_http=0)
            qs,src=d.get('quality_score',0.5),d.get('source','unknown')
            f.update(quality_score=qs,is_high=1 if qs>0.7 else 0,src_pub=1 if src=='public_lists' else 0,is_active=1 if d.get('is_active') else 0)
            fl.append(f)
        df=pd.DataFrame(fl)
        for c in df.columns:
            if c!='is_active' and df[c].dtype=='object':
                df[c]=pd.to_numeric(df[c],errors='coerce').fillna(0)
        return df
    
    def train(self, df: pd.DataFrame) -> Dict:
        if len(df)<10:
            return {'error':'Insuficiente'}
        X,y=df.drop('is_active',axis=1),df['is_active']
        self.features=X.columns.tolist()
        Xt,Xv,yt,yv=train_test_split(X,y,test_size=self.config.test_size,random_state=self.config.random_state,stratify=y)
        self.model=RandomForestClassifier(n_estimators=self.config.n_estimators,max_depth=self.config.max_depth,random_state=self.config.random_state)
        self.model.fit(self.scaler.fit_transform(Xt),yt)
        acc=accuracy_score(yv,self.model.predict(self.scaler.transform(Xv)))
        self.trained=True
        logger.info(f"Treinado: {acc:.3f}")
        return {'accuracy':acc,'samples':len(Xt)}
    
    def predict(self, data: List[Dict]) -> List[float]:
        if not self.trained:
            return [0.5]*len(data)
        df=self._feats(data)
        X=df.drop('is_active',axis=1) if 'is_active' in df.columns else df
        return self.model.predict_proba(self.scaler.transform(X.reindex(columns=self.features,fill_value=0)))[:,1].tolist()
    
    def save(self, path: Optional[Path]=None):
        p=path or self.config.model_path
        joblib.dump({'model':self.model,'scaler':self.scaler,'features':self.features},p)
    
    def load(self, path: Optional[Path]=None) -> bool:
        p=path or self.config.model_path
        if not p.exists():
            return False
        try:
            d=joblib.load(p)
            self.model,self.scaler,self.features=d['model'],d['scaler'],d['features']
            self.trained=True
            return True
        except:
            return False

class ProxygenesisAI:
    def __init__(self, config: Optional[Config]=None, shodan_api_key: Optional[str]=None):
        self.config=config or Config()
        if shodan_api_key:
            self.config.shodan_api_key=shodan_api_key
        self.collector,self.validator,self.predictor=ProxyCollector(self.config),ProxyValidator(self.config),ProxyPredictor(self.config)
        self.cycle=self.found=self.validated=self.active=0
        self.predictor.load()
    
    async def run_cycle(self) -> Dict:
        self.cycle+=1
        logger.info(f"=== CICLO {self.cycle} ===")
        start=time.time()
        stats={'cycle':self.cycle,'collected':0,'tested':0,'active':0,'retrained':False}
        try:
            cands=await self.collector.collect_all()
            stats['collected']=len(cands)
            if not cands:
                return stats
            if self.predictor.trained:
                probs=self.predictor.predict(cands)
                for i,c in enumerate(cands):
                    c['ml_probability']=probs[i]
                cands.sort(key=lambda x:x.get('ml_probability',0.5)*0.7+x.get('quality_score',0.5)*0.3,reverse=True)
                cands=cands[:self.config.top_candidates_to_test]
            res=await self.validator.validate_batch([c['proxy'] for c in cands])
            stats['tested']=len(res)
            acts=[r for r in res if r.is_active]
            stats['active']=len(acts)
            self.found+=len(cands)
            self.validated+=len(res)
            self.active+=len(acts)
            if acts:
                with open(self.config.active_proxies_path,'a') as f:
                    for r in acts:
                        f.write(f"{r.proxy}\n")
            meta={c['proxy']:c for c in cands}
            new=[{**r.to_dict(),**{k:meta[r.proxy].get(k) for k in ['source','discovery_method','quality_score']}} for r in res if r.proxy in meta]
            old=pd.read_csv(self.config.training_data_path).to_dict('records') if self.config.training_data_path.exists() else []
            all_d=old+new
            pd.DataFrame(all_d).to_csv(self.config.training_data_path,index=False)
            if self.cycle%self.config.retrain_frequency==0 or not self.predictor.trained:
                if len(all_d)>=self.config.min_training_samples:
                    m=self.predictor.train(pd.DataFrame(all_d))
                    if 'error' not in m:
                        self.predictor.save()
                        stats['retrained']=True
                        logger.info(f"Retreinado: {m['accuracy']:.3f}")
            stats.update(duration=time.time()-start,rate=len(acts)/len(res)*100 if res else 0)
            logger.info(f"Ciclo {self.cycle}: {len(acts)} ativos ({stats['rate']:.1f}%) em {stats['duration']:.1f}s")
        except Exception as e:
            logger.error(f"Erro: {e}")
            stats['error']=str(e)
        return stats
    
    def get_stats(self):
        return {'cycles':self.cycle,'found':self.found,'validated':self.validated,'active':self.active,
                'rate':self.active/self.validated*100 if self.validated else 0,'trained':self.predictor.trained}
    
    async def run_continuous(self, max_cycles: Optional[int]=None):
        logger.info("Iniciando...")
        cyc=0
        try:
            while max_cycles is None or cyc<max_cycles:
                cyc+=1
                s=await self.run_cycle()
                print(f"\n=== {s['cycle']} ===\nAtivos: {s['active']}\nSucesso: {s.get('rate',0):.1f}%")
                if max_cycles is None or cyc<max_cycles:
                    await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Interrompido")
        finally:
            st=self.get_stats()
            print(f"\n=== FINAL ===\nCiclos: {st['cycles']}\nAtivos: {st['active']}")
