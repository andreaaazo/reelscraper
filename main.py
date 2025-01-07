def main():
    # Import your package modules:
    from reelscraper import ReelScraper, ReelMultiScraper
    from reelscraper.utils import AccountManager, Extractor, InstagramAPI

    print("=== DEMO: instascraper Package ===")

    # 1. Demonstrate InstaScraper usage
    # Instantiate your scraper class (example usage):
    scraper = ReelScraper()
    print("Created InstaScraper instance:", scraper)
    # Possibly call scraper.get_user_reels("someuser")

    # 2. Demonstrate MultiInstaScraper usage
    multi_scraper = ReelMultiScraper()
    print("Created MultiInstaScraper instance:", multi_scraper)
    # Possibly call multi_scraper.scrape_accounts("accounts.txt")

    print("=== END OF DEMO ===")


if __name__ == "__main__":
    main()
