import requests
from bs4 import BeautifulSoup
import re
import random
import time
import json
import os
import html
from urllib.parse import urlparse, quote, unquote
import logging
import unicodedata
from datetime import datetime
import base64

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_2024_to_2008_fixed.log'),
        logging.StreamHandler()
    ]
)

class CompleteArchiveScraper:
    def __init__(self):
        self.base_url = 'http://www.vermelhodepaixao.com.br'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
        })
        self.used_ids = set()
        self.scraped_posts = []
        self.visited_urls = set()
        self.oldest_date = None
        self.newest_date = None
        self.last_post_count = 0
        self.consecutive_duplicate_pages = 0
        
    def clean_text(self, text):
        """Clean text to be JSON-safe and remove problematic characters"""
        if not text:
            return ""
        
        text = str(text)
        text = html.unescape(text)
        
        # Remove control characters (except newline and tab)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Replace problematic Unicode characters
        text = text.replace('\u2028', ' ')
        text = text.replace('\u2029', ' ')
        text = text.replace('\uFEFF', '')
        
        # Replace smart quotes and other problematic characters
        replacements = {
            '\u2018': "'", '\u2019': "'", '\u201C': '"', '\u201D': '"',
            '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u00A0': ' ',
            '\u200B': '', '\u200E': '', '\u200F': '', '\u00AD': '',
            '\u201A': "'", '\u201E': '"', '\u02C6': '^', '\u2039': '<', '\u203A': '>'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        text = unicodedata.normalize('NFKC', text)
        
        # Remove emojis but keep Portuguese characters and common symbols
        text = re.sub(r'[^\x00-\x7FáàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ\s\.,!?;:\(\)\[\]\-\'"@#$%&\*\+\/=\|<>]', '', text)
        
        # Strip extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def clean_url(self, url):
        """Clean and validate URLs specifically"""
        if not url or url == 'None':
            return 'None'
        
        url = str(url)
        
        # Decode HTML entities
        url = html.unescape(url)
        
        # Remove control characters from URLs
        url = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', url)
        
        # Properly escape spaces and special characters
        if url.startswith('http'):
            # For regular URLs, ensure proper encoding
            try:
                parsed = urlparse(url)
                # Reconstruct with proper encoding
                url = parsed._replace(path=quote(unquote(parsed.path))).geturl()
            except:
                pass
        
        # Handle data URLs (base64) - ensure they're properly formatted
        elif url.startswith('data:'):
            # Ensure data URLs are properly terminated
            if ';base64,' in url:
                try:
                    # Extract the base64 part
                    header, data = url.split(';base64,', 1)
                    # Validate base64
                    if re.match(r'^[A-Za-z0-9+/]*={0,2}$', data):
                        # Reconstruct with proper formatting
                        url = f"{header};base64,{data}"
                    else:
                        # Invalid base64, return None
                        url = 'None'
                except:
                    url = 'None'
        
        return url
    
    def escape_js_string(self, text):
        """Properly escape strings for JavaScript with Unicode handling"""
        if not isinstance(text, str):
            text = str(text)
        
        # Escape backslashes first
        text = text.replace('\\', '\\\\')
        
        # Escape quotes
        text = text.replace('"', '\\"')
        text = text.replace("'", "\\'")
        
        # Escape control characters
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        text = text.replace('\b', '\\b')
        text = text.replace('\f', '\\f')
        
        # Escape forward slash to prevent XSS and closing script tags
        text = text.replace('/', '\\/')
        
        # Escape Unicode line and paragraph separators
        text = text.replace('\u2028', '\\u2028')
        text = text.replace('\u2029', '\\u2029')
        
        # Escape other problematic Unicode characters
        result = []
        for char in text:
            code = ord(char)
            if code < 32 or code == 127:  # Control characters
                result.append(f'\\x{code:02x}')
            elif 0xD800 <= code <= 0xDFFF:  # Surrogate pairs
                result.append(f'\\u{code:04x}')
            elif code > 0xFFFF:  # Supplementary characters
                result.append(f'\\u{code:04x}')
            else:
                result.append(char)
        
        return ''.join(result)
    
    def escape_json_string(self, text):
        """Escape strings for JSON output"""
        if not isinstance(text, str):
            text = str(text)
        
        # Use json.dumps for proper JSON escaping
        return json.dumps(text, ensure_ascii=False)[1:-1]  # Remove surrounding quotes
    
    def extract_year_from_date(self, date_str):
        """Extract year from date string"""
        if not date_str:
            return None
        
        patterns = [
            r'(\d{1,2})\s+de\s+([a-z]{3,8})\.?\s+de\s+(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'\b(200[0-9]|201[0-9]|202[0-9]|203[0-9])\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    return int(match.group(3)) if 'de' in pattern or '/' in pattern else int(match.group(1))
                else:
                    return int(match.group(1))
        
        return None
    
    def safe_request(self, url, max_retries=5):
        """Make request with retry logic"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 3 * (attempt + 1)
                    logging.info(f"Retry {attempt} for {url} after {wait_time}s")
                    time.sleep(wait_time)
                
                response = self.session.get(url, timeout=60)
                response.raise_for_status()
                
                if response.encoding is None:
                    response.encoding = 'utf-8'
                
                content_lower = response.text.lower()
                if any(word in content_lower for word in ['captcha', 'blocked', 'access denied', 'forbidden', 'rate limit']):
                    logging.warning(f"Possible blocking detected on {url}")
                    if attempt == max_retries - 1:
                        return None
                    continue
                
                return response
                
            except requests.exceptions.Timeout:
                logging.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(30)
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request error on attempt {attempt + 1} for {url}: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(10)
        
        return None
    
    def extract_post_data(self, post_div):
        """Extract and clean data from a post div with YouTube video support"""
        try:
            post_id = random.randint(10000, 99999)
            while post_id in self.used_ids:
                post_id = random.randint(10000, 99999)
            self.used_ids.add(post_id)
            
            # Multiple selectors for each field
            titulo_elem = (post_div.find('h3', class_='post-title entry-title') or 
                          post_div.find('h3', class_='post-title') or
                          post_div.find('h2', class_='post-title') or
                          post_div.find('h1', class_='post-title'))
            raw_titulo = titulo_elem.get_text(strip=True) if titulo_elem else ''
            
            conteudo_elem = (post_div.find('div', class_='post-body entry-content') or
                            post_div.find('div', class_='post-body') or
                            post_div.find('div', class_='entry-content'))
            raw_conteudo = conteudo_elem.get_text(strip=True) if conteudo_elem else ''
            
            # Extract YouTube iframe information
            video_src = 'None'
            video_width = 'None'
            video_height = 'None'
            
            if conteudo_elem:
                # Look for YouTube iframes
                iframe = conteudo_elem.find('iframe')
                if iframe and iframe.get('src'):
                    src = iframe.get('src')
                    # Check if it's a YouTube URL
                    youtube_patterns = [
                        r'youtube\.com/embed/',
                        r'youtu\.be/',
                        r'youtube\.com/watch\?v='
                    ]
                    
                    for pattern in youtube_patterns:
                        if re.search(pattern, src, re.IGNORECASE):
                            video_src = src
                            video_width = iframe.get('width', '560')  # Default width
                            video_height = iframe.get('height', '315')  # Default height
                            break
            
            data_elem = (post_div.find('h2', class_='date-header') or
                        post_div.find('span', class_='post-date') or
                        post_div.find('span', class_='date'))
            raw_data = data_elem.get_text(strip=True) if data_elem else ''
            
            year = self.extract_year_from_date(raw_data)
            
            if year:
                if self.newest_date is None or year > self.newest_date:
                    self.newest_date = year
                if self.oldest_date is None or year < self.oldest_date:
                    self.oldest_date = year
            
            if ',' in raw_data:
                raw_data = raw_data.split(',')[0].strip()
            
            hora_elem = (post_div.find('a', class_='timestamp-link') or
                        post_div.find('span', class_='post-time') or
                        post_div.find('time'))
            raw_hora = hora_elem.get_text(strip=True) if hora_elem else ''
            
            autor_elem = (post_div.find('span', class_='fn') or
                         post_div.find('span', class_='author') or
                         post_div.find('span', class_='post-author'))
            raw_autor = autor_elem.get_text(strip=True) if autor_elem else 'Edmo Anderson'
            
            img = post_div.find('img')
            if not img and conteudo_elem:
                img = conteudo_elem.find('img')
            
            raw_imgsrc = img.get('src') if img else 'None'
            raw_imgwth = img.get('width') if img else 'None'
            raw_imghgt = img.get('height') if img else 'None'
            
            # Clean fields with appropriate methods
            titulo = self.clean_text(raw_titulo)
            conteudo = self.clean_text(raw_conteudo)
            data = self.clean_text(raw_data)
            hora = self.clean_text(raw_hora)
            autor = self.clean_text(raw_autor)
            
            # Special handling for URLs
            imgsrc = self.clean_url(raw_imgsrc)
            videosrc = self.clean_url(video_src)
            
            # Convert width/height to strings
            imgwth = str(raw_imgwth) if raw_imgwth not in ['None', None] else 'None'
            imghgt = str(raw_imghgt) if raw_imghgt not in ['None', None] else 'None'
            videowth = str(video_width) if video_width not in ['None', None] else 'None'
            videohgt = str(video_height) if video_height not in ['None', None] else 'None'
            
            return {
                '_id': post_id,
                '_titulo': titulo,
                '_conteudo': conteudo,
                '_data': data,
                '_hora': hora,
                '_autor': autor,
                '_imgsrc': imgsrc,
                '_imgwth': imgwth,
                '_imghgt': imghgt,
                '_videosrc': videosrc,
                '_videowth': videowth,
                '_videohgt': videohgt,
                '_year': year
            }
        except Exception as e:
            logging.error(f"Error extracting post: {e}")
            return None
    
    def get_next_url(self, soup, current_url):
        """Get next (older) URL from page"""
        older_link = None
        
        older_link = soup.find('a', class_='blog-pager-older-link')
        
        if not older_link:
            older_link = soup.find('a', id='Blog1_blog-pager-older-link')
        
        if not older_link:
            for link in soup.find_all('a'):
                if link.string and 'Posts mais antigos' in link.string:
                    older_link = link
                    break
        
        if not older_link:
            for link in soup.find_all('a'):
                if link.string and 'Older Posts' in link.string:
                    older_link = link
                    break
        
        if older_link and older_link.get('href'):
            next_url = older_link['href']
            if not next_url.startswith('http'):
                next_url = self.base_url + next_url
            
            # Clean the URL
            next_url = self.clean_url(next_url)
            
            return next_url
        
        return None
    
    def scrape_page(self, url, page_num):
        """Scrape a single page - collect ALL posts without duplicate checking"""
        logging.info(f"Page {page_num}: {url}")
        
        response = self.safe_request(url)
        if not response:
            logging.error(f"Failed to fetch {url}")
            return None, None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        posts = soup.find_all('div', class_='post hentry uncustomized-post-template')
        if not posts:
            posts = soup.find_all('article', class_='post')
        if not posts:
            posts = soup.find_all('div', class_='post')
        if not posts:
            posts = soup.find_all('div', class_='blog-post')
        
        if not posts:
            logging.warning(f"No posts found on page {page_num}")
            return [], None
        
        page_posts = []
        for post_div in posts:
            post_data = self.extract_post_data(post_div)
            if post_data:
                page_posts.append(post_data)
        
        logging.info(f"Found {len(page_posts)} posts")
        
        next_url = self.get_next_url(soup, url)
        
        return page_posts, next_url
    
    def scrape_2024_to_2008(self, max_pages=5000):
        """Scrape from 2024 URL back to 2008 - collect ALL posts"""
        start_url = "http://www.vermelhodepaixao.com.br/search?updated-max=2024-04-12T18:29:00-03:00&max-results=56"
        current_url = start_url
        page_num = 1
        pages_without_new_posts = 0
        max_pages_without_new = 5
        
        while current_url and page_num <= max_pages:
            
            # Skip if we've already visited this URL
            if current_url in self.visited_urls:
                logging.info(f"Already visited URL {current_url}, skipping to next")
                # Try to get next URL by parsing from the current page
                response = self.safe_request(current_url)
                if response:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    next_url = self.get_next_url(soup, current_url)
                    if next_url and next_url != current_url:
                        current_url = next_url
                        continue
                break
            
            self.visited_urls.add(current_url)
            
            posts, next_url = self.scrape_page(current_url, page_num)
            
            if posts is None:
                break
            
            # Add all posts from this page
            new_post_count = 0
            for post in posts:
                self.scraped_posts.append(post)
                new_post_count += 1
            
            logging.info(f"Page {page_num}: Added {new_post_count} posts, Total: {len(self.scraped_posts)}")
            
            # Check if we're making progress
            if new_post_count == 0:
                pages_without_new_posts += 1
                logging.warning(f"Page {page_num} had 0 new posts. Consecutive: {pages_without_new_posts}")
            else:
                pages_without_new_posts = 0
            
            # Save checkpoint every 100 pages
            if page_num % 100 == 0:
                self.save_checkpoint(page_num)
            
            # Stop if we've had too many pages without new posts
            if pages_without_new_posts >= max_pages_without_new:
                logging.warning(f"Stopping: {max_pages_without_new} consecutive pages without new posts")
                break
            
            # Check if we've reached 2008 (based on oldest post year)
            if self.oldest_date and self.oldest_date <= 2008:
                logging.info(f"Reached target year 2008 (oldest: {self.oldest_date}). Continuing to collect all 2008 posts...")
                # Don't break, continue to get all 2008 posts
            
            if not next_url or next_url == current_url:
                logging.info("No more pages or reached end")
                break
            
            current_url = next_url
            page_num += 1
            
            # Random delay to avoid being blocked
            delay = 1 + (random.random() * 2)
            time.sleep(delay)
        
        logging.info(f"Finished. Scraped {page_num} pages, {len(self.scraped_posts)} total posts.")
        if self.newest_date:
            logging.info(f"Newest year found: {self.newest_date}")
        if self.oldest_date:
            logging.info(f"Oldest year found: {self.oldest_date}")
        
        return self.scraped_posts
    
    def save_checkpoint(self, page_num):
        """Save checkpoint with safe JSON serialization"""
        checkpoint_file = f'checkpoint_page_{page_num}.json'
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_posts, f, 
                         indent=2, 
                         ensure_ascii=False,
                         separators=(',', ': '))
            
            logging.info(f"Checkpoint saved: {checkpoint_file}")
        except Exception as e:
            logging.error(f"Error saving checkpoint: {e}")
    
    def save_single_output(self):
        """Save all posts to single JSON and JS files"""
        # Use ALL scraped posts
        all_posts = self.scraped_posts.copy()
        
        logging.info(f"Saving {len(all_posts)} posts to files")
        
        # Simple deduplication by ID only - preserve original order
        unique_posts = []
        seen_ids = set()
        
        # Keep the first occurrence of each ID (which is the original order)
        for post in all_posts:
            post_id = post['_id']
            if post_id not in seen_ids:
                seen_ids.add(post_id)
                unique_posts.append(post)
        
        logging.info(f"After ID deduplication: {len(unique_posts)} posts")
        
        # DO NOT SORT - keep the original order from scraping
        # This is already newest to oldest as scraped
        
        # 1. Save as single JSON file
        json_file = 'posts_complete.json'
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(unique_posts, f, 
                         indent=2, 
                         ensure_ascii=False,
                         separators=(',', ': '))
            logging.info(f"JSON saved: {json_file} with {len(unique_posts)} posts")
        except Exception as e:
            logging.error(f"Error saving JSON: {e}")
            self.save_json_manually(unique_posts, json_file)
        
        # 2. Save as single JS file
        js_file = 'materias.js'
        self.save_as_javascript(unique_posts, js_file)
        
        # 3. Save HTML preview
        html_file = 'posts_preview.html'
        self.save_as_html_preview(unique_posts, html_file)
        
        # 4. Save statistics
        self.save_statistics(unique_posts)
        
        return len(unique_posts)

    def save_json_manually(self, posts, filename):
        """Manual JSON saving as fallback"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('[\n')
                for i, post in enumerate(posts):
                    f.write('  {\n')
                    
                    items = []
                    for key, value in post.items():
                        if isinstance(value, str):
                            escaped = self.escape_json_string(value)
                            items.append(f'    "{key}": "{escaped}"')
                        elif isinstance(value, (int, float)):
                            items.append(f'    "{key}": {value}')
                        elif value is None:
                            items.append(f'    "{key}": null')
                        else:
                            items.append(f'    "{key}": "{str(value)}"')
                    
                    f.write(',\n'.join(items))
                    f.write('\n  }' + (',' if i < len(posts) - 1 else '') + '\n')
                
                f.write(']\n')
            
            logging.info(f"Manual JSON saved: {filename}")
        except Exception as e:
            logging.error(f"Failed manual JSON save: {e}")
    
    def save_as_javascript(self, posts, filename):
        """Save as single JavaScript file with proper escaping"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('// Generated by total Vdp Scraper by anti-matrix\n')
                f.write(f'// Scraped on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'// Total posts: {len(posts)}\n')
                if self.newest_date and self.oldest_date:
                    f.write(f'// Year range: {self.oldest_date} - {self.newest_date}\n')
                f.write('\n')
                
                # Use var for compatibility
                f.write('var x = [\n')
                
                for i, post in enumerate(posts):
                    try:
                        # Escape each field properly
                        f.write('  {\n')
                        f.write(f'    _id: {post.get("_id", "null")},\n')
                        f.write(f'    _titulo: "{self.escape_js_string(post.get("_titulo", ""))}",\n')
                        f.write(f'    _conteudo: "{self.escape_js_string(post.get("_conteudo", ""))}",\n')
                        f.write(f'    _data: "{self.escape_js_string(post.get("_data", ""))}",\n')
                        f.write(f'    _hora: "{self.escape_js_string(post.get("_hora", ""))}",\n')
                        f.write(f'    _autor: "{self.escape_js_string(post.get("_autor", ""))}",\n')
                        f.write(f'    _imgsrc: "{self.escape_js_string(post.get("_imgsrc", "None"))}",\n')
                        f.write(f'    _imgwth: "{self.escape_js_string(post.get("_imgwth", "None"))}",\n')
                        f.write(f'    _imghgt: "{self.escape_js_string(post.get("_imghgt", "None"))}",\n')
                        # Add video fields
                        f.write(f'    _videosrc: "{self.escape_js_string(post.get("_videosrc", "None"))}",\n')
                        f.write(f'    _videowth: "{self.escape_js_string(post.get("_videowth", "None"))}",\n')
                        f.write(f'    _videohgt: "{self.escape_js_string(post.get("_videohgt", "None"))}"\n')
                        f.write('  }' + (',' if i < len(posts) - 1 else '') + '\n')
                    except Exception as e:
                        logging.error(f"Error writing post {i} to JavaScript: {e}")
                        # Write a minimal post with error indicator
                        f.write('  {\n')
                        f.write(f'    _id: {post.get("_id", i)},\n')
                        f.write(f'    _titulo: "ERROR LOADING POST {i}",\n')
                        f.write(f'    _conteudo: "Error processing this post during export",\n')
                        f.write(f'    _data: "",\n')
                        f.write(f'    _hora: "",\n')
                        f.write(f'    _autor: "System",\n')
                        f.write(f'    _imgsrc: "None",\n')
                        f.write(f'    _imgwth: "None",\n')
                        f.write(f'    _imghgt: "None",\n')
                        f.write(f'    _videosrc: "None",\n')
                        f.write(f'    _videowth: "None",\n')
                        f.write(f'    _videohgt: "None"\n')
                        f.write('  }' + (',' if i < len(posts) - 1 else '') + '\n')
                
                f.write('];\n\n')
                f.write(f'var totalPosts = x.length;\n')
                if self.newest_date and self.oldest_date:
                    f.write(f'var newestYear = {self.newest_date};\n')
                    f.write(f'var oldestYear = {self.oldest_date};\n')
                
                # Add helper functions
                f.write('''
// Helper function to validate the data
function validateData() {
    var errors = [];
    for (var i = 0; i < x.length; i++) {
        var post = x[i];
        if (typeof post._id !== 'number') errors.push('Post ' + i + ' has invalid _id');
        if (typeof post._titulo !== 'string') errors.push('Post ' + i + ' has invalid _titulo');
        if (typeof post._conteudo !== 'string') errors.push('Post ' + i + ' has invalid _conteudo');
        if (typeof post._data !== 'string') errors.push('Post ' + i + ' has invalid _data');
    }
    return errors;
}

// Search function
function searchPosts(query) {
    var results = [];
    var q = query.toLowerCase();
    for (var i = 0; i < x.length; i++) {
        var post = x[i];
        if (post._titulo.toLowerCase().includes(q) || 
            post._conteudo.toLowerCase().includes(q) ||
            post._autor.toLowerCase().includes(q)) {
            results.push(post);
        }
    }
    return results;
}

// Get post by ID
function getPostById(id) {
    for (var i = 0; i < x.length; i++) {
        if (x[i]._id === id) return x[i];
    }
    return null;
}

console.log('Loaded ' + totalPosts + ' posts (' + oldestYear + ' - ' + newestYear + ')');
''')
            
            logging.info(f"JavaScript saved: {filename} with {len(posts)} posts")
            
        except Exception as e:
            logging.error(f"Error saving JavaScript: {e}")
            self.save_javascript_fallback(posts, filename)
    
    def save_javascript_fallback(self, posts, filename):
        """Fallback method to save JavaScript if the main method fails"""
        try:
            logging.warning(f"Trying fallback JavaScript save for {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('// Generated by Complete Archive Scraper - FALLBACK MODE\n')
                f.write(f'// Scraped on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'// Total posts: {len(posts)}\n')
                f.write('\nvar x = [\n')
                
                for i, post in enumerate(posts):
                    # Extract and clean each field separately
                    titulo = post.get("_titulo", "").replace('"', "'").replace("\\", "\\\\")
                    conteudo = post.get("_conteudo", "").replace('"', "'").replace("\\", "\\\\")
                    imgsrc = post.get("_imgsrc", "None").replace('"', "'").replace("\\", "\\\\")
                    videosrc = post.get("_videosrc", "None").replace('"', "'").replace("\\", "\\\\")
                    
                    f.write('  {\n')
                    f.write(f'    _id: {post.get("_id", i)},\n')
                    f.write(f'    _titulo: "{titulo}",\n')
                    f.write(f'    _conteudo: "{conteudo}",\n')
                    f.write(f'    _data: "{post.get("_data", "")}",\n')
                    f.write(f'    _hora: "{post.get("_hora", "")}",\n')
                    f.write(f'    _autor: "{post.get("_autor", "")}",\n')
                    f.write(f'    _imgsrc: "{imgsrc}",\n')
                    f.write(f'    _imgwth: "{post.get("_imgwth", "None")}",\n')
                    f.write(f'    _imghgt: "{post.get("_imghgt", "None")}",\n')
                    f.write(f'    _videosrc: "{videosrc}",\n')
                    f.write(f'    _videowth: "{post.get("_videowth", "None")}",\n')
                    f.write(f'    _videohgt: "{post.get("_videohgt", "None")}",\n')
                    year_val = post.get("_year")
                    f.write(f'    _year: {year_val if year_val is not None else "null"}\n')
                    f.write('  }' + (',' if i < len(posts) - 1 else '') + '\n')
                
                f.write('];\n')
                f.write(f'var totalPosts = x.length;\n')
            
            logging.info(f"Fallback JavaScript saved: {filename}")
        except Exception as e:
            logging.error(f"Fallback JavaScript save also failed: {e}")
    def save_as_html_preview(self, posts, filename, max_posts=100):
        """Save HTML preview"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Complete Archive Preview</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8f9fa; padding: 20px; }
        .post-card { margin-bottom: 15px; border-left: 4px solid #dc3545; }
        .post-title { color: #dc3545; font-size: 1.1rem; }
        .stats-card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .year-badge { background: #dc3545; color: white; }
        .url-truncate { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .video-badge { background: #ff0000; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="stats-card shadow-sm">
            <h1 class="h3">Complete Archive Preview (2024 to 2008)</h1>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Statistics</h5>
''')
                
                f.write(f'<p class="card-text">Total posts: <strong>{len(posts)}</strong></p>')
                if self.newest_date and self.oldest_date:
                    f.write(f'<p class="card-text">Year range: <strong>{self.oldest_date} - {self.newest_date}</strong></p>')
                
                # Count posts by year and videos
                years = {}
                videos_count = 0
                for post in posts:
                    year = post.get('_year')
                    if year:
                        years[year] = years.get(year, 0) + 1
                    if post.get('_videosrc') and post.get('_videosrc') != 'None':
                        videos_count += 1
                
                if years:
                    f.write('<p class="card-text">Posts by year:</p>')
                    f.write('<div style="max-height: 200px; overflow-y: auto;">')
                    for year in sorted(years.keys(), reverse=True):
                        f.write(f'<div class="d-flex justify-content-between"><span>{year}</span><span>{years[year]}</span></div>')
                    f.write('</div>')
                
                f.write(f'<p class="card-text mt-3">Posts with videos: <strong>{videos_count}</strong></p>')
                
                f.write('''
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Files Generated</h5>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item">posts_complete.json (main data)</li>
                                <li class="list-group-item">materias.js (for website with YouTube videos)</li>
                                <li class="list-group-item">posts_preview.html (this preview)</li>
                                <li class="list-group-item">scraping_stats.json (statistics)</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <h2 class="h4 mb-3">Post Preview (Newest First)</h2>
''')
                
                for i, post in enumerate(posts[:max_posts]):
                    year = post.get('_year', 'N/A')
                    title = html.escape(post.get('_titulo', 'No title'))
                    if len(title) > 80:
                        title = title[:77] + '...'
                    
                    content = html.escape(post.get('_conteudo', ''))
                    if len(content) > 150:
                        content = content[:147] + '...'
                    
                    has_video = post.get('_videosrc') and post.get('_videosrc') != 'None'
                    has_image = post.get('_imgsrc') and post.get('_imgsrc') != 'None'
                    
                    f.write(f'''
        <div class="card post-card shadow-sm">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <h6 class="card-title post-title mb-0">{title}</h6>
                    <div>
                        <span class="badge year-badge">{year}</span>
                        {f'<span class="badge video-badge ms-1">Video</span>' if has_video else ''}
                        {f'<span class="badge bg-secondary ms-1">Image</span>' if has_image and not has_video else ''}
                    </div>
                </div>
                <div class="text-muted small mb-2">
                    <span class="me-2">{html.escape(post.get('_data', ''))}</span>
                    <span class="me-2">{html.escape(post.get('_hora', ''))}</span>
                    <span class="me-2">{html.escape(post.get('_autor', ''))}</span>
                </div>
                <p class="card-text small">{content}</p>
                <div class="text-muted small">
                    <span class="me-2">ID: {post.get('_id', '')}</span>
''')
                    
                    if has_video:
                        video_src = post.get('_videosrc', '')
                        f.write(f'<div class="url-truncate" title="{html.escape(video_src)}">Video: {html.escape(video_src[:50])}...</div>')
                    elif has_image:
                        img_src = post.get('_imgsrc', '')
                        if img_src.startswith('data:'):
                            f.write(f'<div class="url-truncate" title="Base64 image (truncated)">Image: [Base64 data]</div>')
                        else:
                            f.write(f'<div class="url-truncate" title="{html.escape(img_src)}">Image: {html.escape(img_src[:50])}...</div>')
                    
                    f.write('''
                </div>
            </div>
        </div>
''')
                
                f.write(f'''
        <div class="alert alert-info mt-4">
            <strong>Showing {min(max_posts, len(posts))} of {len(posts)} posts</strong><br>
            Full data available in <code>materias.js</code> and <code>posts_complete.json</code><br>
            Posts with videos: {videos_count} | Posts with images: {len([p for p in posts if p.get('_imgsrc') and p.get('_imgsrc') != 'None'])}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>''')
            
            logging.info(f"HTML preview saved: {filename}")
        except Exception as e:
            logging.error(f"Error saving HTML preview: {e}")
    
    def save_statistics(self, posts):
        """Save scraping statistics"""
        stats = {
            'total_posts': len(posts),
            'newest_year': self.newest_date,
            'oldest_year': self.oldest_date,
            'scraping_completed': datetime.now().isoformat(),
            'posts_by_year': {},
            'url_types': {
                'http_urls': 0,
                'data_urls': 0,
                'no_image': 0
            },
            'videos_count': 0
        }
        
        # Count posts by year and URL types
        for post in posts:
            year = post.get('_year')
            if year:
                stats['posts_by_year'][str(year)] = stats['posts_by_year'].get(str(year), 0) + 1
            
            img_src = post.get('_imgsrc', '')
            if img_src == 'None':
                stats['url_types']['no_image'] += 1
            elif img_src.startswith('data:'):
                stats['url_types']['data_urls'] += 1
            elif img_src.startswith('http'):
                stats['url_types']['http_urls'] += 1
            
            # Count videos
            if post.get('_videosrc') and post.get('_videosrc') != 'None':
                stats['videos_count'] += 1
        
        try:
            with open('scraping_stats.json', 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            logging.info(f"Statistics saved: scraping_stats.json")
        except Exception as e:
            logging.error(f"Error saving statistics: {e}")


def main():
    """Main function"""
    print("=" * 70)
    print("Total Vdp Scraper (2024 to 2008) - ALL POSTS VERSION")
    print("Starting from April 2024, scraping back to 2008")
    print("=" * 70)
    
    scraper = CompleteArchiveScraper()
    
    print("\nStarting URL: http://www.vermelhodepaixao.com.br/search?updated-max=2024-04-12T18:29:00-03:00&max-results=56")
    print("Target oldest year: 2008")
    print("Max pages: 5000")
    print("\nThis will scrape from 2024 backwards until reaching 2008.")
    print("Collecting ALL posts (no duplicate filtering during scraping)")
    print("Checkpoints saved every 100 pages.")
    print("Press Ctrl+C to stop and save progress.\n")
    
    input("Press Enter to start scraping...")
    
    try:
        # Run scraper
        scraper.scrape_2024_to_2008(max_pages=5000)
        
        # Save final output
        count = scraper.save_single_output()
        
        print("\n" + "=" * 70)
        print(f"SCRAPING COMPLETE! {count} posts saved")
        if scraper.newest_date and scraper.oldest_date:
            print(f"Year range: {scraper.oldest_date} - {scraper.newest_date}")
        
        # Count videos
        videos_count = sum(1 for post in scraper.scraped_posts if post.get('_videosrc') and post.get('_videosrc') != 'None')
        print(f"YouTube videos found: {videos_count}")
        
        print("\nSingle file output:")
        print("  - posts_complete.json (all posts in one JSON file)")
        print("  - materias.js (all posts in one JS file for website WITH VIDEOS)")
        print("  - posts_preview.html (HTML preview with video indicators)")
        print("  - scraping_stats.json (statistics including video count)")
        print("=" * 70)
        
        print("\nKey improvements:")
        print("  1. Collects ALL posts without duplicate filtering during scraping")
        print("  2. Only removes duplicates by ID in final output")
        print("  3. Continues scraping even after reaching 2008 to get all posts")
        print("  4. Increased max pages to 5000")
        
        print("\nNext steps:")
        print("1. Use 'materias.js' in your website (replace existing file)")
        print("2. Update 'main.js' to display YouTube videos")
        print("3. Check 'posts_preview.html' to verify all posts were collected")
        print("4. 'posts_complete.json' is your backup")
        
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
        print("Saving progress...")
        count = scraper.save_single_output()
        print(f"Progress saved with {count} posts.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        print("Saving progress...")
        count = scraper.save_single_output()
        print(f"Progress saved with {count} posts.")


if __name__ == '__main__':
    main()