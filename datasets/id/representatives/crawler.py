from normality import collapse_spaces, slugify
from typing import Dict, List
import re
from lxml import etree

from zavod import Context
from zavod import helpers as h
from zavod.logic.pep import categorise
from zavod.util import ElementOrTree

# December 21, 1967
FORMATS = ["%B, %d %Y"]
MONTHS = [
    ("Januari", "January"),
    ("Februari", "February"),
    ("Maret", "March"),
    ("April", "April"),
    ("Mei", "May"),
    ("Juni", "June"),
    ("Juli", "July"),
    ("Agustus", "August"),
    ("September", "September"),
    ("Oktober", "October"),
    ("November", "November"),
    ("Desember", "December"),
]


def parse_date(date_str: str) -> str:
    for ind, eng in MONTHS:
        date_str = date_str.replace(ind, eng)
    return h.parse_date(date_str, formats=FORMATS)


def onclick_link(row: ElementOrTree) -> str:
    onclick = row.get("onclick")
    if onclick is None:
        return
    return re.sub(r".*window.location='([^']+)'.*", r"\1", onclick)


def crawl_row(context: Context, url: str):
    doc = context.fetch_html(url, cache_days=1)
    person = context.make("Person")
    name = collapse_spaces(doc.findtext(".//h3"))
    person.id = context.make_id(name)
    person.add("name", name)

    # Place of Birth / Date of Birth
    birth_label = doc.xpath("//div[contains(text(),'Tempat Lahir / Tgl Lahir')]")
    birth_value = birth_label[0].getnext()
    assert "input" in birth_value.get("class")
    birth_place, birth_date = birth_value.text_content().split("/")
    person.add("birthPlace", birth_place.strip(), lang="ind")
    person.add("birthDate", parse_date(birth_date.strip()))

    context.emit(person, target=True)



def crawl(context: Context):
    print(context.fetch_html("https://www.dpr.go.id", headers={"referer": "https://www.dpr.go.id/"}, cache_days=1))
    print(context.fetch_html("https://www.dpr.go.id/anggota", headers={"referer": "https://www.dpr.go.id/"}, cache_days=1))
    doc = context.fetch_html(context.data_url, headers={"referer": "https://www.dpr.go.id/"}, cache_days=1)
    for row in doc.find("//table[@id='data-anggota2']").findall("//tr"):
        url = onclick_link(row)
        if not url:
            context.log.warning("No link for row", row=row.text_content())
            continue
        crawl_row(context, url)