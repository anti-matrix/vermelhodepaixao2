from email import header
from urllib import request
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import math 
import random

url = 'http://www.vermelhodepaixao.com.br/p/quem-somos.html';

headers = {
    'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
}

site = requests.get(url, headers=headers)
soup = BeautifulSoup(site.content, 'html.parser')

blocos = soup.find_all('div', class_='post hentry uncustomized-post-template')

total = len(blocos)

with open ('quemsomos.js', 'a', newline='', encoding='utf-8') as json:   

    i = 0
    while i < total:
        for bloco in blocos:
            titulo = bloco.find('h3', class_='post-title entry-title').get_text().strip()
            conteudo = bloco.find('div', class_='post-body entry-content')
            ctd1 = conteudo.get_text().strip()
            ctd2 = conteudo.find('i').get_text().strip()
            id_ = random.randint(1000, 9999) 
            
            linha = f"z[{i}]=";
            linha2 = "{" + "_id:{}, _titulo:'{}', _conteudo:'{}'".format(id_, titulo, conteudo) + "};" + '\n'
            i = i + 1
            print(ctd2);            