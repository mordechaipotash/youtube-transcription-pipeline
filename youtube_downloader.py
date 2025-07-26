#!/usr/bin/env python3
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import yt_dlp
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self):
        self.channel_list = os.getenv('CHANNEL_LIST', '').split(',')
        self.download_path = os.getenv('DOWNLOAD_PATH', '/tmp/downloads')
        self.watched_folder = os.getenv('WATCHED_FOLDER', '')
        self.max_videos = int(os.getenv('MAX_VIDEOS_PER_RUN', '10'))
        self.video_quality = os.getenv('VIDEO_QUALITY', 'best')
        
        # Initialize Supabase
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        
        # Create directories
        Path(self.download_path).mkdir(parents=True, exist_ok=True)
        if self.watched_folder:
            Path(self.watched_folder).mkdir(parents=True, exist_ok=True)
        
        # Configure yt-dlp
        self.ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.watched_folder, '%(channel)s/%(upload_date)s_%(title)s.%(ext)s'),
            'download_archive': 'downloaded.txt',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'keepvideo': True,
            'writethumbnail': True,
            'writeinfojson': True,
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'extract_flat': False,
        }
    
    def sync_channels(self):
        """Sync channel list with database"""
        for channel_id in self.channel_list:
            if not channel_id.strip():
                continue
                
            channel_url = f'https://www.youtube.com/channel/{channel_id}'
            
            try:
                # Get channel info
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(channel_url, download=False, process=False)
                    channel_name = info.get('uploader', channel_id)
                
                # Upsert channel to database
                self.supabase.table('channels').upsert({
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'channel_url': channel_url,
                    'is_active': True
                }, on_conflict='channel_id').execute()
                
                logger.info(f'Synced channel: {channel_name} ({channel_id})')
            except Exception as e:
                logger.error(f'Error syncing channel {channel_id}: {e}')
    
    def download_channel_videos(self, channel_id: str):
        """Download latest videos from a channel"""
        channel_url = f'https://www.youtube.com/channel/{channel_id}/videos'
        
        def progress_hook(d):
            if d['status'] == 'finished':
                logger.info(f"Downloaded: {d['filename']}")
        
        self.ydl_opts['progress_hooks'] = [progress_hook]
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Get channel videos
                info = ydl.extract_info(channel_url, download=False)
                
                # Get channel from database
                channel_result = self.supabase.table('channels').select('*').eq('channel_id', channel_id).single().execute()
                channel_db_id = channel_result.data['id']
                
                # Process only recent videos
                videos_processed = 0
                for entry in info['entries'][:self.max_videos]:
                    if videos_processed >= self.max_videos:
                        break
                    
                    video_id = entry['id']
                    
                    # Check if already in database
                    existing = self.supabase.table('videos').select('id').eq('video_id', video_id).execute()
                    if existing.data:
                        logger.info(f'Video {video_id} already processed, skipping')
                        continue
                    
                    # Insert video metadata
                    video_data = {
                        'channel_id': channel_db_id,
                        'video_id': video_id,
                        'title': entry.get('title', ''),
                        'description': entry.get('description', ''),
                        'duration': entry.get('duration', 0),
                        'upload_date': datetime.strptime(entry.get('upload_date', ''), '%Y%m%d').date() if entry.get('upload_date') else None,
                        'thumbnail_url': entry.get('thumbnail', ''),
                        'video_url': f"https://www.youtube.com/watch?v={video_id}",
                        'download_status': 'downloading'
                    }
                    
                    video_record = self.supabase.table('videos').insert(video_data).execute()
                    video_db_id = video_record.data[0]['id']
                    
                    # Download the video
                    try:
                        logger.info(f'Downloading: {entry["title"]}')
                        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                        
                        # Update status
                        self.supabase.table('videos').update({
                            'download_status': 'completed',
                            'downloaded_at': datetime.now().isoformat(),
                            'file_path': os.path.join(self.watched_folder, f"{entry.get('channel', 'unknown')}/{entry.get('upload_date', '')}_{entry.get('title', '')}.mp4")
                        }).eq('id', video_db_id).execute()
                        
                        videos_processed += 1
                        
                    except Exception as e:
                        logger.error(f'Error downloading video {video_id}: {e}')
                        self.supabase.table('videos').update({
                            'download_status': 'failed'
                        }).eq('id', video_db_id).execute()
                
                logger.info(f'Downloaded {videos_processed} videos from {channel_id}')
                
        except Exception as e:
            logger.error(f'Error processing channel {channel_id}: {e}')
    
    def run(self):
        """Main execution method"""
        logger.info('Starting YouTube download process')
        
        # Sync channels
        self.sync_channels()
        
        # Get active channels
        active_channels = self.supabase.table('channels').select('channel_id').eq('is_active', True).execute()
        
        # Download videos from each channel
        for channel in active_channels.data:
            logger.info(f"Processing channel: {channel['channel_id']}")
            self.download_channel_videos(channel['channel_id'])
        
        logger.info('Download process completed')

if __name__ == '__main__':
    downloader = YouTubeDownloader()
    downloader.run()