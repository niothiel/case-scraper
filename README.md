# Virginia Court Case Scraper

This is a Scrapy bot that I wrote one night to scrape Virginia Court Case information. I got curious how hard it would be to build up a dataset of this in machine-readable formats. Turns out, pretty easy. This is my first Scrapy project so no best practices to be found here.

## Installation

Install scrapy: `pip install Scrapy`

## Running

It only works for a single court at a time. Get the court name and code from the website, and set it in `cases/spiders/case_spider.py`. Then run: `scrapy crawl cases --verwrite-output=cases.csv` and wait.