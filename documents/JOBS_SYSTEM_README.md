# Jobs System - Scheduled RSS Digest Generation

The News02 Jobs System provides automated, scheduled digest generation using RSS profiles with configurable timing, models, and article limits.

## Features

### ✅ **RSS Profile Integration**
- Select any saved RSS profile for scheduled generation
- Profiles contain collections of RSS feeds grouped by topic/purpose
- Create profiles in the RSS Feeds page (`/feeds`)

### ✅ **Flexible Scheduling**
- **Time Format**: 24-hour format (HH:MM) for precise timing
- **Recurrence Options**:
  - `Once` - Single execution
  - `Daily` - Every day at specified time
  - `Weekdays` - Monday through Friday only
  - `Weekends` - Saturday and Sunday only

### ✅ **Model Configuration**
- **Summary Model**: Choose LLM for article summarization
- **Broadcast Model**: Choose LLM for final broadcast generation
- **Articles per Feed**: Control content volume (1-5 articles per feed)

### ✅ **Job Queue Management**
- **Conflict Prevention**: Only one job runs at a time
- **Queue System**: Multiple jobs scheduled for same time are queued
- **Real-time Status**: Live updates on job execution progress

### ✅ **Current Time Display**
- System time updates every second
- 24-hour format display for accurate scheduling
- Helps users plan job timing

## How to Use

### 1. Create RSS Profiles
Before scheduling jobs, create RSS profiles:

1. Go to **RSS Feeds** page (`/feeds`)
2. Add your desired RSS feed URLs
3. Click **"Manage Profiles"** button
4. Save current feeds as a named profile
5. Repeat for different feed collections (e.g., "Tech News", "World Events")

### 2. Schedule a Job

1. Navigate to **Jobs** page (`/jobs`)
2. Fill out the job form:
   - **Job Name**: Descriptive name (e.g., "Morning Tech News")
   - **Schedule Time**: Use 24-hour format (e.g., 07:30)
   - **RSS Profile**: Select from your saved profiles
   - **Articles per Feed**: Choose how many articles per RSS feed
   - **Models**: Select summary and broadcast generation models
   - **Recurrence**: Choose frequency
3. Click **"Schedule Job"**

### 3. Monitor Jobs

#### Job List
- View all scheduled jobs with status indicators
- Green play icon = enabled
- Yellow pause icon = disabled
- See next run time and last execution

#### Job Actions
- **👁 View**: See detailed job configuration and execution history
- **⏸ Pause/▶ Play**: Enable/disable job
- **▶ Run Now**: Execute immediately (added to queue)
- **🗑 Delete**: Remove job permanently

#### Real-time Status
- **Current Execution**: Shows running job progress
- **Job Queue**: Lists jobs waiting to execute
- **Statistics**: Track total, completed, pending, and failed jobs

## Technical Details

### Database Schema
```sql
-- Scheduled jobs configuration
scheduled_jobs (
    id TEXT PRIMARY KEY,           -- UUID
    name TEXT NOT NULL,            -- User-friendly name
    time TEXT NOT NULL,            -- HH:MM format
    profile TEXT NOT NULL,         -- RSS profile name
    articles_per_feed INTEGER,     -- Articles per RSS feed
    summary_model TEXT,            -- LLM model for summaries
    broadcast_model TEXT,          -- LLM model for broadcast
    recurrence TEXT,               -- once|daily|weekdays|weekends
    enabled BOOLEAN,               -- Job active status
    created_at TIMESTAMP,          -- Job creation time
    last_run TIMESTAMP,            -- Last execution time
    next_run TIMESTAMP,            -- Next scheduled time
    run_count INTEGER,             -- Total executions
    success_count INTEGER,         -- Successful executions
    last_error TEXT,               -- Last error message
    last_output TEXT               -- Last output file path
);

-- Job execution history
job_executions (
    id INTEGER PRIMARY KEY,
    job_id TEXT,                   -- Foreign key to scheduled_jobs
    started_at TIMESTAMP,          -- Execution start time
    completed_at TIMESTAMP,        -- Execution end time
    status TEXT,                   -- running|completed|failed
    error_message TEXT,            -- Error details if failed
    output_file TEXT,              -- Generated markdown file
    audio_file TEXT,               -- Generated audio file
    article_count INTEGER          -- Articles processed
);
```

