#!/usr/bin/env python3
import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import openai
from supabase import create_client, Client
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranscriptHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor
        self.pattern = os.getenv('TRANSCRIPT_FILE_PATTERN', '*_transcript.txt')
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('_transcript.txt'):
            logger.info(f'New transcript detected: {event.src_path}')
            # Wait a bit to ensure file is completely written
            time.sleep(2)
            self.processor.process_transcript(event.src_path)

class TranscriptProcessor:
    def __init__(self):
        self.watched_folder = os.getenv('WATCHED_FOLDER', '')
        
        # Initialize Supabase
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        
        # Initialize OpenRouter (uses OpenAI client)
        self.openai_client = openai.Client(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        )
        
        # Processing prompts
        self.prompts = {
            'summary': """Summarize this YouTube video transcript in 3-5 paragraphs. Include key points and main takeaways. Transcript: {transcript}""",
            'chapters': """Create chapter timestamps for this video transcript. Format each line as: [HH:MM:SS] Chapter Title. Transcript: {transcript}""",
            'keywords': """Extract 10-15 important keywords/phrases from this transcript. Focus on technical terms, topics, and key concepts. Return as a comma-separated list. Transcript: {transcript}""",
            'insights': """Analyze this transcript and provide: 1. Main topic and subtopics, 2. Key insights or learnings, 3. Actionable takeaways, 4. Related topics to explore. Format as JSON. Transcript: {transcript}"""
        }
        
        self.models = {
            'summary': 'anthropic/claude-3-haiku',
            'chapters': 'openai/gpt-4-turbo',
            'keywords': 'anthropic/claude-3-haiku',
            'insights': 'anthropic/claude-3-sonnet'
        }
    
    def find_video_by_filename(self, transcript_path: str) -> Optional[Dict]:
        """Find video record by matching filename pattern"""
        filename = Path(transcript_path).stem.replace('_transcript', '')
        
        # Try to extract video info from filename
        # Expected format: YYYYMMDD_Title
        parts = filename.split('_', 1)
        if len(parts) >= 2:
            date_str = parts[0]
            title_part = parts[1]
            
            # Search for video by title similarity
            result = self.supabase.table('videos').select('*').ilike('title', f'%{title_part[:20]}%').execute()
            if result.data:
                return result.data[0]
        
        return None
    
    def process_transcript(self, transcript_path: str):
        """Process a new transcript file"""
        try:
            # Read transcript
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
            
            # Find associated video
            video = self.find_video_by_filename(transcript_path)
            if not video:
                logger.warning(f'Could not find video for transcript: {transcript_path}')
                return
            
            # Save transcript to database
            word_count = len(transcript_text.split())
            transcript_record = self.supabase.table('transcripts').insert({
                'video_id': video['id'],
                'raw_transcript': transcript_text,
                'transcript_format': 'txt',
                'word_count': word_count,
                'language': 'en',
                'transcribed_at': datetime.now().isoformat()
            }).execute()
            
            transcript_id = transcript_record.data[0]['id']
            logger.info(f'Saved transcript for video: {video["title"]}')
            
            # Process with AI
            self.process_with_ai(transcript_id, transcript_text)
            
        except Exception as e:
            logger.error(f'Error processing transcript {transcript_path}: {e}')
    
    def process_with_ai(self, transcript_id: str, transcript_text: str):
        """Process transcript with OpenRouter AI models"""
        for process_type, prompt_template in self.prompts.items():
            try:
                start_time = time.time()
                
                # Prepare prompt
                prompt = prompt_template.format(transcript=transcript_text[:8000])  # Limit context
                
                # Call OpenRouter
                response = self.openai_client.chat.completions.create(
                    model=self.models[process_type],
                    messages=[{
                        'role': 'user',
                        'content': prompt
                    }],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Extract content
                content = response.choices[0].message.content
                
                # Parse content based on type
                if process_type == 'keywords':
                    content_json = {'keywords': [k.strip() for k in content.split(',')]}
                elif process_type == 'insights':
                    try:
                        content_json = json.loads(content)
                    except:
                        content_json = {'raw': content}
                else:
                    content_json = {'content': content}
                
                # Save to database
                processing_time = int((time.time() - start_time) * 1000)
                
                self.supabase.table('processed_content').insert({
                    'transcript_id': transcript_id,
                    'processing_type': process_type,
                    'content': content_json,
                    'model_used': self.models[process_type],
                    'tokens_used': response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else None,
                    'processing_time_ms': processing_time
                }).execute()
                
                logger.info(f'Completed {process_type} processing for transcript {transcript_id}')
                
            except Exception as e:
                logger.error(f'Error in {process_type} processing: {e}')
    
    def scan_existing_transcripts(self):
        """Scan for existing transcript files on startup"""
        logger.info(f'Scanning for existing transcripts in {self.watched_folder}')
        
        for transcript_file in Path(self.watched_folder).rglob('*_transcript.txt'):
            # Check if already processed
            filename = transcript_file.stem.replace('_transcript', '')
            video = self.find_video_by_filename(str(transcript_file))
            
            if video:
                # Check if transcript already exists
                existing = self.supabase.table('transcripts').select('id').eq('video_id', video['id']).execute()
                if not existing.data:
                    logger.info(f'Processing existing transcript: {transcript_file}')
                    self.process_transcript(str(transcript_file))
    
    def run(self):
        """Start watching for transcripts"""
        # First scan for existing files
        self.scan_existing_transcripts()
        
        # Set up file watcher
        event_handler = TranscriptHandler(self)
        observer = Observer()
        observer.schedule(event_handler, self.watched_folder, recursive=True)
        observer.start()
        
        logger.info(f'Watching for transcripts in: {self.watched_folder}')
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == '__main__':
    processor = TranscriptProcessor()
    processor.run()