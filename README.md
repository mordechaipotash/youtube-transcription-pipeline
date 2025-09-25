# YouTube Knowledge Pipeline

> Production-grade automated video processing system with ML transcription, semantic search, and AI-powered content extraction.

## 📊 Production Metrics

- **6,095+ channels** monitored across tech, business, educational content
- **32,579+ videos** processed and catalogued
- **41.8M words** of searchable transcript content
- **99.9% storage compression** (MP3 → transcript conversion)
- **15,162 transcripts** generated with local ML
- **Zero ongoing API costs** (local AI/ML processing)

## 🎯 Problem & Solution

**Problem**: Consuming and retaining knowledge from thousands of hours of video content across hundreds of channels is impossible manually.

**Solution**: Automated pipeline that downloads, transcribes, and semantically indexes video content for instant searchability and AI-powered insights.

## ✨ Key Features

- 🎥 **Automated Download**: Monitors channels every 2 hours, downloads new content
- 🎙️ **Local ML Transcription**: MacWhisper Pro + Parakeet-MLX for offline processing
- 💾 **Semantic Storage**: PostgreSQL + pgvector for embedding-based search
- 🤖 **AI Processing**: OpenRouter integration for summaries, chapters, insights
- 📊 **Real-time Dashboard**: Next.js frontend for browsing and searching
- 🔄 **Incremental Processing**: Only processes new content, skips duplicates
- 🚂 **Production Ready**: Railway deployment, error recovery, monitoring

## 🏗️ Technical Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  yt-dlp         │─────▶│  MacWhisper Pro  │─────▶│  Parakeet-MLX   │
│  Downloader     │      │  File Watcher    │      │  Transcription  │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                                                    │
         ▼                                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Supabase PostgreSQL                             │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ Channels │  │  Videos  │  │ Transcripts │  │ Vector Embeddings│ │
│  └──────────┘  └──────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
         │                                                    │
         ▼                                                    ▼
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Next.js        │      │  OpenRouter AI   │      │  pgvector       │
│  Dashboard      │      │  Processing      │      │  Search         │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- MacWhisper Pro (for transcription)
- Supabase account
- Railway account (for deployment)

### Local Development

```bash
# Clone repository
git clone https://github.com/mordechaipotash/youtube-transcription-pipeline.git
cd youtube-transcription-pipeline

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run pipeline
python main.py
```

### Environment Variables

```bash
# YouTube Configuration
CHANNEL_LIST=UCxxxxx,UCyyyyy  # Comma-separated channel IDs

# Transcription
WATCHED_FOLDER=/path/to/macwhisper/folder

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# AI Processing (Optional)
OPENROUTER_API_KEY=your-key
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# Deployment
LOG_LEVEL=INFO
RAILWAY_ENVIRONMENT=production  # Auto-set by Railway
```

## 📁 Project Structure

```
youtube-transcription-pipeline/
├── main.py                      # Application entry point, scheduler
├── youtube_downloader.py        # yt-dlp integration, channel monitoring
├── transcript_processor.py      # MacWhisper integration, AI processing
├── requirements.txt             # Python dependencies
├── railway.toml                 # Railway deployment config
├── .env.example                 # Environment template
└── README.md
```

## 🗄️ Database Schema

**channels**
- `channel_id` (text, primary key)
- `channel_name`, `videos_count`, `status`, `last_check`
- `videos_found`, `videos_processed`

**youtube** (videos)
- `youtube_id` (text, unique)
- `title`, `description`, `url`
- `channel_name`, `channel_id`, `duration`
- `view_count`, `like_count`, `upload_date`
- `has_transcript`, `watch_count`

**Additional Tables**
- `transcripts`: Raw transcription data
- `processed_content`: AI summaries and insights

## 🔄 Processing Flow

1. **Discovery**: `youtube_downloader.py` checks configured channels for new videos
2. **Download**: Uses `yt-dlp` to download audio-only MP3 (storage efficient)
3. **Transcription**: MacWhisper Pro watches folder, auto-transcribes with Parakeet-MLX
4. **Processing**: `transcript_processor.py` detects new transcripts, generates embeddings
5. **AI Enhancement**: OpenRouter creates summaries, chapters, key points
6. **Storage**: All data stored in Supabase with vector embeddings for semantic search

## 🎛️ Deployment

### Railway (Recommended)

```bash
# Railway automatically deploys on push
railway up
```

Configuration:
- Add all env vars from `.env.example`
- Cron runs every 2 hours automatically
- Logs available in Railway dashboard

### Local with LaunchD/Cron

```bash
# Add to crontab for 2-hour intervals
0 */2 * * * cd /path/to/pipeline && python main.py
```

## 📈 Performance Characteristics

- **Processing Speed**: ~1 video/minute (download + transcribe)
- **Storage Efficiency**: 99.9% compression (video → audio → text)
- **Scalability**: Handles 6,000+ channels, 32,000+ videos
- **Cost**: $0/month API costs (local ML), minimal storage (~500MB for 41.8M words)
- **Reliability**: Error recovery, duplicate detection, incremental processing

## 🛠️ Tech Stack

**Core**:
- Python 3.9+
- yt-dlp (YouTube downloading)
- MacWhisper Pro (transcription)
- Parakeet-MLX (ML model)

**Data**:
- PostgreSQL 15+
- Supabase (database hosting)
- pgvector (semantic search)

**AI**:
- OpenRouter (LLM gateway)
- Anthropic Claude / OpenAI GPT
- Vector embeddings

**Infrastructure**:
- Railway (cloud hosting)
- LaunchD/Cron (scheduling)
- Environment-based configuration

## 🔍 Use Cases

1. **Personal Knowledge Base**: Build searchable library of educational content
2. **Research Assistant**: Find specific topics across thousands of videos
3. **Content Curation**: Track channels, analyze trends, discover patterns
4. **Learning Analytics**: Track consumption, measure topic coverage
5. **AI Training Data**: Clean transcripts for fine-tuning or RAG systems

## 🤝 Contributing

This is a personal project, but suggestions and improvements welcome via issues.

## 📝 License

MIT License - see LICENSE file for details

## 🔗 Related Projects

- [Sparkii Command Center](https://github.com/mordechaipotash/sparkii-command-center) - Full-stack dashboard for the pipeline
- [Google Apps Script Portfolio](https://github.com/mordechaipotash/google-apps-script-portfolio) - 41 automation solutions

---

**Status**: Production (300+ hours development, actively processing 32K+ videos)  
**Maintained**: Yes (regular updates and monitoring)