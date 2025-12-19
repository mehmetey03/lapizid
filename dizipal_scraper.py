#!/usr/bin/env python3
"""
DÜZGÜN DİZİPAL SCRAPER - GitHub Actions Uyumlu
"""

import cloudscraper
import requests
import re
import time
import sys
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup

class DizipalScraper:
    def __init__(self):
        self.base_url = self.get_current_domain()
        print(f"🔗 Domain: {self.base_url}")
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url
        })
        
        # Tüm yıllar
        self.years = list(range(2025, 1959, -1))
        
        # GitHub Actions için sınırlı kategori (test için)
        if os.getenv('GITHUB_ACTIONS') == 'true':
            print("⚡ GitHub Actions modu: Sınırlı kategori")
            self.film_turleri = {
                'aksiyon': 'aksiyon',
                'komedi': 'komedi',
                'dram': 'dram'
            }
        else:
            # Tam kategori listesi
            self.film_turleri = {
                'aile': 'aile',
                'aksiyon': 'aksiyon', 
                'animasyon': 'animasyon',
                'anime': 'anime',
                'belgesel': 'belgesel',
                'bilimkurgu': 'bilimkurgu',
                'biyografi': 'biyografi',
                'dram': 'dram',
                'editorun-sectikleri': 'editorun-sectikleri',
                'erotik': 'erotik',
                'fantastik': 'fantastik',
                'gerilim': 'gerilim',
                'gizem': 'gizem',
                'komedi': 'komedi',
                'korku': 'korku',
                'macera': 'macera',
                'mubi': 'mubi',
                'muzik': 'muzik',
                'romantik': 'romantik',
                'savas': 'savas',
                'spor': 'spor',
                'suc': 'suc',
                'tarih': 'tarih',
                'western': 'western',
                'yerli': 'yerli'
            }

    def get_current_domain(self):
        """GitHub'dan güncel domain'i al"""
        try:
            url = "https://raw.githubusercontent.com/mehmetey03/doma/refs/heads/main/lapiziddomain.txt"
            r = requests.get(url, timeout=10)
            for line in r.text.split('\n'):
                if line.startswith('guncel_domain='):
                    domain = line.split('=', 1)[1].strip()
                    if domain:
                        return domain.rstrip('/')
        except Exception as e:
            print(f"⚠️ Domain alınamadı: {e}")
        return "https://dizipal1222.com"

    def crawl_film_category(self, tur_name, tur_slug):
        """Film kategorisini tüm yıllar için çek"""
        print(f"\n🎬 FİLM KATEGORİSİ: {tur_name.upper()} (Slug: {tur_slug})")
        
        all_films = []
        
        # GitHub Actions için sadece son 2 yıl
        if os.getenv('GITHUB_ACTIONS') == 'true':
            years_to_check = self.years[:2]  # Sadece 2025, 2024
        else:
            years_to_check = self.years
        
        for year in years_to_check:
            print(f"   📅 Yıl: {year}")
            
            encoded_genre = quote(f'/tur/{tur_slug}?', safe='')
            base_url = f"{self.base_url}/tur/{tur_slug}?genre={encoded_genre}&yil={year}&kelime="
            
            page = 1
            year_films_count = 0
            
            while True:
                if page == 1:
                    url = base_url
                else:
                    url = f"{base_url}&sayfa={page}"
                
                print(f"      📄 Sayfa {page}")
                
                try:
                    r = self.scraper.get(url, timeout=30)
                    
                    if r.status_code != 200:
                        print(f"      ❌ HTTP {r.status_code}")
                        break
                    
                    soup = BeautifulSoup(r.content, 'html.parser')
                    
                    # Film linklerini al
                    film_links = []
                    items = soup.select('article.type2 ul li a')
                    
                    for item in items:
                        href = item.get('href', '')
                        if href and '/film/' in href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in film_links:
                                film_links.append(full_url)
                    
                    print(f"      ✅ {len(film_links)} film bulundu")
                    
                    if not film_links:
                        break
                    
                    # Her film için bilgileri çek
                    for film_url in film_links[:3]:  # GitHub Actions için sınırlı sayı
                        try:
                            r2 = self.scraper.get(film_url, timeout=30)
                            
                            if r2.status_code != 200:
                                continue
                            
                            soup2 = BeautifulSoup(r2.content, 'html.parser')
                            
                            # Film başlığını al
                            title_tag = soup2.find('title')
                            if title_tag:
                                title_text = title_tag.text
                                if ' İzle |' in title_text:
                                    film_title = title_text.split(' İzle |')[0].strip()
                                elif ' | dizipal' in title_text:
                                    film_title = title_text.split(' |')[0].strip()
                                else:
                                    film_title = title_text.strip()
                            else:
                                film_title = "Bilinmeyen Film"
                            
                            # Logo
                            logo = ""
                            meta_image = soup2.find('meta', property='og:image')
                            if meta_image:
                                logo = meta_image.get('content', '')
                            
                            # tvg-id oluştur
                            clean_title = re.sub(r'[^\w\s-]', '', film_title.lower())
                            clean_title = clean_title.replace(' ', '_').replace('__', '_')
                            tvg_id = f"{clean_title}_{year}"
                            
                            all_films.append({
                                'url': film_url,
                                'title': f"{film_title} ({year})",
                                'tvg_id': tvg_id,
                                'logo': logo,
                                'group_title': f"Film - {tur_name.upper()}",
                                'type': 'film'
                            })
                            
                            year_films_count += 1
                            
                        except Exception as e:
                            print(f"         ❌ Film hatası: {str(e)[:50]}")
                            continue
                    
                    # Sonraki sayfa kontrolü
                    next_page = soup.select_one('a[rel="next"]')
                    if not next_page:
                        break
                    
                    page += 1
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ Sayfa hatası: {str(e)[:50]}")
                    break
            
            print(f"      📊 {year} yılı: {year_films_count} film")
            
            if year_films_count > 0:
                time.sleep(1)
        
        print(f"   📊 Kategori toplam: {len(all_films)} film")
        return all_films

    def generate_m3u(self, films, filename='dizipal_filmler.m3u'):
        """M3U dosyası oluştur"""
        print(f"\n📝 M3U dosyası oluşturuluyor: {filename}")
        
        # M3U başlığı
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m3u_lines = [
            '#EXTM3U',
            f'# Generated by Dizipal Scraper on {timestamp}',
            f'# Total films: {len(films)}',
            '#'
        ]
        
        # Filmleri gruplara ayır
        grouped_films = {}
        for film in films:
            group = film['group_title']
            if group not in grouped_films:
                grouped_films[group] = []
            grouped_films[group].append(film)
        
        # Her grup için M3U satırları
        for group_title, films_in_group in sorted(grouped_films.items()):
            m3u_lines.append(f'\n# GROUP-TITLE: "{group_title}"')
            
            for film in sorted(films_in_group, key=lambda x: x['title']):
                m3u_lines.append(f'#EXTINF:-1 tvg-id="{film["tvg_id"]}" tvg-name="{film["title"]}" tvg-logo="{film["logo"]}" group-title="{group_title}", {film["title"]}')
                m3u_lines.append(film['url'])
        
        m3u_content = '\n'.join(m3u_lines)
        
        # Dosyaya yaz
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"✅ M3U dosyası oluşturuldu: {filename}")
        print(f"📊 Toplam film: {len(films)}")
        print(f"📁 Dosya boyutu: {len(m3u_content.encode('utf-8'))} bytes")
        
        return filename

    def run_github_actions_mode(self):
        """GitHub Actions için optimize edilmiş mod"""
        print("=" * 60)
        print("⚡ GITHUB ACTIONS MODU")
        print("=" * 60)
        
        all_films = []
        total_categories = len(self.film_turleri)
        current_category = 1
        
        for tur_name, tur_slug in self.film_turleri.items():
            print(f"\n[{current_category}/{total_categories}] ", end="")
            films = self.crawl_film_category(tur_name, tur_slug)
            all_films.extend(films)
            
            current_category += 1
            time.sleep(1)  # Sunucu yükünü azalt
        
        # M3U dosyasını oluştur
        if all_films:
            self.generate_m3u(all_films)
        else:
            print("❌ Film bulunamadı!")
            # Boş bir M3U dosyası oluştur
            with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n# No films found\n')
        
        return len(all_films)

    def run_full_mode(self):
        """Tam mod (yerel kullanım için)"""
        print("=" * 60)
        print("🚀 TAM MOD - TÜM KATEGORİLER")
        print("=" * 60)
        
        all_films = []
        total_categories = len(self.film_turleri)
        current_category = 1
        
        for tur_name, tur_slug in self.film_turleri.items():
            print(f"\n[{current_category}/{total_categories}] ", end="")
            films = self.crawl_film_category(tur_name, tur_slug)
            all_films.extend(films)
            
            current_category += 1
            time.sleep(2)
        
        # M3U dosyasını oluştur
        self.generate_m3u(all_films)
        
        return len(all_films)

