def crawl_film_category_correct(self, tur_name, tur_slug):
    """DOĞRU ŞEKİLDE: Film kategorisini tüm yıllar için çek"""
    print(f"\n🎬 FİLM KATEGORİSİ: {tur_name.upper()} (Slug: {tur_slug})")
    
    all_films = []
    
    # Her yıl için ayrı ayrı tarama
    for year in self.years:
        print(f"   📅 Yıl: {year}")
        
        # DÜZELTME: BASİT URL YAPISI KULLAN
        # HTML'de gördüğümüz gibi: /tur/aksiyon?
        base_url = f"{self.base_url}/tur/{tur_slug}?yil={year}"
        
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
                r = self.make_request(url, timeout=30)
                
                if not r or r.status_code != 200:
                    status_code = getattr(r, 'status_code', 'Bilinmiyor')
                    print(f"      ❌ HTTP Hatası {status_code}")
                    break
                
                soup = BeautifulSoup(r.content, 'html.parser')
                
                # DEĞİŞİKLİK: Farklı HTML yapısı için seçicileri güncelle
                # Önce sayfanın yapısını kontrol et
                print(f"      🔍 HTML analizi...")
                
                # 1. Farklı seçiciler deneyelim
                film_links = []
                
                # Seçenek 1: div içindeki film linkleri
                movie_divs = soup.select('div.movie-item, div.film-item, div.item')
                for div in movie_divs:
                    links = div.select('a[href*="/film/"]')
                    for link in links:
                        href = link.get('href', '')
                        if href and '/film/' in href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in film_links:
                                film_links.append(full_url)
                
                # Seçenek 2: Direkt tüm film linkleri
                if not film_links:
                    all_links = soup.find_all('a', href=lambda x: x and '/film/' in x)
                    for link in all_links:
                        href = link.get('href', '')
                        full_url = urljoin(self.base_url, href)
                        if full_url not in film_links:
                            film_links.append(full_url)
                
                # Seçenek 3: data-href veya data-url attribute'ları
                if not film_links:
                    data_links = soup.find_all(attrs={"data-href": lambda x: x and '/film/' in str(x)})
                    for elem in data_links:
                        href = elem.get('data-href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in film_links:
                                film_links.append(full_url)
                
                print(f"      ✅ {len(film_links)} film linki bulundu")
                
                # HTML'de hata ayıklama için ilk 1000 karakteri göster
                if not film_links and page == 1:
                    print(f"      🐛 DEBUG: Sayfa içeriğinin ilk 1000 karakteri:")
                    print(str(soup)[:1000])
                
                if not film_links:
                    if page == 1:
                        print(f"      ⚠️  {year} yılı için film bulunamadı")
                    break
                
                # 3. Her film için bilgileri çek (ilk 3 filmle sınırla test için)
                for film_url in film_links[:3]:  # Test için sadece ilk 3 film
                    try:
                        r2 = self.make_request(film_url, timeout=30)
                        
                        if not r2 or r2.status_code != 200:
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
                        
                        # Yılı URL'den çıkar
                        year_match = re.search(r'(\d{4})', film_url)
                        film_year = year_match.group(1) if year_match else str(year)
                        
                        # tvg-id oluştur
                        clean_title = re.sub(r'[^\w\s-]', '', film_title.lower())
                        clean_title = clean_title.replace(' ', '_').replace('__', '_')
                        tvg_id = f"{clean_title}_{film_year}"
                        
                        all_films.append({
                            'url': film_url,
                            'title': f"{film_title} ({film_year})",
                            'tvg_id': tvg_id,
                            'logo': logo,
                            'group_title': f"Film - {tur_name.upper()}",
                            'type': 'film'
                        })
                        
                        year_films_count += 1
                        print(f"         ✅ İşlendi: {film_title}")
                        
                    except Exception as e:
                        print(f"         ❌ Film bilgisi alınamadı: {str(e)[:50]}")
                        continue
                
                # 4. Sonraki sayfa kontrolü
                next_page = soup.select_one('a[rel="next"], .pagination .next, a:contains("Sonraki")')
                if not next_page:
                    break
                
                page += 1
                time.sleep(1)  # Sunucu yükünü azalt
                
            except Exception as e:
                print(f"      ❌ {year} - Sayfa {page} hatası: {str(e)[:50]}")
                break
        
        print(f"      📊 {year} yılı: {year_films_count} film")
        
        # Her yıl arasında biraz bekle
        if year_films_count > 0:
            time.sleep(2)
    
    print(f"   📊 Kategori toplam: {len(all_films)} film")
    return all_films
