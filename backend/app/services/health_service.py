import time
from typing import Dict, Any
from app.core.database import db
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class HealthService:
    '''Service for system health monitoring'''
    
    @staticmethod
    def get_basic_health() -> Dict[str, Any]:
        '''Get basic health information'''
        return {
            'status': 'healthy',
            'app_name': settings.app_name,
            'version': settings.app_version,
            'debug': settings.debug,
            'timestamp': time.time()
        }
    
    @staticmethod
    def check_database_health() -> Dict[str, Any]:
        '''Check database connectivity and performance'''
        try:
            start_time = time.time()
            
            # Test database connection
            db.connect(reuse_if_open=True)
            
            # Test a simple query
            result = db.execute_sql('SELECT 1 as test').fetchone()
            
            end_time = time.time()
            connection_time_ms = round((end_time - start_time) * 1000, 2)
            
            if result and result[0] == 1:
                return {
                    'status': 'connected',
                    'connection_time_ms': connection_time_ms,
                    'database_type': 'sqlite',
                    'database_path': settings.database_url.replace('sqlite:///', ''),
                    'timestamp': time.time()
                }
            else:
                return {
                    'status': 'error',
                    'error': 'Database query failed',
                    'connection_time_ms': connection_time_ms,
                    'timestamp': time.time()
                }
                
        except Exception as e:
            logger.error(f'Database health check failed: {e}')
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
        finally:
            try:
                db.close()
            except:
                pass
    
    @staticmethod
    def get_comprehensive_health(check_db: bool = False) -> Dict[str, Any]:
        '''Get comprehensive health information'''
        health_data = HealthService.get_basic_health()
        
        if check_db:
            health_data['database'] = HealthService.check_database_health()
            
            # Update overall status based on database health
            if health_data['database']['status'] != 'connected':
                health_data['status'] = 'degraded'
        
        return health_data
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        '''Get system information for monitoring'''
        import sys
        import platform
        
        return {
            'python_version': sys.version,
            'platform': platform.platform(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'hostname': platform.node(),
            'timestamp': time.time()
        }