#!/usr/bin/env python3
"""
DİZİPAL SCRAPER - Selenium ile JavaScript Desteği
"""

import requests
import re
import time
import json
import os
from datetime import datetime
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class DizipalScraper:
    def __init__(self, use_selenium=True):
        """Scraper başlatıcı
        
        Args:
            use_selenium (bool): JavaScript içerik için Selenium kullan
        """
        print("🚀 Dizipal Scraper başlatılıyor...")
        self.use_selenium = use_selenium
        
        # Domain'i al
        self.base_url = self.get_current_domain()
        print(f"🔗 Domain: {self.base_url}")
        print(f"🔄 Selenium Kullanımı: {'EVET' if use_selenium else 'HAYIR'}")
        
        # Selenium driver'ı başlat
        self.driver = None
        if use_selenium:
            self.init_selenium()
        
        # Normal requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        
        # GitHub Actions için optimize
        self.is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        
        # Kategoriler (GitHub Actions için sınırlı)
        if self.is_github_actions:
            print("⚡ GitHub Actions modu: Sınırlı kategori")
            self.categories = {
                'aksiyon': 'aksiyon',
                'komedi': 'komedi'
            }
            self.years = [2024]
        else:
            self.categories = {
                'aksiyon': 'aksiyon',
                'komedi': 'komedi',
                'dram': 'dram',
                'korku': 'korku'
            }
            self.years = [2024, 2023]

    def init_selenium(self):
        """Selenium driver'ını başlat"""
        try:
            print("🌐 Selenium driver başlatılıyor...")
            chrome_options = Options()
            
            # Headless mod (sunucu için)
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Cloudflare bypass için
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # WebDriverManager ile otomatik driver yükleme
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Bot tespitini önle
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Selenium driver başlatıldı")
            
        except Exception as e:
            print(f"❌ Selenium başlatma hatası: {e}")
            print("⚠️ Selenium olmadan devam ediliyor...")
            self.use_selenium = False

    def get_current_domain(self):
        """Güncel domain'i al"""
        try:
            url = "https://raw.githubusercontent.com/koprulu555/domain-kontrol2/refs/heads/main/dizipaldomain.txt"
            response = requests.get(url, timeout=10)
            for line in response.text.split('\n'):
                if line.startswith('guncel_domain='):
                    domain = line.split('=', 1)[1].strip()
                    if domain:
                        return domain.rstrip('/')
        except Exception as e:
            print(f"⚠️ Domain alınamadı: {e}")
        
        return "https://dizipal1223.com"

    def get_page_with_selenium(self, url):
        """Selenium ile sayfa içeriğini al"""
        if not self.driver:
            return None
        
        try:
            print(f"🌐 Selenium ile açılıyor: {url}")
            self.driver.get(url)
            
            # Sayfanın yüklenmesini bekle
            time.sleep(3)
            
            # JavaScript'in tamamlanmasını bekle
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Sayfa kaynağını al
            page_source = self.driver.page_source
            return page_source
            
        except Exception as e:
            print(f"❌ Selenium hatası: {e}")
            return None

    def scrape_with_selenium(self, url):
        """Selenium ile film linklerini scrape et"""
        print(f"\n🔍 Selenium ile taranıyor: {url}")
        
        page_source = self.get_page_with_selenium(url)
        if not page_source:
            return []
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Film linklerini bul - çeşitli seçiciler deneyelim
        film_links = []
        
        # 1. Tüm olası film linklerini bul
        selectors = [
            'a[href*="/film/"]',
            '[data-url*="/film/"]',
            '[href*="/izle/"]',
            '.film-list a',
            '.movie-list a',
            '.poster a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get('href') or elem.get('data-url')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if '/film/' in full_url and full_url not in film_links:
                        film_links.append(full_url)
        
        # Benzersiz linkler
        unique_links = list(set(film_links))
        print(f"✅ {len(unique_links)} film linki bulundu")
        
        return unique_links[:10] if self.is_github_actions else unique_links[:20]

    def get_film_info(self, film_url):
        """Film bilgilerini al"""
        try:
            print(f"🎥 Film bilgisi: {film_url}")
            
            # Selenium kullanarak film sayfasını aç
            if self.use_selenium and self.driver:
                page_source = self.get_page_with_selenium(film_url)
                if not page_source:
                    return None
                soup = BeautifulSoup(page_source, 'html.parser')
            else:
                response = self.session.get(film_url, timeout=20)
                if response.status_code != 200:
                    return None
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Film başlığı
            film_title = "Bilinmeyen Film"
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.text
                if 'izle' in title_text.lower():
                    parts = title_text.lower().split('izle')
                    film_title = parts[0].strip().title()
                elif ' | ' in title_text:
                    film_title = title_text.split(' | ')[0].strip()
                else:
                    film_title = title_text.strip()
            
            # H1'den kontrol et
            if film_title == "Bilinmeyen Film":
                h1_tag = soup.find('h1')
                if h1_tag:
                    film_title = h1_tag.text.strip()
            
            # Logo
            logo = ""
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                logo = meta_image.get('content', '')
            
            # Yıl
            year = "2024"
            year_match = re.search(r'(\d{4})', film_url)
            if year_match:
                year = year_match.group(1)
            
            # tvg-id
            clean_title = re.sub(r'[^\w\s-]', '', film_title.lower())
            clean_title = re.sub(r'\s+', '_', clean_title)
            tvg_id = f"{clean_title}_{year}"
            
            return {
                'url': film_url,
                'title': f"{film_title} ({year})",
                'tvg_id': tvg_id,
                'logo': logo,
                'year': year
            }
            
        except Exception as e:
            print(f"❌ Film bilgisi hatası: {e}")
            return None

    def scrape_category(self, category_name, category_slug):
        """Bir kategoriyi scrape et"""
        print(f"\n🎬 Kategori: {category_name.upper()}")
        
        category_films = []
        
        for year in self.years:
            print(f"   📅 {year} yılı")
            
            # URL oluştur
            url = f"{self.base_url}/tur/{category_slug}?yil={year}"
            
            # Selenium ile film linklerini al
            film_links = self.scrape_with_selenium(url)
            
            if not film_links:
                print(f"   ⚠️  Film bulunamadı")
                continue
            
            # Film bilgilerini al
            for i, film_url in enumerate(film_links):
                if self.is_github_actions and i >= 3:  # GitHub için sınırlı
                    break
                
                film_info = self.get_film_info(film_url)
                if film_info:
                    film_info['group_title'] = f"Film - {category_name.upper()}"
                    category_films.append(film_info)
                    print(f"      ✅ {film_info['title']}")
                
                time.sleep(1)  # Sunucu yükünü azalt
            
            if self.is_github_actions and len(category_films) >= 3:
                break
        
        print(f"   📊 Toplam: {len(category_films)} film")
        return category_films

    def generate_m3u(self, films, filename='dizipal_filmler.m3u'):
        """M3U dosyası oluştur"""
        print(f"\n📝 M3U oluşturuluyor: {filename}")
        
        # Eğer film yoksa test M3U oluştur
        if not films:
            print("⚠️  Film bulunamadı, test M3U oluşturuluyor...")
            films = [{
                'url': self.base_url,
                'title': 'Dizipal Filmleri',
                'tvg_id': 'dizipal_main',
                'logo': '',
                'group_title': 'Film - TEST',
                'year': '2024'
            }]
        
        # M3U başlığı
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m3u_lines = [
            '#EXTM3U',
            f'# Dizipal Filmleri',
            f'# Oluşturulma: {timestamp}',
            f'# Toplam: {len(films)} film',
            f'# URL: {self.base_url}',
            '#'
        ]
        
        # Filmleri ekle
        for film in films:
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{film["tvg_id"]}" tvg-logo="{film["logo"]}" group-title="{film["group_title"]}", {film["title"]}')
            m3u_lines.append(film['url'])
        
        # Dosyaya yaz
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(m3u_lines))
            
            print(f"✅ {filename} oluşturuldu")
            print(f"📁 Boyut: {len('\\n'.join(m3u_lines))} karakter")
            
            # İlk 5 satırı göster
            print(f"\n📋 İlk 5 satır:")
            lines = '\n'.join(m3u_lines).split('\n')
            for i in range(min(5, len(lines))):
                print(f"  {i+1}. {lines[i][:80]}{'...' if len(lines[i]) > 80 else ''}")
            
            return True
            
        except Exception as e:
            print(f"❌ M3U yazma hatası: {e}")
            return False

    def run(self):
        """Ana çalıştırma"""
        print("=" * 60)
        print("🚀 DİZİPAL M3U SCRAPER - SELENIUM")
        print("=" * 60)
        
        all_films = []
        total_categories = len(self.categories)
        
        for i, (category_name, category_slug) in enumerate(self.categories.items(), 1):
            print(f"\n[{i}/{total_categories}] ", end="")
            films = self.scrape_category(category_name, category_slug)
            all_films.extend(films)
            
            if i < total_categories:
                time.sleep(2)
        
        # M3U oluştur
        self.generate_m3u(all_films)
        
        print("\n" + "=" * 60)
        print(f"✅ TAMAMLANDI!")
        print(f"📊 Toplam film: {len(all_films)}")
        
        if all_films:
            print(f"\n🎬 BULUNAN FİLMLER:")
            for i, film in enumerate(all_films[:10], 1):
                print(f"  {i}. {film['title']}")
            if len(all_films) > 10:
                print(f"  ... ve {len(all_films) - 10} film daha")
        
        print("=" * 60)
        
        # Selenium'u kapat
        if self.driver:
            self.driver.quit()
            print("🌐 Selenium kapatıldı")
        
        return len(all_films)

def main():
    """Ana fonksiyon"""
    try:
        # GitHub Actions için Selenium kullan
        use_selenium = True
        
        scraper = DizipalScraper(use_selenium=use_selenium)
        film_count = scraper.run()
        
        # En az 1 film yoksa test M3U oluştur
        if film_count == 0:
            print("\n⚠️ Film bulunamadı, test M3U oluşturuluyor...")
            with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n#EXTINF:-1,Dizipal Test\nhttps://dizipal1223.com\n')
        
        # Başarılı çık
        exit(0)
        
    except Exception as e:
        print(f"\n❌ KRİTİK HATA: {e}")
        import traceback
        traceback.print_exc()
        
        # Hata durumunda test M3U
        try:
            with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
                f.write(f'#EXTM3U\n# Hata: {str(e)[:100]}\n')
        except:
            pass
        
        exit(1)

if __name__ == "__main__":
    main()