### Job Execution Flow
1. **Scheduler Loop**: Checks for due jobs every 30 seconds
2. **Queue Management**: Immediate jobs and scheduled jobs share a queue
3. **Profile Loading**: Loads RSS feeds from selected profile
4. **Environment Setup**: Sets model and article count preferences
5. **Article Processing**: Fetches → Summarizes → Broadcasts → Saves
6. **File Generation**: Creates markdown digest and MP3 audio
7. **Status Updates**: Records execution results and schedules next run

### File Naming Convention
Generated files use job names for organization:
- **Markdown**: `{JobName}_{timestamp}.md`
- **Audio**: `{JobName}_{timestamp}.mp3`
- **Default**: `digest_{timestamp}.md` (manual generation)

### Conflict Resolution
- **Single Execution**: Only one job runs at a time
- **Queue System**: Conflicting jobs wait in execution queue
- **Priority**: Manual "Run Now" jobs take priority over scheduled jobs
- **Error Handling**: Failed jobs don't block subsequent executions

## API Endpoints

### Job Management
- `GET /api/scheduled_jobs` - List all jobs
- `POST /api/scheduled_jobs` - Create new job
- `GET /api/scheduled_jobs/{id}` - Get job details
- `DELETE /api/scheduled_jobs/{id}` - Delete job
- `POST /api/scheduled_jobs/{id}/enable` - Enable job
- `POST /api/scheduled_jobs/{id}/disable` - Disable job
- `POST /api/scheduled_jobs/{id}/run` - Run job immediately

### Status Monitoring
- `GET /api/job_status` - Current execution status and queue

### RSS Profiles (Used by Jobs)
- `GET /api/rss_profiles` - List all profiles
- `POST /api/rss_profiles` - Create/update profile
- `POST /api/rss_profiles/{name}/load` - Load profile into current feeds

## Example Usage Scenarios

### Scenario 1: Daily Morning Briefing
```
Job Name: "Morning World News"
Time: 06:30
Profile: "World Events" (contains BBC, Reuters, AP News feeds)
Recurrence: Daily
Articles per Feed: 2
Models: Gemini Flash for speed
```

### Scenario 2: Weekday Tech Updates
```
Job Name: "Tech Industry Updates"
Time: 09:00
Profile: "Technology" (contains TechCrunch, Ars Technica, Wired feeds)
Recurrence: Weekdays
Articles per Feed: 3
Models: Gemini Pro for detailed analysis
```

### Scenario 3: Weekend Summary
```
Job Name: "Weekend Wrap-up"
Time: 19:00
Profile: "General News" (contains CNN, NPR, Guardian feeds)
Recurrence: Weekends
Articles per Feed: 5
Models: Default models
```

## Troubleshooting

### Common Issues

**Job Not Running**
- Check if job is enabled (green play icon)
- Verify RSS profile exists and has valid feeds
- Check system time matches expected execution time
- Review job execution history for errors

**No Articles Generated**
- RSS feeds may be down or changed URLs
- Database may show all articles as already processed
- Try "Reset Processed" in Settings to allow reprocessing
- Verify RSS profile contains working feed URLs

**Audio Generation Fails**
- Check TTS settings in main Settings page
- Verify edge-tts is properly installed
- Check output directory permissions

**Jobs Queue Not Moving**
- Check if a job is stuck in "running" state
- Restart the web application to reset execution status
- Review logs for detailed error messages

### Logs and Debugging
- Job execution logs appear in the application console
- Detailed error messages stored in job execution history
- Use "View Details" button to see full job configuration and history

## Integration with Existing Features

### RSS Feeds Page
- Create and manage RSS profiles
- Test individual feeds before scheduling
- Import/export OPML files for profile management

### Settings Page
- Configure default models used by jobs
- Set TTS voice for audio generation
- Database settings affect job execution tracking

### History Page
- View all generated digests (manual and scheduled)
- Access past job outputs
- Review article processing statistics

### Lounge Page
- Play audio from scheduled job outputs
- Read generated digests
- Access source articles and metadata

---

## Security Notes

- Job execution uses same security context as manual generation
- RSS profiles stored in YAML files (not database) for portability
- No external job scheduling dependencies (self-contained)
- Jobs automatically disabled after single execution ("once" recurrence)

## Performance Considerations

- Jobs respect the same rate limiting as manual generation
- Multiple articles from same feed are processed sequentially
- Large RSS profiles may take longer to process
- Consider staggering job times to avoid resource conflicts

The Jobs System provides powerful automation while maintaining the flexibility and control of the manual digest generation process.