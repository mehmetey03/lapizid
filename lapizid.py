#!/usr/bin/env python3
"""
DÜZGÜN 
"""

import cloudscraper
import requests
import re
import time
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
        
        # Tüm yıllar (2025'ten 1960'a kadar)
        self.years = list(range(2025, 1959, -1))
        
        # TÜM FİLM KATEGORİLERİ (Sizin verdiğiniz listeye göre)
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
        except:
            pass
        return "https://dizipal1222.com"

    def crawl_film_category_correct(self, tur_name, tur_slug):
        """DOĞRU ŞEKİLDE: Film kategorisini tüm yıllar için çek"""
        print(f"\n🎬 FİLM KATEGORİSİ: {tur_name.upper()} (Slug: {tur_slug})")
        
        all_films = []
        
        # Her yıl için ayrı ayrı tarama
        for year in self.years:
            print(f"   📅 Yıl: {year}")
            
            # DOĞRU URL YAPISI: /tur/aksiyon?genre=%2Ftur%2Faksiyon%3F&yil=2000&kelime=
            encoded_genre = quote(f'/tur/{tur_slug}?', safe='')
            
            # Temel URL'yi oluştur
            base_url = f"{self.base_url}/tur/{tur_slug}?genre={encoded_genre}&yil={year}&kelime="
            
            page = 1
            year_films_count = 0
            
            while True:
                # Sayfa numarasını ekle
                if page == 1:
                    url = base_url
                else:
                    url = f"{base_url}&sayfa={page}"
                
                print(f"      📄 Sayfa {page}: {url[:80]}...")
                
                try:
                    r = self.scraper.get(url, timeout=30)
                    
                    # HTTP hata kodlarını kontrol et
                    if r.status_code != 200:
                        print(f"      ❌ HTTP Hatası {r.status_code}")
                        break
                    
                    soup = BeautifulSoup(r.content, 'html.parser')
                    
                    # 1. Sayfada film var mı kontrol et
                    # Boş sayfa kontrolü
                    movie_items = soup.select('article.type2 ul li')
                    
                    if not movie_items:
                        if page == 1:
                            print(f"      ⚠️  {year} yılı için film bulunamadı")
                        break
                    
                    # 2. Film linklerini al
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
                    
                    # 3. Her film için bilgileri çek
                    for film_url in film_links:
                        try:
                            r2 = self.scraper.get(film_url, timeout=30)
                            
                            if r2.status_code != 200:
                                continue
                            
                            soup2 = BeautifulSoup(r2.content, 'html.parser')
                            
                            # Film başlığını al - DOĞRU ŞEKİLDE
                            title_tag = soup2.find('title')
                            if title_tag:
                                title_text = title_tag.text
                                # "Film Adı İzle | dizipal" formatından sadece film adını al
                                if ' İzle |' in title_text:
                                    film_title = title_text.split(' İzle |')[0].strip()
                                elif ' | dizipal' in title_text:
                                    film_title = title_text.split(' |')[0].strip()
                                else:
                                    film_title = title_text.strip()
                            else:
                                film_title = "Bilinmeyen Film"
                            
                            # Logoyu al
                            logo = ""
                            meta_image = soup2.find('meta', property='og:image')
                            if meta_image:
                                logo = meta_image.get('content', '')
                            
                            # Alternatif logo kaynağı
                            if not logo:
                                poster_img = soup2.find('div', class_='cover')
                                if poster_img and 'style' in poster_img.attrs:
                                    style = poster_img['style']
                                    logo_match = re.search(r'url\((https://[^)]+)\)', style)
                                    if logo_match:
                                        logo = logo_match.group(1)
                            
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
                            print(f"         ❌ Film bilgisi alınamadı {film_url}: {str(e)[:50]}")
                            continue
                    
                    # 4. Sonraki sayfa var mı kontrol et
                    next_page = soup.select_one('a[rel="next"]')
                    if not next_page:
                        break
                    
                    page += 1
                    time.sleep(0.5)  # Sunucu yükünü azalt
                    
                except Exception as e:
                    print(f"      ❌ {year} - Sayfa {page} hatası: {str(e)[:50]}")
                    break
            
            print(f"      📊 {year} yılı: {year_films_count} film")
            
            # Her yıl arasında biraz bekle
            if year_films_count > 0:
                time.sleep(1)
        
        print(f"   📊 Kategori toplam: {len(all_films)} film")
        return all_films

    def crawl_all_film_categories(self):
        """Tüm film kategorilerini çek"""
        print("=" * 60)
        print("🎬 TÜM FİLM KATEGORİLERİ ÇEKİLİYOR")
        print("=" * 60)
        
        all_films = []
        total_categories = len(self.film_turleri)
        current_category = 1
        
        for tur_name, tur_slug in self.film_turleri.items():
            print(f"\n[{current_category}/{total_categories}] ", end="")
            films = self.crawl_film_category_correct(tur_name, tur_slug)
            all_films.extend(films)
            
            # Kategori arasında bekle
            if films:
                time.sleep(2)
            
            current_category += 1
        
        return all_films

    def test_single_category(self):
        """Tek bir kategoriyi test etmek için"""
        print("=" * 60)
        print("🧪 TEK KATEGORİ TEST MODU")
        print("=" * 60)
        
        # Sadece "aksiyon" kategorisini test et
        tur_name = "aksiyon"
        tur_slug = "aksiyon"
        
        print(f"Test edilen kategori: {tur_name}")
        print(f"URL örneği: {self.base_url}/tur/{tur_slug}?genre=%2Ftur%2F{tur_slug}%3F&yil=2024&kelime=")
        
        films = self.crawl_film_category_correct(tur_name, tur_slug)
        
        # İlk 5 filmi göster
        print(f"\n📋 İlk 5 film:")
        for i, film in enumerate(films[:5], 1):
            print(f"  {i}. {film['title']}")
            print(f"     URL: {film['url']}")
            print(f"     Logo: {film['logo'][:50]}..." if film['logo'] else "     Logo: Yok")
        
        return films

    def run_films_only(self):
        """Sadece filmleri çekmek için"""
        print("=" * 60)
        print("🚀 SADECE FİLMLER ÇEKİLİYOR")
        print("=" * 60)
        
        all_films = self.crawl_all_film_categories()
        
        # M3U dosyasını oluştur
        m3u_lines = ['#EXTM3U x-tvg-url="https://github.com/botallen/epg/releases/download/latest/epg.xml"']
        
        # Filmleri gruplara ayır
        grouped_films = {}
        for film in all_films:
            group = film['group_title']
            if group not in grouped_films:
                grouped_films[group] = []
            grouped_films[group].append(film)
        
        # Her grup için M3U satırlarını oluştur
        for group_title, films in sorted(grouped_films.items()):
            m3u_lines.append(f'\n# GROUP-TITLE: "{group_title}"')
            
            for film in sorted(films, key=lambda x: x['title']):
                m3u_lines.append(f'#EXTINF:-1 tvg-id="{film["tvg_id"]}" tvg-name="{film["title"]}" tvg-logo="{film["logo"]}" group-title="{group_title}", {film["title"]}')
                m3u_lines.append(film['url'])
        
        m3u_content = '\n'.join(m3u_lines)
        
        # Dosyaya yaz
        with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print("\n" + "=" * 60)
        print(f"✅ FİLMLER TAMAMLANDI!")
        print(f"📁 Çıktı: lapizid_filmler.m3u")
        print(f"📊 Toplam film: {len(all_films)}")
        print("=" * 60)
        
        # Kategori istatistikleri
        print("\n📊 KATEGORİ İSTATİSTİKLERİ:")
        for tur_name in self.film_turleri.keys():
            category_films = [f for f in all_films if f'Film - {tur_name.upper()}' in f['group_title']]
            if category_films:
                print(f"   {tur_name.upper()}: {len(category_films)} film")

    def run_full_test(self):
        """Tam test modu"""
        print("=" * 60)
        print("🧪 TAM TEST MODU - 3 KATEGORİ")
        print("=" * 60)
        
        # Sadece 3 kategori test et
        test_categories = {
            'aksiyon': 'aksiyon',
            'korku': 'korku', 
            'komedi': 'komedi'
        }
        
        all_films = []
        
        for tur_name, tur_slug in test_categories.items():
            print(f"\n🎬 TEST: {tur_name.upper()}")
            films = self.crawl_film_category_correct(tur_name, tur_slug)
            all_films.extend(films)
            time.sleep(2)
        
        print(f"\n📊 TEST SONUÇLARI: {len(all_films)} film bulundu")

# Kullanım
if __name__ == "__main__":
    scraper = DizipalScraper()
    
    # Seçenek 1: Tam sürüm (TÜM kategoriler)
    # scraper.run_films_only()
    
    # Seçenek 2: Test modu (tek kategori)
    # scraper.test_single_category()
    
    # Seçenek 3: Tam test (3 kategori)
    scraper.run_full_test()
