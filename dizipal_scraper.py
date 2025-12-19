#!/usr/bin/env python3
"""
TMDb API kullanarak film listesinden M3U oluşturucu.
GitHub Actions ile uyumludur.
"""

import requests
import os
from datetime import datetime

class TMDB_M3U_Generator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base = "https://image.tmdb.org/t/p/w500"

        # Tür ID'leri (PHP kodunuzdaki listeye benzer)
        self.genres = {
            'Aksiyon': 28,
            'Komedi': 35,
            'Dram': 18,
            'Korku': 27,
            'Bilim Kurgu': 878,
            'Macera': 12,
            'Romantik': 10749,
        }

    def get_movies_by_genre(self, genre_name, genre_id, year=2024, page=1):
        """TMDb'den belirli tür ve yıla ait filmleri getir."""
        url = f"{self.base_url}/discover/movie"
        params = {
            'api_key': self.api_key,
            'with_genres': genre_id,
            'primary_release_year': year,
            'sort_by': 'popularity.desc',
            'page': page,
            'language': 'tr-TR'  # Türkçe bilgiler için
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            print(f"❌ '{genre_name}' türü çekilirken hata: {e}")
            return []

    def generate_m3u(self, filename='tmdb_filmler.m3u'):
        """Tüm kategorilerden filmleri alıp M3U dosyası oluştur."""
        print("🎬 TMDb'den film verileri alınıyor...")
        all_movies = []

        for genre_name, genre_id in self.genres.items():
            print(f"   📂 Kategori: {genre_name}")
            movies = self.get_movies_by_genre(genre_name, genre_id, 2024)

            for movie in movies[:5]:  # Her kategoriden ilk 5 film
                # Film detay sayfasının URL'sini oluştur (örnek)
                movie_url = f"https://www.themoviedb.org/movie/{movie.get('id')}"

                movie_data = {
                    'title': f"{movie.get('title', 'Bilinmeyen')} ({movie.get('release_date', '')[:4]})",
                    'url': movie_url,  # Burayı kendi yönlendirme sisteminize göre değiştirebilirsiniz
                    'tvg_logo': f"{self.image_base}{movie.get('poster_path', '')}" if movie.get('poster_path') else '',
                    'group_title': f"Film - {genre_name.upper()}"
                }
                all_movies.append(movie_data)
                print(f"      ✅ {movie_data['title']}")

        # M3U içeriğini oluştur
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m3u_lines = ['#EXTM3U']

        for movie in all_movies:
            m3u_lines.append(f"#EXTINF:-1 tvg-logo=\"{movie['tvg_logo']}\" group-title=\"{movie['group_title']}\", {movie['title']}")
            m3u_lines.append(movie['url'])

        # Dosyaya yaz
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(m3u_lines))
            print(f"\n✅ '{filename}' başarıyla oluşturuldu!")
            print(f"📊 Toplam {len(all_movies)} film eklendi.")
            return True
        except Exception as e:
            print(f"❌ M3U dosyası yazılırken hata: {e}")
            return False

if __name__ == "__main__":
    # KENDİ TMDb API ANAHTARINIZI BURAYA YAZIN
    API_KEY = "BURAYA_KENDI_API_ANAHTARINIZI_YAZIN"

    if API_KEY == "BURAYA_KENDI_API_ANAHTARINIZI_YAZIN":
        print("⚠️  Lütfen TMDb'den aldığınız geçerli API anahtarını script içine ekleyin.")
    else:
        generator = TMDB_M3U_Generator(API_KEY)
        generator.generate_m3u()
