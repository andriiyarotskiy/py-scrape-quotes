import asyncio
import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, ResultSet, Tag


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


QUOTE_COLUMNS = [f.name for f in fields(Quote)]

BASE_URL = "https://quotes.toscrape.com"


def parse_single_quote(soup: Tag) -> Quote:
    return Quote(
        text=soup.select_one(".text").text,
        author=soup.select_one("span > small[itemprop=author]").text,
        tags=[tag.text for tag in soup.select(".tags > .tag")]
    )


def parse_page_quotes(quotes: ResultSet[Tag]) -> list[Quote]:
    return [parse_single_quote(soup) for soup in quotes]


async def get_page_quotes() -> list[Quote]:
    page_num = 1
    all_quotes = []
    async with httpx.AsyncClient() as client:
        while True:
            request_url = urljoin(BASE_URL, f"/page/{page_num}/")
            response = await client.get(request_url)
            soup = BeautifulSoup(response.content, "html.parser")
            page_quotes = soup.find_all("div", class_="quote")

            if not page_quotes:
                break

            all_quotes.extend(parse_page_quotes(page_quotes))
            page_num += 1

    return all_quotes


def write_quotes_to_csv(output_csv_path: str, quotes: list[Quote]) -> None:
    with open(output_csv_path, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(QUOTE_COLUMNS)
        writer.writerows([astuple(quote) for quote in quotes])


async def main(output_csv_path: str) -> None:
    quotes = await get_page_quotes()
    write_quotes_to_csv(output_csv_path, quotes)


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main("quotes.csv"))
    end = time.time() - start
    print(f"Time elapsed: {end} seconds")