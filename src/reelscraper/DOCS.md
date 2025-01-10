# ReelScraper Documentation

> _"Scraping Instagram reels is like collecting Pokémon… except you don’t need to walk around the neighborhood—just let your code do the hustle!”_  
> — Some Developer With Too Much Coffee

This documentation covers two classes: **[`ReelScraper`](#reelscraper)** and **[`ReelMultiScraper`](#reelmultiscraper)**. Together, they provide a flexible, threaded approach to pulling Reels data for one or multiple Instagram users. Below, you’ll find a comprehensive breakdown of their APIs, attributes, methods, and usage examples.

---

## Table of Contents

1. [ReelScraper](#reelscraper)  
   1.1. [Overview](#reelscraper-overview)  
   1.2. [Constructor](#reelscraper-constructor)  
   1.3. [Methods](#reelscraper-methods)  
       - [`_fetch_reels()`](#_fetch_reels)  
       - [`get_user_reels()`](#get_user_reels)  
   1.4. [Attributes](#reelscraper-attributes)  
   1.5. [Example Usage](#reelscraper-example)  

2. [ReelMultiScraper](#reelmultiscraper)  
   2.1. [Overview](#reelmultiscraper-overview)  
   2.2. [Constructor](#reelmultiscraper-constructor)  
   2.3. [Methods](#reelmultiscraper-methods)  
       - [`scrape_accounts()`](#scrape_accounts)  
   2.4. [Attributes](#reelmultiscraper-attributes)  
   2.5. [Example Usage](#reelmultiscraper-example)  

3. [Frequently Asked Questions (FAQs)](#faqs)  
4. [Additional Tips](#additional-tips)

---

## ReelScraper

### ReelScraper Overview

The **`ReelScraper`** class is designed to fetch Instagram Reels for a single user at a time. It leverages two primary components:

- **`InstagramAPI`**: Manages direct requests to Instagram endpoints.
- **`Extractor`**: Processes raw data into structured Reel information.

> **Fun Fact**: If you ever fantasized about turning into a secret agent while sniffing out hidden data, `ReelScraper` is a good place to start. Mission: Instagram Reels!

---

### ReelScraper Constructor

```python
def __init__(self, timeout: int, proxy: Optional[str]) -> None:
    """
    Initializes ReelScraper with an InstagramAPI and an Extractor.

    :param timeout: Connection timeout in seconds
    :param proxy: Proxy string or None
    """
```

**Parameters:**

- **timeout** (`int`):  
  Specifies how many seconds to wait for a response before timing out.  
  - Example: `timeout=10` → The scraper will wait 10 seconds for a response before giving up.
- **proxy** (`Optional[str]`):  
  A string containing the proxy server address, or `None` if no proxy is used.  
  - Example: `proxy="http://127.0.0.1:8080"` → Route requests through a local proxy.

---

### ReelScraper Methods

#### `_fetch_reels()`

```python
def _fetch_reels(
    self, username: str, max_id: Optional[str], max_retries: int
) -> Dict:
    """
    Retrieves the first or subsequent batch of reels and returns a dictionary
    containing items and paging info. Retries up to max_retries times if fetching fails.

    :param username: The Instagram username whose reels are being fetched
    :param max_id: A string representing the last reel’s identifier for pagination
                   (None for the first batch of reels)
    :param max_retries: Maximum retry attempts if a fetch fails
    :return: Dictionary containing reel items and associated paging information
    :raises Exception: If data cannot be fetched within the specified max_retries
    """
```

**Key Points:**

- Uses **`InstagramAPI`** to either fetch the first set of reels (`get_user_first_reels()`) or a subsequent paginated batch (`get_user_paginated_reels()`).
- Will attempt multiple fetches (up to `max_retries`) before throwing an exception.
- Returns a dictionary structured like:
  ```python
  {
      "items": [...],
      "paging_info": {
          "max_id": "...",
          "more_available": True/False
      }
  }
  ```

> **Tip**: If you hear your network groaning, it might be time to reduce `max_retries` or give your internet hamster a treat.

---

#### `get_user_reels()`

```python
def get_user_reels(
    self, username: str, max_posts: Optional[int] = None, max_retries: int = 10
) -> List[Dict]:
    """
    Gathers user reels up to max_posts. Paginates through all available reels,
    retrying each batch up to max_retries if necessary.

    :param username: The Instagram username to retrieve reels for
    :param max_posts: Max number of reels to fetch (default: 50 if not specified)
    :param max_retries: Maximum retries for each paginated batch
    :return: List of reel information dictionaries
    :raises Exception: If the first batch cannot be fetched for the given username
    """
```

**Key Points:**

- **max_posts** controls how many reels to return (default is 50).
- Internally calls `_fetch_reels()` for paginated data.  
- The returned list is composed of reel data dictionaries, courtesy of the **`Extractor`**.  
- Continues retrieving further pages (`while paging_info.get("more_available", False)`) until either:
  - No more reels are available, or
  - `max_posts` is reached.

> **Heads Up**: If your user has 10,000 reels, you might be there for a while. Perhaps consider grabbing a coffee (or a pizza).  

---

### ReelScraper Attributes

- **`api`** (`InstagramAPI`):  
  Responsible for making the actual requests to Instagram’s endpoints, respecting your `timeout` and `proxy` settings.

- **`extractor`** (`Extractor`):  
  Processes raw Instagram reel data into a more structured form.

---

### ReelScraper Example

```python
from reelscraper.utils import InstagramAPI, Extractor
from reelscraper.reel_scraper import ReelScraper

# Initialize a ReelScraper instance
scraper = ReelScraper(timeout=10, proxy=None)

# Fetch up to 20 reels for the user 'cat_with_a_hat'
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

### ReelMultiScraper Overview

The **`ReelMultiScraper`** class extends the functionality of `ReelScraper` to handle **multiple** Instagram usernames concurrently. If you have a text file brimming with Instagram handles, `ReelMultiScraper` is your sidekick for scraping them all in parallel.

> **Pro Tip**: Think of it like a multi-lane highway. Each lane (thread) can independently fetch reels for a different user. No traffic jams if you keep it sensible!

---

### ReelMultiScraper Constructor

```python
def __init__(
    self,
    accounts_file: str,
    scraper: ReelScraper,
    max_workers: int = 5,
) -> None:
    """
    Initializes ReelMultiScraper by loading account names and storing references.

    :param accounts_file: Path to a text file containing one username per line
    :param scraper: Instance of ReelScraper used to fetch reels
    :param max_workers: Maximum number of threads to use for concurrent requests
    """
```

**Parameters:**

- **accounts_file** (`str`):  
  Path to a text file containing Instagram usernames, one per line, e.g.:  
  ```
  cat_with_a_hat
  travel_dude
  retro_games
  ```
- **scraper** (`ReelScraper`):  
  A pre-configured `ReelScraper` instance for fetching reels.
- **max_workers** (`int`):  
  Number of threads to spawn in the thread pool.  
  - Default: `5`  
  - *Warning*: Setting `max_workers` too high can lead to your CPU performing interpretive dance.

---

### ReelMultiScraper Methods

#### `scrape_accounts()`

```python
def scrape_accounts(self) -> Dict[str, List[Dict]]:
    """
    Scrapes reels for each account in parallel, returning a dictionary
    keyed by username with reel data as lists.

    :return: Dictionary mapping each username to a list of reel info dictionaries
    """
```

**Details:**

1. Creates a `ThreadPoolExecutor` with `max_workers` threads.  
2. Submits the scraping task (`scraper.get_user_reels()`) for every username found in `accounts_file`.
3. Collects the results as they complete, logging any errors (no meltdown—just a polite message).
4. Returns a dictionary:  
   ```python
   {
       "cat_with_a_hat": [{...}, {...}, ...],
       "travel_dude": [{...}, {...}, ...],
       ...
   }
   ```

> **Note**: Error handling ensures that the entire scraping operation won’t halt if one account has issues (e.g., private or invalid username).  

---

### ReelMultiScraper Attributes

- **`account_manager`** (`AccountManager`):  
  Utility that reads and manages the list of accounts from `accounts_file`.
- **`scraper`** (`ReelScraper`):  
  The user-provided `ReelScraper` for retrieving reel data from Instagram.  
- **`max_workers`** (`int`):  
  Defines the size of the thread pool.  
- **`accounts`** (`List[str]`):  
  List of usernames retrieved from `accounts_file`.

---

### ReelMultiScraper Example

```python
from reelscraper.reel_scraper import ReelScraper
from reelscraper.multi_scraper import ReelMultiScraper

# 1. Create a ReelScraper object
my_scraper = ReelScraper(timeout=10, proxy=None)

# 2. Specify the file with usernames (one per line)
accounts_file_path = "my_accounts.txt"  # e.g., contains "cat_with_a_hat" on one line, "travel_dude" on another...

# 3. Initialize ReelMultiScraper
multi_scraper = ReelMultiScraper(
    accounts_file=accounts_file_path,
    scraper=my_scraper,
    max_workers=5
)

# 4. Scrape accounts in parallel
results = multi_scraper.scrape_accounts()

# 5. Check out the results
for username, reels_list in results.items():
    print(f"User: {username} | Reels Count: {len(reels_list)}")
```

**Sample Output:**
```
Done with account: cat_with_a_hat
Done with account: travel_dude
Error with account: definitely_not_real
User: cat_with_a_hat | Reels Count: 10
User: travel_dude | Reels Count: 8
```

---

## FAQs

1. **How many accounts can I load into `ReelMultiScraper`?**  
   - As many as you’d like! But be mindful of rate limits and performance. If you have thousands of accounts, you might want to break them into batches or schedule the scraping.

2. **Does `ReelScraper` handle Instagram rate limiting automatically?**  
   - Not inherently. You may need to add logic to pause or throttle requests if you’re hitting Instagram’s rate limits.

3. **What if my user has no reels or the account is private?**  
   - You’ll get either an empty list or an error. The `ReelMultiScraper` logs an error message for that account, while `ReelScraper` itself may throw an exception if it can’t fetch data.

4. **Can I change the number of threads on the fly?**  
   - You’d need to create a new `ReelMultiScraper` instance with a different `max_workers` value if you want to adjust concurrency.

5. **Does `ReelScraper` or `ReelMultiScraper` store data long-term?**  
   - No. They only return data. It’s up to you to store it (e.g., saving to a database or JSON file).

> **Random Gag**: If your CPU starts humming Beethoven’s 5th Symphony while multi-scraping, you probably have your threads turned up to 11. Time to give it a little break!

---

## Additional Tips

- **Handling Large Data**: If you plan on scraping thousands of reels, consider streaming the data or storing incrementally rather than loading everything into memory.
- **Polite Scraping**: Instagram may block or throttle your requests if you scrape too aggressively. Insert delays or exponential backoff if needed.
- **Logging**: For production use, integrate a proper logging framework instead of `print` statements to keep track of successes and failures more effectively.

---

## Happy Scraping!

Remember: “With great power comes great responsibility.” Or in this case:  
**With great concurrency comes cooler CPU fans.**

> **End Note**: If you find yourself frequently giggling while reading logs like, “Done with account: cat_with_a_hat,” just imagine your code giving a virtual high-five.  