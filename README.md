[![PyPI version](https://img.shields.io/pypi/v/reelscraper.svg)](https://pypi.org/project/reelscraper/)
[![Build](https://github.com/andreaaazo/reelscraper/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/andreaaazo/reelscraper/actions/workflows/tests.yml)
[![Code Tests Coverage](https://codecov.io/gh/andreaaazo/reelscraper/branch/master/graph/badge.svg)](https://codecov.io/gh/andreaaazo/reelscraper)

<h1 align="center">
  ReelScraper
  <br>
</h1>

<h4 align="center">
Scrape Instagram Reels data with ease—be it a single account or many in parallel—using Python, threading, robust logging, and optional data-saving.
</h4>

<p align="center">
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-classes">Classes</a> •
  <a href="#-documentation">Documentation</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a> •
  <a href="#-acknowledgments">Acknowledgments</a> •
  <a href="#-disclaimer">Disclaimer</a>
</p>

---

## 💻 Installation

Requires **Python 3.9+**. Install directly from PyPI:

```bash
pip install reelscraper
```

Or clone from GitHub:

```bash
git clone https://github.com/andreaaazo/reelscraper.git
cd reelscraper
python -m pip install .
```

---

## 🚀 Usage

ReelScraper supports detailed logging and optional data-saving. Choose between single-session scraping or multi-account concurrency.

### 1. Single-Account Scraping

Use **`ReelScraper`** to fetch Reels for a single account. Optionally pass a `LoggerManager` for retry logs and progress tracking.

```python
from reelscraper import ReelScraper
from reelscraper.utils import LoggerManager

# Optional logger setup
logger = LoggerManager()

# Initialize scraper with a 30-second timeout, no proxy, and logging
scraper = ReelScraper(timeout=30, proxy=None, logger_manager=logger)

# Fetch up to 10 reels for "someaccount"
reels_data = scraper.get_user_reels("someaccount", max_posts=10)
for reel in reels_data:
    print(reel)
```

### 2. Multi-Account Concurrency & Data Saving

Use **`ReelMultiScraper`** to process many accounts concurrently. Configure logging (`LoggerManager`) and data-saving (`DataSaver`) if desired.

```python
from reelscraper import ReelScraper, ReelMultiScraper
from reelscraper.utils import LoggerManager
from reelscraper.utils.database import DBManager

# Configure logger and data saver
logger = LoggerManager()
db_manager = DBManager()

# Create a single scraper instance
single_scraper = ReelScraper(timeout=30, proxy=None, logger_manager=logger)

# MultiScraper for concurrency, data saving, and auto-logging
multi_scraper = ReelMultiScraper(
    single_scraper,
    max_workers=5,
    db_manager=db_manager,
)

# File contains one username per line, e.g.:
#   user1
#   user2
accounts_file_path = "accounts.txt"

# Scrape accounts concurrently
all_reels = multi_scraper.scrape_accounts(
    accounts_file=accounts_file_path,
    max_posts_per_profile=20,
    max_retires_per_profile=10
)

print(f"Total reels scraped: {len(all_reels)}")
```

> **Note:** MultiScraper will gather usernames from the specified file, log progress if a `LoggerManager` is used, and optionally save aggregated reels if a `DBManager` is provided.

---

## 🏗 Classes

### `ReelScraper`
- **Purpose:**  
  Fetches Instagram Reels for a single user session.
- **Key Components:**  
  - `InstagramAPI`: Manages HTTP requests and proxy usage.  
  - `Extractor`: Structures raw reel data.  
  - `LoggerManager` (optional): Logs retries and status events.
- **Key Method:**  
  - `get_user_reels(username, max_posts, max_retries)`: Retrieves reels, handling pagination and retries.

### `ReelMultiScraper`
- **Purpose:**  
  Scrapes multiple accounts in parallel, powered by a single `ReelScraper` instance.
- **Key Components:**  
  - `ThreadPoolExecutor`: Enables concurrent scraping.  
  - `AccountManager`: Reads accounts from a local file.  
  - `LoggerManager` (optional): Captures multi-account events.  
  - `DBManager` (optional): Saves aggregated results to disk.
- **Key Method:**  
  - `scrape_accounts(accounts_file, max_posts_per_profile, max_retires_per_profile)`: Concurrently processes all accounts found in the file.

---

## 📄 Documentation

Find full usage details in the [DOCS.md](https://github.com/andreaaazo/reelscraper/blob/master/DOCS.md) file.

---

## 🤝 Contributing

We welcome PRs that enhance features, fix bugs, or improve docs.

1. **Fork** the repo.
2. **Create** a new branch.
3. **Commit** code changes (add tests where possible).
4. **Open** a pull request.

Your contributions are appreciated—happy coding!

---

## 📄 License

Licensed under the [MIT License](https://github.com/andreaaazo/reelscraper/blob/master/LICENSE.txt). Feel free to modify and distribute, but please be mindful of best practices and ethical scraping.

---

## 🙏 Acknowledgments

- **Python Community**: For making concurrency and requests straightforward to implement.  
- **Instagram**: For providing reel content that inspires creativity.  
- **Beverages**: For fueling long coding sessions (coffee or tea).

---

## ⚠ Disclaimer

This software is for **personal and educational** purposes only. Use it in accordance with Instagram’s Terms of Service. We do not promote or condone large-scale commercial scraping or any violation of privacy/IP rights.

---

Enjoy scraping, and may your concurrency be swift! 
```