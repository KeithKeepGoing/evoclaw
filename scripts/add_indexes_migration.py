#!/usr/bin/env python3
"""
資料庫索引優化遷移腳本

為 EvoClaw 資料庫添加額外索引以提升查詢效能。
這些索引對於大型資料庫尤其重要。

使用方法：
    python -m scripts.add_indexes_migration

或者從 host 目錄下執行：
    python -c "from host.db import add_performance_indexes; add_performance_indexes()"
"""
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("evoclaw.migration")


def add_performance_indexes(db_path: Path) -> None:
    """
    為現有資料庫添加效能優化索引。
    
    這些索引包括：
    - immune_threats 表：pattern_hash, blocked 狀態
    - messages 表：sender, is_bot_message
    - scheduled_tasks 表：status, group_folder
    - task_run_logs 表：task_id, run_at
    - evolution_runs 表：success
    - group_genome 表：updated_at
    - chats 表：last_message_time
    """
    if not db_path.exists():
        log.error(f"Database not found: {db_path}")
        return
    
    log.info(f"Adding performance indexes to {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    indexes = [
        ("immune_threats", "idx_immune_pattern", "immune_threats(pattern_hash)"),
        ("immune_threats", "idx_immune_blocked", "immune_threats(blocked)"),
        ("messages", "idx_messages_sender", "messages(sender)"),
        ("messages", "idx_messages_bot", "messages(is_bot_message)"),
        ("scheduled_tasks", "idx_tasks_status", "scheduled_tasks(status)"),
        ("scheduled_tasks", "idx_tasks_group", "scheduled_tasks(group_folder)"),
        ("task_run_logs", "idx_task_logs_task", "task_run_logs(task_id)"),
        ("task_run_logs", "idx_task_logs_time", "task_run_logs(run_at)"),
        ("evolution_runs", "idx_evolution_success", "evolution_runs(success)"),
        ("group_genome", "idx_genome_updated", "group_genome(updated_at)"),
        ("chats", "idx_chats_last_msg", "chats(last_message_time)"),
    ]
    
    created = 0
    skipped = 0
    
    for table, idx_name, on_clause in indexes:
        try:
            # 檢查索引是否已存在
            exists = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name=?
            """, (idx_name,)).fetchone()
            
            if exists:
                log.debug(f"Index {idx_name} already exists, skipping")
                skipped += 1
                continue
            
            # 建立索引
            conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {on_clause}")
            log.info(f"Created index: {idx_name} ON {on_clause}")
            created += 1
            
        except Exception as e:
            log.error(f"Failed to create index {idx_name}: {e}")
    
    conn.commit()
    conn.close()
    
    log.info(f"Migration complete: {created} indexes created, {skipped} skipped")


if __name__ == "__main__":
    from host import config
    db_path = config.STORE_DIR / "messages.db"
    add_performance_indexes(db_path)
