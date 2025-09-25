"""
ماژول مشاوره مالی و تریدینگ
تحلیل بازار، ارزهای دیجیتال، سهام
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import yfinance as yf
from dataclasses import dataclass
import ta  # Technical Analysis library

from config.settings import settings


@dataclass
class MarketData:
    """داده‌های بازار"""
    symbol: str
    price: float
    change_24h: float
    change_percent_24h: float
    volume_24h: float
    market_cap: Optional[float]
    timestamp: datetime


@dataclass
class TradingSignal:
    """سیگنال معاملاتی"""
    symbol: str
    signal_type: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0-1
    price_target: Optional[float]
    stop_loss: Optional[float]
    reasoning: str
    timestamp: datetime


class CryptoAnalyzer:
    """تحلیلگر ارزهای دیجیتال"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """دریافت قیمت ارز دیجیتال"""
        
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': symbol.lower(),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                
                if symbol.lower() in data:
                    crypto_data = data[symbol.lower()]
                    
                    return {
                        "success": True,
                        "symbol": symbol.upper(),
                        "price": crypto_data.get('usd', 0),
                        "change_24h": crypto_data.get('usd_24h_change', 0),
                        "volume_24h": crypto_data.get('usd_24h_vol', 0),
                        "market_cap": crypto_data.get('usd_market_cap', 0),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Cryptocurrency {symbol} not found"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching crypto price: {str(e)}"
            }
    
    async def get_trending_cryptos(self, limit: int = 10) -> Dict[str, Any]:
        """دریافت ارزهای ترند"""
        
        try:
            url = f"{self.base_url}/search/trending"
            
            async with self.session.get(url) as response:
                data = await response.json()
                
                trending = []
                for coin in data.get('coins', [])[:limit]:
                    coin_data = coin.get('item', {})
                    trending.append({
                        'id': coin_data.get('id'),
                        'name': coin_data.get('name'),
                        'symbol': coin_data.get('symbol'),
                        'market_cap_rank': coin_data.get('market_cap_rank'),
                        'price_btc': coin_data.get('price_btc')
                    })
                
                return {
                    "success": True,
                    "trending_cryptos": trending,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching trending cryptos: {str(e)}"
            }
    
    async def get_crypto_history(
        self, 
        symbol: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """دریافت تاریخچه قیمت"""
        
        try:
            url = f"{self.base_url}/coins/{symbol.lower()}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily' if days > 90 else 'hourly'
            }
            
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                
                prices = data.get('prices', [])
                volumes = data.get('total_volumes', [])
                
                history = []
                for i, (timestamp, price) in enumerate(prices):
                    volume = volumes[i][1] if i < len(volumes) else 0
                    
                    history.append({
                        'timestamp': datetime.fromtimestamp(timestamp/1000).isoformat(),
                        'price': price,
                        'volume': volume
                    })
                
                return {
                    "success": True,
                    "symbol": symbol.upper(),
                    "history": history,
                    "days": days
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching crypto history: {str(e)}"
            }


class StockAnalyzer:
    """تحلیلگر سهام"""
    
    def __init__(self):
        pass
    
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """دریافت قیمت سهام"""
        
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            history = stock.history(period="2d")
            
            if history.empty:
                return {
                    "success": False,
                    "error": f"No data found for stock {symbol}"
                }
            
            current_price = history['Close'].iloc[-1]
            previous_price = history['Close'].iloc[-2] if len(history) > 1 else current_price
            change = current_price - previous_price
            change_percent = (change / previous_price) * 100 if previous_price != 0 else 0
            
            return {
                "success": True,
                "symbol": symbol.upper(),
                "price": float(current_price),
                "change": float(change),
                "change_percent": float(change_percent),
                "volume": float(history['Volume'].iloc[-1]),
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "company_name": info.get('longName'),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching stock price: {str(e)}"
            }
    
    async def get_stock_analysis(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """تحلیل تکنیکال سهام"""
        
        try:
            stock = yf.Ticker(symbol)
            history = stock.history(period=period)
            
            if history.empty:
                return {
                    "success": False,
                    "error": f"No data found for stock {symbol}"
                }
            
            # محاسبه اندیکاتورهای تکنیکال
            df = history.copy()
            
            # Moving Averages
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
            df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
            
            # RSI
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # MACD
            df['MACD'] = ta.trend.macd_diff(df['Close'])
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['Close'])
            df['BB_upper'] = bb.bollinger_hband()
            df['BB_lower'] = bb.bollinger_lband()
            
            # آخرین مقادیر
            latest = df.iloc[-1]
            
            # تحلیل سیگنال‌ها
            signals = self._analyze_signals(df)
            
            return {
                "success": True,
                "symbol": symbol.upper(),
                "current_price": float(latest['Close']),
                "technical_indicators": {
                    "sma_20": float(latest['SMA_20']) if not pd.isna(latest['SMA_20']) else None,
                    "sma_50": float(latest['SMA_50']) if not pd.isna(latest['SMA_50']) else None,
                    "rsi": float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
                    "macd": float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
                    "bb_upper": float(latest['BB_upper']) if not pd.isna(latest['BB_upper']) else None,
                    "bb_lower": float(latest['BB_lower']) if not pd.isna(latest['BB_lower']) else None
                },
                "signals": signals,
                "analysis_period": period,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in stock analysis: {str(e)}"
            }
    
    def _analyze_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """تحلیل سیگنال‌های معاملاتی"""
        
        latest = df.iloc[-1]
        signals = []
        overall_signal = "HOLD"
        confidence = 0.5
        
        # RSI Analysis
        rsi = latest['RSI']
        if not pd.isna(rsi):
            if rsi < 30:
                signals.append("RSI oversold - potential BUY signal")
                confidence += 0.1
            elif rsi > 70:
                signals.append("RSI overbought - potential SELL signal")
                confidence -= 0.1
        
        # Moving Average Analysis
        price = latest['Close']
        sma_20 = latest['SMA_20']
        sma_50 = latest['SMA_50']
        
        if not pd.isna(sma_20) and not pd.isna(sma_50):
            if price > sma_20 > sma_50:
                signals.append("Price above moving averages - BULLISH")
                overall_signal = "BUY"
                confidence += 0.15
            elif price < sma_20 < sma_50:
                signals.append("Price below moving averages - BEARISH")
                overall_signal = "SELL"
                confidence -= 0.15
        
        # MACD Analysis
        macd = latest['MACD']
        if not pd.isna(macd):
            if macd > 0:
                signals.append("MACD positive - BULLISH momentum")
                confidence += 0.05
            else:
                signals.append("MACD negative - BEARISH momentum")
                confidence -= 0.05
        
        # Bollinger Bands Analysis
        bb_upper = latest['BB_upper']
        bb_lower = latest['BB_lower']
        
        if not pd.isna(bb_upper) and not pd.isna(bb_lower):
            if price >= bb_upper:
                signals.append("Price at upper Bollinger Band - potential SELL")
                confidence -= 0.1
            elif price <= bb_lower:
                signals.append("Price at lower Bollinger Band - potential BUY")
                confidence += 0.1
        
        confidence = max(0.1, min(0.9, confidence))  # محدود کردن بین 0.1 و 0.9
        
        return {
            "overall_signal": overall_signal,
            "confidence": confidence,
            "individual_signals": signals,
            "recommendation": self._get_recommendation(overall_signal, confidence)
        }
    
    def _get_recommendation(self, signal: str, confidence: float) -> str:
        """تولید توصیه"""
        
        if confidence < 0.4:
            return "سیگنال ضعیف - بهتر است منتظر بمانید"
        elif signal == "BUY" and confidence > 0.6:
            return "سیگنال خرید قوی - در نظر گیری خرید"
        elif signal == "SELL" and confidence > 0.6:
            return "سیگنال فروش قوی - در نظر گیری فروش"
        else:
            return "سیگنال متعادل - نگهداری موقعیت فعلی"


class TradingAdvisor:
    """مشاور معاملاتی اصلی"""
    
    def __init__(self):
        self.crypto_analyzer = CryptoAnalyzer()
        self.stock_analyzer = StockAnalyzer()
        self.portfolio = {}
        self.trading_history = []
        self.watchlist = []
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """نمای کلی بازار"""
        
        overview = {
            "timestamp": datetime.now().isoformat(),
            "crypto_market": {},
            "stock_market": {},
            "trending": {}
        }
        
        try:
            # بررسی ارزهای اصلی
            major_cryptos = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana']
            
            async with self.crypto_analyzer as crypto:
                crypto_data = []
                for symbol in major_cryptos:
                    price_data = await crypto.get_crypto_price(symbol)
                    if price_data["success"]:
                        crypto_data.append(price_data)
                
                overview["crypto_market"]["major_coins"] = crypto_data
                
                # ارزهای ترند
                trending = await crypto.get_trending_cryptos(5)
                if trending["success"]:
                    overview["trending"]["crypto"] = trending["trending_cryptos"]
            
            # بررسی سهام اصلی
            major_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
            stock_data = []
            
            for symbol in major_stocks:
                price_data = await self.stock_analyzer.get_stock_price(symbol)
                if price_data["success"]:
                    stock_data.append(price_data)
            
            overview["stock_market"]["major_stocks"] = stock_data
            
            return {
                "success": True,
                "market_overview": overview
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting market overview: {str(e)}"
            }
    
    async def analyze_asset(
        self, 
        symbol: str, 
        asset_type: str = "auto"
    ) -> Dict[str, Any]:
        """تحلیل دارایی"""
        
        try:
            if asset_type == "crypto" or (asset_type == "auto" and len(symbol) > 4):
                # تحلیل ارز دیجیتال
                async with self.crypto_analyzer as crypto:
                    price_data = await crypto.get_crypto_price(symbol)
                    history_data = await crypto.get_crypto_history(symbol, 30)
                    
                    if price_data["success"]:
                        analysis = {
                            "asset_type": "cryptocurrency",
                            "current_data": price_data,
                            "technical_analysis": self._analyze_crypto_trends(history_data) if history_data["success"] else {},
                            "recommendation": self._get_crypto_recommendation(price_data, history_data)
                        }
                        
                        return {
                            "success": True,
                            "symbol": symbol.upper(),
                            "analysis": analysis
                        }
            
            else:
                # تحلیل سهام
                price_data = await self.stock_analyzer.get_stock_price(symbol)
                technical_analysis = await self.stock_analyzer.get_stock_analysis(symbol)
                
                if price_data["success"]:
                    analysis = {
                        "asset_type": "stock",
                        "current_data": price_data,
                        "technical_analysis": technical_analysis.get("technical_indicators", {}) if technical_analysis["success"] else {},
                        "signals": technical_analysis.get("signals", {}) if technical_analysis["success"] else {},
                        "recommendation": technical_analysis.get("signals", {}).get("recommendation", "No recommendation available")
                    }
                    
                    return {
                        "success": True,
                        "symbol": symbol.upper(),
                        "analysis": analysis
                    }
            
            return {
                "success": False,
                "error": f"Could not analyze asset {symbol}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analyzing asset: {str(e)}"
            }
    
    def _analyze_crypto_trends(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        """تحلیل ترند ارز دیجیتال"""
        
        if not history_data.get("success") or not history_data.get("history"):
            return {}
        
        history = history_data["history"]
        prices = [float(item["price"]) for item in history]
        
        if len(prices) < 7:
            return {"error": "Insufficient data for trend analysis"}
        
        # محاسبه میانگین‌های متحرک ساده
        sma_7 = np.mean(prices[-7:])
        sma_14 = np.mean(prices[-14:]) if len(prices) >= 14 else sma_7
        sma_30 = np.mean(prices) if len(prices) >= 30 else sma_14
        
        current_price = prices[-1]
        
        # تعیین ترند
        if current_price > sma_7 > sma_14:
            trend = "BULLISH"
            trend_strength = "Strong"
        elif current_price > sma_7:
            trend = "BULLISH"
            trend_strength = "Moderate"
        elif current_price < sma_7 < sma_14:
            trend = "BEARISH"
            trend_strength = "Strong"
        elif current_price < sma_7:
            trend = "BEARISH"
            trend_strength = "Moderate"
        else:
            trend = "SIDEWAYS"
            trend_strength = "Neutral"
        
        # محاسبه نوسانات
        price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        volatility = np.std(price_changes) / np.mean(prices) * 100
        
        return {
            "trend": trend,
            "trend_strength": trend_strength,
            "sma_7": sma_7,
            "sma_14": sma_14,
            "sma_30": sma_30,
            "volatility_percent": volatility,
            "price_change_7d": ((current_price - prices[-7]) / prices[-7] * 100) if len(prices) >= 7 else 0
        }
    
    def _get_crypto_recommendation(
        self, 
        price_data: Dict[str, Any], 
        history_data: Dict[str, Any]
    ) -> str:
        """تولید توصیه برای ارز دیجیتال"""
        
        if not price_data.get("success"):
            return "داده‌های کافی برای توصیه موجود نیست"
        
        change_24h = price_data.get("change_24h", 0)
        
        if change_24h > 10:
            return "رشد قوی 24 ساعته - احتمال تصحیح قیمت وجود دارد، منتظر بمانید"
        elif change_24h > 5:
            return "رشد مثبت - می‌توان برای خرید در نظر گرفت"
        elif change_24h < -10:
            return "کاهش شدید - ممکن است فرصت خرید باشد اما ریسک بالا"
        elif change_24h < -5:
            return "کاهش قیمت - بررسی بیشتر قبل از تصمیم‌گیری"
        else:
            return "قیمت نسبتاً پایدار - نگهداری موقعیت فعلی"
    
    async def create_trading_plan(
        self, 
        symbols: List[str], 
        investment_amount: float,
        risk_tolerance: str = "moderate"
    ) -> Dict[str, Any]:
        """ایجاد برنامه معاملاتی"""
        
        try:
            plan = {
                "total_investment": investment_amount,
                "risk_tolerance": risk_tolerance,
                "asset_allocation": {},
                "recommendations": [],
                "created_at": datetime.now().isoformat()
            }
            
            # تحلیل هر دارایی
            analyses = []
            for symbol in symbols:
                analysis = await self.analyze_asset(symbol)
                if analysis["success"]:
                    analyses.append(analysis)
            
            if not analyses:
                return {
                    "success": False,
                    "error": "No valid assets to analyze"
                }
            
            # تخصیص سرمایه بر اساس ریسک
            risk_weights = {
                "conservative": {"crypto": 0.2, "stock": 0.8},
                "moderate": {"crypto": 0.4, "stock": 0.6},
                "aggressive": {"crypto": 0.6, "stock": 0.4}
            }
            
            weights = risk_weights.get(risk_tolerance, risk_weights["moderate"])
            
            # تقسیم سرمایه
            crypto_allocation = investment_amount * weights["crypto"]
            stock_allocation = investment_amount * weights["stock"]
            
            crypto_assets = [a for a in analyses if a["analysis"]["asset_type"] == "cryptocurrency"]
            stock_assets = [a for a in analyses if a["analysis"]["asset_type"] == "stock"]
            
            # تخصیص به ارزهای دیجیتال
            if crypto_assets:
                crypto_per_asset = crypto_allocation / len(crypto_assets)
                for asset in crypto_assets:
                    plan["asset_allocation"][asset["symbol"]] = {
                        "amount": crypto_per_asset,
                        "type": "cryptocurrency",
                        "recommendation": asset["analysis"]["recommendation"]
                    }
            
            # تخصیص به سهام
            if stock_assets:
                stock_per_asset = stock_allocation / len(stock_assets)
                for asset in stock_assets:
                    plan["asset_allocation"][asset["symbol"]] = {
                        "amount": stock_per_asset,
                        "type": "stock",
                        "recommendation": asset["analysis"]["recommendation"]
                    }
            
            # توصیه‌های کلی
            plan["recommendations"] = [
                f"سطح ریسک انتخابی: {risk_tolerance}",
                f"تخصیص {weights['crypto']*100:.0f}% به ارزهای دیجیتال و {weights['stock']*100:.0f}% به سهام",
                "همیشه stop-loss تعیین کنید",
                "پورتفولیو را به صورت منظم بررسی کنید",
                "فقط پولی سرمایه‌گذاری کنید که از دست دادنش برایتان مشکل نباشد"
            ]
            
            return {
                "success": True,
                "trading_plan": plan
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating trading plan: {str(e)}"
            }
    
    def add_to_watchlist(self, symbol: str, notes: str = "") -> Dict[str, Any]:
        """اضافه کردن به لیست نظارت"""
        
        watchlist_item = {
            "symbol": symbol.upper(),
            "added_at": datetime.now().isoformat(),
            "notes": notes
        }
        
        # بررسی تکراری نبودن
        if not any(item["symbol"] == symbol.upper() for item in self.watchlist):
            self.watchlist.append(watchlist_item)
            return {
                "success": True,
                "message": f"{symbol.upper()} به لیست نظارت اضافه شد"
            }
        else:
            return {
                "success": False,
                "error": f"{symbol.upper()} قبلاً در لیست نظارت موجود است"
            }
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """دریافت لیست نظارت"""
        return self.watchlist
    
    async def get_portfolio_performance(self) -> Dict[str, Any]:
        """عملکرد پورتفولیو"""
        
        if not self.portfolio:
            return {
                "success": False,
                "error": "No portfolio data available"
            }
        
        try:
            total_value = 0
            total_cost = 0
            performance_data = []
            
            for symbol, holding in self.portfolio.items():
                # دریافت قیمت فعلی
                current_data = await self.analyze_asset(symbol)
                
                if current_data["success"]:
                    current_price = current_data["analysis"]["current_data"]["price"]
                    quantity = holding["quantity"]
                    cost_basis = holding["cost_basis"]
                    
                    current_value = current_price * quantity
                    total_cost_for_asset = cost_basis * quantity
                    
                    pnl = current_value - total_cost_for_asset
                    pnl_percent = (pnl / total_cost_for_asset) * 100 if total_cost_for_asset > 0 else 0
                    
                    performance_data.append({
                        "symbol": symbol,
                        "quantity": quantity,
                        "cost_basis": cost_basis,
                        "current_price": current_price,
                        "current_value": current_value,
                        "pnl": pnl,
                        "pnl_percent": pnl_percent
                    })
                    
                    total_value += current_value
                    total_cost += total_cost_for_asset
            
            total_pnl = total_value - total_cost
            total_pnl_percent = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
            
            return {
                "success": True,
                "portfolio_performance": {
                    "total_value": total_value,
                    "total_cost": total_cost,
                    "total_pnl": total_pnl,
                    "total_pnl_percent": total_pnl_percent,
                    "holdings": performance_data,
                    "last_updated": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error calculating portfolio performance: {str(e)}"
            }
    
    def get_trading_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """تاریخچه معاملات"""
        return self.trading_history[-limit:]
    
    async def get_market_news_summary(self) -> Dict[str, Any]:
        """خلاصه اخبار بازار"""
        
        # این یک شبیه‌سازی است - در پیاده‌سازی واقعی باید از API اخبار استفاده کرد
        
        news_summary = {
            "crypto_news": [
                "Bitcoin reaches new monthly high amid institutional adoption",
                "Ethereum 2.0 staking rewards attract more validators",
                "Regulatory clarity boosts crypto market confidence"
            ],
            "stock_news": [
                "Tech stocks rally on positive earnings reports",
                "Federal Reserve maintains current interest rates",
                "Energy sector shows strong performance this quarter"
            ],
            "market_sentiment": "Cautiously optimistic",
            "key_events": [
                "FOMC meeting scheduled for next week",
                "Major tech earnings reports due this week",
                "Crypto regulation bill under review"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "news_summary": news_summary
        }
