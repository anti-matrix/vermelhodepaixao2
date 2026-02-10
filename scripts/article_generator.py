import json
import random
import sys
import time
import threading
from datetime import datetime, timedelta
from collections import Counter
import re
from groq import Groq
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import base64
import urllib.parse
import os

# RENDER.COM DEPLOYMENT: Hard-coded port for Render
PORT = 10000  # Render default port

class ArticleGenerator:
    def __init__(self, api_key="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"):
        now = datetime.now()
        self.article_mindate = now.strftime("%d, %m, %Y")
        self.api_key = api_key
        self.rate_limited_models = set()
        self.slow_models = set()
        self.last_rate_limit_check = {}
        self.current_model_index = 0
        
        self.freepik_api_key = "FPSX2a0b7c19ee152bde00b37a38038b394d"
        
        # Get script directory for file operations
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        if not self.api_key:
            print("Warning: No API key provided.")
            print("Get one from: https://console.groq.com/keys")
            self.client = None
            return
        
        try:
            self.client = Groq(api_key=self.api_key)
            print("Groq client initialized")
        except Exception as e:
            print(f"Warning: Error initializing Groq client: {e}")
            self.client = None
            return
        
        self.available_models = self.get_all_available_models()
        if not self.available_models:
            print("Warning: No models available.")
            return
        
        print(f"Available models: {', '.join(self.available_models)}")
        self.select_best_model()
        
        # Load existing articles - non-critical operation
        try:
            self.load_existing_articles()
            self.analyze_article_patterns()
        except Exception as e:
            print(f"Warning: Could not load existing articles: {e}")
            # Initialize with empty data instead of crashing
            self.existing_articles = []
            self.good_articles = []
            self.authors = []
            self.all_titles = []
            self.all_contents = []
            self.common_title_patterns = []
            self.common_openings = []
            self.common_closings = []
            self.common_phrases = []
            self.mentioned_names = []
            self.date_references = []
    
    def get_all_available_models(self):
        if not self.client:
            return []
            
        try:
            print("Fetching all available Groq models...")
            models = self.client.models.list()
            all_models = [model.id for model in models.data]
            
            def model_sort_key(model_name):
                if 'llama-3.3' in model_name:
                    return 0
                elif 'llama-3.1' in model_name:
                    return 1
                elif 'mixtral' in model_name:
                    return 2
                elif 'gemma' in model_name:
                    return 3
                elif '70b' in model_name:
                    return 4
                elif '8b' in model_name:
                    return 5
                else:
                    return 6
            
            sorted_models = sorted(all_models, key=model_sort_key)
            print(f"Found {len(sorted_models)} total models")
            return sorted_models
        except Exception as e:
            print(f"Error fetching available models: {e}")
            # Fallback to known models
            fallback_models = [
                'llama-3.3-70b-versatile',
                'llama-3.1-70b-versatile', 
                'llama-3.1-8b-instant',
                'mixtral-8x7b-32768',
                'gemma2-9b-it'
            ]
            return fallback_models
    
    def select_best_model(self):
        if not self.available_models:
            return
            
        for model in self.available_models:
            if model not in self.rate_limited_models and model not in self.slow_models:
                self.model_name = model
                self.current_model_index = self.available_models.index(model)
                print(f"Selected model: {self.model_name}")
                return
        
        print("All models problematic, clearing caches...")
        self.rate_limited_models.clear()
        self.slow_models.clear()
        if self.available_models:
            self.model_name = self.available_models[0]
            self.current_model_index = 0
            print(f"Selected model: {self.model_name}")
    
    def switch_to_next_model(self):
        if not self.available_models:
            return False
        
        self.rate_limited_models.add(self.model_name)
        
        original_index = self.current_model_index
        for i in range(1, len(self.available_models) + 1):
            next_index = (self.current_model_index + i) % len(self.available_models)
            next_model = self.available_models[next_index]
            
            if next_model not in self.rate_limited_models and next_model not in self.slow_models:
                self.model_name = next_model
                self.current_model_index = next_index
                print(f"Switched from {self.available_models[original_index]} to {self.model_name}")
                return True
        
        return False
    
    def load_existing_articles(self, json_file='posts_complete.json'):
        try:
            json_path = os.path.join(self.script_dir, json_file)
            print(f"Looking for {json_file} at: {json_path}")
            
            if not os.path.exists(json_path):
                print(f"Warning: {json_file} not found at {json_path}")
                self.existing_articles = []
                self.good_articles = []
                self.authors = []
                self.all_titles = []
                self.all_contents = []
                return
                
            with open(json_path, 'r', encoding='utf-8') as f:
                self.existing_articles = json.load(f)
            print(f"Loaded {len(self.existing_articles)} existing articles for context")
            
            self.authors = list(set([article.get('_autor', '') for article in self.existing_articles if article.get('_autor')]))
            
            self.good_articles = [
                article for article in self.existing_articles 
                if article.get('_titulo') and article.get('_conteudo') 
                and len(str(article.get('_conteudo'))) > 100
            ]
            print(f"Found {len(self.good_articles)} articles with substantial content")
            
            self.all_titles = [str(art.get('_titulo', '')).strip() for art in self.existing_articles if art.get('_titulo')]
            self.all_contents = [str(art.get('_conteudo', '')).strip() for art in self.existing_articles if art.get('_conteudo') and len(str(art.get('_conteudo'))) > 100]
            
        except Exception as e:
            print(f"Warning: Error loading {json_file}: {e}")
            self.existing_articles = []
            self.good_articles = []
            self.authors = []
            self.all_titles = []
            self.all_contents = []
    
    def analyze_article_patterns(self):
        print("Analyzing article patterns for context injection...")
        
        self.common_title_patterns = self.extract_title_patterns()
        self.common_openings = self.extract_opening_sentences()
        self.common_closings = self.extract_closing_sentences()
        self.common_phrases = self.extract_common_phrases()
        self.mentioned_names = self.extract_mentioned_names()
        self.date_references = self.extract_date_patterns()
        
        print(f"  Title patterns: {len(self.common_title_patterns)}")
        print(f"  Opening sentences: {len(self.common_openings)}")
        print(f"  Closing sentences: {len(self.common_closings)}")
        print(f"  Common phrases: {len(self.common_phrases)}")
        print(f"  Mentioned names: {len(self.mentioned_names)}")
    
    def extract_title_patterns(self):
        patterns = []
        for title in self.all_titles:
            if len(title) > 10:
                patterns.append(title)
        
        return patterns[:20]
    
    def extract_opening_sentences(self):
        openings = []
        for content in self.all_contents:
            first_part = content[:200].strip()
            sentence_end = max(first_part.find('.'), first_part.find('!'), first_part.find('?'))
            if sentence_end > 30:
                opening = first_part[:sentence_end + 1].strip()
                if len(opening) > 20:
                    openings.append(opening)
        
        unique_openings = list(set(openings))
        return unique_openings[:15]
    
    def extract_closing_sentences(self):
        closings = []
        for content in self.all_contents:
            if len(content) > 200:
                last_part = content[-200:].strip()
                sentences = re.split(r'[.!?]', last_part)
                if len(sentences) > 1 and len(sentences[-2]) > 20:
                    closing = sentences[-2].strip() + '.'
                    closings.append(closing)
        
        unique_closings = list(set(closings))
        return unique_closings[:15]
    
    def extract_common_phrases(self):
        if not self.all_contents:
            return []
            
        all_text = ' '.join(self.all_contents).lower()
        
        common_terms = [
            "Mecão", "alvirrubro", "Dragão", "Orgulho do RN", "Alvirrubro da Rodrigues Alves",
            "torcida alvirrubra", "a maior da capital", "Máfia", "TMV", "torcida do Mecão",
            "torcida do América", "torcida do Maior do RN", "Arena das Dunas", "Arena América",
            "Série D", "campeonato brasileiro", "Copa do Nordeste", "Frasqueirão", "Marias Lamas",
            "Abc", "rival", "clássico", "alvirrubro potiguar", "time do povo", "vermelho e branco"
        ]
        
        words = re.findall(r'\b\w+\b', all_text)
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        
        bigram_counts = Counter(bigrams)
        trigram_counts = Counter(trigrams)
        
        common_bigrams = [phrase for phrase, count in bigram_counts.most_common(30) if count > 2]
        common_trigrams = [phrase for phrase, count in trigram_counts.most_common(30) if count > 1]
        
        all_phrases = common_terms + common_bigrams + common_trigrams
        return list(set(all_phrases))[:50]
    
    def extract_mentioned_names(self):
        names = []
        
        name_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            r'\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b',
            r'\b[A-Z][a-z]+ [dD][aeo] [A-Z][a-z]+\b',
        ]
        
        for content in self.all_contents:
            for pattern in name_patterns:
                found_names = re.findall(pattern, content)
                names.extend(found_names)
        
        predefined_names = [
            "João Pedro", "Matheusinho", "Alemão", "Felipe Azevedo", "Juninho", 
            "Marcinho", "Rafael Carioca", "Max", "Pardal", "Cascata",
            "Roberto Fernandes", "Pedro Weber", "Vitor Arteiro", "Moacir Jr.", "Leston Júnior", "Francisco Diá", "Marcelo Chamusca", "Ranielle Ribeiro", "Marquinho Santos",
            "Carlão", "Beto", "Maeterlinck Rêgo", "Sérgio Fraiman"
        ]
        
        all_names = list(set(names + predefined_names))
        return all_names[:30]
    
    def extract_date_patterns(self):
        date_patterns = set()
        
        for content in self.all_contents:
            date_matches = re.findall(r'\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4}', content, re.IGNORECASE)
            date_patterns.update(date_matches)
            
            time_refs = re.findall(r'(hoje|ontem|amanhã|semana passada|mês passado|ano passado|próxima semana|próximo mês|próximo ano)', content, re.IGNORECASE)
            date_patterns.update(time_refs)
        
        return list(date_patterns)
    
    def get_random_player(self):
        if hasattr(self, 'mentioned_names') and self.mentioned_names:
            player_names = [name for name in self.mentioned_names if len(name.split()) <= 3]
            if player_names:
                return random.choice(player_names)
        
        players = ["João Pedro", "Matheusinho", "Alemão", "Felipe Azevedo", "Juninho", "Marcinho", "Rafael Carioca", "Max", "Pardal", "Cascata"]
        return random.choice(players)
    
    def get_random_staff(self):
        if hasattr(self, 'mentioned_names') and self.mentioned_names:
            staff_names = [name for name in self.mentioned_names 
                          if any(title in name.lower() for title in ['técnico', 'preparador', 'médico', 'massagista', 'diretor', 'presidente'])]
            if staff_names:
                return random.choice(staff_names)
        
        staff = ["CEO Pedro Weber", "CEO Vitor Arteiro", "diretor de futebol Luciano Mancha", "Técnico Roberto Fernandes", "Técnico Moacir Jr.", "Técnico Leston Júnior", "Técnico Francisco Diá", "Técnico Marcelo Chamusca", "Preparador físico Carlão", "Massagista Beto", "médico Maeterlinck Rêgo"]
        return random.choice(staff)
    
    def test_model_connection(self, model=None):
        test_model = model or self.model_name
        
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
                timeout=10
            )
            elapsed = time.time() - start_time
            
            if elapsed > 5:
                print(f"Model {test_model} is slow (took {elapsed:.2f}s)")
                self.slow_models.add(test_model)
                
            return True
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate_limit" in error_msg:
                print(f"Model {test_model} is rate limited")
                self.rate_limited_models.add(test_model)
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                print(f"Model {test_model} timed out")
                self.slow_models.add(test_model)
            return False
    
    def generate_article(self, topic=None, max_length=500, max_retries=5):
        if not self.client:
            return None
        
        author = random.choice(self.authors) if self.authors else "Sérgio Fraiman"
        
        if not topic:
            if self.all_titles:
                pattern = random.choice(self.common_title_patterns) if self.common_title_patterns else random.choice(self.all_titles)
                words = pattern.split()
                if len(words) > 3:
                    topic = ' '.join(words[:3]) + " do América FC"
                else:
                    topic = pattern
            else:
                topic = "América FC no campeonato"
        
        current_date = datetime.now().strftime("%d/%m/%Y")
        player = self.get_random_player()
        staff = self.get_random_staff()
        target_length = max_length
        
        retry_count = 0
        original_model = self.model_name
        
        while retry_count < max_retries:
            try:
                print(f"Generating article on: {topic}")
                print(f"   Using model: {self.model_name}")
                
                prompt = self.create_contextual_prompt(topic, author, current_date, player, staff, target_length)
                
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é o Sérgio Fraiman, editor do blog 'Vermelho de Paixão' sobre o América Futebol Clube (RN). Seu estilo é jornalístico, direto, apaixonado e informativo."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=max_length * 3,
                    top_p=0.9,
                    timeout=25 + 5
                )
                
                elapsed_time = time.time() - start_time
                print(f"   Response time: {elapsed_time:.2f}s")
                
                if elapsed_time > 25:
                    print(f"   Model {self.model_name} too slow ({elapsed_time:.2f}s > 25s)")
                    self.slow_models.add(self.model_name)
                    
                    if self.switch_to_next_model():
                        retry_count += 1
                        print(f"Retrying with {self.model_name} (attempt {retry_count}/{max_retries})")
                        continue
                    else:
                        print("No more models available")
                        break
                
                generated_text = response.choices[0].message.content
                
                article_data = self.parse_generated_text(generated_text, author)
                
                article_data['_generated'] = True
                article_data['_generation_date'] = datetime.now().isoformat()
                article_data['_model'] = self.model_name
                article_data['_topic'] = topic
                article_data['_provider'] = 'groq'
                article_data['_response_time'] = elapsed_time
                
                print(f"Successfully generated: {article_data.get('_titulo', 'Untitled')}")
                return article_data
                
            except Exception as e:
                error_msg = str(e)
                print(f"Error with model {self.model_name}: {error_msg[:100]}...")
                
                if "429" in error_msg or "rate_limit" in error_msg:
                    print(f"Rate limit hit for {self.model_name}")
                    self.rate_limited_models.add(self.model_name)
                    
                elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    print(f"Timeout for {self.model_name}")
                    self.slow_models.add(self.model_name)
                    
                elif "model_not_found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    print(f"Model {self.model_name} not available")
                    if self.model_name in self.available_models:
                        self.available_models.remove(self.model_name)
                
                if self.switch_to_next_model():
                    retry_count += 1
                    print(f"Retrying with {self.model_name} (attempt {retry_count}/{max_retries})")
                    continue
                else:
                    print("No more models available")
                    break
        
        print(f"Failed to generate article after {retry_count} retries")
        return None
    
    def extract_keywords(self, text):
        words = text.lower().split()
        common_words = ['o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas', 
                       'por', 'para', 'com', 'sem', 'que', 'se', 'um', 'uma', 'uns', 'umas', 'é', 'são', 'foi',
                       'está', 'foram', 'ser', 'ter', 'há', 'como', 'mas', 'e', 'ou', 'nao', 'não', 'sim', 
                       'também', 'mais', 'muito', 'pouco', 'todo', 'toda', 'todos', 'todas']
        
        filtered_words = [w for w in words if len(w) > 3 and w not in common_words]
        word_count = {}
        for word in filtered_words:
            word_count[word] = word_count.get(word, 0) + 1
        
        return sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    
    def create_contextual_prompt(self, topic, author, current_date, player, staff, target_length):
        
        if self.good_articles:
            examples = random.sample(self.good_articles, min(5, len(self.good_articles)))
        else:
            examples = []
        
        examples_text = ""
        if examples:
            examples_text = "EXEMPLOS DE ARTIGOS REAIS DO BLOG (ANALISE BEM O ESTILO, ESTRUTURA E LINGUAGEM):\n\n"
            for i, ex in enumerate(examples, 1):
                title = ex.get('_titulo', '').strip()
                content = ex.get('_conteudo', '').strip()
                if len(content) > 500:
                    first_part = content[:300]
                    middle_start = len(content) // 3
                    middle_part = content[middle_start:middle_start+200]
                    content = first_part + " [...] " + middle_part + "..."
                elif len(content) > 300:
                    content = content[:400] + "..."
                
                examples_text += f"═" * 50 + f"\n"
                examples_text += f"EXEMPLO {i} - TÍTULO: {title}\n"
                examples_text += f"CONTEÚDO:\n{content}\n\n"
                examples_text += f"═" * 50 + f"\n\n"
        
        patterns_text = ""
        if hasattr(self, 'common_title_patterns') and self.common_title_patterns:
            patterns_text += "PADRÕES DE TÍTULO COMUNS:\n"
            for i, pattern in enumerate(self.common_title_patterns[:10], 1):
                patterns_text += f"  {i}. {pattern}\n"
            patterns_text += "\n"
        
        if hasattr(self, 'common_openings') and self.common_openings:
            patterns_text += "INÍCIOS DE FRASE COMUNS:\n"
            for i, opening in enumerate(self.common_openings[:8], 1):
                patterns_text += f"  {i}. {opening}\n"
            patterns_text += "\n"
        
        if hasattr(self, 'common_closings') and self.common_closings:
            patterns_text += "FINAIS DE FRASE COMUNS:\n"
            for i, closing in enumerate(self.common_closings[:8], 1):
                patterns_text += f"  {i}. {closing}\n"
            patterns_text += "\n"
        
        if hasattr(self, 'common_phrases') and self.common_phrases:
            patterns_text += "TERMOS E EXPRESSÕES CHAVE (USE-OS):\n"
            phrases_list = ", ".join(self.common_phrases[:30])
            patterns_text += f"  {phrases_list}\n\n"
        
        prompt = f"""{examples_text}

{patterns_text}

ANÁLISE DE PADRÕES E CONTEXTO EXTRAÍDO DOS ARTIGOS EXISTENTES:

{self.get_wikipedia_context()}

INSTRUÇÕES PARA NOVO ARTIGO JORNALÍSTICO (SEGUINDO ESTRITAMENTE OS EXEMPLOS ACIMA):

TÓPICO PRINCIPAL: {topic}
AUTOR DESTE ARTIGO: {author}
DATA DE REFERÊNCIA (usar datas depois de {self.article_mindate}): {current_date}

REGRAS ABSOLUTAS (BASEADAS NOS EXEMPLOS):
1. ESTILO: COPIE EXATAMENTE o estilo jornalístico dos exemplos - tom, estrutura, formato
2. TERMINOLOGIA: USE os termos e expressões listados acima frequentemente
3. REFERÊNCIAS: 
   - Jogadores: {player} (ou nomes similares dos exemplos)
   - Comissão técnica: {staff} (ou nomes similares dos exemplos)
   - Se necessário, invente nomes que soem reais (como nos exemplos)
4. TEMPORALIDADE: Datas recentes (após {self.article_mindate})
5. COMPRIMENTO: Aproximadamente {target_length} caracteres
6. AUTENTICIDADE: O artigo deve parecer 100% real, como se fosse escrito por {author}
7. ESTRUTURA: 
   - Título no estilo exato dos exemplos
   - Abertura no estilo dos exemplos
   - Desenvolvimento seguindo padrões dos exemplos
   - Conclusão no estilo dos exemplos

CONTEXTO IMPORTANTE DO AMÉRICA-RN ("América", "América de Natal", "Mecão"):
- Atualmente na Série D do Brasileirão ({self.article_mindate})
- Estádios: Arena das Dunas (principal) e Arena América (em construção/expansão)
- Torcida: "Máfia" (TMV) é a principal organizada
- Apelidos: Mecão (PRINCIPAL), Dragão, Alvirrubro
- Maior rival: Abc (não ABC)

ESTRUTURA DE RESPOSTA [[OBRIGATÓRIA]]:
TÍTulo: [título no estilo exato dos exemplos]
CONTEÚDO: [conteúdo completo, seguindo estruturas dos exemplos]

CRÍTICO: Não mencione que é gerado por IA. Seja natural como os exemplos.
IMPORTANTE: Analise bem os exemplos e replique seu estilo, tom e estrutura.
"""
        
        return prompt
    
    def get_wikipedia_context(self):
        return """CONTEXTO HISTÓRICO (da Wikipedia):
América Futebol Clube (América de Natal, Mecão, AFC) - Fundado em 14 de julho de 1915.
Cores: vermelho e branco. Sede: bairro do Tirol, Natal-RN.
Principais títulos: Copa do Nordeste 1998, Norte-Nordeste 1973, Série D 2022.
Participações: Série A, Série B, Série C, Copa do Brasil, Copa Conmebol (único do RN).
Estádios: Arena das Dunas (32.000 lugares) e Arena América (em expansão para 15.000).
Rival histórico: Abc (ABC Futebol Clube). Torcida: "Máfia" (TMV).
Situação atual (2026): Competindo na Série D do Campeonato Brasileiro."""
    
    def parse_generated_text(self, text, author):
        lines = text.strip().split('\n')
        
        titulo = ""
        conteudo = ""
        
        for i, line in enumerate(lines):
            if line.strip().upper().startswith("TÍTULO:"):
                titulo = line.split(":", 1)[1].strip()
                break
        
        for i, line in enumerate(lines):
            if line.strip().upper().startswith("CONTEÚDO:"):
                conteudo = '\n'.join(lines[i+1:]).strip()
                if ':' in line:
                    first_part = line.split(":", 1)[1].strip()
                    if first_part:
                        conteudo = first_part + '\n' + conteudo
                break
        
        if not titulo or not conteudo:
            if len(lines) > 1:
                titulo = lines[0].strip()
                conteudo = '\n'.join(lines[1:]).strip()
            else:
                titulo = "Artigo Gerado"
                conteudo = text.strip()
        
        now = datetime.now()
        data = now.strftime("%d/%m/%Y")
        hora = now.strftime("%H:%M")
        
        article = {
            "_id": random.randint(10000, 99999),
            "_titulo": titulo,
            "_conteudo": conteudo,
            "_data": data,
            "_hora": hora,
            "_autor": author,
            "_imgsrc": "None",
            "_imgwth": "None",
            "_imghgt": "None",
            "_videosrc": "None",
            "_videowth": "None",
            "_videohgt": "None",
            "_year": now.year
        }
        
        return article
    
    def generate_image_for_article(self, titulo, conteudo):
        print(f"   Creating image prompt...")
        
        try:
            groq_prompt = f"""You are an expert at creating detailed image prompts for AI image generation.

Given this Brazilian football article about América Futebol Clube (RN), create a detailed, vivid image prompt based on the following article's title and content.

Article Title: {titulo}
Article Content: {conteudo[:500]}

Generate ONLY the image prompt, nothing else. Make it vivid and detailed."""
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert image prompt engineer for sports photography."
                    },
                    {
                        "role": "user",
                        "content": groq_prompt
                    }
                ],
                temperature=0.8,
                max_tokens=200,
                top_p=0.9
            )
            
            image_prompt = response.choices[0].message.content.strip()
            image_prompt = image_prompt.replace('"', '').replace("'", '').strip()
            
        except Exception as e:
            print(f"   Error creating prompt: {e}")
            combined = f"{titulo} {conteudo[:200]}".lower()
            
            if any(word in combined for word in ['gol', 'goal', 'comemoração']):
                image_prompt = "football goal celebration, América FC red and white colors, Brazilian football stadium, dynamic action, photorealistic"
            elif any(word in combined for word in ['treino', 'treinamento']):
                image_prompt = "football training session, América FC red and white colors, Brazilian football stadium, dynamic action, photorealistic"
            elif any(word in combined for word in ['torcida', 'torcedor', 'fans']):
                image_prompt = "passionate football fans in stadium, América FC red and white colors, Brazilian football stadium, crowd atmosphere, photorealistic"
            elif any(word in combined for word in ['vitória', 'campeão']):
                image_prompt = "victory celebration, América FC red and white colors, Brazilian football stadium, trophy celebration, photorealistic"
            elif any(word in combined for word in ['jogo', 'partida', 'match']):
                image_prompt = "football match action, América FC red and white colors, Brazilian football stadium, night game, photorealistic"
            elif any(word in combined for word in ['arena', 'estádio']):
                image_prompt = "modern football stadium, América FC red and white colors, aerial view, photorealistic"
            else:
                image_prompt = "professional football scene, América FC red and white colors, Brazilian football stadium, dynamic action, photorealistic"
        
        print(f"   Prompt: {image_prompt[:80]}...")
        print(f"   Generating image with Freepik API...")
        
        freepik_result = self.try_freepik(image_prompt)
        if freepik_result:
            print(f"   SUCCESS with Freepik!")
            return freepik_result
        
        placeholder_result = self.create_placeholder(titulo)
        if placeholder_result:
            print(f"   Created placeholder image")
            return placeholder_result
        
        print("   Image generation failed - saving article without image")
        return None
    
    def try_freepik(self, image_prompt):
        try:
            print(f"   Calling CORRECT Freepik API endpoint...")
            
            url = "https://api.freepik.com/v1/ai/text-to-image"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'x-freepik-api-key': self.freepik_api_key
            }
            
            payload = {
                "prompt": image_prompt,
                "image": {
                    "size": "widescreen_16_9"
                },
                "num_images": 1,
                "filter_nsfw": True
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and len(result['data']) > 0:
                    base64_data = result['data'][0]['base64']
                    
                    return {
                        '_imgsrc': f"data:image/jpeg;base64,{base64_data}",
                        '_imgwth': '780',
                        '_imghgt': '720'
                    }
                else:
                    print(f"   No image data in response.")
            else:
                print(f"   API error {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"   Freepik API call failed: {str(e)}")
            
        return None

    def create_placeholder(self, titulo):
        try:
            # Try to import PIL, but don't crash if it fails
            try:
                from PIL import Image, ImageDraw, ImageFont
                pillow_available = True
            except ImportError:
                pillow_available = False
                print("   Pillow not available for placeholder generation")
                return None
            
            import io
            
            img = Image.new('RGB', (800, 600), color=(139, 0, 0))
            
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            draw.text((50, 200), "América FC", fill=(255, 255, 255), font=font)
            draw.text((50, 250), titulo[:50], fill=(255, 255, 255), font=font)
            draw.text((50, 300), "Imagem em breve...", fill=(200, 200, 200), font=font)
            
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return {
                '_imgsrc': f"data:image/png;base64,{img_str}",
                '_imgwth': '800',
                '_imghgt': '600'
            }
            
        except Exception as e:
            print(f"   Placeholder error: {e}")
            return None
    
    def generate_multiple_articles(self, count=5, topic=None):
        if not self.client:
            print("Error: Groq client not initialized")
            return []
            
        articles = []
        successful = 0
        failed = 0
        
        print(f"\nGenerating {count} articles...")
        print(f"Available models: {len(self.available_models)}")
        print(f"Rate limited models: {len(self.rate_limited_models)}")
        print(f"Slow models: {len(self.slow_models)}")
        print("=" * 70)
        
        for i in range(count):
            print(f"\n[{i+1}/{count}] ", end="")
            
            article_topic = topic
            if not article_topic and self.common_title_patterns:
                pattern = random.choice(self.common_title_patterns)
                words = pattern.split()
                if len(words) > 2:
                    article_topic = ' '.join(words[:min(3, len(words))]) + " do América"
                else:
                    article_topic = pattern
            
            article = self.generate_article(topic=article_topic, max_retries=len(self.available_models))
            
            if article:
                print(f"   Generating image for: {article['_titulo'][:50]}...")
                image_data = self.generate_image_for_article(
                    titulo=article['_titulo'], 
                    conteudo=article['_conteudo']
                )
                
                if image_data:
                    article.update(image_data)
                    print(f"   Image generated successfully!")
                else:
                    print(f"   Image generation failed, saving article without image")
                
                articles.append(article)
                successful += 1
            else:
                failed += 1
        
        print(f"\n{'='*70}")
        print(f"GENERATION SUMMARY")
        print(f"{'='*70}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Current model: {self.model_name}")
        print(f"Rate limited models: {len(self.rate_limited_models)}")
        print(f"Slow models: {len(self.slow_models)}")
        
        images_generated = sum(1 for a in articles if a.get('_imgsrc', 'None') != 'None')
        print(f"Images generated: {images_generated}/{len(articles)}")
        
        if articles:
            self.save_all_articles(articles, "generated_articles.json")
            self.save_to_materias_js(articles, "materias_generated.js")
            self.save_cumulative_articles(articles, "all_articles.json", "all_materias.js")

        return articles
    
    def save_all_articles(self, articles, filename):
        try:
            file_path = os.path.join(self.script_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(articles)} articles to {file_path}")
        except Exception as e:
            print(f"Error saving articles: {e}")
    
    def save_to_materias_js(self, articles, filename):
        try:
            file_path = os.path.join(self.script_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('// Generated articles by Groq AI\n')
                f.write(f'// Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'// Total generated articles: {len(articles)}\n')
                f.write(f'// Model used: {self.model_name}\n')
                
                images_generated = sum(1 for a in articles if a.get('_imgsrc', 'None') != 'None')
                f.write(f'// Images generated: {images_generated}/{len(articles)}\n')
                
                f.write('\n')
                f.write('var x = [\n')
                
                for i, article in enumerate(articles):
                    f.write('  {\n')
                    f.write(f'    _id: {article.get("_id", i)},\n')
                    f.write(f'    _titulo: "{self.escape_js_string(article.get("_titulo", ""))}",\n')
                    f.write(f'    _conteudo: "{self.escape_js_string(article.get("_conteudo", ""))}",\n')
                    f.write(f'    _data: "{self.escape_js_string(article.get("_data", ""))}",\n')
                    f.write(f'    _hora: "{self.escape_js_string(article.get("_hora", ""))}",\n')
                    f.write(f'    _autor: "{self.escape_js_string(article.get("_autor", ""))}",\n')
                    
                    imgsrc = article.get('_imgsrc', 'None')
                    if imgsrc != 'None':
                        f.write(f'    _imgsrc: "{self.escape_js_string(imgsrc)}",\n')
                        f.write(f'    _imgwth: "{self.escape_js_string(article.get("_imgwth", "800"))}",\n')
                        f.write(f'    _imghgt: "{self.escape_js_string(article.get("_imghgt", "800"))}",\n')
                    else:
                        f.write(f'    _imgsrc: "None",\n')
                        f.write(f'    _imgwth: "None",\n')
                        f.write(f'    _imghgt: "None",\n')
                    
                    f.write(f'    _videosrc: "{self.escape_js_string(article.get("_videosrc", "None"))}",\n')
                    f.write(f'    _videowth: "{self.escape_js_string(article.get("_videowth", "None"))}",\n')
                    f.write(f'    _videohgt: "{self.escape_js_string(article.get("_videohgt", "None"))}"\n')
                    f.write('  }' + (',' if i < len(articles) - 1 else '') + '\n')
                
                f.write('];\n')
            
            print(f"Saved {len(articles)} articles to {file_path} in materias.js format")
            
        except Exception as e:
            print(f"Error saving to materias.js format: {e}")
    
    def escape_js_string(self, text):
        if not isinstance(text, str):
            text = str(text)
        
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        
        return text
    
    def merge_with_existing(self, generated_articles, output_file="posts_complete_with_generated.json"):
        try:
            merged = self.existing_articles.copy()
            
            for article in generated_articles:
                merged.append(article)
            
            merged.sort(key=lambda x: x.get('_year', 0), reverse=True)
            
            file_path = os.path.join(self.script_dir, output_file)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)
            
            print(f"Merged {len(generated_articles)} generated articles with {len(self.existing_articles)} existing articles")
            print(f"Total: {len(merged)} articles saved to {file_path}")
            
            return merged
            
        except Exception as e:
            print(f"Error merging articles: {e}")
            return None

    def save_cumulative_articles(self, articles, json_file="all_articles.json", js_file="all_materias.js"):
        try:
            print(f"\nSaving {len(articles)} articles to cumulative files...")
            
            json_path = os.path.join(self.script_dir, json_file)
            js_path = os.path.join(self.script_dir, js_file)
            
            existing_articles = []
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    existing_articles = json.load(f)
                print(f"   Loaded {len(existing_articles)} existing articles from {json_path}")
            except (FileNotFoundError, json.JSONDecodeError):
                print(f"   No existing {json_path} found, creating new file")
                existing_articles = []
            
            articles_to_save = []
            
            for article in articles:
                article_copy = article.copy()
                
                if '_generated' not in article_copy:
                    article_copy['_generated'] = True
                if '_generation_date' not in article_copy:
                    article_copy['_generation_date'] = datetime.now().isoformat()
                if '_model' not in article_copy:
                    article_copy['_model'] = self.model_name
                if '_provider' not in article_copy:
                    article_copy['_provider'] = 'groq'
                
                articles_to_save.append(article_copy)
            
            all_articles_dict = {}
            
            for article in existing_articles:
                article_id = article.get('_id')
                if article_id:
                    all_articles_dict[article_id] = article
            
            for article in articles_to_save:
                article_id = article.get('_id')
                if article_id:
                    all_articles_dict[article_id] = article
            
            merged_articles = list(all_articles_dict.values())
            
            merged_articles.sort(
                key=lambda x: (
                    datetime.strptime(x.get('_data', '01/01/2000'), '%d/%m/%Y') 
                    if x.get('_data') and '/' in x.get('_data', '') 
                    else datetime(2000, 1, 1)
                ), 
                reverse=True
            )
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(merged_articles, f, indent=2, ensure_ascii=False)
            print(f"   Saved {len(merged_articles)} total articles to {json_path}")
            
            self.save_cumulative_js_format(merged_articles, js_path)
            
            return True
            
        except Exception as e:
            print(f"   Error saving cumulative articles: {e}")
            return False

    def save_cumulative_js_format(self, articles, js_file):
        try:
            with open(js_file, 'w', encoding='utf-8') as f:
                f.write('// Cumulative articles database\n')
                f.write(f'// Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'// Total articles: {len(articles)}\n')
                f.write(f'// Auto-updated by article_generator.py\n')
                f.write('\n')
                f.write('var x = [\n')
                
                for i, article in enumerate(articles):
                    f.write('  {\n')
                    f.write(f'    _id: {article.get("_id", i)},\n')
                    f.write(f'    _titulo: "{self.escape_js_string(article.get("_titulo", ""))}",\n')
                    f.write(f'    _conteudo: "{self.escape_js_string(article.get("_conteudo", ""))}",\n')
                    f.write(f'    _data: "{self.escape_js_string(article.get("_data", ""))}",\n')
                    f.write(f'    _hora: "{self.escape_js_string(article.get("_hora", ""))}",\n')
                    f.write(f'    _autor: "{self.escape_js_string(article.get("_autor", ""))}",\n')
                    
                    imgsrc = article.get('_imgsrc', 'None')
                    if imgsrc != 'None':
                        f.write(f'    _imgsrc: "{self.escape_js_string(imgsrc)}",\n')
                        f.write(f'    _imgwth: "{self.escape_js_string(article.get("_imgwth", "800"))}",\n')
                        f.write(f'    _imghgt: "{self.escape_js_string(article.get("_imghgt", "800"))}",\n')
                    else:
                        f.write(f'    _imgsrc: "None",\n')
                        f.write(f'    _imgwth: "None",\n')
                        f.write(f'    _imghgt: "None",\n')
                    
                    f.write(f'    _videosrc: "{self.escape_js_string(article.get("_videosrc", "None"))}",\n')
                    f.write(f'    _videowth: "{self.escape_js_string(article.get("_videowth", "None"))}",\n')
                    f.write(f'    _videohgt: "{self.escape_js_string(article.get("_videohgt", "None"))}"\n')
                    f.write('  }' + (',' if i < len(articles) - 1 else '') + '\n')
                
                f.write('];\n')
            
            print(f"   Saved JS format to {js_file}")
            
        except Exception as e:
            print(f"   Error saving JS format: {e}")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global generator instance - initialized lazily with thread safety
generator_instance = None
generator_lock = threading.Lock()

# Root endpoint for Render.com health checks
@app.route('/', methods=['GET'])
def root():
    """Root endpoint - responds immediately without any initialization"""
    return jsonify({
        'service': 'Vermelho de Paixão - Article Generator API',
        'status': 'running',
        'version': '2.0',
        'endpoints': {
            'health': '/api/health - Check service health',
            'generate': '/api/generate - Generate articles (POST)',
            'models': '/api/models - List available models'
        },
        'note': 'Generator initializes lazily on first /api/generate request',
        'deployment': 'Render.com',
        'python_version': sys.version.split()[0]
    })

# Lazy initialization function with thread safety
def get_generator():
    """Initialize the ArticleGenerator only when needed"""
    global generator_instance, generator_lock
    
    with generator_lock:
        if generator_instance is None:
            try:
                print("Initializing ArticleGenerator...")
                generator_instance = ArticleGenerator(
                    api_key="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"
                )
                
                if generator_instance.client and generator_instance.available_models:
                    print(f"Generator initialized successfully with model: {generator_instance.model_name}")
                else:
                    print("Warning: Generator partially initialized")
                    
            except Exception as e:
                print(f"Error initializing generator: {e}")
                import traceback
                traceback.print_exc()
                generator_instance = None
    
    return generator_instance

@app.route('/api/generate', methods=['POST'])
def generate_api():
    generator = get_generator()
    
    if not generator or not generator.client:
        return jsonify({
            'success': False, 
            'error': 'Article generator not available or failed to initialize',
            'available_models': generator.available_models if generator else []
        }), 503
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    query = data.get('query', '')
    count = min(data.get('count', 3), 10)
    
    if not query:
        return jsonify({'success': False, 'error': 'No query provided'}), 400
    
    try:
        print(f"\n[API] Received request: {count} articles about: {query}")
        print(f"[API] Current model: {generator.model_name}")
        
        articles = generator.generate_multiple_articles(
            count=count, 
            topic=query
        )
        
        if articles:
            articles_data = []
            for article in articles:
                articles_data.append({
                    '_id': article.get('_id'),
                    '_titulo': article.get('_titulo'),
                    '_conteudo': article.get('_conteudo'),
                    '_data': article.get('_data'),
                    '_hora': article.get('_hora'),
                    '_autor': article.get('_autor'),
                    '_imgsrc': article.get('_imgsrc', 'None'),
                    '_imgwth': article.get('_imgwth'),
                    '_imghgt': article.get('_imghgt'),
                    '_videosrc': article.get('_videosrc'),
                    '_videowth': article.get('_videowth'),
                    '_videohgt': article.get('_videohgt')
                })
            
            images_generated = sum(1 for a in articles_data if a['_imgsrc'] != 'None')
            print(f"[API] {len(articles)} articles generated successfully!")
            
            return jsonify({
                'success': True, 
                'articles': articles_data,
                'model_used': generator.model_name,
                'images_generated': images_generated
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Failed to generate articles',
                'available_models': generator.available_models
            }), 500
    except Exception as e:
        print(f"[API] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': str(e),
            'available_models': generator.available_models if generator else []
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint - responds immediately without initialization"""
    generator = generator_instance
    
    if generator and generator.client and generator.available_models:
        return jsonify({
            'success': True, 
            'status': 'API is fully operational', 
            'current_model': generator.model_name,
            'available_models_count': len(generator.available_models),
            'flask_running': True,
            'generator_ready': True,
            'deployment': 'Render.com',
            'python_version': sys.version.split()[0]
        })
    else:
        return jsonify({
            'success': True, 
            'status': 'API is running',
            'flask_running': True,
            'generator_ready': False,
            'message': 'Generator will initialize on first /api/generate request',
            'deployment': 'Render.com',
            'python_version': sys.version.split()[0]
        }), 200

@app.route('/api/models', methods=['GET'])
def list_models():
    generator = get_generator()
    
    if generator and generator.available_models:
        return jsonify({
            'success': True,
            'available_models': generator.available_models,
            'current_model': generator.model_name
        })
    else:
        return jsonify({
            'success': False, 
            'error': 'Generator not initialized or no models available',
            'available_models': []
        }), 503

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Startup message
print("=" * 70)
print("✓ Flask app module loaded successfully")
print(f"✓ PORT configured: {PORT} (Render.com)")
print(f"✓ Python version: {sys.version.split()[0]}")
print(f"✓ Registered routes:")
for rule in app.url_map.iter_rules():
    methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"  {rule.rule:40s} [{methods}]")
print("✓ App ready to serve requests (Generator initializes lazily)")
print("=" * 70)

if __name__ == "__main__":
    print(f"\nStarting server on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)