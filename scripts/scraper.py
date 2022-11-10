from email import header
from urllib import request
import requests
from bs4 import BeautifulSoup
import re
import math 
import random

url = 'http://www.vermelhodepaixao.com.br/search?max-results=56';

headers = {
    'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
}

site = requests.get(url, headers=headers)
soup = BeautifulSoup(site.content, 'html.parser')

blocos = soup.find_all('div', class_='post hentry uncustomized-post-template')

total = len(blocos)

with open ('materias.js', 'a', newline='', encoding='utf-8') as json:   

    i = 0
    while i < total:
        for bloco in blocos:
            titulo = bloco.find('h3', class_='post-title entry-title').get_text().strip()
            conteudo = bloco.find('div', class_='post-body entry-content').get_text().strip()
            data = bloco.find('h2', class_='date-header').get_text().strip()
            hora = bloco.find('a', class_='timestamp-link').get_text().strip()
            autor = bloco.find('span', class_='fn').get_text().strip()
            img = bloco.find('img')
            imgsrc = img.get('src')
            imgwidth = img.get('width')
            imgheight = img.get('height')
            id_ = random.randint(1000, 9999) 
            
            linha = f"x[{i}]=";
            linha2 = "{" + "_id:{}, _titulo:'{}', _conteudo:'{}', _data:'{}', _hora:'{}', _autor:'{}', _imgsrc:'{}', _imgwth:'{}', _imghgt:'{}'".format(id_, titulo, conteudo, data, hora, autor, imgsrc, imgwidth, imgheight) + "};" + '\n'
            json.write(linha + linha2)
            i = i + 1
            print(id_)            