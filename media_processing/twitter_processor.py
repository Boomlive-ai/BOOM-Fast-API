import requests
import os
import tempfile
from urllib.parse import urlparse
import mimetypes
from moviepy.video.io.VideoFileClip import VideoFileClip
from media_processing.video_processing import process_video_file
from media_processing.audio_processing import process_audio_file
from media_processing.image_processing import extract_text_from_image
import re
from bs4 import BeautifulSoup


class TwitterMediaProcessor:
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        self.supported_image_types = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        self.supported_video_types = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
        self.supported_audio_types = {'mp3', 'wav', 'aac', 'm4a'}
        
    def extract_media_urls_from_twitter(self, twitter_url):
        """
        Extract media URLs from Twitter/X post
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(twitter_url, headers=headers)
            if response.status_code != 200:
                return None, f"Failed to fetch Twitter page: {response.status_code}"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            media_urls = []
            
            # Look for various media URL patterns in Twitter/X
            # Images
            img_tags = soup.find_all('img')
            for img in img_tags:
                src = img.get('src', '')
                if any(domain in src for domain in ['pbs.twimg.com', 'video.twimg.com']):
                    if not src.startswith('http'):
                        src = 'https:' + src
                    media_urls.append(src)
            
            # Videos - look for video tags and meta properties
            video_tags = soup.find_all('video')
            for video in video_tags:
                src = video.get('src', '')
                if src:
                    if not src.startswith('http'):
                        src = 'https:' + src
                    media_urls.append(src)
            
            # Look for meta tags with video content
            meta_tags = soup.find_all('meta', property=re.compile(r'og:video|twitter:player'))
            for meta in meta_tags:
                content = meta.get('content', '')
                if content and any(domain in content for domain in ['video.twimg.com', 'pbs.twimg.com']):
                    media_urls.append(content)
            
            return list(set(media_urls)), None  # Remove duplicates
            
        except Exception as e:
            return None, f"Error extracting media URLs: {str(e)}"
    
    def detect_media_type(self, url):
        """
        Detect if URL contains image, video, or audio based on URL patterns and content type
        """
        try:
            # First check URL patterns
            url_lower = url.lower()
            
            # Check file extension in URL
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            
            if any(ext in path for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return 'image'
            elif any(ext in path for ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']):
                return 'video'
            elif any(ext in path for ext in ['.mp3', '.wav', '.aac', '.m4a']):
                return 'audio'
            
            # If no clear extension, try to get content type from headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            head_response = requests.head(url, headers=headers, timeout=10)
            content_type = head_response.headers.get('content-type', '').lower()
            
            if content_type.startswith('image/'):
                return 'image'
            elif content_type.startswith('video/'):
                return 'video'
            elif content_type.startswith('audio/'):
                return 'audio'
            
            # Default fallback - assume image for Twitter media
            return 'image'
            
        except Exception as e:
            print(f"Error detecting media type: {e}")
            return 'image'  # Default fallback
    
    def download_media(self, url, media_type):
        """
        Download media file from URL
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://twitter.com/'
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if media_type == 'image':
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'  # Default
            elif media_type == 'video':
                ext = '.mp4'  # Default for videos
            else:  # audio
                ext = '.mp3'  # Default for audio
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=self.upload_folder)
            
            # Download and save
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            
            temp_file.close()
            return temp_file.name, None
            
        except Exception as e:
            return None, f"Error downloading media: {str(e)}"
    
    def process_media_file(self, file_path, media_type):
        """
        Process the media file based on its type
        """
        try:
            if media_type == 'image':
                result = extract_text_from_image(file_path)
                return {
                    'type': 'image',
                    'text': result,
                    'summary': f"Extracted text from image: {result[:200]}..." if len(result) > 200 else f"Extracted text from image: {result}"
                }
            
            elif media_type == 'video':
                # Get video duration first
                video_clip = VideoFileClip(file_path)
                duration = video_clip.duration
                video_clip.close()
                
                # Process video for transcript
                transcript_result = process_video_file(file_path)
                transcript = transcript_result.text if hasattr(transcript_result, 'text') else str(transcript_result)
                
                return {
                    'type': 'video',
                    'duration': duration,
                    'transcript': transcript,
                    'summary': f"Video duration: {duration:.2f}s. Transcript: {transcript[:300]}..." if len(transcript) > 300 else f"Video duration: {duration:.2f}s. Transcript: {transcript}"
                }
            
            elif media_type == 'audio':
                transcript = process_audio_file(file_path)
                return {
                    'type': 'audio',
                    'transcript': transcript,
                    'summary': f"Audio transcript: {transcript[:300]}..." if len(transcript) > 300 else f"Audio transcript: {transcript}"
                }
            
            else:
                return {'error': f'Unsupported media type: {media_type}'}
                
        except Exception as e:
            return {'error': f'Error processing {media_type}: {str(e)}'}
    
    def process_twitter_url(self, twitter_url):
        """
        Main method to process Twitter URL and extract/summarize all media
        """
        try:
            # Extract media URLs from Twitter post
            media_urls, error = self.extract_media_urls_from_twitter(twitter_url)
            if error:
                return {'error': error}
            
            if not media_urls:
                return {'error': 'No media found in the Twitter post'}
            
            results = []
            
            for url in media_urls:
                # Detect media type
                media_type = self.detect_media_type(url)
                
                # Download media
                file_path, download_error = self.download_media(url, media_type)
                if download_error:
                    results.append({
                        'url': url,
                        'error': download_error
                    })
                    continue
                
                # Process media
                processing_result = self.process_media_file(file_path, media_type)
                processing_result['url'] = url
                processing_result['file_path'] = file_path
                
                results.append(processing_result)
                
                # Clean up temporary file
                try:
                    os.unlink(file_path)
                except:
                    pass
            
            return {
                'twitter_url': twitter_url,
                'media_count': len(results),
                'media_results': results
            }
            
        except Exception as e:
            return {'error': f'Error processing Twitter URL: {str(e)}'}