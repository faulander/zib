# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-24-async-category-mark-read/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## Technical Requirements

- **Background job system** - Use asyncio tasks to process bulk operations without blocking API requests
- **Job tracking and status** - Provide unique job IDs and status tracking for background operations
- **Batch database operations** - Use efficient SQL batch operations instead of individual article updates
- **Real-time progress updates** - Send progress updates to frontend via WebSocket or polling mechanism
- **Memory efficient processing** - Process articles in chunks to avoid loading thousands of articles into memory
- **Graceful error handling** - Handle partial failures and continue processing remaining articles

## Approach Options

**Option A: Simple Asyncio Background Tasks**
- Pros: No new dependencies, integrates with existing FastAPI async, simple implementation
- Cons: Jobs don't persist across restarts, limited scalability, no advanced scheduling

**Option B: Database-Based Job Queue** (Selected)
- Pros: Persistent jobs, can track progress, integrates well with existing SQLite database
- Cons: Requires new database tables, more complex implementation

**Option C: External Job Queue (Redis/Celery)**
- Pros: Production-ready, scalable, advanced features
- Cons: New infrastructure dependency, overengineered for current needs

**Rationale:** Option B provides persistence and tracking while maintaining the self-contained nature of the RSS reader with SQLite.

## External Dependencies

- **No new major dependencies** - Use existing asyncio and SQLite capabilities

## Implementation Architecture

### Database Schema for Job Tracking

#### New Table: bulk_operation_jobs
```sql
CREATE TABLE bulk_operation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    user_id INTEGER NOT NULL,
    parameters TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_bulk_jobs_user_status ON bulk_operation_jobs (user_id, status);
CREATE INDEX idx_bulk_jobs_created ON bulk_operation_jobs (created_at);
```

### Job Processing System

#### BulkOperationManager
```python
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime

class BulkOperationManager:
    def __init__(self):
        self.active_jobs: Dict[int, asyncio.Task] = {}
    
    async def create_job(self, job_type: str, user_id: int, parameters: Dict[str, Any]) -> int:
        """Create a new bulk operation job"""
        job_data = {
            'job_type': job_type,
            'status': 'pending',
            'user_id': user_id,
            'parameters': json.dumps(parameters),
            'created_at': pendulum.now('UTC').to_datetime_string(),
            'total': await self._estimate_total_items(job_type, parameters)
        }
        
        job = BulkOperationJob.create(**job_data)
        
        # Start processing the job asynchronously
        task = asyncio.create_task(self._process_job(job.id))
        self.active_jobs[job.id] = task
        
        return job.id
    
    async def _process_job(self, job_id: int):
        """Process a bulk operation job"""
        try:
            job = BulkOperationJob.get_by_id(job_id)
            job.status = 'running'
            job.started_at = pendulum.now('UTC').to_datetime_string()
            job.save()
            
            parameters = json.loads(job.parameters)
            
            if job.job_type == 'mark_category_read':
                await self._process_mark_category_read(job_id, job.user_id, parameters)
            elif job.job_type == 'mark_feed_read':
                await self._process_mark_feed_read(job_id, job.user_id, parameters)
            
            # Mark job as completed
            job = BulkOperationJob.get_by_id(job_id)
            job.status = 'completed'
            job.completed_at = pendulum.now('UTC').to_datetime_string()
            job.save()
            
        except Exception as e:
            # Mark job as failed
            job = BulkOperationJob.get_by_id(job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = pendulum.now('UTC').to_datetime_string()
            job.save()
        finally:
            # Clean up active job tracking
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
```

### Optimized Database Operations

#### Batch Processing Strategy
```python
async def _process_mark_category_read(self, job_id: int, user_id: int, parameters: Dict[str, Any]):
    """Process mark category as read with batch operations"""
    category_id = parameters['category_id']
    batch_size = 100
    processed = 0
    
    # Get all article IDs in the category
    article_ids = list(
        Article
        .select(Article.id)
        .join(Feed)
        .where(Feed.category_id == category_id)
        .scalar()
    )
    
    total_articles = len(article_ids)
    
    # Update job with actual total
    job = BulkOperationJob.get_by_id(job_id)
    job.total = total_articles
    job.save()
    
    # Process in batches
    for i in range(0, total_articles, batch_size):
        batch_ids = article_ids[i:i + batch_size]
        
        # Use batch insert/update for efficiency
        await self._batch_mark_articles_read(user_id, batch_ids)
        
        processed += len(batch_ids)
        
        # Update progress
        job = BulkOperationJob.get_by_id(job_id)
        job.progress = processed
        job.save()
        
        # Small delay to prevent database lock contention
        await asyncio.sleep(0.1)

async def _batch_mark_articles_read(self, user_id: int, article_ids: List[int]):
    """Efficiently mark multiple articles as read using batch operations"""
    timestamp = pendulum.now('UTC').to_datetime_string()
    
    # First, update existing ReadStatus records
    ReadStatus.update(
        is_read=True,
        read_at=timestamp,
        updated_at=timestamp
    ).where(
        (ReadStatus.user_id == user_id) & 
        (ReadStatus.article_id.in_(article_ids))
    ).execute()
    
    # Then, insert new ReadStatus records for articles that don't have one
    existing_ids = set(
        ReadStatus
        .select(ReadStatus.article_id)
        .where(
            (ReadStatus.user_id == user_id) & 
            (ReadStatus.article_id.in_(article_ids))
        )
        .scalar()
    )
    
    new_article_ids = [aid for aid in article_ids if aid not in existing_ids]
    
    if new_article_ids:
        batch_data = [
            {
                'user_id': user_id,
                'article_id': article_id,
                'is_read': True,
                'read_at': timestamp,
                'created_at': timestamp,
                'updated_at': timestamp
            }
            for article_id in new_article_ids
        ]
        
        ReadStatus.insert_many(batch_data).execute()
```

