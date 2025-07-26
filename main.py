#!/usr/bin/env python3
import os
import sys
import logging
import schedule
import time
import threading
from youtube_downloader import YouTubeDownloader
from transcript_processor import TranscriptProcessor
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_downloader():
    """Run the YouTube downloader"""
    try:
        logger.info('Starting scheduled YouTube download')
        downloader = YouTubeDownloader()
        downloader.run()
    except Exception as e:
        logger.error(f'Error in scheduled download: {e}')

def run_transcript_processor():
    """Run the transcript processor in a separate thread"""
    processor = TranscriptProcessor()
    processor.run()

def main():
    """Main application entry point"""
    logger.info('Starting YouTube Transcription Pipeline')
    
    # Check if running in Railway with cron
    if os.getenv('RAILWAY_ENVIRONMENT'):
        # In Railway, just run the downloader once (cron will handle scheduling)
        run_downloader()
    else:
        # Local development - run both services
        # Start transcript processor in background thread
        processor_thread = threading.Thread(target=run_transcript_processor, daemon=True)
        processor_thread.start()
        
        # Schedule downloader every 2 hours
        schedule.every(2).hours.do(run_downloader)
        
        # Run immediately on startup
        run_downloader()
        
        # Keep running
        logger.info('Scheduler started. Downloads will run every 2 hours.')
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == '__main__':
    main()