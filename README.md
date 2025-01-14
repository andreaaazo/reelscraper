[![PyPI version](https://img.shields.io/pypi/v/reelscraper.svg)](https://pypi.org/project/reelscraper/)
[![Build](https://github.com/andreaaazo/reelscraper/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/andreaaazo/reelscraper/actions/workflows/tests.yml)
[![Code Tests Coverage](https://codecov.io/gh/andreaaazo/reelscraper/branch/master/graph/badge.svg)](https://codecov.io/gh/andreaaazo/reelscraper)

<h1 align="center">
  Reel Scraper
  <br>
</h1>

<h4 align="center">
Scrape Instagram Reels data with ease—be it a single account or many in parallel—using Python, threading, robust logging, and optional data-saving.
</h4>

<p align="center">
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-classes">Classes</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a> •
  <a href="#-acknowledgments">Acknowledgments</a> •
  <a href="#-disclaimer">Disclaimer</a>
</p>

---

## 💻 Installation

Reel Scraper requires **Python 3.9+**. Install it from PyPI:

```bash
pip install reelscraper
```

Alternatively, clone from GitHub:

```bash
git clone https://github.com/andreaaazo/reelscraper.git
cd reelscraper
python -m pip install .
```

---

## 🚀 Usage

Reel Scraper now supports additional logging and data-saving functionalities. Below are two common ways to run the scraper—either interactively or via a CLI entry point (if provided).

### 1. Single Account or Single-Session Scraping

Use the `ReelScraper` class for scraping Reels from one Instagram account at a time. Optionally, integrate a `LoggerManager` to get detailed logs during retries and processing.

```python
from reelscraper import ReelScraper
from reelscraper.utils import LoggerManager

# Optionally configure the logger
logger = LoggerManager()

# Initialize with a 30-second timeout, no proxy, and logging enabled
scraper = ReelScraper(timeout=30, proxy=None, logger_manager=logger)

# Fetch up to 10 reels for username "someaccount"
reels_data = scraper.get_user_reels("someaccount", max_posts=10)
for reel in reels_data:
    print(reel)
```

### 2. Multiple Accounts with Concurrency & Data Saving

Use the `ReelMultiScraper` class to process multiple Instagram accounts concurrently. In addition to concurrency, you can now enable logging and automatically save the results using a `DataSaver`.

```python
from reelscraper import ReelScraper, ReelMultiScraper
from reelscraper.utils import LoggerManager, DataSaver

# Configure logger and data saver
logger = LoggerManager()
data_saver = DataSaver("json")

# Initialize a single scraper instance with logging
single_scraper = ReelScraper(timeout=30, proxy=None, logger_manager=logger)

# Initialize the multi-scraper with the data saver and custom concurrency settings
multi_scraper = ReelMultiScraper(
    scraper=single_scraper,
    logger_manager=logger,
    max_workers=5,      # Number of threads
    data_saver=data_saver
)

# Provide a file with one username per line:
# accounts.txt content example:
#   user1
#   user2
#   user3
accounts_file_path = "accounts.txt"

# Start the multi-account scraping process:
# Optionally, define max_posts_per_profile and max_retries_per_profile.
all_reels = multi_scraper.scrape_accounts(
    accounts_file=accounts_file_path,
    max_posts_per_profile=20,
    max_retires_per_profile=10
)

# Display overall (aggregated) results:
print(f"Total reels scraped: {len(all_reels)}")
```

> **Note:** The multi-account scraper reads usernames from your provided file (one per line) and aggregates reels across all accounts. Logging messages and progress are displayed during processing if `LoggerManager` is configured. The final result is saved if `DataSaver` is configured.

---

## 🏗 Classes

### `ReelScraper`
- **Purpose:**  
  Retrieves Instagram Reels data for a single account.
- **Key Components:**  
  - **InstagramAPI:** Handles HTTP requests.  
  - **Extractor:** Formats raw data into structured reels information.  
  - **LoggerManager (optional):** Logs retries and status events.
- **Key Method:**  
  - `get_user_reels(username, max_posts, max_retries)`: Fetches reels for the specified user, applying pagination, retries, and logging.

### `ReelMultiScraper`
- **Purpose:**  
  Scrapes multiple accounts concurrently using an underlying `ReelScraper` instance.
- **Key Components:**  
  - **ThreadPoolExecutor:** Manages concurrent requests.  
  - **AccountManager:** Loads accounts from a file.  
  - **LoggerManager (optional):** Tracks start, successes, errors, and final statistics.  
  - **DataSaver (optional):** Saves results to a file.
- **Key Method:**  
  - `scrape_accounts(accounts_file, max_posts_per_profile, max_retires_per_profile)`: Executes parallel scraping across the accounts listed in the provided file.

---

## 🤝 Contributing

We welcome contributions that make this scraper smarter, faster, or more resilient to changes. To contribute:

1. **Fork** the project.
2. **Create** a new branch.
3. **Commit** your improvements (bonus points for clear comments and even a dash of humor).
4. **Submit** a pull request.

Your contributions—whether bug fixes, new features, or documentation updates—are greatly appreciated!

---

## 📄 License

This project is licensed under the [MIT License](https://github.com/andreaaazo/reelscraper/blob/master/LICENSE.txt). Use, modify, or distribute the project freely (just be kind to your fellow developers and remember your caffeine intake).

---

## 🙏 Acknowledgments

- **Python Community:** For enabling an accessible approach to concurrency, API integration, and packaging.
- **Instagram:** For providing reels that inspire both creativity and the need for efficient scraping.
- **Coffee & Tea:** The timeless fuels behind countless hours of problem-solving and debugging.

---

## ⚠ Disclaimer

This project is for **educational and personal use only**. Always use it responsibly and in compliance with Instagram’s Terms of Service. We do not condone or endorse large-scale commercial scraping or any activity that violates policies. When in doubt, respect intellectual property and privacy the way you’d guard your grandmother’s cookie jar.

---

Happy scraping and may your CPU fans stay cool!