import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import time
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Technical analysis indicators for forex trading"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD indicator"""
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        sma = TechnicalIndicators.sma(data, period)
        std = data.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band

class TradingStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.signals = []
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate trading signal based on strategy logic"""
        raise NotImplementedError("Subclasses must implement generate_signal method")

class TrendFollowingStrategy(TradingStrategy):
    """Trend following strategy using moving averages"""
    
    def __init__(self):
        super().__init__("Trend Following")
        self.short_ma_period = 10
        self.long_ma_period = 30
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        if len(data) < self.long_ma_period:
            return {"signal": "HOLD", "confidence": 0, "reason": "Insufficient data"}
        
        close_prices = data['Close']
        short_ma = TechnicalIndicators.sma(close_prices, self.short_ma_period)
        long_ma = TechnicalIndicators.sma(close_prices, self.long_ma_period)
        
        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        prev_short = short_ma.iloc[-2]
        prev_long = long_ma.iloc[-2]
        
        # Golden cross (bullish signal)
        if prev_short <= prev_long and current_short > current_long:
            return {
                "signal": "BUY",
                "confidence": 0.7,
                "reason": "Golden cross detected",
                "entry_price": data['Close'].iloc[-1],
                "stop_loss": data['Close'].iloc[-1] * 0.98,
                "take_profit": data['Close'].iloc[-1] * 1.04
            }
        
        # Death cross (bearish signal)
        elif prev_short >= prev_long and current_short < current_long:
            return {
                "signal": "SELL",
                "confidence": 0.7,
                "reason": "Death cross detected",
                "entry_price": data['Close'].iloc[-1],
                "stop_loss": data['Close'].iloc[-1] * 1.02,
                "take_profit": data['Close'].iloc[-1] * 0.96
            }
        
        return {"signal": "HOLD", "confidence": 0, "reason": "No clear trend signal"}

class MeanReversionStrategy(TradingStrategy):
    """Mean reversion strategy using RSI and Bollinger Bands"""
    
    def __init__(self):
        super().__init__("Mean Reversion")
        self.rsi_period = 14
        self.bb_period = 20
        self.rsi_oversold = 30
        self.rsi_overbought = 70
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        if len(data) < max(self.rsi_period, self.bb_period):
            return {"signal": "HOLD", "confidence": 0, "reason": "Insufficient data"}
        
        close_prices = data['Close']
        rsi = TechnicalIndicators.rsi(close_prices, self.rsi_period)
        upper_bb, middle_bb, lower_bb = TechnicalIndicators.bollinger_bands(close_prices, self.bb_period)
        
        current_rsi = rsi.iloc[-1]
        current_price = close_prices.iloc[-1]
        current_upper = upper_bb.iloc[-1]
        current_lower = lower_bb.iloc[-1]
        
        # Oversold condition
        if current_rsi < self.rsi_oversold and current_price < current_lower:
            return {
                "signal": "BUY",
                "confidence": 0.8,
                "reason": f"Oversold: RSI={current_rsi:.2f}, Price below lower BB",
                "entry_price": current_price,
                "stop_loss": current_price * 0.97,
                "take_profit": middle_bb.iloc[-1]
            }
        
        # Overbought condition
        elif current_rsi > self.rsi_overbought and current_price > current_upper:
            return {
                "signal": "SELL",
                "confidence": 0.8,
                "reason": f"Overbought: RSI={current_rsi:.2f}, Price above upper BB",
                "entry_price": current_price,
                "stop_loss": current_price * 1.03,
                "take_profit": middle_bb.iloc[-1]
            }
        
        return {"signal": "HOLD", "confidence": 0, "reason": "No mean reversion signal"}

class BreakoutStrategy(TradingStrategy):
    """Breakout strategy using support and resistance levels"""
    
    def __init__(self):
        super().__init__("Breakout")
        self.lookback_period = 20
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        if len(data) < self.lookback_period:
            return {"signal": "HOLD", "confidence": 0, "reason": "Insufficient data"}
        
        recent_data = data.tail(self.lookback_period)
        resistance = recent_data['High'].max()
        support = recent_data['Low'].min()
        current_price = data['Close'].iloc[-1]
        
        # Breakout above resistance
        if current_price > resistance * 1.001:  # 0.1% buffer
            return {
                "signal": "BUY",
                "confidence": 0.75,
                "reason": f"Breakout above resistance at {resistance:.5f}",
                "entry_price": current_price,
                "stop_loss": resistance * 0.999,
                "take_profit": current_price + (current_price - resistance) * 2
            }
        
        # Breakdown below support
        elif current_price < support * 0.999:  # 0.1% buffer
            return {
                "signal": "SELL",
                "confidence": 0.75,
                "reason": f"Breakdown below support at {support:.5f}",
                "entry_price": current_price,
                "stop_loss": support * 1.001,
                "take_profit": current_price - (support - current_price) * 2
            }
        
        return {"signal": "HOLD", "confidence": 0, "reason": "No breakout signal"}

class RiskManager:
    """Risk management system for forex trading"""
    
    def __init__(self, max_risk_per_trade: float = 0.02, max_daily_loss: float = 0.05):
        self.max_risk_per_trade = max_risk_per_trade  # 2% per trade
        self.max_daily_loss = max_daily_loss  # 5% daily loss limit
        self.daily_pnl = 0
        self.account_balance = 10000  # Starting balance
    
    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk management rules"""
        risk_amount = self.account_balance * self.max_risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 0
        
        position_size = risk_amount / price_diff
        return min(position_size, self.account_balance * 0.1)  # Max 10% of balance per trade
    
    def validate_trade(self, signal: Dict) -> bool:
        """Validate if trade should be executed based on risk rules"""
        # Check daily loss limit
        if self.daily_pnl <= -self.account_balance * self.max_daily_loss:
            logger.warning("Daily loss limit reached. Trade rejected.")
            return False
        
        # Check if signal has required fields
        required_fields = ['signal', 'entry_price', 'stop_loss']
        if not all(field in signal for field in required_fields):
            logger.warning("Signal missing required fields. Trade rejected.")
            return False
        
        # Check confidence threshold
        if signal.get('confidence', 0) < 0.6:
            logger.info("Signal confidence too low. Trade rejected.")
            return False
        
        return True

