from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ForexData(db.Model):
    __tablename__ = 'forex_data'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)  # e.g., 'EURUSD'
    timestamp = db.Column(db.DateTime, nullable=False)
    open_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float, nullable=False)
    low_price = db.Column(db.Float, nullable=False)
    close_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Float, default=0)
    
    def __repr__(self):
        return f'<ForexData {self.symbol} {self.timestamp}>'

class TradingSignal(db.Model):
    __tablename__ = 'trading_signals'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    signal_type = db.Column(db.String(10), nullable=False)  # 'BUY' or 'SELL'
    strategy = db.Column(db.String(50), nullable=False)  # Strategy name
    confidence = db.Column(db.Float, nullable=False)  # 0-1 confidence score
    entry_price = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    status = db.Column(db.String(20), default='PENDING')  # PENDING, EXECUTED, CANCELLED
    
    def __repr__(self):
        return f'<TradingSignal {self.symbol} {self.signal_type} {self.timestamp}>'

class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    trade_type = db.Column(db.String(10), nullable=False)  # 'BUY' or 'SELL'
    entry_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime)
    entry_price = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float)
    quantity = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    profit_loss = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='OPEN')  # OPEN, CLOSED, CANCELLED
    strategy = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f'<Trade {self.symbol} {self.trade_type} {self.entry_time}>'

