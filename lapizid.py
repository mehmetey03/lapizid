#!/usr/bin/env python3
import cloudscraper
import requests
import time
import re
from bs4 import BeautifulSoup


BASE_FALLBACK = "https://dizipal1223.com"


class DizipalFilmScraper:
    def __init__(self):
        self.base = self.get_domain()
        print(f"🔗 Domain: {self.base}")

        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        self.categories = [
            "aile","aksiyon","animasyon","anime","belgesel","bilimkurgu",
            "biyografi","dram","fantastik","gerilim","gizem","komedi",
            "korku","macera","muzik","romantik","savas","spor",
            "suc","tarih","western","yerli"
        ]

        self.years = range(2025, 1959, -1)

    def get_domain(self):
        try:
            r = requests.get(
                "https://raw.githubusercontent.com/mehmetey03/doma/refs/heads/main/lapiziddomain.txt",
                timeout=10
            )
            for line in r.text.splitlines():
                if line.startswith("guncel_domain="):
                    return line.split("=",1)[1].strip().rstrip("/")
        except:
            pass
        return BASE_FALLBACK

    def fetch_movies(self, category, year, page):
        data = {
            "action": "filter_movies",
            "genre": category,
            "year": year,
            "paged": page
        }

        r = self.scraper.post(
            f"{self.base}/wp-admin/admin-ajax.php",
            headers=self.headers,
            data=data,
            timeout=20
        )

        if r.status_code != 200 or len(r.text) < 50:
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        return soup.select("article")

    def run(self):
        movies = []

        for cat in self.categories:
            print(f"\n🎬 KATEGORİ: {cat.upper()}")

            for year in self.years:
                print(f"  📅 {year}", end=" ")

                page = 1
                year_count = 0

                while True:
                    items = self.fetch_movies(cat, year, page)
                    if not items:
                        break

                    for item in items:
                        a = item.find("a", href=True)
                        if not a:
                            continue

                        url = a["href"]
                        title = a.get("title","").strip()
                        if not title:
                            continue

                        tvg_id = re.sub(r"\W+", "_", title.lower())

                        movies.append({
                            "title": f"{title} ({year})",
                            "url": url,
                            "group": f"Film - {cat.upper()}",
                            "tvg_id": tvg_id
                        })
                        year_count += 1

                    page += 1
                    time.sleep(0.3)

                print(f"→ {year_count}")

        self.write_m3u(movies)
        print(f"\n✅ TOPLAM FİLM: {len(movies)}")

    def write_m3u(self, movies):
        with open("dizipal_filmler.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for m in movies:
                f.write(
                    f'#EXTINF:-1 tvg-id="{m["tvg_id"]}" '
                    f'group-title="{m["group"]}",{m["title"]}\n'
                )
                f.write(m["url"] + "\n")


if __name__ == "__main__":
    DizipalFilmScraper().run()
