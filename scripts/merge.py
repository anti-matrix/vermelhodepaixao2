# combine_json_to_js.py
import json
import re
import random
import html
import unicodedata
import os
from datetime import datetime
import sys

def clean_text(text):
    """Clean text to be JSON-safe and remove problematic characters"""
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # Decode HTML entities first
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
    
    # Normalize Unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Escape backslashes
    text = text.replace('\\', '\\\\')
    
    # Strip extra whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def escape_js_string(text):
    """Escape string for JavaScript string literal"""
    if not isinstance(text, str):
        text = str(text)
    
    # Escape special characters for JS string
    replacements = {
        '\\': '\\\\',
        '"': '\\"',
        "'": "\\'",
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\b': '\\b',
        '\f': '\\f',
        '/': '\\/',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def extract_date_info(date_str):
    """Extract year from date string for sorting"""
    if not date_str:
        return None
    
    # Try multiple date patterns
    patterns = [
        r'(\d{1,2})\s+de\s+([a-z]{3,8})\.?\s+de\s+(\d{4})',  # 26 de mai. de 2017
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 26/05/2017
        r'(\d{4})-(\d{2})-(\d{2})',  # 2017-05-26
        r'(\d{1,2})\s+de\s+([a-z]{3,8})\s+de\s+(\d{4})',  # 26 de maio de 2017
    ]
    
    date_str_lower = date_str.lower()
    
    for pattern in patterns:
        match = re.search(pattern, date_str_lower)
        if match:
            if 'de' in pattern:
                _, _, year = match.groups()
                return int(year)
            elif '/' in pattern:
                _, _, year = match.groups()
                return int(year)
            else:
                year, _, _ = match.groups()
                return int(year)
    
    # Try to extract just the year
    year_match = re.search(r'\b(19[0-9]{2}|20[0-9]{2})\b', date_str)
    if year_match:
        return int(year_match.group(1))
    
    return None

def parse_date_for_sorting(date_str):
    """Parse date string to datetime for sorting"""
    if not date_str:
        return datetime.min
    
    month_map = {
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12,
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5,
        'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10,
        'novembro': 11, 'dezembro': 12
    }
    
    # Try to parse Portuguese date format
    pattern = r'(\d{1,2})\s+de\s+([a-z]{3,8})\.?\s+de\s+(\d{4})'
    match = re.search(pattern, date_str.lower())
    
    if match:
        day, month_str, year = match.groups()
        month = month_map.get(month_str.rstrip('.'))
        if month:
            try:
                return datetime(int(year), month, int(day))
            except:
                pass
    
    # If we can't parse properly, return by year
    year = extract_date_info(date_str)
    if year:
        return datetime(year, 1, 1)
    
    return datetime.min

def load_and_clean_json_files(files):
    """Load multiple JSON files and clean the data"""
    all_posts = []
    used_ids = set()
    year_range = {'min': None, 'max': None}
    
    for file_path in files:
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"📂 Loading {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                posts = json.load(f)
            
            if not isinstance(posts, list):
                print(f"⚠️  {file_path} doesn't contain a list, skipping")
                continue
                
            print(f"   Loaded {len(posts)} posts")
            
            for post in posts:
                # Generate new ID if needed or use existing
                if 'id' in post:
                    post_id = post['id']
                elif '_id' in post:
                    post_id = post['_id']
                else:
                    post_id = random.randint(10000, 99999)
                
                # Clean all text fields
                cleaned_post = {}
                
                # Map field names to cleaned versions
                field_mapping = {
                    'id': 'id',
                    '_id': '_id',
                    'titulo': '_titulo',
                    '_titulo': '_titulo',
                    'conteudo': '_conteudo',
                    '_conteudo': '_conteudo',
                    'data': '_data',
                    '_data': '_data',
                    'hora': '_hora',
                    '_hora': '_hora',
                    'autor': '_autor',
                    '_autor': '_autor',
                    'imgsrc': '_imgsrc',
                    '_imgsrc': '_imgsrc',
                    'imgwth': '_imgwth',
                    '_imgwth': '_imgwth',
                    'imghgt': '_imghgt',
                    '_imghgt': '_imghgt',
                    'permalink': '_permalink',
                    'year': '_year'
                }
                
                for old_field, new_field in field_mapping.items():
                    if old_field in post and post[old_field] is not None:
                        if old_field in ['id', '_id', 'year', '_year']:
                            cleaned_post[new_field] = post[old_field]
                        else:
                            cleaned_post[new_field] = clean_text(post[old_field])
                
                # Ensure we have an _id field
                if '_id' not in cleaned_post:
                    if 'id' in cleaned_post:
                        cleaned_post['_id'] = cleaned_post.pop('id')
                    else:
                        cleaned_post['_id'] = post_id
                
                # Track year range
                year = extract_date_info(cleaned_post.get('_data', ''))
                if year:
                    if year_range['min'] is None or year < year_range['min']:
                        year_range['min'] = year
                    if year_range['max'] is None or year > year_range['max']:
                        year_range['max'] = year
                    cleaned_post['_year'] = year
                
                # Add to collection if ID is unique
                if cleaned_post['_id'] not in used_ids:
                    used_ids.add(cleaned_post['_id'])
                    all_posts.append(cleaned_post)
                    
        except json.JSONDecodeError as e:
            print(f"❌ Error decoding JSON from {file_path}: {e}")
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
    
    return all_posts, year_range

def remove_duplicates(posts):
    """Remove duplicate posts using multiple criteria"""
    unique_posts = []
    seen_titles = set()
    seen_content_hashes = set()
    
    for post in posts:
        # Create hash from title + first 100 chars of content
        title = post.get('_titulo', '').lower().strip()
        content_preview = post.get('_conteudo', '')[:100].lower().strip()
        content_hash = hash(title + content_preview)
        
        # Check if we've seen this post before
        if title not in seen_titles and content_hash not in seen_content_hashes:
            seen_titles.add(title)
            seen_content_hashes.add(content_hash)
            unique_posts.append(post)
        else:
            print(f"   Skipped duplicate: {title[:50]}...")
    
    return unique_posts

def save_as_javascript(posts, output_file, year_range):
    """Save posts as JavaScript file in the array format"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write('// Generated by JSON Merger Script\n')
            f.write(f'// Created on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'// Total posts: {len(posts)}\n')
            if year_range['min'] and year_range['max']:
                f.write(f'// Year range: {year_range["min"]} - {year_range["max"]}\n')
            f.write('\n')
            
            # Use window.x to avoid conflicts
            f.write('if (typeof window.x === "undefined") {\n')
            f.write('    window.x = [];\n')
            f.write('}\n\n')
            
            # Write the array
            f.write('window.x = [\n')
            
            for i, post in enumerate(posts):
                # Ensure all required fields exist
                required_fields = ['_id', '_titulo', '_conteudo', '_data', '_hora', 
                                  '_autor', '_imgsrc', '_imgwth', '_imghgt']
                
                for field in required_fields:
                    if field not in post:
                        post[field] = ''
                
                # Build the object
                obj_lines = []
                obj_lines.append(f'    _id: {post["_id"]},')
                obj_lines.append(f'    _titulo: "{escape_js_string(post["_titulo"])}",')
                obj_lines.append(f'    _conteudo: "{escape_js_string(post["_conteudo"])}",')
                obj_lines.append(f'    _data: "{escape_js_string(post["_data"])}",')
                obj_lines.append(f'    _hora: "{escape_js_string(post["_hora"])}",')
                obj_lines.append(f'    _autor: "{escape_js_string(post["_autor"])}",')
                obj_lines.append(f'    _imgsrc: "{escape_js_string(post["_imgsrc"])}",')
                obj_lines.append(f'    _imgwth: "{escape_js_string(post["_imgwth"])}",')
                obj_lines.append(f'    _imghgt: "{escape_js_string(post["_imghgt"])}"')
                
                # Add year if available
                if '_year' in post:
                    obj_lines.append(f'    _year: {post["_year"]}')
                
                f.write('  {\n' + ',\n'.join(obj_lines) + '\n  }')
                f.write(',\n' if i < len(posts) - 1 else '\n')
            
            f.write('];\n\n')
            
            # Write helper variables
            f.write(f'// Helper variables\n')
            f.write(f'const totalPosts = window.x.length;\n')
            if year_range['min'] and year_range['max']:
                f.write(f'const oldestYear = {year_range["min"]};\n')
                f.write(f'const newestYear = {year_range["max"]};\n')
            f.write(f'console.log(`Loaded ${totalPosts} posts`);\n')
            
            # Write a function to get posts by year
            f.write('\n')
            f.write('// Function to get posts by year\n')
            f.write('function getPostsByYear(year) {\n')
            f.write('    return window.x.filter(post => {\n')
            f.write('        if (post._year) return post._year === year;\n')
            f.write('        // Try to extract year from _data\n')
            f.write('        const match = post._data.match(/\\b(19|20)\\d{2}\\b/);\n')
            f.write('        return match && parseInt(match[0]) === year;\n')
            f.write('    });\n')
            f.write('}\n')
        
        print(f"✅ JavaScript file saved: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving JavaScript file: {e}")
        return False

def save_as_json(posts, output_file, year_range):
    """Also save as JSON for backup"""
    try:
        # Sort posts by date (newest first)
        posts_sorted = sorted(posts, 
                             key=lambda x: parse_date_for_sorting(x.get('_data', '')),
                             reverse=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(posts_sorted, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON backup saved: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving JSON backup: {e}")
        return False

def create_html_preview(posts, output_file, year_range):
    """Create HTML preview of the combined data"""
    try:
        # Take first 50 posts for preview
        preview_posts = posts[:50]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Combined Posts Preview</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background: #f8f9fa; padding: 20px; }}
        .post-card {{ margin-bottom: 15px; border-left: 4px solid #dc3545; }}
        .post-title {{ color: #dc3545; font-size: 1.1rem; }}
        .stats-card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
        .year-badge {{ background: #dc3545; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="stats-card shadow-sm">
            <h1 class="h3">📊 Combined Posts Preview</h1>
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">📈 Statistics</h5>
                            <p class="card-text">Total posts: <strong>{len(posts)}</strong></p>
                            <p class="card-text">Preview showing: <strong>{len(preview_posts)}</strong></p>
''')
            
            if year_range['min'] and year_range['max']:
                f.write(f'''                            <p class="card-text">Year range: <strong>{year_range['min']} - {year_range['max']}</strong></p>''')
            
            f.write(f'''                        </div>
                    </div>
                </div>
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">📁 Source Files</h5>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item">checkpoint_page_160.json</li>
                                <li class="list-group-item">checkpoint_page_195.json</li>
                                <li class="list-group-item">checkpoint_370.json</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <h2 class="h4 mb-3">📝 Post Preview (Newest First)</h2>
''')
            
            for i, post in enumerate(preview_posts):
                year = post.get('_year', 'N/A')
                title = html.escape(post.get('_titulo', 'No title'))
                if len(title) > 80:
                    title = title[:77] + '...'
                
                content = html.escape(post.get('_conteudo', ''))
                if len(content) > 150:
                    content = content[:147] + '...'
                
                f.write(f'''
        <div class="card post-card shadow-sm">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <h6 class="card-title post-title mb-0">{title}</h6>
                    <span class="badge year-badge">{year}</span>
                </div>
                <div class="text-muted small mb-2">
                    <span class="me-2">📅 {html.escape(post.get('_data', ''))}</span>
                    <span class="me-2">🕒 {html.escape(post.get('_hora', ''))}</span>
                    <span class="me-2">✍️ {html.escape(post.get('_autor', ''))}</span>
                </div>
                <p class="card-text small">{content}</p>
                <div class="text-muted small">
                    <span class="me-2">🆔 {post.get('_id', '')}</span>
                    {f'<span>📷 Image: {html.escape(post.get("_imgsrc", "")[:50])}...</span>' if post.get('_imgsrc') and post.get('_imgsrc') != 'None' else ''}
                </div>
            </div>
        </div>
''')
            
            f.write(f'''
        <div class="alert alert-info mt-4">
            <strong>Showing {len(preview_posts)} of {len(posts)} posts</strong><br>
            Full data available in <code>materias_combined.js</code> and <code>posts_combined.json</code>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>''')
        
        print(f"✅ HTML preview saved: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating HTML preview: {e}")
        return False

def main():
    """Main function"""
    print("="*70)
    print("🔄 JSON FILES MERGER")
    print("Combining checkpoint files into a single JavaScript array")
    print("="*70)
    
    # List of files to combine (in order from newest to oldest)
    files_to_combine = [
        'checkpoint_page_160.json',  # Youngest
        'checkpoint_page_195.json',  # Middle
        'checkpoint_370.json'        # Oldest
    ]
    
    # Check which files exist
    existing_files = [f for f in files_to_combine if os.path.exists(f)]
    
    if not existing_files:
        print("❌ No JSON files found!")
        print("Please ensure the JSON files are in the same directory.")
        return
    
    print(f"Found {len(existing_files)} JSON files:")
    for file in existing_files:
        print(f"  - {file}")
    
    print("\n📥 Loading and cleaning data...")
    
    # Load and clean all posts
    all_posts, year_range = load_and_clean_json_files(existing_files)
    
    if not all_posts:
        print("❌ No posts loaded!")
        return
    
    print(f"\n✅ Loaded {len(all_posts)} total posts")
    
    # Remove duplicates
    print("\n Removing duplicates...")
    unique_posts = remove_duplicates(all_posts)
    print(f"   Removed {len(all_posts) - len(unique_posts)} duplicates")
    print(f"   Unique posts: {len(unique_posts)}")
    
    # Sort by date (newest first)
    print("\n Sorting by date (newest first)...")
    sorted_posts = sorted(unique_posts, 
                         key=lambda x: parse_date_for_sorting(x.get('_data', '')),
                         reverse=True)
    
    # Display year range
    if year_range['min'] and year_range['max']:
        print(f"   Year range: {year_range['min']} - {year_range['max']}")
    
    # Save as JavaScript
    print("\n Saving output files...")
    
    # 1. Save as JavaScript
    js_output = 'materias_combined.js'
    save_as_javascript(sorted_posts, js_output, year_range)
    
    # 2. Save as JSON backup
    json_output = 'posts_combined.json'
    save_as_json(sorted_posts, json_output, year_range)
    
    # 3. Create HTML preview
    html_output = 'combined_preview.html'
    create_html_preview(sorted_posts, html_output, year_range)
    
    print("\n" + "="*70)
    print(" MERGE COMPLETE!")
    print("="*70)
    print(f"\n Output files created:")
    print(f"   1. {js_output} - JavaScript array for your website")
    print(f"   2. {json_output} - JSON backup")
    print(f"   3. {html_output} - HTML preview")
    
    print(f"\n Final statistics:")
    print(f"   Total unique posts: {len(sorted_posts)}")
    if year_range['min'] and year_range['max']:
        print(f"   Year coverage: {year_range['min']} - {year_range['max']}")
    
    print("\n  Next steps:")
    print("   1. Replace your existing 'materias.js' with 'materias_combined.js'")
    print("   2. Update your index.html to remove duplicate 'let x = []' declaration")
    print("   3. Open 'combined_preview.html' to verify the data")
    print("="*70)

if __name__ == '__main__':
    main()