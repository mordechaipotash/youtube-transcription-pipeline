# YouTube Transcription Pipeline

Automated YouTube video downloader with MacWhisper transcription integration, Supabase storage, and OpenRouter AI processing.

## Features

- 🎥 Automatic YouTube video/audio download every 2 hours
- 🎙️ MacWhisper Pro integration for high-quality transcription
- 💾 Supabase database for transcript storage
- 🤖 OpenRouter AI processing for summaries, chapters, and insights
- 🚂 Railway deployment ready

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python main.py
```

### 3. Railway Deployment

1. Connect this GitHub repository to Railway
2. Add all environment variables from `.env.example`
3. Deploy!

The cron job will automatically run every 2 hours to download new videos.

## Architecture

1. **YouTube Downloader**: Downloads videos/audio from configured channels
2. **MacWhisper Integration**: Watches folder for automatic transcription
3. **Transcript Processor**: Monitors transcripts and processes with AI
4. **Supabase Storage**: Stores all metadata and transcripts
5. **OpenRouter Processing**: Generates summaries, chapters, and insights

## Database Schema

- `channels`: YouTube channels to monitor
- `videos`: Downloaded video metadata
- `transcripts`: Raw transcriptions from MacWhisper
- `processed_content`: AI-generated summaries and insights

## Configuration

### Channel List

Add YouTube channel IDs to `CHANNEL_LIST` environment variable:

```
CHANNEL_LIST=UCddiUEpeqJcYeBxX1IVBKvQ,UCX6OQ3DkcsbYNE6H8uQQuVA
```

### MacWhisper Folder

Set `WATCHED_FOLDER` to your MacWhisper watched folder path:

```
WATCHED_FOLDER=/Users/mordechai/Youtube-macwhispper-watched-folder
```

## Monitoring

Check logs in Railway dashboard or locally with:

```bash
tail -f *.log
```