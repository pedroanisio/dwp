import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from ..models.chain import (
    ChainDefinition, ChainExecutionResult, ChainTemplate, 
    ChainAnalytics, ChainValidationResult
)


class ChainFileStorage:
    """Enhanced file-based storage with metadata indexing"""
    
    def __init__(self, base_dir: str = "app/data"):
        self.base_dir = Path(base_dir)
        self.chains_dir = self.base_dir / "chains" / "definitions"
        self.executions_dir = self.base_dir / "chains" / "executions"
        self.templates_dir = self.base_dir / "chains" / "templates"
        self.metadata_file = self.base_dir / "chains" / "metadata.json"
        
        # Create directory structure
        for dir_path in [self.chains_dir, self.executions_dir, self.templates_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_chain(self, chain: ChainDefinition) -> bool:
        """Save chain with metadata tracking"""
        try:
            # Update timestamps
            chain.updated_at = datetime.now().isoformat()
            
            # Save chain definition
            chain_file = self.chains_dir / f"{chain.id}.json"
            with open(chain_file, 'w', encoding='utf-8') as f:
                json.dump(chain.dict(), f, indent=2, ensure_ascii=False)
            
            # Update metadata index
            self._update_metadata_index(chain)
            return True
            
        except Exception as e:
            print(f"Failed to save chain {chain.id}: {e}")
            return False
    
    def load_chain(self, chain_id: str) -> Optional[ChainDefinition]:
        """Load chain definition from disk"""
        try:
            chain_file = self.chains_dir / f"{chain_id}.json"
            if not chain_file.exists():
                return None
                
            with open(chain_file, 'r', encoding='utf-8') as f:
                chain_data = json.load(f)
            return ChainDefinition(**chain_data)
            
        except Exception as e:
            print(f"Failed to load chain {chain_id}: {e}")
            return None
    
    def list_chains(self, tags: List[str] = None, template_only: bool = False) -> List[ChainDefinition]:
        """List all available chains with optional filtering"""
        chains = []
        metadata = self._load_metadata_index()
        
        for chain_id, chain_meta in metadata.items():
            # Filter by template status
            if template_only and not chain_meta.get("is_template", False):
                continue
                
            # Filter by tags
            if tags and not any(tag in chain_meta.get("tags", []) for tag in tags):
                continue
            
            chain = self.load_chain(chain_id)
            if chain:
                chains.append(chain)
        
        return sorted(chains, key=lambda x: x.updated_at, reverse=True)
    
    def delete_chain(self, chain_id: str) -> bool:
        """Delete chain and update metadata"""
        try:
            chain_file = self.chains_dir / f"{chain_id}.json"
            if chain_file.exists():
                chain_file.unlink()
            
            # Update metadata index
            metadata = self._load_metadata_index()
            if chain_id in metadata:
                del metadata[chain_id]
                self._save_metadata_index(metadata)
            
            return True
            
        except Exception as e:
            print(f"Failed to delete chain {chain_id}: {e}")
            return False
    
    def search_chains(self, query: str = "", tags: List[str] = None) -> List[Dict[str, Any]]:
        """Search chains by name, description, or tags"""
        metadata = self._load_metadata_index()
        results = []
        
        for chain_id, chain_meta in metadata.items():
            # Text search
            if query:
                query_lower = query.lower()
                if (query_lower not in chain_meta.get("name", "").lower() and 
                    query_lower not in chain_meta.get("description", "").lower()):
                    continue
            
            # Tag filtering
            if tags and not any(tag in chain_meta.get("tags", []) for tag in tags):
                continue
            
            results.append({
                "id": chain_id,
                **chain_meta
            })
        
        return sorted(results, key=lambda x: x.get("updated_at", ""), reverse=True)
    
    def save_execution_result(self, result: ChainExecutionResult) -> bool:
        """Save execution results for history/debugging"""
        try:
            # Organize by date
            date_str = datetime.fromisoformat(result.started_at.replace('Z', '+00:00')).strftime("%Y-%m-%d")
            date_dir = self.executions_dir / date_str
            date_dir.mkdir(exist_ok=True)
            
            # Save execution result
            exec_file = date_dir / f"{result.execution_id}.json"
            with open(exec_file, 'w', encoding='utf-8') as f:
                json.dump(result.dict(), f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            print(f"Failed to save execution result: {e}")
            return False
    
    def get_execution_history(self, chain_id: str, limit: int = 50) -> List[ChainExecutionResult]:
        """Get execution history for a chain"""
        executions = []
        
        # Scan execution directories
        for date_dir in sorted(self.executions_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
                
            for exec_file in sorted(date_dir.glob("*.json"), reverse=True):
                try:
                    with open(exec_file, 'r', encoding='utf-8') as f:
                        exec_data = json.load(f)
                    
                    if exec_data.get("chain_id") == chain_id:
                        executions.append(ChainExecutionResult(**exec_data))
                        
                    if len(executions) >= limit:
                        return executions
                        
                except Exception:
                    continue
        
        return executions
    
    def save_template(self, template: ChainTemplate) -> bool:
        """Save chain template"""
        try:
            template_file = self.templates_dir / f"{template.id}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template.dict(), f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            print(f"Failed to save template {template.id}: {e}")
            return False
    
    def load_template(self, template_id: str) -> Optional[ChainTemplate]:
        """Load chain template"""
        try:
            template_file = self.templates_dir / f"{template_id}.json"
            if not template_file.exists():
                return None
                
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            return ChainTemplate(**template_data)
            
        except Exception as e:
            print(f"Failed to load template {template_id}: {e}")
            return None
    
    def list_templates(self, category: str = None) -> List[ChainTemplate]:
        """List all available templates"""
        templates = []
        
        for template_file in self.templates_dir.glob("*.json"):
            try:
                template = self.load_template(template_file.stem)
                if template and (not category or template.category == category):
                    templates.append(template)
            except Exception:
                continue
        
        return sorted(templates, key=lambda x: x.name)
    
    def _update_metadata_index(self, chain: ChainDefinition):
        """Maintain searchable metadata index"""
        metadata = self._load_metadata_index()
        
        metadata[chain.id] = {
            "name": chain.name,
            "description": chain.description,
            "version": chain.version,
            "tags": chain.tags,
            "is_template": chain.is_template,
            "created_at": chain.created_at,
            "updated_at": chain.updated_at,
            "author": chain.author,
            "node_count": len(chain.nodes),
            "connection_count": len(chain.connections),
            "plugin_types": list(set(node.plugin_id for node in chain.nodes if node.plugin_id))
        }
        
        self._save_metadata_index(metadata)
    
    def _load_metadata_index(self) -> Dict[str, Any]:
        """Load metadata index"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_metadata_index(self, metadata: Dict[str, Any]):
        """Save metadata index"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save metadata index: {e}")


class ChainDatabaseStorage:
    """SQLite-based storage for enhanced analytics and querying"""
    
    def __init__(self, db_path: str = "app/data/chains.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS chains (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT,
                    definition TEXT,  -- JSON blob
                    input_schema TEXT,  -- JSON blob
                    output_schema TEXT,  -- JSON blob
                    tags TEXT,  -- JSON array
                    is_template BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    author TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS chain_executions (
                    id TEXT PRIMARY KEY,
                    chain_id TEXT,
                    input_data TEXT,  -- JSON blob
                    output_data TEXT,  -- JSON blob
                    node_results TEXT,  -- JSON blob  
                    execution_time REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    execution_graph TEXT,  -- JSON blob
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (chain_id) REFERENCES chains (id)
                );
                
                CREATE TABLE IF NOT EXISTS chain_analytics (
                    chain_id TEXT PRIMARY KEY,
                    total_executions INTEGER DEFAULT 0,
                    successful_executions INTEGER DEFAULT 0,
                    failed_executions INTEGER DEFAULT 0,
                    average_execution_time REAL DEFAULT 0.0,
                    last_execution TIMESTAMP,
                    success_rate REAL DEFAULT 0.0,
                    most_common_errors TEXT,  -- JSON blob
                    performance_trend TEXT,  -- JSON blob
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chain_id) REFERENCES chains (id)
                );
                
                CREATE TABLE IF NOT EXISTS chain_sharing (
                    id TEXT PRIMARY KEY,
                    chain_id TEXT,
                    shared_by TEXT,
                    shared_with TEXT,
                    permissions TEXT,  -- JSON: read, write, execute
                    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chain_id) REFERENCES chains (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_chains_name ON chains(name);
                CREATE INDEX IF NOT EXISTS idx_chains_tags ON chains(tags);
                CREATE INDEX IF NOT EXISTS idx_chains_updated ON chains(updated_at);
                CREATE INDEX IF NOT EXISTS idx_executions_chain ON chain_executions(chain_id);
                CREATE INDEX IF NOT EXISTS idx_executions_date ON chain_executions(started_at);
                CREATE INDEX IF NOT EXISTS idx_executions_success ON chain_executions(success);
            """)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def save_execution_to_db(self, result: ChainExecutionResult) -> bool:
        """Save execution result to database"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO chain_executions (
                        id, chain_id, input_data, output_data, node_results,
                        execution_time, success, error_message, execution_graph,
                        started_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.execution_id,
                    result.chain_id,
                    json.dumps({}),  # input_data would need to be passed separately
                    json.dumps(result.results),
                    json.dumps(result.node_results),
                    result.execution_time,
                    result.success,
                    result.error,
                    json.dumps(result.execution_graph),
                    result.started_at,
                    result.completed_at
                ))
                
                # Update analytics
                self._update_chain_analytics(conn, result.chain_id)
                
            return True
            
        except Exception as e:
            print(f"Failed to save execution to database: {e}")
            return False
    
    def get_chain_analytics(self, chain_id: str) -> Optional[ChainAnalytics]:
        """Get execution analytics for a chain"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM chain_analytics WHERE chain_id = ?
                """, (chain_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return ChainAnalytics(
                    chain_id=row['chain_id'],
                    total_executions=row['total_executions'],
                    successful_executions=row['successful_executions'],
                    failed_executions=row['failed_executions'],
                    average_execution_time=row['average_execution_time'],
                    last_execution=row['last_execution'],
                    success_rate=row['success_rate'],
                    most_common_errors=json.loads(row['most_common_errors'] or '[]'),
                    performance_trend=json.loads(row['performance_trend'] or '[]')
                )
                
        except Exception as e:
            print(f"Failed to get chain analytics: {e}")
            return None
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get overall stats
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT chain_id) as total_chains,
                        COUNT(*) as total_executions,
                        AVG(execution_time) as avg_execution_time,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_executions
                    FROM chain_executions
                """)
                
                stats = cursor.fetchone()
                
                # Get popular chains
                cursor.execute("""
                    SELECT 
                        c.name,
                        COUNT(e.id) as execution_count,
                        AVG(e.execution_time) as avg_time
                    FROM chains c
                    LEFT JOIN chain_executions e ON c.id = e.chain_id
                    GROUP BY c.id, c.name
                    ORDER BY execution_count DESC
                    LIMIT 10
                """)
                
                popular_chains = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "total_chains": stats['total_chains'] or 0,
                    "total_executions": stats['total_executions'] or 0,
                    "average_execution_time": stats['avg_execution_time'] or 0,
                    "success_rate": (stats['successful_executions'] / stats['total_executions'] * 100) if stats['total_executions'] else 0,
                    "popular_chains": popular_chains
                }
                
        except Exception as e:
            print(f"Failed to get system analytics: {e}")
            return {}
    
    def _update_chain_analytics(self, conn: sqlite3.Connection, chain_id: str):
        """Update analytics for a chain"""
        cursor = conn.cursor()
        
        # Calculate new analytics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_executions,
                AVG(execution_time) as avg_execution_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_executions,
                MAX(completed_at) as last_execution
            FROM chain_executions 
            WHERE chain_id = ?
        """, (chain_id,))
        
        result = cursor.fetchone()
        if not result or not result['total_executions']:
            return
        
        total = result['total_executions']
        successful = result['successful_executions']
        success_rate = (successful / total * 100) if total > 0 else 0
        
        # Update or insert analytics
        cursor.execute("""
            INSERT OR REPLACE INTO chain_analytics (
                chain_id, total_executions, successful_executions, 
                failed_executions, average_execution_time, last_execution,
                success_rate, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            chain_id,
            total,
            successful,
            total - successful,
            result['avg_execution_time'],
            result['last_execution'],
            success_rate
        ))


class ChainStorageManager:
    """Unified interface for both file and database storage"""
    
    def __init__(self, base_dir: str = "app/data"):
        self.file_storage = ChainFileStorage(base_dir)
        self.db_storage = ChainDatabaseStorage(f"{base_dir}/chains.db")
    
    def save_chain(self, chain: ChainDefinition) -> bool:
        """Save chain to file storage"""
        return self.file_storage.save_chain(chain)
    
    def load_chain(self, chain_id: str) -> Optional[ChainDefinition]:
        """Load chain from file storage"""
        return self.file_storage.load_chain(chain_id)
    
    def list_chains(self, **kwargs) -> List[ChainDefinition]:
        """List chains from file storage"""
        return self.file_storage.list_chains(**kwargs)
    
    def delete_chain(self, chain_id: str) -> bool:
        """Delete chain from both storages"""
        return self.file_storage.delete_chain(chain_id)
    
    def search_chains(self, **kwargs) -> List[Dict[str, Any]]:
        """Search chains"""
        return self.file_storage.search_chains(**kwargs)
    
    def save_execution_result(self, result: ChainExecutionResult) -> bool:
        """Save execution result to both storages"""
        file_success = self.file_storage.save_execution_result(result)
        db_success = self.db_storage.save_execution_to_db(result)
        return file_success  # File storage is primary
    
    def get_execution_history(self, chain_id: str, limit: int = 50) -> List[ChainExecutionResult]:
        """Get execution history"""
        return self.file_storage.get_execution_history(chain_id, limit)
    
    def get_chain_analytics(self, chain_id: str) -> Optional[ChainAnalytics]:
        """Get chain analytics from database"""
        return self.db_storage.get_chain_analytics(chain_id)
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get system analytics"""
        return self.db_storage.get_system_analytics()
    
    def save_template(self, template: ChainTemplate) -> bool:
        """Save chain template"""
        return self.file_storage.save_template(template)
    
    def load_template(self, template_id: str) -> Optional[ChainTemplate]:
        """Load chain template"""
        return self.file_storage.load_template(template_id)
    
    def list_templates(self, **kwargs) -> List[ChainTemplate]:
        """List templates"""
        return self.file_storage.list_templates(**kwargs) 