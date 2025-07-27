import requests
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTechnicalIndicators:
    """Simplified technical analysis indicators"""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> float:
        """Simple Moving Average"""
        if len(prices) < period:
            return 0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

class SimpleTradingStrategy:
    """Base class for simplified trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.signals = []
    
    def generate_signal(self, prices: List[float]) -> Dict:
        """Generate trading signal based on strategy logic"""
        raise NotImplementedError("Subclasses must implement generate_signal method")

class SimpleTrendFollowingStrategy(SimpleTradingStrategy):
    """Simplified trend following strategy using moving averages"""
    
    def __init__(self):
        super().__init__("Simple Trend Following")
        self.short_ma_period = 5
        self.long_ma_period = 15
    
    def generate_signal(self, prices: List[float]) -> Dict:
        if len(prices) < self.long_ma_period:
            return {"signal": "HOLD", "confidence": 0, "reason": "Insufficient data"}
        
        short_ma = SimpleTechnicalIndicators.sma(prices, self.short_ma_period)
        long_ma = SimpleTechnicalIndicators.sma(prices, self.long_ma_period)
        current_price = prices[-1]
        
        # Simple crossover strategy
        if short_ma > long_ma and current_price > short_ma:
            return {
                "signal": "BUY",
                "confidence": 0.7,
                "reason": "Short MA above Long MA",
                "entry_price": current_price,
                "stop_loss": current_price * 0.98,
                "take_profit": current_price * 1.04
            }
        elif short_ma < long_ma and current_price < short_ma:
            return {
                "signal": "SELL",
                "confidence": 0.7,
                "reason": "Short MA below Long MA",
                "entry_price": current_price,
                "stop_loss": current_price * 1.02,
                "take_profit": current_price * 0.96
            }
        
        return {"signal": "HOLD", "confidence": 0, "reason": "No clear trend signal"}

class SimpleMeanReversionStrategy(SimpleTradingStrategy):
    """Simplified mean reversion strategy using RSI"""
    
    def __init__(self):
        super().__init__("Simple Mean Reversion")
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
    
    def generate_signal(self, prices: List[float]) -> Dict:
        if len(prices) < self.rsi_period + 1:
            return {"signal": "HOLD", "confidence": 0, "reason": "Insufficient data"}
        
        rsi = SimpleTechnicalIndicators.rsi(prices, self.rsi_period)
        current_price = prices[-1]
        
        # Oversold condition
        if rsi < self.rsi_oversold:
            return {
                "signal": "BUY",
                "confidence": 0.8,
                "reason": f"Oversold: RSI={rsi:.2f}",
                "entry_price": current_price,
                "stop_loss": current_price * 0.97,
                "take_profit": current_price * 1.03
            }
        
        # Overbought condition
        elif rsi > self.rsi_overbought:
            return {
                "signal": "SELL",
                "confidence": 0.8,
                "reason": f"Overbought: RSI={rsi:.2f}",
                "entry_price": current_price,
                "stop_loss": current_price * 1.03,
                "take_profit": current_price * 0.97
            }
        
        return {"signal": "HOLD", "confidence": 0, "reason": "No mean reversion signal"}

class SimpleRiskManager:
    """Simplified risk management system"""
    
    def __init__(self, max_risk_per_trade: float = 0.02, max_daily_loss: float = 0.05):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.daily_pnl = 0
        self.account_balance = 10000
    
    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk management rules"""
        risk_amount = self.account_balance * self.max_risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 0
        
        position_size = risk_amount / price_diff
        return min(position_size, self.account_balance * 0.1)
    
    def validate_trade(self, signal: Dict) -> bool:
        """Validate if trade should be executed based on risk rules"""
        if self.daily_pnl <= -self.account_balance * self.max_daily_loss:
            logger.warning("Daily loss limit reached. Trade rejected.")
            return False
        
        required_fields = ['signal', 'entry_price', 'stop_loss']
        if not all(field in signal for field in required_fields):
            logger.warning("Signal missing required fields. Trade rejected.")
            return False
        
        if signal.get('confidence', 0) < 0.6:
            logger.info("Signal confidence too low. Trade rejected.")
            return False
        
        return True

class SimpleForexDataProvider:
    """Simplified data provider for forex market data"""
    
    def __init__(self):
        self.currency_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF',
            'AUDUSD', 'USDCAD', 'NZDUSD'
        ]
        self.price_history = {}
    
    def get_mock_price_data(self, symbol: str, count: int = 50) -> List[float]:
        """Get mock price data for testing"""
        import random
        
        # Generate mock price data
        base_price = 1.0850 if 'EUR' in symbol else 1.2500
        prices = []
        current_price = base_price
        
        for _ in range(count):
            # Random walk with slight trend
            change = random.uniform(-0.002, 0.002)
            current_price += change
            prices.append(round(current_price, 5))
        
        return prices
    
    def get_real_time_price(self, symbol: str) -> float:
        """Get current price for a currency pair (mock implementation)"""
        try:
            # In a real implementation, this would fetch from a forex API
            # For now, return a mock price
            import random
            base_price = 1.0850 if 'EUR' in symbol else 1.2500
            return round(base_price + random.uniform(-0.01, 0.01), 5)
        except Exception as e:
            logger.error(f"Error fetching real-time price for {symbol}: {e}")
            return 0

class SimpleForexTradingRobot:
    """Simplified forex trading robot class"""
    
    def __init__(self):
        self.data_provider = SimpleForexDataProvider()
        self.risk_manager = SimpleRiskManager()
        self.strategies = [
            SimpleTrendFollowingStrategy(),
            SimpleMeanReversionStrategy()
        ]
        self.active_trades = []
        self.trade_history = []
        self.is_running = False
    
    def analyze_market(self, symbol: str) -> List[Dict]:
        """Analyze market using all strategies"""
        prices = self.data_provider.get_mock_price_data(symbol)
        if not prices:
            return []
        
        signals = []
        for strategy in self.strategies:
            signal = strategy.generate_signal(prices)
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
            'id': len(self.trade_history) + len(self.active_trades) + 1,
            'symbol': signal['symbol'],
            'strategy': signal['strategy'],
            'signal_type': signal['signal'],
            'entry_price': signal['entry_price'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal.get('take_profit'),
            'position_size': position_size,
            'entry_time': datetime.now().isoformat(),
            'status': 'OPEN'
        }
        
        self.active_trades.append(trade)
        logger.info(f"Trade executed: {trade}")
        return True
    
    def monitor_trades(self):
        """Monitor active trades and close if conditions are met"""
        for trade in self.active_trades[:]:
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
        trade['exit_time'] = datetime.now().isoformat()
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
        logger.info("Simple forex trading robot started!")
        
        while self.is_running:
            try:
                self.run_trading_cycle()
                time.sleep(300)  # Wait 5 minutes between cycles
            except KeyboardInterrupt:
                logger.info("Trading robot stopped by user.")
                self.stop_trading()
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
                time.sleep(60)
    
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