class ForexDataProvider:
    """Data provider for forex market data"""
    
    def __init__(self):
        self.currency_pairs = [
            'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDCHF=X',
            'AUDUSD=X', 'USDCAD=X', 'NZDUSD=X'
        ]
    
    def get_historical_data(self, symbol: str, period: str = "1mo", interval: str = "1h") -> pd.DataFrame:
        """Get historical forex data"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_real_time_price(self, symbol: str) -> float:
        """Get current price for a currency pair"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return data['Close'].iloc[-1]
            return 0
        except Exception as e:
            logger.error(f"Error fetching real-time price for {symbol}: {e}")
            return 0

class ForexTradingRobot:
    """Main forex trading robot class"""
    
    def __init__(self):
        self.data_provider = ForexDataProvider()
        self.risk_manager = RiskManager()
        self.strategies = [
            TrendFollowingStrategy(),
            MeanReversionStrategy(),
            BreakoutStrategy()
        ]
        self.active_trades = []
        self.trade_history = []
        self.is_running = False
    
    def analyze_market(self, symbol: str) -> List[Dict]:
        """Analyze market using all strategies"""
        data = self.data_provider.get_historical_data(symbol)
        if data.empty:
            return []
        
        signals = []
        for strategy in self.strategies:
            signal = strategy.generate_signal(data)
            signal['strategy'] = strategy.name
            signal['symbol'] = symbol
            signal['timestamp'] = datetime.now()
            signals.append(signal)
        
        return signals
    
    def execute_trade(self, signal: Dict) -> bool:
        """Execute a trade based on signal"""
        if not self.risk_manager.validate_trade(signal):
            return False
        
        position_size = self.risk_manager.calculate_position_size(
            signal['entry_price'], signal['stop_loss']
        )
        
        if position_size <= 0:
            logger.warning("Position size too small. Trade not executed.")
            return False
        
        trade = {
            'id': len(self.trade_history) + 1,
            'symbol': signal['symbol'],
            'strategy': signal['strategy'],
            'signal_type': signal['signal'],
            'entry_price': signal['entry_price'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal.get('take_profit'),
            'position_size': position_size,
            'entry_time': datetime.now(),
            'status': 'OPEN'
        }
        
        self.active_trades.append(trade)
        logger.info(f"Trade executed: {trade}")
        return True
    
    def monitor_trades(self):
        """Monitor active trades and close if conditions are met"""
        for trade in self.active_trades[:]:  # Copy list to avoid modification during iteration
            current_price = self.data_provider.get_real_time_price(trade['symbol'])
            
            if current_price == 0:
                continue
            
            # Check stop loss
            if ((trade['signal_type'] == 'BUY' and current_price <= trade['stop_loss']) or
                (trade['signal_type'] == 'SELL' and current_price >= trade['stop_loss'])):
                self.close_trade(trade, current_price, 'STOP_LOSS')
            
            # Check take profit
            elif (trade['take_profit'] and
                  ((trade['signal_type'] == 'BUY' and current_price >= trade['take_profit']) or
                   (trade['signal_type'] == 'SELL' and current_price <= trade['take_profit']))):
                self.close_trade(trade, current_price, 'TAKE_PROFIT')
    
    def close_trade(self, trade: Dict, exit_price: float, reason: str):
        """Close a trade and calculate P&L"""
        if trade['signal_type'] == 'BUY':
            pnl = (exit_price - trade['entry_price']) * trade['position_size']
        else:
            pnl = (trade['entry_price'] - exit_price) * trade['position_size']
        
        trade['exit_price'] = exit_price
        trade['exit_time'] = datetime.now()
        trade['pnl'] = pnl
        trade['status'] = 'CLOSED'
        trade['close_reason'] = reason
        
        self.risk_manager.daily_pnl += pnl
        self.risk_manager.account_balance += pnl
        
        self.active_trades.remove(trade)
        self.trade_history.append(trade)
        
        logger.info(f"Trade closed: {trade}")
    
    def run_trading_cycle(self):
        """Run one complete trading cycle"""
        logger.info("Starting trading cycle...")
        
        # Monitor existing trades
        self.monitor_trades()
        
        # Analyze market for new opportunities
        for symbol in self.data_provider.currency_pairs:
            signals = self.analyze_market(symbol)
            
            for signal in signals:
                if signal['signal'] in ['BUY', 'SELL']:
                    logger.info(f"Signal generated: {signal}")
                    self.execute_trade(signal)
        
        logger.info(f"Trading cycle complete. Active trades: {len(self.active_trades)}")
    
    def start_trading(self):
        """Start the trading robot"""
        self.is_running = True
        logger.info("Forex trading robot started!")
        
        while self.is_running:
            try:
                self.run_trading_cycle()
                time.sleep(300)  # Wait 5 minutes between cycles
            except KeyboardInterrupt:
                logger.info("Trading robot stopped by user.")
                self.stop_trading()
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def stop_trading(self):
        """Stop the trading robot"""
        self.is_running = False
        logger.info("Trading robot stopped.")
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.trade_history:
            return {"message": "No trades executed yet"}
        
        total_trades = len(self.trade_history)
        winning_trades = len([t for t in self.trade_history if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        
        total_pnl = sum(t['pnl'] for t in self.trade_history)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "account_balance": round(self.risk_manager.account_balance, 2),
            "active_trades": len(self.active_trades)
        }

