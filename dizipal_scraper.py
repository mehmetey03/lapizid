import cloudscraper
import requests
import re
import time
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup

class DizipalScraper:
    def __init__(self, use_proxy=False):
        # Proxy kullanımını aktif etmek için: DizipalScraper(use_proxy=True)
        self.use_proxy = use_proxy
        self.proxy_base = "https://api.codetabs.com/v1/proxy?quest="
        self.base_url = self.get_current_domain()
        print(f"🔗 Domain: {self.base_url}")
        print(f"🔄 Proxy Kullanımı: {'EVET' if self.use_proxy else 'HAYIR'}")

        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url
        })
        
        # Kategoriler
        if self.is_github_actions:
            print("⚡ GitHub Actions modu: Sınırlı kategori")
            self.categories = {
                'aksiyon': 'aksiyon',
                'komedi': 'komedi'
            }
            self.years = [2024, 2023]  # Daha gerçekçi yıllar
        else:
            self.categories = {
                'aksiyon': 'aksiyon',
                'komedi': 'komedi',
                'dram': 'dram',
                'korku': 'korku',
                'macera': 'macera'
            }
            self.years = list(range(2024, 2019, -1))

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
        
        # Fallback domain - sitenin gerçek domain'ini kontrol et
        test_domains = [
            "https://dizipal1222.com",
            "https://dizipal1223.com", 
            "https://dizipal1.com",
            "https://dizipal.com"
        ]
        
        for domain in test_domains:
            try:
                print(f"🔍 Domain test ediliyor: {domain}")
                response = requests.get(domain, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    print(f"✅ Çalışan domain bulundu: {domain}")
                    return domain
            except:
                continue
        
        # Son çare
        return "https://dizipal1223.com"

    def test_website(self):
        """Websitenin erişilebilirliğini test et"""
        try:
            print(f"\n🌐 Website test ediliyor: {self.base_url}")
            response = self.scraper.get(self.base_url, timeout=10)
            print(f"✅ Website erişilebilir: Status {response.status_code}")
            
            # HTML içeriğini kontrol et
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title')
            if title:
                print(f"📝 Sayfa başlığı: {title.text}")
            
            # Film linkleri var mı kontrol et
            film_links = soup.find_all('a', href=re.compile(r'/film/'))
            if film_links:
                print(f"🎬 Ana sayfada {len(film_links)} film linki bulundu")
                for link in film_links[:3]:
                    print(f"   🔗 {link.get('href')}")
            
            # Kategori linkleri var mı kontrol et
            kategori_links = soup.find_all('a', href=re.compile(r'/tur/'))
            if kategori_links:
                print(f"📂 {len(kategori_links)} kategori linki bulundu")
            
            return True
            
        except Exception as e:
            print(f"❌ Website test hatası: {e}")
            return False

    def get_film_links_from_page(self, url):
        """Sayfadan film linklerini al"""
        try:
            print(f"   📄 Sayfa çekiliyor: {url[:80]}...")
            response = self.scraper.get(url, timeout=20)
            
            if response.status_code != 200:
                print(f"   ❌ HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # FARKLI HTML YAPILARINI DENE
            
            # 1. Yöntem: article.type2 ul li a
            film_links = []
            
            # Deneme 1: article.type2
            articles = soup.select('article.type2 a[href*="/film/"]')
            for a in articles:
                href = a.get('href')
                if href and '/film/' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in film_links:
                        film_links.append(full_url)
            
            # Deneme 2: Tüm film linkleri
            if not film_links:
                all_links = soup.find_all('a', href=re.compile(r'/film/'))
                for link in all_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in film_links:
                            film_links.append(full_url)
            
            # Deneme 3: data-url attribute'u olanlar
            if not film_links:
                data_links = soup.find_all(attrs={"data-url": re.compile(r'/film/')})
                for elem in data_links:
                    href = elem.get('data-url')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in film_links:
                            film_links.append(full_url)
            
            print(f"   ✅ {len(film_links)} film linki bulundu")
            
            # Benzersiz linkler
            unique_links = []
            for link in film_links:
                if link not in unique_links:
                    unique_links.append(link)
            
            return unique_links
            
        except Exception as e:
            print(f"   ❌ Sayfa çekme hatası: {e}")
            return []

    def get_film_links_for_category(self, category_slug, year):
        """Kategori ve yıl için film linklerini al"""
        try:
            # URL oluştur - FARKLI FORMATLARI DENE
            urls_to_try = [
                # Format 1
                f"{self.base_url}/tur/{category_slug}?yil={year}",
                # Format 2
                f"{self.base_url}/tur/{category_slug}/?yil={year}",
                # Format 3
                f"{self.base_url}/tur/{category_slug}?genre={category_slug}&yil={year}",
                # Format 4 (encoded)
                f"{self.base_url}/tur/{category_slug}?genre=%2Ftur%2F{category_slug}%3F&yil={year}&kelime="
            ]
            
            all_links = []
            
            for url in urls_to_try:
                print(f"   🔍 URL deneniyor: {url}")
                links = self.get_film_links_from_page(url)
                if links:
                    all_links.extend(links)
                    time.sleep(1)  # Sunucu yükünü azalt
                    break  # Çalışan formatı bulduk
            
            return all_links[:5] if self.is_github_actions else all_links[:15]
            
        except Exception as e:
            print(f"   ❌ Kategori tarama hatası: {e}")
            return []

    def get_film_info(self, film_url):
        """Film bilgilerini al"""
        try:
            print(f"      🎥 Film bilgisi alınıyor: {film_url}")
            response = self.scraper.get(film_url, timeout=20)
            
            if response.status_code != 200:
                print(f"      ❌ HTTP {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Film başlığı
            film_title = "Bilinmeyen Film"
            
            # 1. title tag'den
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.text
                if 'izle' in title_text.lower():
                    parts = title_text.split('izle')
                    if parts:
                        film_title = parts[0].strip()
                elif ' | ' in title_text:
                    film_title = title_text.split(' | ')[0].strip()
                else:
                    film_title = title_text.strip()
            
            # 2. h1 tag'den
            if film_title == "Bilinmeyen Film":
                h1_tag = soup.find('h1')
                if h1_tag:
                    film_title = h1_tag.text.strip()
            
            # Logo
            logo = ""
            
            # 1. og:image meta tag
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                logo = meta_image.get('content', '')
            
            # 2. poster image
            if not logo:
                poster = soup.find('img', class_=re.compile(r'poster|cover|film'))
                if poster and poster.get('src'):
                    logo = urljoin(self.base_url, poster.get('src'))
            
            # Yıl
            year = "2024"
            year_match = re.search(r'(\d{4})', film_url)
            if year_match:
                year = year_match.group(1)
            else:
                # Sayfa içinde yıl ara
                year_text = soup.find(string=re.compile(r'\b(19|20)\d{2}\b'))
                if year_text:
                    year_match = re.search(r'\b(19|20)\d{2}\b', year_text)
                    if year_match:
                        year = year_match.group(0)
            
            # tvg-id oluştur
            clean_title = re.sub(r'[^\w\s-]', '', film_title.lower())
            clean_title = re.sub(r'\s+', '_', clean_title)
            clean_title = clean_title.strip('_')
            tvg_id = f"{clean_title}_{year}"
            
            film_info = {
                'url': film_url,
                'title': f"{film_title} ({year})",
                'tvg_id': tvg_id,
                'logo': logo,
                'year': year
            }
            
            print(f"      ✅ {film_title} ({year})")
            return film_info
            
        except Exception as e:
            print(f"      ❌ Film bilgisi hatası: {e}")
            return None

    def scrape_direct_from_homepage(self):
        """Ana sayfadan direkt film çek"""
        print("\n🏠 ANA SAYFADAN FİLM ÇEKİLİYOR...")
        
        try:
            response = self.scraper.get(self.base_url, timeout=20)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            films = []
            
            # Ana sayfadaki tüm film linklerini bul
            all_film_links = []
            
            # Farklı seçiciler deneyelim
            selectors = [
                'a[href*="/film/"]',
                'article a[href*="/film/"]',
                '.film-item a',
                '.movie-item a',
                '[data-url*="/film/"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for elem in elements:
                    href = elem.get('href') or elem.get('data-url')
                    if href and '/film/' in href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in all_film_links:
                            all_film_links.append(full_url)
                
                if all_film_links:
                    break
            
            print(f"📊 Ana sayfada {len(all_film_links)} film linki bulundu")
            
            # İlk birkaç film için bilgileri al
            for i, film_url in enumerate(all_film_links[:10] if self.is_github_actions else all_film_links[:30]):
                film_info = self.get_film_info(film_url)
                if film_info:
                    film_info['group_title'] = "Film - ANA SAYFA"
                    films.append(film_info)
                
                if self.is_github_actions and len(films) >= 5:
                    break
                time.sleep(0.5)
            
            return films
            
        except Exception as e:
            print(f"❌ Ana sayfa scrape hatası: {e}")
            return []

    def scrape_category(self, category_name, category_slug):
        """Bir kategoriyi scrape et"""
        print(f"\n🎬 Kategori: {category_name.upper()}")
        
        category_films = []
        
        for year in self.years:
            print(f"   📅 {year} yılı için filmler aranıyor...")
            
            film_links = self.get_film_links_for_category(category_slug, year)
            
            for film_url in film_links:
                film_info = self.get_film_info(film_url)
                if film_info:
                    film_info['group_title'] = f"Film - {category_name.upper()}"
                    category_films.append(film_info)
                
                # GitHub Actions için sınırlı sayıda film
                if self.is_github_actions and len(category_films) >= 3:
                    break
                time.sleep(0.5)
            
            if self.is_github_actions and len(category_films) >= 3:
                break
            time.sleep(1)
        
        print(f"   📊 Toplam: {len(category_films)} film")
        return category_films

    def generate_m3u(self, films, filename='dizipal_filmler.m3u'):
        """M3U dosyası oluştur"""
        if not films:
            print("❌ Film bulunamadı! Boş M3U oluşturuluyor...")
            films = [{
                'url': self.base_url,
                'title': 'Dizipal - Film Bulunamadı',
                'tvg_id': 'dizipal_no_films',
                'logo': '',
                'group_title': 'Film - TEST',
                'year': '2024'
            }]
        
        print(f"\n📝 M3U dosyası oluşturuluyor: {filename}")
        print(f"📊 Toplam film: {len(films)}")
        
        # Filmleri gruplara göre sırala
        films_by_group = {}
        for film in films:
            group = film.get('group_title', 'Film - DİĞER')
            if group not in films_by_group:
                films_by_group[group] = []
            films_by_group[group].append(film)
        
        # M3U başlığı
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m3u_lines = [
            '#EXTM3U',
            f'# Dizipal Filmleri',
            f'# Oluşturulma Tarihi: {timestamp}',
            f'# Toplam Film: {len(films)}',
            f'# URL: {self.base_url}',
            '#'
        ]
        
        # Her grup için filmleri ekle
        for group_title, group_films in films_by_group.items():
            m3u_lines.append(f'\n# GROUP-TITLE="{group_title}"')
            
            for film in group_films:
                m3u_lines.append(f'#EXTINF:-1 tvg-id="{film["tvg_id"]}" tvg-logo="{film["logo"]}" group-title="{group_title}", {film["title"]}')
                m3u_lines.append(film['url'])
        
        # Dosyaya yaz
        m3u_content = '\n'.join(m3u_lines)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            
            print(f"✅ M3U dosyası oluşturuldu: {filename}")
            print(f"📁 Dosya boyutu: {len(m3u_content.encode('utf-8'))} bytes")
            
            # İlk 5 satırı göster
            print(f"\n📋 İlk 5 satır:")
            for i, line in enumerate(m3u_content.split('\n')[:10], 1):
                print(f"  {i:2}. {line[:100]}{'...' if len(line) > 100 else ''}")
            
            return True
            
        except Exception as e:
            print(f"❌ M3U dosyası yazılamadı: {e}")
            return False

    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("=" * 60)
        print("🚀 DİZİPAL M3U SCRAPER")
        print("=" * 60)
        
        # Website test
        if not self.test_website():
            print("❌ Website erişilemez!")
            return 0
        
        all_films = []
        
        # Önce ana sayfadan film çek (güvenilir)
        homepage_films = self.scrape_direct_from_homepage()
        all_films.extend(homepage_films)
        
        # Sonra kategorilerden çek
        if not self.is_github_actions or len(all_films) < 3:
            print("\n📂 KATEGORİLERDEN FİLM ÇEKİLİYOR...")
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
            
            # Film listesini göster
            if all_films:
                print(f"\n🎬 BULUNAN FİLMLER:")
                for i, film in enumerate(all_films[:10], 1):
                    print(f"  {i:2}. {film['title']}")
                if len(all_films) > 10:
                    print(f"  ... ve {len(all_films) - 10} film daha")
        else:
            print("⚠️ İŞLEM TAMAMLANDI (sınırlı sonuç)")
        
        print("=" * 60)
        
        return len(all_films)

# Ana fonksiyon
def main():
    try:
        scraper = DizipalScraper()
        film_count = scraper.run()
        
        # En az 1 film bulundu mu kontrol et
        if film_count == 0:
            print("\n⚠️ Film bulunamadı, test M3U oluşturuluyor...")
            # Test M3U oluştur
            with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                f.write('#EXTINF:-1 tvg-id="dizipal_test" tvg-logo="" group-title="TEST", Dizipal Test Kanalı\n')
                f.write('https://dizipal1223.com\n')
        
        sys.exit(0 if film_count > 0 else 1)
            
    except KeyboardInterrupt:
        print("\n❌ Kullanıcı tarafından durduruldu!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ KRİTİK HATA: {e}")
        import traceback
        traceback.print_exc()
        
        # Hata durumunda boş M3U oluştur
        try:
            with open('dizipal_filmler.m3u', 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n# Hata oluştu: ' + str(e)[:100] + '\n')
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
