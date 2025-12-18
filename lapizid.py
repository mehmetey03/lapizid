#!/usr/bin/env python3
"""
DİZİPAL FİLM SCRAPER – TAM VE DÜZGÜN SÜRÜM
"""

import cloudscraper
import requests
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class DizipalScraper:
    def __init__(self):
        self.base_url = self.get_current_domain()
        print(f"🔗 Aktif Domain: {self.base_url}")

        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "tr-TR,tr;q=0.9"
        })

        self.years = list(range(2025, 1959, -1))

        self.film_turleri = [
            "aile", "aksiyon", "animasyon", "anime", "belgesel",
            "bilimkurgu", "biyografi", "dram", "erotik",
            "fantastik", "gerilim", "gizem", "komedi", "korku",
            "macera", "muzik", "romantik", "savas", "spor",
            "suc", "tarih", "western", "yerli"
        ]

    def get_current_domain(self):
        try:
            r = requests.get(
                "https://raw.githubusercontent.com/mehmetey03/doma/refs/heads/main/lapiziddomain.txt",
                timeout=10
            )
            for line in r.text.splitlines():
                if line.startswith("guncel_domain="):
                    return line.split("=", 1)[1].strip().rstrip("/")
        except:
            pass
        return "https://dizipal1222.com"

    def crawl_category(self, slug):
        print(f"\n🎬 KATEGORİ: {slug.upper()}")
        films = []

        for year in self.years:
            print(f"  📅 {year}")
            page = 1

            while True:
                if page == 1:
                    url = f"{self.base_url}/tur/{slug}/?yil={year}&s="
                else:
                    url = f"{self.base_url}/tur/{slug}/sayfa/{page}/?yil={year}&s="

                print(f"     📄 Sayfa {page}")

                r = self.scraper.get(url, timeout=20)
                if r.status_code != 200:
                    break

                soup = BeautifulSoup(r.text, "html.parser")
                items = soup.select("article.type2")

                if not items:
                    break

                for item in items:
                    a = item.find("a", href=True)
                    if not a or "/film/" not in a["href"]:
                        continue

                    film_url = urljoin(self.base_url, a["href"])

                    try:
                        fr = self.scraper.get(film_url, timeout=20)
                        fs = BeautifulSoup(fr.text, "html.parser")

                        title = fs.title.text.split(" İzle")[0].strip()

                        logo = ""
                        og = fs.find("meta", property="og:image")
                        if og:
                            logo = og.get("content", "")

                        tvg_id = re.sub(r"\W+", "_", title.lower())

                        films.append({
                            "title": f"{title} ({year})",
                            "url": film_url,
                            "logo": logo,
                            "tvg_id": tvg_id,
                            "group": f"Film - {slug.upper()}"
                        })

                    except:
                        continue

                page += 1
                time.sleep(0.4)

            time.sleep(0.6)

        print(f"   ✅ {len(films)} film")
        return films

    def run(self):
        all_films = []

        for slug in self.film_turleri:
            all_films.extend(self.crawl_category(slug))
            time.sleep(1)

        with open("dizipal_filmler.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for film in all_films:
                f.write(
                    f'#EXTINF:-1 tvg-id="{film["tvg_id"]}" '
                    f'tvg-logo="{film["logo"]}" '
                    f'group-title="{film["group"]}",'
                    f'{film["title"]}\n'
                )
                f.write(film["url"] + "\n")

        print("\n🎉 TAMAMLANDI")
        print(f"📦 Toplam Film: {len(all_films)}")
        print("📁 dosya: dizipal_filmler.m3u")


if __name__ == "__main__":
    DizipalScraper().run()
