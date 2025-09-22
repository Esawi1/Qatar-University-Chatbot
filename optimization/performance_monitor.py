"""
Performance monitoring and optimization for Qatar University Chatbot
Tracks usage patterns and optimizes for cost efficiency
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass
from collections import defaultdict, deque
import psutil
import os

@dataclass
class PerformanceMetrics:
    response_time: float
    token_count: int
    cache_hit: bool
    document_count: int
    error_count: int
    timestamp: datetime

class PerformanceMonitor:
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 requests
        self.session_metrics = defaultdict(list)
        self.daily_stats = defaultdict(lambda: defaultdict(int))
        self.error_log = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('chatbot_performance.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def record_request(self, session_id: str, metrics: PerformanceMetrics):
        """Record performance metrics for a request"""
        self.metrics_history.append(metrics)
        self.session_metrics[session_id].append(metrics)
        
        # Update daily stats
        date_key = metrics.timestamp.date()
        self.daily_stats[date_key]['total_requests'] += 1
        self.daily_stats[date_key]['total_response_time'] += metrics.response_time
        self.daily_stats[date_key]['total_tokens'] += metrics.token_count
        
        if metrics.cache_hit:
            self.daily_stats[date_key]['cache_hits'] += 1
        
        if metrics.error_count > 0:
            self.daily_stats[date_key]['errors'] += metrics.error_count
        
        # Log performance issues
        if metrics.response_time > 10.0:  # More than 10 seconds
            self.logger.warning(f"Slow response: {metrics.response_time:.2f}s for session {session_id}")
        
        if metrics.error_count > 0:
            self.logger.error(f"Request errors: {metrics.error_count} for session {session_id}")
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"message": "No recent metrics available"}
        
        avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        total_requests = len(recent_metrics)
        cache_hit_rate = sum(1 for m in recent_metrics if m.cache_hit) / total_requests
        total_tokens = sum(m.token_count for m in recent_metrics)
        error_rate = sum(m.error_count for m in recent_metrics) / total_requests
        
        return {
            "period_hours": hours,
            "total_requests": total_requests,
            "average_response_time": round(avg_response_time, 2),
            "cache_hit_rate": round(cache_hit_rate * 100, 2),
            "total_tokens_used": total_tokens,
            "error_rate": round(error_rate * 100, 2),
            "estimated_cost": self._estimate_cost(total_tokens),
            "performance_score": self._calculate_performance_score(recent_metrics)
        }
    
    def _estimate_cost(self, total_tokens: int) -> float:
        """Estimate Azure OpenAI costs based on token usage"""
        # Approximate pricing (adjust based on current Azure OpenAI pricing)
        input_token_cost = 0.00003  # $0.03 per 1K tokens
        output_token_cost = 0.00006  # $0.06 per 1K tokens
        
        # Assume 70% input tokens, 30% output tokens
        input_tokens = total_tokens * 0.7
        output_tokens = total_tokens * 0.3
        
        cost = (input_tokens * input_token_cost / 1000) + (output_tokens * output_token_cost / 1000)
        return round(cost, 4)
    
    def _calculate_performance_score(self, metrics: List[PerformanceMetrics]) -> int:
        """Calculate overall performance score (0-100)"""
        if not metrics:
            return 0
        
        # Factors: response time, cache hit rate, error rate
        avg_response_time = sum(m.response_time for m in metrics) / len(metrics)
        cache_hit_rate = sum(1 for m in metrics if m.cache_hit) / len(metrics)
        error_rate = sum(m.error_count for m in metrics) / len(metrics)
        
        # Scoring (higher is better)
        response_score = max(0, 100 - (avg_response_time * 10))  # Penalty for slow responses
        cache_score = cache_hit_rate * 30  # Bonus for cache hits
        error_score = max(0, 50 - (error_rate * 100))  # Penalty for errors
        
        total_score = min(100, response_score + cache_score + error_score)
        return round(total_score)
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations based on performance data"""
        recommendations = []
        
        # Analyze recent performance
        summary = self.get_performance_summary(24)
        
        if summary.get("average_response_time", 0) > 5.0:
            recommendations.append("Consider implementing more aggressive caching strategies")
        
        if summary.get("cache_hit_rate", 0) < 30:
            recommendations.append("Increase cache TTL and implement semantic caching")
        
        if summary.get("error_rate", 0) > 5:
            recommendations.append("Review error handling and implement retry mechanisms")
        
        # Analyze resource usage
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 80:
            recommendations.append("High CPU usage detected - consider scaling or optimization")
        
        if memory_percent > 85:
            recommendations.append("High memory usage - implement memory cleanup strategies")
        
        # Cost optimization
        if summary.get("total_tokens_used", 0) > 100000:  # High token usage
            recommendations.append("Consider reducing context length or implementing smarter chunking")
        
        return recommendations
    
    def cleanup_old_data(self, days: int = 7):
        """Clean up old performance data to save space"""
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        # Remove old daily stats
        old_dates = [date for date in self.daily_stats.keys() if date < cutoff_date]
        for date in old_dates:
            del self.daily_stats[date]
        
        # Remove old error logs
        cutoff_time = datetime.now() - timedelta(days=days)
        self.error_log = [error for error in self.error_log if error.get('timestamp', datetime.min) >= cutoff_time]
        
        self.logger.info(f"Cleaned up data older than {days} days")
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file for analysis"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "daily_stats": {str(date): stats for date, stats in self.daily_stats.items()},
            "recent_metrics": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "response_time": m.response_time,
                    "token_count": m.token_count,
                    "cache_hit": m.cache_hit,
                    "document_count": m.document_count,
                    "error_count": m.error_count
                }
                for m in list(self.metrics_history)[-100:]  # Last 100 metrics
            ],
            "performance_summary": self.get_performance_summary(24),
            "recommendations": self.get_optimization_recommendations()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Metrics exported to {filepath}")
    
    def monitor_system_resources(self) -> Dict[str, Any]:
        """Monitor system resource usage"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }
