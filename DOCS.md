# ReelScraper Documentation

> _"Scraping Instagram reels is like collecting Pokémon… except you don’t need to walk around the neighborhood—just let your code do the hustle!”_  
> — Some Developer With Too Much Coffee

Documentation covers two primary classes: **[`ReelScraper`](#reelscraper)** and **[`ReelMultiScraper`](#reelmultiscraper)**. Together, they offer a robust, threaded solution to fetch Instagram Reels data for one or more users while logging progress and optionally saving results. Below is a detailed overview of their APIs, methods, attributes, and usage examples.

---

## Table of Contents

1. [ReelScraper](#reelscraper)  
   1.1. [Overview](#overview)  
   1.2. [Constructor](#constructors)  
   1.3. [Methods](#methods)  
       - [`get_user_reels()`](#get_user_reels)  
   1.4. [Attributes](#attributes)  
   1.5. [Example Usage](#example-usage)  

2. [ReelMultiScraper](#reelmultiscraper)  
   2.1. [Overview](#overview-1)  
   2.2. [Constructor](#constructor-1)  
   2.3. [Methods](#methods-1)  
       - [`scrape_accounts()`](#scrape_accounts)  
   2.4. [Attributes](#attributes-1)  
   2.5. [Example Usage](#example-usage-1)  

3. [Frequently Asked Questions (FAQs)](#faqs)  
4. [Additional Tips](#additional-tips)

---

## ReelScraper

### Overview

**`ReelScraper`** focuses on retrieving Instagram Reels for a single user. It achieves this by composing three core components:

- **`InstagramAPI`**: Handles direct interactions with Instagram endpoints.
- **`Extractor`**: Processes raw API responses into structured reel details.
- **`LoggerManager`** (optional): Logs retry attempts, scraping progress, and errors.

This design allows for flexible error handling and detailed logging during the scraping process.

---

### Constructor

```python
def __init__(
    self,
    timeout: Optional[int] = None,
    proxy: Optional[str] = None,
    logger_manager: Optional[LoggerManager] = None,
) -> None:
    """
    Initializes ReelScraper with an InstagramAPI, Extractor, and optional LoggerManager.

    :param timeout: Connection timeout in seconds.
        - Example: timeout=10 → Waits 10 seconds for each response.
    :param proxy: Proxy string in the format 'username:password@IP:PORT' or None.
        - Example: proxy="user:pass@127.0.0.1:8080" routes requests through the given proxy.
    :param logger_manager: Optional LoggerManager instance for logging events.
    """
```

---

### Methods

#### `get_user_reels()`

```python
def get_user_reels(
    self, username: str, max_posts: int = 50, max_retries: int = 10
) -> List[Dict]:
    """
    Fetches reels for a specific user up to max_posts. Utilizes internal retry logic
    and pagination via the private method _fetch_reels().

    :param username: Instagram username whose reels are to be fetched.
    :param max_posts: Maximum number of reels to retrieve (default: 50).
    :param max_retries: Maximum number of attempts for each paginated request.
    :return: List of dictionaries, each representing a reel.
    :raises Exception: If the initial reel batch cannot be retrieved.
    """
```

**Additional Details:**

- **Retry Logic & Logging**  
  If a request fails, `_fetch_reels()` retries up to `max_retries` times, logging each retry (if a `LoggerManager` is provided).

- **Pagination**  
  After retrieving the first batch, this method continues fetching subsequent pages (while `paging_info.get("more_available", False)` is true) until `max_posts` reels are collected.

- **Extraction**  
  Each reel’s media information is processed by `Extractor` to produce a standardized reel info dictionary.

---

### Attributes

- **`api`** (`InstagramAPI`):  
  Manages HTTP requests to Instagram, respecting timeout and proxy configurations.

- **`extractor`** (`Extractor`):  
  Converts raw reel data into a structured format suitable for further processing.

- **`logger_manager`** (`LoggerManager`, optional):  
  Records key events such as retries, successful scrapes, and account errors.

---

### Example Usage

```python
from reelscraper.reel_scraper import ReelScraper
from reelscraper.utils import LoggerManager

# Optionally set up logging
logger = LoggerManager()

# Create a ReelScraper instance with a 10-second timeout and no proxy
scraper = ReelScraper(timeout=10, proxy=None, logger_manager=logger)

# Retrieve up to 20 reels for user 'cat_with_a_hat'
reels = scraper.get_user_reels("cat_with_a_hat", max_posts=20)

print(f"Fetched {len(reels)} reels!")
for reel in reels:
    print(reel)
```

**Sample Output:**
```
Fetched 20 reels!
{'id': '1234567890', 'caption': 'Dancing cat reel!', 'like_count': 42, ...}
{'id': '1234567891', 'caption': 'Cat in a new hat', 'like_count': 56, ...}
...
```

---

## ReelMultiScraper

### Overview

**`ReelMultiScraper`** extends single-user scraping to support concurrent processing across multiple Instagram accounts. It uses Python’s `ThreadPoolExecutor` for parallel requests, integrating with:

- **`ReelScraper`** for data retrieval.
- **`DataSaver`** (optional) for persistence of gathered reel data.
- **`AccountManager`** to load account names from a provided file.

Think of it as a multi-lane highway where each thread processes a different Instagram account simultaneously.

---

### Constructor

```python
def __init__(
    self,
    scraper: ReelScraper,
    max_workers: int = 5,
    data_saver: Optional[DataSaver] = None,
) -> None:
    """
    Initializes ReelMultiScraper with necessary components for concurrent scraping.

    :param scraper: An instance of ReelScraper for fetching reel data.
    :param logger_manager: Optional LoggerManager for logging multi-scraping events.
    :param max_workers: Maximum number of threads for parallel requests (default: 5).
        - Note: Too many threads may overwhelm your CPU.
    :param data_saver: Optional DataSaver instance to save the final results.
    """
```

---

### Methods

#### `scrape_accounts()`

```python
def scrape_accounts(
    self,
    accounts_file: str,
    max_posts_per_profile: Optional[int] = None,
    max_retires_per_profile: Optional[int] = None,
) -> List[Dict]:
    """
    Concurrently scrapes reels from all Instagram accounts specified in a file.
    Each account is processed in a separate thread.

    :param accounts_file: Path to a text file with one Instagram username per line.
    :param max_posts_per_profile: Maximum number of reels to fetch per profile.
    :param max_retires_per_profile: Maximum number of retries per profile.
    :return: A concatenated list of all reels from all accounts.
             (Aggregates reels across accounts.)
    """
```

**Operational Details:**

1. **Loading Accounts**  
   Uses `AccountManager` to read and store usernames from the specified file.

2. **Threaded Scraping**  
   A `ThreadPoolExecutor` with `max_workers` threads submits `get_user_reels()` tasks for each account.

3. **Data Persistence**  
   If a `DataSaver` is provided, results are saved after processing.

4. **Completion Logging**  
   After all accounts are processed, a final log entry records the total reels scraped and the number of accounts processed.

---

### Attributes

- **`scraper`** (`ReelScraper`):  
  Core scraping instance used to fetch reels for each account.

- **`max_workers`** (`int`):  
  Number of threads for parallel account scraping.

- **`data_saver`** (`DataSaver`, optional):  
  Saves the complete aggregated dataset once scraping is done.

---

### Example Usage

```python
from reelscraper.reel_scraper import ReelScraper
from reelscraper.multi_scraper import ReelMultiScraper
from reelscraper.utils import LoggerManager, DataSaver

# Optionally configure logging and data saving
logger = LoggerManager()
data_saver = DataSaver(full_path="results.json")

# Create a ReelScraper instance
my_scraper = ReelScraper(timeout=10, proxy=None, logger_manager=logger)

# Initialize ReelMultiScraper with the pre-configured ReelScraper
multi_scraper = ReelMultiScraper(
    scraper=my_scraper,
    max_workers=5,
    data_saver=data_saver
)

# Specify the path to the accounts file (one username per line)
accounts_file_path = "my_accounts.txt"

# Start the multi-account scraping process
results = multi_scraper.scrape_accounts(
    accounts_file=accounts_file_path,
    max_posts_per_profile=20,      # up to 20 reels per account
    max_retires_per_profile=10     # 10 retries per account (if needed)
)

# Display overall results (aggregated reels from all accounts)
print(f"Total reels scraped: {len(results)}")
```

**Sample Output:**
```
Done with account: cat_with_a_hat
Done with account: travel_dude
Error with account: definitely_not_real
Total reels scraped: 38
```

---

## FAQs

1. **How do I provide logging functionality?**  
   Create an instance of `LoggerManager` and pass it to `ReelScraper` or `ReelMultiScraper`. Logs will include retries, successes, errors, and other key events.

2. **Can I save results automatically?**  
   Supply a `DataSaver` instance to `ReelMultiScraper`. Results are saved after processing completes.

3. **What if some accounts are private or do not have reels?**  
   An empty list is returned or an error is logged for those accounts. The multi-scraper continues with other accounts.

4. **Can I adjust concurrency?**  
   Yes, set the `max_workers` parameter in `ReelMultiScraper`. Adjust according to your system’s capability and Instagram’s rate limits.

5. **Are scraped data stored permanently?**  
   Not by default. Data is returned as a list of dictionaries. Use `DataSaver` or your own persistence method for long-term storage.

---

## Additional Tips

- **Handling Large-Scale Scraping**  
  For thousands of reels, consider streaming data to disk or using a database to avoid high memory usage.

- **Rate-Limiting and Delays**  
  Instagram may throttle or block aggressive scraping. Integrate delays or exponential backoff if you encounter throttling issues.

- **Enhanced Logging**  
  In production, replace or extend `LoggerManager` with a comprehensive logging framework to capture and monitor events effectively.

- **Thread Management**  
  Adjust `max_workers` to balance scraping speed and system resources.

---

## Happy Scraping!

Remember: “With great power comes great responsibility.”  
And in this case: **With great concurrency comes cooler CPU fans.**

> **Final Note:** If you ever catch yourself smiling at log messages like “Done with account: cat_with_a_hat,” imagine your code delivering a virtual high-five every time it succeeds.