# Ana fonksiyon
def main():
    scraper = DizipalScraper()
    
    # Ortam değişkenine göre mod seç
    if os.getenv('GITHUB_ACTIONS') == 'true':
        film_count = scraper.run_github_actions_mode()
    else:
        # Kullanıcı seçeneği
        print("\n🔧 Çalışma Modunu Seçin:")
        print("1. GitHub Actions Modu (Test - Hızlı)")
        print("2. Tam Mod (Tüm kategoriler)")
        print("3. Tek Kategori Testi")
        
        choice = input("\nSeçiminiz (1-3): ").strip()
        
        if choice == '1':
            film_count = scraper.run_github_actions_mode()
        elif choice == '2':
            film_count = scraper.run_full_mode()
        elif choice == '3':
            # Test için tek kategori
            print("\n🧪 TEK KATEGORİ TESTİ")
            tur_name = "aksiyon"
            tur_slug = "aksiyon"
            films = scraper.crawl_film_category(tur_name, tur_slug)
            scraper.generate_m3u(films, 'dizipal_test.m3u')
            film_count = len(films)
        else:
            print("❌ Geçersiz seçim!")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print(f"✅ İŞLEM TAMAMLANDI!")
    print(f"📊 Toplam film: {film_count}")
    print("=" * 60)
    
    # Başarılı çıkış
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Kullanıcı tarafından durduruldu!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        # Hata durumunda bile boş bir M3U dosyası oluştur
        try:
            with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n# Error occurred during scraping\n')
        except:
            pass
        sys.exit(1)
