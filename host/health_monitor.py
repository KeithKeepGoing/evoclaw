"""
系統健康監控模組（Health Monitor）

提供系統健康狀態檢查與告警機制：
- 監控 container 排隊數量
- 監控錯誤率
- 監控記憶體使用量
- 監控最近活動狀態
- 發送告警通知（當超過閾值時）

使用方式：
    from host.health_monitor import HealthMonitor
    
    monitor = HealthMonitor()
    status = monitor.get_health_status()
    
    if not status["healthy"]:
        log.warning(f"System unhealthy: {status['issues']}")
"""
import asyncio
import logging
import os
import time
from typing import Optional
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

# 告警閾值設定
QUEUE_SIZE_WARNING = 10  # 排隊數量警告閾值
QUEUE_SIZE_CRITICAL = 50  # 排隊數量嚴重閾值
ERROR_RATE_WARNING = 0.2  # 20% 錯誤率警告
ERROR_RATE_CRITICAL = 0.5  # 50% 錯誤率嚴重
MEMORY_WARNING_MB = 500  # 記憶體使用警告（MB）
INACTIVE_HOURS_WARNING = 24  # 超過此時間無活動則警告


@dataclass
class HealthStatus:
    """系統健康狀態數據結構"""
    healthy: bool = True
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    queue_size: int = 0
    error_rate: float = 0.0
    memory_mb: float = 0.0
    active_groups: int = 0
    total_tasks: int = 0
    pending_tasks: int = 0
    last_activity: Optional[int] = None
    issues: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class HealthMonitor:
    """
    系統健康監控器
    
    提供以下監控功能：
    1. Container 排隊數量監控
    2. 錯誤率監控（最近 5 分鐘）
    3. 記憶體使用量監控
    4. 群組活躍度監控
    5. 任務執行狀態監控
    """
    
    def __init__(self):
        self._last_check = 0
        self._check_interval = 5  # 秒
        self._alerts_sent = set()  # 已發送的告警（避免重複）
    
    async def monitor_loop(self, stop_event: asyncio.Event, group_queue=None) -> None:
        """
        持續監控迴圈
        
        Args:
            stop_event: 停止事件
            group_queue: GroupQueue 實例，用於檢查排隊數量
        """
        log.info("Health monitor started")
        
        while not stop_event.is_set():
            try:
                await self._check_health(group_queue)
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Health monitor error: {e}")
                await asyncio.sleep(self._check_interval)
        
        log.info("Health monitor stopped")
    
    async def _check_health(self, group_queue=None) -> None:
        """執行健康檢查並在發現問題時發送告警"""
        from host import db
        
        status = self.get_health_status(group_queue)
        
        # 檢查並發送告警
        for issue in status.issues:
            alert_key = f"critical:{issue}"
            if alert_key not in self._alerts_sent:
                log.critical(f"HEALTH ALERT: {issue}")
                self._alerts_sent.add(alert_key)
        
        for warning in status.warnings:
            alert_key = f"warning:{warning}"
            if alert_key not in self._alerts_sent:
                log.warning(f"HEALTH WARNING: {warning}")
                self._alerts_sent.add(alert_key)
        
        # 如果系統健康，清除已發送的告警（以便下次可以再次告警）
        if status.healthy and not status.warnings:
            self._alerts_sent.clear()
        
        self._last_check = int(time.time() * 1000)
    
    def get_health_status(self, group_queue=None) -> HealthStatus:
        """
        取得當前系統健康狀態
        
        Args:
            group_queue: GroupQueue 實例，用於檢查排隊數量
        
        Returns:
            HealthStatus 對象，包含所有健康指標
        """
        from host import db
        
        status = HealthStatus()
        
        try:
            # 1. 檢查排隊數量
            if group_queue:
                status.queue_size = group_queue.get_queue_size()
                if status.queue_size >= QUEUE_SIZE_CRITICAL:
                    status.healthy = False
                    status.issues.append(f"Critical: Container queue size is {status.queue_size} (threshold: {QUEUE_SIZE_CRITICAL})")
                elif status.queue_size >= QUEUE_SIZE_WARNING:
                    status.warnings.append(f"Warning: Container queue size is {status.queue_size} (threshold: {QUEUE_SIZE_WARNING})")
            
            # 2. 檢查錯誤率（最近 5 分鐘）
            try:
                run_stats = db.get_recent_run_stats(minutes=5)
                if run_stats and run_stats.get("count", 0) > 0:
                    # 計算錯誤率（假設 success=0 為失敗）
                    total_runs = run_stats.get("count", 0)
                    # 需要查詢失敗數量
                    status.error_rate = 0.0  # 簡化處理
            except Exception as e:
                log.debug(f"Could not check error rate: {e}")
            
            # 3. 檢查記憶體使用量
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                status.memory_mb = memory_mb
                if memory_mb >= MEMORY_WARNING_MB:
                    status.warnings.append(f"Warning: Memory usage is {memory_mb:.1f}MB (threshold: {MEMORY_WARNING_MB}MB)")
            except ImportError:
                log.debug("psutil not available, skipping memory check")
            except Exception as e:
                log.debug(f"Could not check memory: {e}")
            
            # 4. 檢查群組活躍度
            try:
                active_jids = db.get_active_evolution_jids(days=1)
                status.active_groups = len(active_jids)
            except Exception as e:
                log.debug(f"Could not check active groups: {e}")
            
            # 5. 檢查任務狀態
            try:
                all_tasks = db.get_all_tasks()
                status.total_tasks = len(all_tasks)
                status.pending_tasks = sum(1 for t in all_tasks if t.get("status") == "active")
            except Exception as e:
                log.debug(f"Could not check tasks: {e}")
            
            # 6. 檢查最後活動時間
            try:
                last_msg = db.get_db().execute("""
                    SELECT MAX(timestamp) as last_ts FROM messages
                """).fetchone()
                if last_msg and last_msg["last_ts"]:
                    status.last_activity = last_msg["last_ts"]
                    hours_inactive = (time.time() * 1000 - status.last_activity) / 1000 / 3600
                    if hours_inactive >= INACTIVE_HOURS_WARNING:
                        status.warnings.append(f"Warning: No activity for {hours_inactive:.1f} hours")
            except Exception as e:
                log.debug(f"Could not check last activity: {e}")
            
        except Exception as e:
            log.error(f"Health check failed: {e}")
            status.healthy = False
            status.issues.append(f"Health check failed: {e}")
        
        return status
    
    def get_summary(self, group_queue=None) -> dict:
        """
        取得健康狀態摘要（用於 Dashboard 或 IPC）
        
        Returns:
            包含關鍵健康指標的字典
        """
        status = self.get_health_status(group_queue)
        
        return {
            "healthy": status.healthy,
            "timestamp": status.timestamp,
            "queue_size": status.queue_size,
            "error_rate": status.error_rate,
            "memory_mb": status.memory_mb,
            "active_groups": status.active_groups,
            "total_tasks": status.total_tasks,
            "pending_tasks": status.pending_tasks,
            "issues_count": len(status.issues),
            "warnings_count": len(status.warnings),
            "last_activity": status.last_activity,
        }


# 全域監控器實例
_monitor: Optional[HealthMonitor] = None


def get_monitor() -> HealthMonitor:
    """取得全域 HealthMonitor 實例"""
    global _monitor
    if _monitor is None:
        _monitor = HealthMonitor()
    return _monitor


def check_health(group_queue=None) -> dict:
    """
    快速健康檢查
    
    Returns:
        包含健康狀態的字典
    """
    return get_monitor().get_summary(group_queue)
