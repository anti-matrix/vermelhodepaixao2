# checkprogress.py
import json
import os
import glob
from datetime import datetime
import re

def check_scraping_progress():
    """Check current scraping progress"""
    print("=" * 60)
    print("Vermelho de Paixão - Scraping Progress")
    print("=" * 60)
    
    # Check existing backup
    if os.path.exists('materias_backup.json'):
        try:
            with open('materias_backup.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"\n📊 Current backup: {len(data)} posts")
            
            # Find date range
            dates = [post['_data'] for post in data if post['_data']]
            if dates:
                print(f"   Date range: {dates[-1]} to {dates[0]}")
            
            # Count posts with images
            with_images = sum(1 for post in data if post['_imgsrc'] != 'None')
            print(f"   Posts with images: {with_images}")
            
            # Find oldest year
            years = []
            for post in data:
                if post['_data']:
                    year_match = re.search(r'\b(200[0-9]|201[0-9]|202[0-9])\b', post['_data'])
                    if year_match:
                        years.append(int(year_match.group(1)))
            if years:
                print(f"   Oldest year: {min(years)}")
                print(f"   Newest year: {max(years)}")
                
        except Exception as e:
            print(f"\n❌ Error loading backup: {e}")
    else:
        print("\n📊 No materias_backup.json found")
    
    # Check checkpoint files
    checkpoints = glob.glob('checkpoint_*.json')
    if checkpoints:
        print(f"\n📁 Checkpoint files: {len(checkpoints)}")
        
        # Sort checkpoints by page number (extract number from filename)
        def extract_page_num(filename):
            # Extract numbers from filename like checkpoint_195.json or checkpoint_195_20240118_120000.json
            match = re.search(r'checkpoint_(\d+)', filename)
            return int(match.group(1)) if match else 0
        
        checkpoints.sort(key=extract_page_num)
        
        print("   Latest checkpoints:")
        for cp in checkpoints[-5:]:  # Show last 5
            try:
                with open(cp, 'r', encoding='utf-8') as f:
                    cp_data = json.load(f)
                
                # Extract timestamp if present
                timestamp_match = re.search(r'checkpoint_\d+_(\d{8}_\d{6})', cp)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)
                    try:
                        dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                        time_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        time_str = timestamp
                else:
                    # Old format without timestamp
                    time_str = "Unknown"
                
                # Count posts and find date range
                if cp_data:
                    # Extract years from this checkpoint
                    cp_years = []
                    for post in cp_data:
                        if post.get('_data'):
                            year_match = re.search(r'\b(200[0-9]|201[0-9]|202[0-9])\b', post['_data'])
                            if year_match:
                                cp_years.append(int(year_match.group(1)))
                    
                    year_info = ""
                    if cp_years:
                        year_info = f" | Years: {min(cp_years)}-{max(cp_years)}"
                    
                    print(f"     - {cp}: {len(cp_data)} posts{year_info} ({time_str})")
                else:
                    print(f"     - {cp}: 0 posts ({time_str})")
                    
            except Exception as e:
                print(f"     - {cp}: Error loading - {e}")
    else:
        print("\n📁 No checkpoint files found")
    
    # Check failed pages
    failed_logs = glob.glob('failed_pages*.log')
    if failed_logs:
        for log_file in failed_logs:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if len(lines) > 2:  # Skip header
                    print(f"\n⚠️  {log_file}: {len(lines)-2} failed pages")
            except:
                pass
    
    # Check log files
    log_files = glob.glob('scraper*.log')
    if log_files:
        print(f"\n📝 Log files:")
        for log_file in log_files:
            if os.path.exists(log_file):
                size_mb = os.path.getsize(log_file) / 1024 / 1024
                print(f"   - {log_file}: {size_mb:.2f} MB")
    
    # Check materias.js
    if os.path.exists('materias.js'):
        size_mb = os.path.getsize('materias.js') / 1024 / 1024
        print(f"\n📄 materias.js: {size_mb:.2f} MB")
        
        # Count posts in JS file
        try:
            with open('materias.js', 'r', encoding='utf-8') as f:
                content = f.read()
            post_count = content.count('x[')
            print(f"   Posts in JS file: {post_count}")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("✅ Progress check complete!")
    print("=" * 60)

if __name__ == '__main__':
    check_scraping_progress()