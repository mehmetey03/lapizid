#!/usr/bin/env python3
"""
DİZİPAL M3U SCRAPER - GitHub Actions için optimize edilmiş
"""

import cloudscraper
import requests
import re
import time
import os
import sys
from datetime import datetime
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

class DizipalScraper:
    def __init__(self):
        print("🚀 Dizipal Scraper başlatılıyor...")
        
        # GitHub Actions kontrolü
        self.is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        
        # Domain'i al
        self.base_url = self.get_current_domain()
        print(f"🔗 Domain: {self.base_url}")
        
        # Scraper'ı ayarla
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url
        })
        
        # GitHub Actions için sınırlı, yerel için tam liste
        if self.is_github_actions:
            print("⚡ GitHub Actions modu: Sınırlı kategori")
            self.categories = {
                'aksiyon': 'aksiyon',
                'komedi': 'komedi',
                'dram': 'dram'
            }
            self.years = [2025, 2024]  # Sadece 2 yıl
        else:
            self.categories = {
                'aksiyon': 'aksiyon',
                'komedi': 'komedi',
                'dram': 'dram',
                'korku': 'korku',
                'macera': 'macera',
                'bilimkurgu': 'bilimkurgu',
                'romantik': 'romantik'
            }
            self.years = list(range(2025, 2020, -1))  # Son 5 yıl

    def get_current_domain(self):
        """Güncel domain'i al"""
        try:
            # GitHub'dan domain bilgisini al
            url = "https://raw.githubusercontent.com/mehmetey03/doma/refs/heads/main/lapiziddomain.txt"
            response = requests.get(url, timeout=10)
            for line in response.text.split('\n'):
                if line.startswith('guncel_domain='):
                    domain = line.split('=', 1)[1].strip()
                    if domain:
                        return domain.rstrip('/')
        except Exception as e:
            print(f"⚠️ Domain alınamadı: {e}")
        
        # Fallback domain
        return "https://dizipal1222.com"

    def get_film_links(self, category_slug, year):
        """Belirli kategori ve yıl için film linklerini al"""
        try:
            encoded_genre = quote(f'/tur/{category_slug}?', safe='')
            url = f"{self.base_url}/tur/{category_slug}?genre={encoded_genre}&yil={year}&kelime="
            
            print(f"   🔍 Tarıyor: {year} yılı")
            
            response = self.scraper.get(url, timeout=20)
            if response.status_code != 200:
                print(f"   ❌ HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Film linklerini bul
            film_links = []
            movie_items = soup.select('article.type2 ul li a')
            
            for item in movie_items:
                href = item.get('href', '')
                if href and '/film/' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in film_links:
                        film_links.append(full_url)
            
            print(f"   ✅ {len(film_links)} film bulundu")
            return film_links[:5] if self.is_github_actions else film_links[:10]
            
        except Exception as e:
            print(f"   ❌ Hata: {e}")
            return []

    def get_film_info(self, film_url):
        """Film bilgilerini al"""
        try:
            response = self.scraper.get(film_url, timeout=20)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Film başlığı
            title_tag = soup.find('title')
            if not title_tag:
                return None
            
            title_text = title_tag.text
            if ' İzle |' in title_text:
                film_title = title_text.split(' İzle |')[0].strip()
            elif ' | dizipal' in title_text:
                film_title = title_text.split(' |')[0].strip()
            else:
                film_title = title_text.strip()
            
            # Logo
            logo = ""
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                logo = meta_image.get('content', '')
            
            # Yıl (URL'den çıkar veya tahmin et)
            year_match = re.search(r'(\d{4})', film_url)
            year = year_match.group(1) if year_match else "2024"
            
            # tvg-id oluştur
            clean_title = re.sub(r'[^\w\s-]', '', film_title.lower())
            clean_title = clean_title.replace(' ', '_').replace('__', '_')
            tvg_id = f"{clean_title}_{year}"
            
            return {
                'url': film_url,
                'title': f"{film_title} ({year})",
                'tvg_id': tvg_id,
                'logo': logo,
                'group_title': f"Film - {category_name.upper()}",
                'year': year
            }
            
        except Exception as e:
            print(f"      ❌ Film bilgisi alınamadı: {e}")
            return None

    def scrape_category(self, category_name, category_slug):
        """Bir kategoriyi scrape et"""
        print(f"\n🎬 Kategori: {category_name.upper()}")
        
        category_films = []
        
        for year in self.years:
            film_links = self.get_film_links(category_slug, year)
            
            for film_url in film_links:
                film_info = self.get_film_info(film_url)
                if film_info:
                    category_films.append(film_info)
                    print(f"      ✅ {film_info['title']}")
                
                # GitHub Actions için sınırlı sayıda film
                if self.is_github_actions and len(category_films) >= 3:
                    break
                time.sleep(0.5)  # Sunucu yükünü azalt
            
            if self.is_github_actions and len(category_films) >= 3:
                break
            time.sleep(1)
        
        print(f"   📊 Toplam: {len(category_films)} film")
        return category_films

    def generate_m3u(self, films):
        """M3U dosyası oluştur"""
        if not films:
            print("❌ Film bulunamadı!")
            return False
        
        print(f"\n📝 M3U dosyası oluşturuluyor...")
        print(f"📊 Toplam film: {len(films)}")
        
        # M3U başlığı
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m3u_lines = [
            '#EXTM3U',
            f'# Dizipal Filmleri',
            f'# Oluşturulma Tarihi: {timestamp}',
            f'# Toplam Film: {len(films)}',
            '#'
        ]
        
        # Filmleri ekle
        for film in films:
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{film["tvg_id"]}" tvg-logo="{film["logo"]}" group-title="{film["group_title"]}", {film["title"]}')
            m3u_lines.append(film['url'])
        
        # Dosyaya yaz
        m3u_content = '\n'.join(m3u_lines)
        
        try:
            with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            
            print(f"✅ M3U dosyası oluşturuldu: dizipal_filmler.m3u")
            print(f"📁 Dosya boyutu: {len(m3u_content)} karakter")
            return True
            
        except Exception as e:
            print(f"❌ M3U dosyası yazılamadı: {e}")
            return False

    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("=" * 60)
        print("🚀 DİZİPAL M3U SCRAPER")
        print("=" * 60)
        
        all_films = []
        total_categories = len(self.categories)
        
        for i, (category_name, category_slug) in enumerate(self.categories.items(), 1):
            print(f"\n[{i}/{total_categories}] ", end="")
            films = self.scrape_category(category_name, category_slug)
            all_films.extend(films)
            
            # Kategori arasında bekle
            if i < total_categories:
                time.sleep(2)
        
        # M3U dosyasını oluştur
        success = self.generate_m3u(all_films)
        
        print("\n" + "=" * 60)
        if success:
            print(f"✅ BAŞARIYLA TAMAMLANDI!")
            print(f"📊 Toplam film: {len(all_films)}")
        else:
            print("⚠️ İŞLEM TAMAMLANDI (sınırlı sonuç)")
        
        print("=" * 60)
        
        return len(all_films)

# Ana fonksiyon
def main():
    try:
        scraper = DizipalScraper()
        film_count = scraper.run()
        
        # GitHub Actions için başarı durumu
        if film_count > 0:
            sys.exit(0)
        else:
            # Film bulunamadıysa bile boş M3U oluştur
            with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n# Film bulunamadı\n')
            sys.exit(0)  # Yine de başarılı çık
            
    except Exception as e:
        print(f"\n❌ KRİTİK HATA: {e}")
        # Hata durumunda boş M3U oluştur
        try:
            with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n# Hata oluştu\n')
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
