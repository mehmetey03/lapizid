#!/usr/bin/env python3
"""
DÜZGÜN DİZİPAL SCRAPER - Film Kategorileri Düzeltildi
"""

import cloudscraper
import requests
import re
import time
import sys
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup

class DizipalScraper:
    def __init__(self):
        self.base_url = self.get_current_domain()
        print(f"🔗 Domain: {self.base_url}")
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url,
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Daha dar yıl aralığı (test için)
        self.years = list(range(2024, 2022, -1))  # Sadece 2024-2023 için test
        
        # Test için sadece 3 kategori
        self.film_turleri = {
            'aksiyon': 'aksiyon',
            'korku': 'korku', 
            'komedi': 'komedi'
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
            print(f"⚠️  Domain alınamadı: {e}")
        
        # Test için sabit domain
        return "https://dizipal223.com"

    def test_page_structure(self, url):
        """Sayfa yapısını test etmek için"""
        print(f"\n🔍 Sayfa yapısı testi: {url}")
        try:
            r = self.scraper.get(url, timeout=30)
            print(f"   Status: {r.status_code}")
            
            if r.status_code != 200:
                return None
                
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # 1. Tüm article elementlerini bul
            articles = soup.find_all('article')
            print(f"   Toplam article sayısı: {len(articles)}")
            
            for i, article in enumerate(articles[:3]):  # İlk 3 article
                print(f"   Article {i} class: {article.get('class', ['no-class'])}")
                print(f"   Article {i} içindeki li sayısı: {len(article.find_all('li'))}")
                
                # İçindeki linkleri bul
                links = article.find_all('a', href=True)
                film_links = [a['href'] for a in links if '/film/' in a['href']]
                print(f"   Article {i} film link sayısı: {len(film_links)}")
                
                if film_links:
                    print(f"   Örnek link: {film_links[0]}")
            
            # 2. Type2 class'ını ara
            type2_articles = soup.find_all('article', class_='type2')
            print(f"   Type2 article sayısı: {len(type2_articles)}")
            
            # 3. Alternatif selector'ları test et
            print("\n   🔧 Alternatif selector testleri:")
            
            # a) Tüm film linklerini direkt bul
            all_links = soup.find_all('a', href=True)
            film_links_all = [a['href'] for a in all_links if '/film/' in a['href']]
            print(f"   Tüm sayfadaki film linkleri: {len(film_links_all)}")
            
            # b) Div içindeki filmleri ara
            movie_divs = soup.find_all('div', class_=re.compile(r'movie|film|item'))
            print(f"   Movie/film div sayısı: {len(movie_divs)}")
            
            # c) Liste item'larını ara
            list_items = soup.find_all('li')
            film_in_li = []
            for li in list_items:
                a_tags = li.find_all('a', href=True)
                for a in a_tags:
                    if '/film/' in a['href']:
                        film_in_li.append(a['href'])
            print(f"   Li içindeki film linkleri: {len(film_in_li)}")
            
            return soup
            
        except Exception as e:
            print(f"   ❌ Test hatası: {e}")
            return None

    def crawl_film_category_correct(self, tur_name, tur_slug):
        """DOĞRU ŞEKİLDE: Film kategorisini tüm yıllar için çek"""
        print(f"\n🎬 FİLM KATEGORİSİ: {tur_name.upper()} (Slug: {tur_slug})")
        
        all_films = []
        
        # Önce sayfa yapısını test et
        test_url = f"{self.base_url}/tur/{tur_slug}"
        self.test_page_structure(test_url)
        
        # Her yıl için ayrı ayrı tarama
        for year in self.years:
            print(f"\n   📅 Yıl: {year}")
            
            # DOĞRU URL YAPISI
            encoded_genre = quote(f'/tur/{tur_slug}?', safe='')
            base_url = f"{self.base_url}/tur/{tur_slug}?genre={encoded_genre}&yil={year}&kelime="
            
            page = 1
            year_films_count = 0
            max_pages = 3  # Test için maksimum 3 sayfa
            
            while page <= max_pages:
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
                    
                    # **DÜZELTME: Farklı selector kombinasyonlarını dene**
                    film_links = []
                    
                    # Yöntem 1: Tüm film linklerini direkt topla
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if href and '/film/' in href and not href.startswith('http'):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in film_links:
                                film_links.append(full_url)
                    
                    # Yöntem 2: Article içinde ara
                    if not film_links:
                        articles = soup.find_all('article')
                        for article in articles:
                            article_links = article.find_all('a', href=True)
                            for link in article_links:
                                href = link.get('href', '')
                                if href and '/film/' in href:
                                    full_url = urljoin(self.base_url, href)
                                    if full_url not in film_links:
                                        film_links.append(full_url)
                    
                    # Yöntem 3: Li elementlerinde ara
                    if not film_links:
                        list_items = soup.find_all('li')
                        for li in list_items:
                            a_tags = li.find_all('a', href=True)
                            for a in a_tags:
                                href = a.get('href', '')
                                if href and '/film/' in href:
                                    full_url = urljoin(self.base_url, href)
                                    if full_url not in film_links:
                                        film_links.append(full_url)
                    
                    print(f"      ✅ {len(film_links)} film linki bulundu")
                    
                    if not film_links:
                        if page == 1:
                            print(f"      ⚠️  {year} yılı için film bulunamadı")
                        break
                    
                    # Film detaylarını al (ilk 3 film için test)
                    for film_url in film_links[:3]:  # Test için sadece ilk 3
                        try:
                            film_info = self.get_film_details(film_url, year)
                            if film_info:
                                film_info['group_title'] = f"Film - {tur_name.upper()}"
                                all_films.append(film_info)
                                year_films_count += 1
                                print(f"         🎥 {film_info['title']}")
                                
                        except Exception as e:
                            print(f"         ❌ Film hatası: {str(e)[:50]}")
                            continue
                    
                    # Sonraki sayfa var mı kontrol et
                    next_page = soup.find('a', string=re.compile(r'Sonraki|İleri|next', re.I))
                    if not next_page:
                        next_page = soup.find('a', {'rel': 'next'})
                    
                    if not next_page:
                        # Sayfa numaralarını kontrol et
                        page_links = soup.find_all('a', href=re.compile(r'sayfa=\d+'))
                        if not page_links:
                            break
                    
                    page += 1
                    time.sleep(1)  # Sunucu yükünü azalt
                    
                except Exception as e:
                    print(f"      ❌ Sayfa {page} hatası: {str(e)[:50]}")
                    break
            
            print(f"      📊 {year} yılı: {year_films_count} film")
            
            # Her yıl arasında bekle
            if year_films_count > 0:
                time.sleep(2)
        
        print(f"   📊 Kategori toplam: {len(all_films)} film")
        return all_films

    def get_film_details(self, film_url, default_year):
        """Film detaylarını al"""
        try:
            print(f"         📥 Film detayları alınıyor: {film_url[:60]}...")
            
            r = self.scraper.get(film_url, timeout=30)
            
            if r.status_code != 200:
                print(f"         ❌ HTTP {r.status_code}")
                return None
            
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Film başlığını al
            title_tag = soup.find('title')
            film_title = "Bilinmeyen Film"
            
            if title_tag:
                title_text = title_tag.text
                # Başlığı temizle
                patterns = [
                    r'^(.*?)\s+İzle\s*\||',
                    r'^(.*?)\s*\|\s*dizipal|',
                    r'^(.*?)\s+-\s+Dizipal|',
                    r'^(.*?)\s+Full\s+HD'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, title_text, re.I)
                    if match:
                        film_title = match.group(1).strip()
                        break
                
                if film_title == "Bilinmeyen Film":
                    film_title = title_text.split('|')[0].strip()
            
            # Yıl bilgisini al
            film_year = default_year
            
            # Sayfada yıl ara
            year_patterns = [
                r'Yıl:\s*(\d{4})',
                r'Yapım Yılı:\s*(\d{4})',
                r'(\b19\d{2}\b|\b20\d{2}\b)',
                r'\((\d{4})\)'
            ]
            
            page_text = soup.get_text()
            for pattern in year_patterns:
                match = re.search(pattern, page_text)
                if match:
                    try:
                        film_year = int(match.group(1))
                        break
                    except:
                        pass
            
            # Logoyu al
            logo = ""
            
            # 1. OG Image
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                logo = meta_image.get('content', '')
            
            # 2. Twitter Image
            if not logo:
                twitter_image = soup.find('meta', property='twitter:image')
                if twitter_image:
                    logo = twitter_image.get('content', '')
            
            # 3. Poster/cover image
            if not logo:
                img_tags = soup.find_all('img', src=True)
                for img in img_tags:
                    src = img.get('src', '')
                    if src and ('poster' in src.lower() or 'cover' in src.lower()):
                        logo = src
                        break
            
            # 4. Background image style
            if not logo:
                div_tags = soup.find_all('div', style=True)
                for div in div_tags:
                    style = div.get('style', '')
                    if 'background' in style.lower() and 'url(' in style:
                        match = re.search(r'url\([\'"]?(https?://[^\'"\)]+)[\'"]?\)', style)
                        if match:
                            logo = match.group(1)
                            break
            
            # TVG ID oluştur
            clean_title = re.sub(r'[^\w\s-]', '', film_title.lower())
            clean_title = re.sub(r'\s+', '_', clean_title)
            clean_title = re.sub(r'[^\w_]', '', clean_title)
            tvg_id = f"{clean_title}_{film_year}"
            
            return {
                'url': film_url,
                'title': f"{film_title} ({film_year})",
                'tvg_id': tvg_id,
                'logo': logo,
                'type': 'film',
                'year': film_year
            }
            
        except Exception as e:
            print(f"         ❌ Film detay hatası: {str(e)[:50]}")
            return None

    def test_category_with_debug(self, tur_name, tur_slug):
        """Debug modunda kategori testi"""
        print("\n" + "=" * 60)
        print(f"🔧 DEBUG MODU: {tur_name.upper()}")
        print("=" * 60)
        
        # 1. Önce ana kategori sayfasını test et
        print(f"\n1️⃣ Ana kategori sayfası:")
        main_url = f"{self.base_url}/tur/{tur_slug}"
        self.test_page_structure(main_url)
        
        # 2. Yıllı sayfayı test et
        print(f"\n2️⃣ 2024 yılı sayfası:")
        encoded_genre = quote(f'/tur/{tur_slug}?', safe='')
        year_url = f"{self.base_url}/tur/{tur_slug}?genre={encoded_genre}&yil=2024&kelime="
        self.test_page_structure(year_url)
        
        # 3. Filmleri çek
        print(f"\n3️⃣ Film çekme testi:")
        films = self.crawl_film_category_correct(tur_name, tur_slug)
        
        # 4. Sonuçları göster
        print(f"\n📊 TEST SONUÇLARI:")
        print(f"   Toplam film: {len(films)}")
        
        if films:
            print(f"\n   İlk {min(5, len(films))} film:")
            for i, film in enumerate(films[:5], 1):
                print(f"   {i}. {film['title']}")
                print(f"      URL: {film['url'][:80]}...")
                if film['logo']:
                    print(f"      Logo: {film['logo'][:60]}...")
                else:
                    print(f"      Logo: Yok")
        else:
            print("   ❌ Hiç film bulunamadı!")
            
            # Alternatif URL denemesi
            print(f"\n🔍 Alternatif URL'ler denenecek...")
            alt_urls = [
                f"{self.base_url}/film-{tur_slug}",
                f"{self.base_url}/kategori/{tur_slug}",
                f"{self.base_url}/category/{tur_slug}",
                f"{self.base_url}/movies/{tur_slug}"
            ]
            
            for alt_url in alt_urls:
                print(f"   Deneniyor: {alt_url}")
                try:
                    r = self.scraper.head(alt_url, timeout=10)
                    if r.status_code == 200:
                        print(f"   ✅ Bu URL çalışıyor olabilir: {alt_url}")
                        self.test_page_structure(alt_url)
                except:
                    pass
        
        return films

    def run_debug_mode(self):
        """Debug modunda çalıştır"""
        print("=" * 60)
        print("🐛 DEBUG MODU - TÜM KATEGORİLER TEST EDİLİYOR")
        print("=" * 60)
        
        all_films = []
        
        for tur_name, tur_slug in self.film_turleri.items():
            films = self.test_category_with_debug(tur_name, tur_slug)
            all_films.extend(films)
            
            # Kategori arasında bekle
            time.sleep(3)
        
        # M3U oluştur
        if all_films:
            self.create_m3u_file(all_films, "dizipal_test.m3u")
        
        print(f"\n🎉 DEBUG TAMAMLANDI!")
        print(f"📊 Toplam film: {len(all_films)}")
        
        return all_films

    def create_m3u_file(self, films, filename):
        """M3U dosyası oluştur"""
        print(f"\n💾 {filename} oluşturuluyor...")
        
        m3u_lines = ['#EXTM3U']
        
        # Filmleri gruplara ayır
        grouped_films = {}
        for film in films:
            group = film.get('group_title', 'Film')
            if group not in grouped_films:
                grouped_films[group] = []
            grouped_films[group].append(film)
        
        # Her grup için
        for group_title, group_films in grouped_films.items():
            m3u_lines.append(f'\n# GROUP-TITLE: "{group_title}"')
            
            for film in sorted(group_films, key=lambda x: x['title']):
                extinf_line = f'#EXTINF:-1'
                
                if film.get('tvg_id'):
                    extinf_line += f' tvg-id="{film["tvg_id"]}"'
                
                extinf_line += f' tvg-name="{film["title"]}"'
                
                if film.get('logo'):
                    extinf_line += f' tvg-logo="{film["logo"]}"'
                
                extinf_line += f' group-title="{group_title}"'
                extinf_line += f', {film["title"]}'
                
                m3u_lines.append(extinf_line)
                m3u_lines.append(film['url'])
        
        # Dosyaya yaz
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(m3u_lines))
            print(f"✅ {filename} oluşturuldu ({len(films)} film)")
        except Exception as e:
            print(f"❌ M3U yazma hatası: {e}")

# Kullanım
if __name__ == "__main__":
    print("🚀 Dizipal Scraper - Debug Version")
    print(f"⏰ Başlangıç: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    scraper = DizipalScraper()
    
    # Debug modunda çalıştır
    scraper.run_debug_mode()
    
    print(f"\n⏰ Bitiş: {time.strftime('%Y-%m-%d %H:%M:%S')}")
