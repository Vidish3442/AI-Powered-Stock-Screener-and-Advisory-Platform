"""
Alert Checker Service - Monitors stock prices and triggers alerts
"""

from backend.database import get_db
import mysql.connector
from datetime import datetime
from typing import List, Dict

class AlertChecker:
    """Service to check and trigger alerts based on current stock data."""
    
    def __init__(self):
        self.db = None
        self.cursor = None
    
    def connect(self):
        """Connect to database."""
        self.db = get_db()
        self.cursor = self.db.cursor(dictionary=True)
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all active alerts."""
        self.cursor.execute("""
            SELECT 
                a.alert_id,
                a.user_id,
                a.stock_id,
                a.metric,
                a.operator,
                a.threshold,
                s.symbol,
                s.company_name,
                f.current_price,
                f.pe_ratio,
                f.market_cap,
                f.eps,
                f.roe,
                f.dividend_yield
            FROM alerts a
            JOIN stocks s ON a.stock_id = s.stock_id
            LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
            WHERE a.is_active = TRUE
        """)
        return self.cursor.fetchall()
    
    def get_metric_value(self, alert: Dict) -> float:
        """Get the current value of the metric being monitored."""
        metric_map = {
            'price': 'current_price',
            'pe_ratio': 'pe_ratio',
            'market_cap': 'market_cap',
            'eps': 'eps',
            'roe': 'roe',
            'dividend_yield': 'dividend_yield'
        }
        
        db_field = metric_map.get(alert['metric'])
        if db_field:
            return alert.get(db_field, 0)
        return 0
    
    def check_condition(self, current_value: float, operator: str, threshold: float) -> bool:
        """Check if the alert condition is met."""
        if operator == '>':
            return current_value > threshold
        elif operator == '<':
            return current_value < threshold
        elif operator == '>=':
            return current_value >= threshold
        elif operator == '<=':
            return current_value <= threshold
        elif operator == '=':
            return abs(current_value - threshold) < 0.01  # Allow small floating point difference
        return False
    
    def trigger_alert(self, alert: Dict, current_value: float) -> bool:
        """Trigger an alert by creating an alert event."""
        try:
            # Check if this alert was already triggered recently (within last hour)
            self.cursor.execute("""
                SELECT event_id 
                FROM alert_event 
                WHERE alert_id = %s 
                AND triggered_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ORDER BY triggered_at DESC
                LIMIT 1
            """, (alert['alert_id'],))
            
            recent_trigger = self.cursor.fetchone()
            if recent_trigger:
                # Already triggered recently, skip
                return False
            
            # Create alert event
            self.cursor.execute("""
                INSERT INTO alert_event (alert_id, stock_id, triggered_value, triggered_at)
                VALUES (%s, %s, %s, NOW())
            """, (alert['alert_id'], alert['stock_id'], current_value))
            
            self.db.commit()
            
            print(f"🔔 Alert triggered: {alert['symbol']} - {alert['metric']} {alert['operator']} {alert['threshold']} (Current: {current_value})")
            return True
            
        except mysql.connector.Error as e:
            print(f"❌ Error triggering alert: {e}")
            return False
    
    def check_all_alerts(self) -> Dict:
        """Check all active alerts and trigger if conditions are met."""
        try:
            self.connect()
            
            alerts = self.get_active_alerts()
            
            results = {
                'total_checked': len(alerts),
                'triggered': 0,
                'skipped': 0,
                'triggered_alerts': []
            }
            
            for alert in alerts:
                current_value = self.get_metric_value(alert)
                
                if current_value is None or current_value == 0:
                    results['skipped'] += 1
                    continue
                
                # Check if condition is met
                if self.check_condition(current_value, alert['operator'], alert['threshold']):
                    triggered = self.trigger_alert(alert, current_value)
                    if triggered:
                        results['triggered'] += 1
                        results['triggered_alerts'].append({
                            'alert_id': alert['alert_id'],
                            'symbol': alert['symbol'],
                            'metric': alert['metric'],
                            'operator': alert['operator'],
                            'threshold': alert['threshold'],
                            'current_value': current_value
                        })
            
            return results
            
        except Exception as e:
            print(f"❌ Error checking alerts: {e}")
            return {'error': str(e)}
        finally:
            self.close()
    
    def get_user_triggered_alerts(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recently triggered alerts for a specific user."""
        try:
            self.connect()
            
            self.cursor.execute("""
                SELECT 
                    ae.event_id,
                    ae.alert_id,
                    s.symbol,
                    s.company_name,
                    a.metric,
                    a.operator,
                    a.threshold,
                    ae.triggered_value,
                    ae.triggered_at,
                    CASE 
                        WHEN ae.triggered_at > DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 'new'
                        WHEN ae.triggered_at > DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 'recent'
                        ELSE 'old'
                    END as status
                FROM alert_event ae
                JOIN alerts a ON ae.alert_id = a.alert_id
                JOIN stocks s ON ae.stock_id = s.stock_id
                WHERE a.user_id = %s
                ORDER BY ae.triggered_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            return self.cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error getting user alerts: {e}")
            return []
        finally:
            self.close()


def check_alerts_now():
    """Standalone function to check all alerts immediately."""
    checker = AlertChecker()
    results = checker.check_all_alerts()
    
    print("\n" + "="*80)
    print("🔔 Alert Check Results")
    print("="*80)
    print(f"Total Alerts Checked: {results.get('total_checked', 0)}")
    print(f"Alerts Triggered: {results.get('triggered', 0)}")
    print(f"Alerts Skipped: {results.get('skipped', 0)}")
    
    if results.get('triggered_alerts'):
        print("\n📢 Triggered Alerts:")
        for alert in results['triggered_alerts']:
            print(f"  • {alert['symbol']}: {alert['metric']} {alert['operator']} {alert['threshold']} (Current: {alert['current_value']})")
    
    print("="*80)
    
    return results


if __name__ == "__main__":
    # Run alert checker when script is executed directly
    check_alerts_now()
