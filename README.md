[![PyPI version](https://img.shields.io/pypi/v/reelscraper.svg)](https://pypi.org/project/reelscraper/)
[![Python 3.11](https://github.com/andreaaazo/reelscraper/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/andreaaazo/reelscraper/actions/workflows/tests.yml)

<h1 align="center">
  Reel Scraper
  <br>
</h1>

<h4 align="center">
Scrape Instagram Reels data with ease—single or multiple accounts at once—using Python, threading, and a dash of digital sorcery. 
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

Reel Scraper requires **Python 3.11.9+**. Install it from PyPI:

```bash
pip install reelscraper
```

Or clone from GitHub:

```bash
git clone https://github.com/andreaaazo/reelscraper.git
cd reelscraper
python -m pip install .
```

## 🚀 Usage

Below are two common ways to run the scraper—interactively in Python or via a CLI entry point (if provided).

### 1. Single Account or Single-Session Scraping
Use the `ReelScraper` class for scraping a single Instagram account’s Reels.

```python
from reelscraper import ReelScraper

# Initialize with desired settings
scraper = ReelScraper(timeout=30, proxy=None)

# Fetch up to 10 reels for username "someaccount"
reels_data = scraper.get_user_reels("someaccount", max_posts=10)
for reel in reels_data:
    print(reel)
```

### 2. Multiple Accounts with Concurrency
Use the `ReelMultiScraper` class to scrape Reels from multiple Instagram accounts in parallel.

```python
from reelscraper import ReelScraper
from reelscraper import ReelMultiScraper

# Initialize a single scraper instance
single_scraper = ReelScraper(timeout=30, proxy=None)

# Initialize the multi-scraper with a text file of usernames, one per line
multi_scraper = ReelMultiScraper(
    accounts_file="accounts.txt",
    scraper=single_scraper,
    max_workers=5  # concurrency level
)

# This returns a dict mapping each username to its list of reels
all_reels = multi_scraper.scrape_accounts()
print(all_reels)
```

**File-based approach**: Provide a file named `accounts.txt` with one username per line:
```
user1
user2
user3
```
The code will automatically read these usernames and scrape their Reels in parallel.

---

## 🏗 Classes

### `ReelScraper`
- Wraps around `InstagramAPI` and `Extractor` to fetch Reels data.  
- **Methods**:
  - `get_user_reels(username, max_posts, max_retries)`: Gathers Reels for a given username, with optional pagination and retries.

### `ReelMultiScraper`
- Manages scraping multiple accounts in parallel using `ReelScraper` (or a subclass) under the hood.  
- **Methods**:
  - `scrape_accounts()`: Dispatches concurrent requests to scrape each account listed in `accounts.txt` (or your chosen file).

---

## 🤝 Contributing

We welcome all contributions to make this scraper faster, smarter, or less prone to cosmic errors. To contribute:

1. **Fork** the project.  
2. **Create** a new branch.  
3. **Commit** your improvements.  
4. **Submit** a pull request.  

Adding tests, code comments, and a bit of humor in your commit messages is always appreciated!

---

## 📄 License

This project is licensed under the [MIT License](https://github.com/andreaaazo/reelscraper/blob/master/LICENSE.txt). Feel free to adapt, enhance, or break it—just be kind to fellow developers (and caffeinated beverages).

---

## 🙏 Acknowledgments

- **Python** community for making concurrency and packaging (somewhat) sane.  
- **Instagram** for hosting so many reels and giving us interesting content to scrape—please don’t smite us.  
- **Coffee** (and tea!) for fueling late-night debugging sessions.

---

## ⚠ Disclaimer

This project is for **educational and personal use**. Use it responsibly and within Instagram’s Terms of Service. We do not endorse scraping for malicious or large-scale commercial purposes. When in doubt, show social media platforms the same respect you’d show your grandmother’s cookie jar.