#!/usr/bin/env python3
"""Dizipal Site Test"""

import requests
from bs4 import BeautifulSoup
import re

def test_dizipal():
    url = "https://dizipal1223.com/tur/aksiyon?yil=2024"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"🔍 Test: {url}")
    
    try:
        # 1. Direkt istek
        r = requests.get(url, headers=headers, timeout=10)
        print(f"✅ Status: {r.status_code}")
        print(f"📄 Content length: {len(r.text)} karakter")
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 2. Film linklerini ara
        print("\n🔗 Film linkleri:")
        film_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/film/' in href:
                film_links.append(href)
                print(f"  - {href}")
        
        print(f"\n📊 Toplam film linki: {len(film_links)}")
        
        # 3. Sayfa yapısını kontrol et
        print("\n🏗️ Sayfa yapısı:")
        print(f"  Title: {soup.title.string if soup.title else 'Yok'}")
        
        # 4. JavaScript dosyalarını kontrol et
        print("\n📜 Script dosyaları:")
        scripts = soup.find_all('script', src=True)
        for script in scripts[:5]:
            src = script.get('src', '')
            if src:
                print(f"  - {src}")
        
        # 5. JSON verilerini ara
        print("\n🔎 JSON verileri:")
        json_pattern = re.compile(r'\{.*\}')
        for script in soup.find_all('script'):
            if script.string:
                if 'film' in script.string.lower() or 'movie' in script.string.lower():
                    print("  - Script içinde 'film' kelimesi var")
                    # İlk 500 karakteri göster
                    content = script.string.strip()
                    if len(content) > 500:
                        print(f"    {content[:500]}...")
                    else:
                        print(f"    {content}")
        
        # 6. API endpoint'lerini ara
        print("\n🌐 API endpoint'leri:")
        for tag in soup.find_all(['div', 'span', 'script']):
            if 'data-url' in tag.attrs:
                print(f"  - data-url: {tag['data-url']}")
            if 'data-api' in tag.attrs:
                print(f"  - data-api: {tag['data-api']}")
                
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    test_dizipal()
