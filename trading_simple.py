from flask import Blueprint, jsonify, request
from src.trading_engine_simple import SimpleForexTradingRobot
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

trading_bp = Blueprint('trading', __name__)

# Global trading robot instance
trading_robot = SimpleForexTradingRobot()
trading_thread = None

@trading_bp.route('/start', methods=['POST'])
def start_trading():
    """Start the forex trading robot"""
    global trading_thread
    
    try:
        if trading_robot.is_running:
            return jsonify({"error": "Trading robot is already running"}), 400
        
        # Start trading in a separate thread
        trading_thread = threading.Thread(target=trading_robot.start_trading)
        trading_thread.daemon = True
        trading_thread.start()
        
        return jsonify({
            "message": "Forex trading robot started successfully",
            "status": "running"
        })
    
    except Exception as e:
        logger.error(f"Error starting trading robot: {e}")
        return jsonify({"error": str(e)}), 500

@trading_bp.route('/stop', methods=['POST'])
def stop_trading():
    """Stop the forex trading robot"""
    try:
        if not trading_robot.is_running:
            return jsonify({"error": "Trading robot is not running"}), 400
        
        trading_robot.stop_trading()
        
        return jsonify({
            "message": "Forex trading robot stopped successfully",
            "status": "stopped"
        })
    
    except Exception as e:
        logger.error(f"Error stopping trading robot: {e}")
        return jsonify({"error": str(e)}), 500

@trading_bp.route('/status', methods=['GET'])
def get_status():
    """Get the current status of the trading robot"""
    try:
        return jsonify({
            "is_running": trading_robot.is_running,
            "active_trades": len(trading_robot.active_trades),
            "total_trades": len(trading_robot.trade_history),
            "account_balance": round(trading_robot.risk_manager.account_balance, 2),
            "daily_pnl": round(trading_robot.risk_manager.daily_pnl, 2)
        })
    
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500

@trading_bp.route('/performance', methods=['GET'])
def get_performance():
    """Get performance statistics"""
    try:
        stats = trading_robot.get_performance_stats()
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return jsonify({"error": str(e)}), 500

@trading_bp.route('/trades', methods=['GET'])
def get_trades():
    """Get trade history"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        status = request.args.get('status', 'all')
        
        trades = trading_robot.trade_history.copy()
        
        # Filter by status if specified
        if status != 'all':
            trades = [t for t in trades if t.get('status', '').lower() == status.lower()]
        
        # Limit results
        trades = trades[-limit:] if limit > 0 else trades
        
        return jsonify({
            "trades": trades,
            "total_count": len(trading_robot.trade_history)
        })
    
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return jsonify({"error": str(e)}), 500

@trading_bp.route('/active-trades', methods=['GET'])
def get_active_trades():
    """Get currently active trades"""
    try:
        active_trades = trading_robot.active_trades.copy()
        
        return jsonify({
            "active_trades": active_trades,
            "count": len(active_trades)
        })
    
    except Exception as e:
        logger.error(f"Error getting active trades: {e}")
        return jsonify({"error": str(e)}), 500

@trading_bp.route('/analyze/<symbol>', methods=['GET'])
def analyze_symbol(symbol):
    """Analyze a specific currency pair"""
    try:
        signals = trading_robot.analyze_market(symbol)
        
        # Convert datetime objects to strings for JSON serialization
        for signal in signals:
            if 'timestamp' in signal:
                signal['timestamp'] = signal['timestamp'].isoformat()
        
        return jsonify({
            "symbol": symbol,
            "signals": signals,
            "current_price": trading_robot.data_provider.get_real_time_price(symbol)
        })
    
    except Exception as e:
        logger.error(f"Error analyzing symbol {symbol}: {e}")
        return jsonify({"error": str(e)}), 500

@trading_bp.route('/symbols', methods=['GET'])
def get_symbols():
    """Get list of supported currency pairs"""
    try:
        return jsonify({
            "symbols": trading_robot.data_provider.currency_pairs,
            "count": len(trading_robot.data_provider.currency_pairs)
        })
    
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        return jsonify({"error": str(e)}), 500

@trading_bp.route('/manual-trade', methods=['POST'])
def manual_trade():
    """Execute a manual trade"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['symbol', 'signal', 'entry_price', 'stop_loss']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Create signal object
        signal = {
            'symbol': data['symbol'],
            'signal': data['signal'],
            'entry_price': float(data['entry_price']),
            'stop_loss': float(data['stop_loss']),
            'take_profit': float(data.get('take_profit', 0)) if data.get('take_profit') else None,
            'confidence': float(data.get('confidence', 1.0)),
            'strategy': 'Manual',
            'reason': 'Manual trade execution'
        }
        
        # Execute the trade
        success = trading_robot.execute_trade(signal)
        
        if success:
            return jsonify({
                "message": "Manual trade executed successfully",
                "signal": signal
            })
        else:
            return jsonify({"error": "Trade execution failed"}), 400
    
    except Exception as e:
        logger.error(f"Error executing manual trade: {e}")
        return jsonify({"error": str(e)}), 500

@trading_bp.route('/close-trade/<int:trade_id>', methods=['POST'])
def close_trade_manual(trade_id):
    """Manually close a specific trade"""
    try:
        # Find the trade in active trades
        trade_to_close = None
        for trade in trading_robot.active_trades:
            if trade['id'] == trade_id:
                trade_to_close = trade
                break
        
        if not trade_to_close:
            return jsonify({"error": "Trade not found or already closed"}), 404
        
        # Get current price
        current_price = trading_robot.data_provider.get_real_time_price(trade_to_close['symbol'])
        
        if current_price == 0:
            return jsonify({"error": "Unable to get current price"}), 500
        
        # Close the trade
        trading_robot.close_trade(trade_to_close, current_price, 'MANUAL_CLOSE')
        
        return jsonify({
            "message": f"Trade {trade_id} closed successfully",
            "exit_price": current_price
        })
    
    except Exception as e:
        logger.error(f"Error closing trade {trade_id}: {e}")
        return jsonify({"error": str(e)}), 500

