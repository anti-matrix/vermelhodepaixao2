import requests
from bs4 import BeautifulSoup
import re
import random
import time
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VermelhoPaixaoScraper:
    def __init__(self):
        self.base_url = 'http://www.vermelhodepaixao.com.br'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.used_ids = set()
        self.scraped_posts = []
        
    def parse_date_from_url(self, url):
        """Extract date from updated-max parameter"""
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        
        if 'updated-max' in query:
            date_str = query['updated-max'][0]
            try:
                # Format: 2024-04-01T17:45:00-03:00
                return datetime.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')
            except:
                pass
        return None
    
    def generate_next_url(self, current_url, soup):
        """Generate next URL based on Blogger's pagination"""
        parsed = urlparse(current_url)
        query = parse_qs(parsed.query)
        
        # Check for Older Posts link
        older_link = soup.find('a', class_='blog-pager-older-link')
        if not older_link:
            older_link = soup.find('a', id='Blog1_blog-pager-older-link')
        
        if older_link and older_link.get('href'):
            next_url = older_link['href']
            # Make it absolute if relative
            if not next_url.startswith('http'):
                next_url = self.base_url + next_url
            return next_url
        
        # If no Older Posts link, try to construct next URL
        if 'start' in query:
            current_start = int(query['start'][0])
            query['start'] = [str(current_start + 56)]
        else:
            query['start'] = ['56']
        
        # Rebuild URL
        new_query = urlencode(query, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    
    def extract_post_data(self, post_div):
        """Extract data from a post div"""
        try:
            # Generate unique ID
            post_id = random.randint(1000, 9999)
            while post_id in self.used_ids:
                post_id = random.randint(1000, 9999)
            self.used_ids.add(post_id)
            
            # Title
            titulo_elem = post_div.find('h3', class_='post-title entry-title')
            if not titulo_elem:
                titulo_elem = post_div.find('h3', class_='post-title')
            titulo = titulo_elem.get_text().strip() if titulo_elem else ''
            
            # Content
            conteudo_elem = post_div.find('div', class_='post-body entry-content')
            conteudo = conteudo_elem.get_text().strip() if conteudo_elem else ''
            
            # Clean content for JS
            conteudo_clean = conteudo.replace("'", "\\'").replace('\n', ' ').replace('\r', ' ').strip()
            
            # Date
            data_elem = post_div.find('h2', class_='date-header')
            data = data_elem.get_text().strip() if data_elem else ''
            
            # Clean date
            if ',' in data:
                data = data.split(',')[0]
            
            # Time
            hora_elem = post_div.find('a', class_='timestamp-link')
            hora = hora_elem.get_text().strip() if hora_elem else ''
            
            # Author
            autor_elem = post_div.find('span', class_='fn')
            autor = autor_elem.get_text().strip() if autor_elem else 'Edmo Anderson'
            
            # Image
            img = post_div.find('img')
            imgsrc = img.get('src') if img else 'None'
            imgwth = img.get('width') if img else 'None'
            imghgt = img.get('height') if img else 'None'
            
            return {
                '_id': post_id,
                '_titulo': titulo,
                '_conteudo': conteudo_clean,
                '_data': data,
                '_hora': hora,
                '_autor': autor,
                '_imgsrc': imgsrc,
                '_imgwth': imgwth,
                '_imghgt': imghgt
            }
        except Exception as e:
            logging.error(f"Error extracting post: {e}")
            return None
    
    def scrape_page(self, url):
        """Scrape a single page"""
        try:
            logging.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all posts
            posts = soup.find_all('div', class_='post hentry uncustomized-post-template')
            
            if not posts:
                logging.warning(f"No posts found on {url}")
                return [], None
            
            page_posts = []
            for post_div in posts:
                post_data = self.extract_post_data(post_div)
                if post_data:
                    page_posts.append(post_data)
            
            logging.info(f"Found {len(page_posts)} posts on this page")
            
            # Get next URL
            next_url = self.generate_next_url(url, soup)
            
            return page_posts, next_url
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return [], None
    
    def scrape_all(self, max_pages=100):
        """Scrape all pages with safety limits"""
        current_url = f"{self.base_url}/search?max-results=56"
        page_count = 0
        total_posts = 0
        
        while current_url and page_count < max_pages:
            page_count += 1
            
            posts, next_url = self.scrape_page(current_url)
            
            # Add posts to collection
            for post in posts:
                # Check for duplicates by title
                if not any(p['_titulo'] == post['_titulo'] for p in self.scraped_posts):
                    self.scraped_posts.append(post)
                    total_posts += 1
            
            logging.info(f"Page {page_count}: Total posts so far: {total_posts}")
            
            # Check if we should continue
            if not next_url or next_url == current_url:
                logging.info("No more pages or duplicate URL detected")
                break
            
            current_url = next_url
            
            # Save checkpoint every 10 pages
            if page_count % 10 == 0:
                self.save_checkpoint(page_count)
            
            # Be polite
            time.sleep(0.5)
        
        logging.info(f"Finished. Scraped {page_count} pages, {total_posts} unique posts.")
        return self.scraped_posts
    
    def save_checkpoint(self, page_num):
        """Save progress checkpoint"""
        checkpoint_file = f'checkpoint_page_{page_num}.json'
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_posts, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Checkpoint saved: {checkpoint_file}")
    
    def save_final_output(self):
        """Save final JS and JSON files"""
        # Remove any exact duplicates
        unique_posts = []
        seen = set()
        for post in self.scraped_posts:
            key = (post['_titulo'], post['_data'], post['_conteudo'][:100])
            if key not in seen:
                seen.add(key)
                unique_posts.append(post)
        
        logging.info(f"After deduplication: {len(unique_posts)} posts")
        
        # Save JS file
        js_file = 'materias.js'
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write('// Generated by Vermelho de Paixão Scraper\n\n')
            f.write('let x = [];\n\n')
            
            for i, post in enumerate(unique_posts):
                line = f"x[{i}]={{"
                line += f"_id:{post['_id']}, "
                line += f"_titulo:'{post['_titulo']}', "
                line += f"_conteudo:'{post['_conteudo']}', "
                line += f"_data:'{post['_data']}', "
                line += f"_hora:'{post['_hora']}', "
                line += f"_autor:'{post['_autor']}', "
                line += f"_imgsrc:'{post['_imgsrc']}', "
                line += f"_imgwth:'{post['_imgwth']}', "
                line += f"_imghgt:'{post['_imghgt']}'"
                line += "};\n"
                f.write(line)
            
            f.write(f'\n// Total posts: {len(unique_posts)}\n')
            f.write(f'const totalPosts = {len(unique_posts)};\n')
        
        # Save JSON backup
        json_file = 'materias_backup.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(unique_posts, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Files saved:")
        logging.info(f"  - {js_file}")
        logging.info(f"  - {json_file}")
        
        return len(unique_posts)

def main():
    """Main function"""
    print("=" * 60)
    print("Vermelho de Paixão Scraper")
    print("Using date-based pagination")
    print("=" * 60)
    
    scraper = VermelhoPaixaoScraper()
    
    # Optional: Resume from checkpoint
    checkpoint_files = [f for f in os.listdir('.') if f.startswith('checkpoint_page_')]
    if checkpoint_files:
        print(f"\nFound checkpoints: {checkpoint_files}")
        resume = input("Resume from latest checkpoint? (y/n): ")
        if resume.lower() == 'y':
            # Load latest checkpoint
            latest = max(checkpoint_files, key=lambda x: int(x.split('_')[2].split('.')[0]))
            with open(latest, 'r', encoding='utf-8') as f:
                scraper.scraped_posts = json.load(f)
            print(f"Resumed with {len(scraper.scraped_posts)} posts")
    
    # Ask for max pages
    try:
        max_pages = int(input("\nMax pages to scrape (0 for no limit): ") or "100")
        if max_pages == 0:
            max_pages = 1000
    except:
        max_pages = 100
    
    print(f"\nStarting scrape with max {max_pages} pages...")
    
    # Run scraper
    scraper.scrape_all(max_pages=max_pages)
    
    # Save output
    count = scraper.save_final_output()
    
    print(f"\n" + "=" * 60)
    print(f"✅ Finished! {count} posts saved to materias.js")
    print("=" * 60)

if __name__ == '__main__':
    main()