### API Endpoint Changes

#### Async Category Mark-as-Read Endpoint
```python
@router.post("/bulk/mark-read-by-category/{category_id}", response_model=BulkJobResponse)
async def bulk_mark_read_by_category_async(
    category_id: int,
    current_user: User = Depends(get_current_user)
):
    """Start async bulk mark all articles in a category as read"""
    
    try:
        # Create background job
        job_id = await bulk_operation_manager.create_job(
            job_type='mark_category_read',
            user_id=current_user.id,
            parameters={'category_id': category_id}
        )
        
        return BulkJobResponse(
            job_id=job_id,
            status='pending',
            message=f"Bulk mark-as-read job created for category {category_id}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bulk mark-as-read job: {str(e)}"
        )

@router.get("/bulk/jobs/{job_id}", response_model=BulkJobStatus)
async def get_bulk_job_status(
    job_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get status of a bulk operation job"""
    
    try:
        job = BulkOperationJob.get(
            (BulkOperationJob.id == job_id) & 
            (BulkOperationJob.user_id == current_user.id)
        )
        
        return BulkJobStatus(
            job_id=job.id,
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            total=job.total,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )
        
    except BulkOperationJob.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
```

### Frontend Integration

#### Job Polling and Progress Updates
```javascript
async function markCategoryAsReadAsync(categoryId) {
    try {
        // Start the async job
        const response = await api.post(`/api/articles/bulk/mark-read-by-category/${categoryId}`);
        const { job_id } = response.data;
        
        // Poll for progress
        return await pollJobProgress(job_id);
        
    } catch (error) {
        console.error('Failed to start async mark-as-read:', error);
        throw error;
    }
}

async function pollJobProgress(jobId, onProgress = null) {
    const pollInterval = 1000; // Poll every second
    const maxPollTime = 300000; // Maximum 5 minutes
    const startTime = Date.now();
    
    return new Promise((resolve, reject) => {
        const poll = async () => {
            try {
                if (Date.now() - startTime > maxPollTime) {
                    reject(new Error('Job polling timeout'));
                    return;
                }
                
                const statusResponse = await api.get(`/api/articles/bulk/jobs/${jobId}`);
                const status = statusResponse.data;
                
                // Notify progress callback
                if (onProgress) {
                    onProgress(status);
                }
                
                if (status.status === 'completed') {
                    resolve(status);
                } else if (status.status === 'failed') {
                    reject(new Error(status.error_message));
                } else {
                    // Continue polling
                    setTimeout(poll, pollInterval);
                }
                
            } catch (error) {
                reject(error);
            }
        };
        
        poll();
    });
}
```

### Progress UI Component
```svelte
<script>
    let jobStatus = null;
    let showProgress = false;
    
    async function handleMarkCategoryAsRead(categoryId) {
        showProgress = true;
        
        try {
            await markCategoryAsReadAsync(categoryId, (status) => {
                jobStatus = status;
                // Update UI with progress
                const percentage = Math.round((status.progress / status.total) * 100);
                console.log(`Progress: ${percentage}%`);
            });
            
            // Job completed successfully
            showProgress = false;
            // Refresh article counts and UI
            await refreshData();
            
        } catch (error) {
            showProgress = false;
            console.error('Mark as read failed:', error);
        }
    }
</script>

{#if showProgress && jobStatus}
    <div class="progress-overlay">
        <div class="progress-bar">
            <div class="progress-fill" style="width: {(jobStatus.progress / jobStatus.total) * 100}%"></div>
        </div>
        <p>Marking articles as read... {jobStatus.progress}/{jobStatus.total}</p>
    </div>
{/if}
```