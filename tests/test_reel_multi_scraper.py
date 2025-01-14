import os
import tempfile
import unittest
from typing import Dict, List

# Import della classe sotto test.
from reelscraper import ReelMultiScraper


# -----------------------------------------------------------------------------
# Dummy implementations per il testing:
# -----------------------------------------------------------------------------


class DummyReelScraper:
    """
    Un dummy di ReelScraper che simula risposte di successo e fallimenti.
    Il comportamento è determinato da una mappatura di username a una lista di dizionari (reels)
    oppure a una eccezione.
    """

    def __init__(
        self,
        results: Dict[str, List[Dict]],
        errors: Dict[str, Exception] = None,
        logger_manager=None,
    ):
        """
        :param results: Dizionario che mappa lo username a una lista di dizionari (reels).
        :param errors: Dizionario che mappa lo username a un'eccezione da lanciare.
        """
        self.results = results
        self.errors = errors if errors is not None else {}
        self.logger_manager = logger_manager

    def get_user_reels(
        self, username: str, max_posts: int = None, max_retries: int = 10
    ) -> List[Dict]:
        if username in self.errors:
            if self.logger_manager is not None:
                self.logger_manager.log_account_error(username)
            raise self.errors[username]
        return self.results.get(username, [])


class DummyLoggerManager:
    """
    DummyLoggerManager cattura le chiamate di log in una lista interna per scopi di testing.
    Implementa la stessa interfaccia di LoggerManager.
    """

    def __init__(self):
        self.calls = []  # Lista per registrare tutte le chiamate di log

    def log_account_error(self, account_name: str):
        """
        Registra una chiamata di log per un errore.
        :param account_name: Nome dell'account che ha generato l'errore.
        """
        self.calls.append(("error", account_name))

    def log_retry(self, retry: int, max_retries: int, account_name: str):
        """
        Registra una chiamata di log per un retry.
        :param retry: Numero del tentativo corrente.
        :param max_retries: Numero massimo di retry consentiti.
        :param account_name: Nome dell'account.
        """
        self.calls.append(("retry", retry, max_retries, account_name))

    def log_account_success(self, username: str, reel_count: int):
        """
        Registra una chiamata di log per il successo dello scraping.
        :param username: Nome dell'account.
        :param reel_count: Numero di reels processati.
        """
        self.calls.append(("success", username, reel_count))

    def log_account_begin(self, username: str):
        """
        Registra una chiamata di log per l'inizio dello scraping.
        :param username: Nome dell'account.
        """
        self.calls.append(("begin", username))

    def log_saving_scraping_results(self, reel_count, username):
        self.calls.append(("save_scraping_results", reel_count, username))

    def log_finish_multiscraping(self, total_reels: int, total_accounts: int):
        """
        Registra il completamento dello scraping in parallelo.
        """
        self.calls.append(("finish", total_reels, total_accounts))

    def log_reels_scraped(self, message_or_value):
        self.calls.append(("reels_scraped", message_or_value))


class DummyDBManager:
    """
    A mock DBManager that records when 'store_reels' is called.
    """

    def __init__(self):
        self.calls = []

    def store_reels(self, username, reels):
        self.calls.append(("store_reels", username, reels))


# -----------------------------------------------------------------------------
# Test Suite per ReelMultiScraper
# -----------------------------------------------------------------------------


class TestReelMultiScraper(unittest.TestCase):

    def setUp(self):
        # Create a temp file with some usernames
        self.temp_file = tempfile.NamedTemporaryFile("w+", delete=False)
        self.usernames = ["alice", "bob", "charlie"]
        self.temp_file.write("\n".join(self.usernames))
        self.temp_file.flush()
        self.temp_file.close()
        self.dummy_logger = DummyLoggerManager()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_scrape_accounts_all_successful(self):
        """
        Verifica che lo scraping di tutti gli account, eseguito in parallelo, restituisca
        i risultati attesi quando non si verificano errori, e che vengano registrati i log di successo.
        """
        # Prepara i risultati dummy per ogni account.
        dummy_results = {
            "alice": [{"reel": {"code": "a1"}}],
            "bob": [{"reel": {"code": "b1"}}, {"reel": {"code": "b2"}}],
            "charlie": [],  # Nessun reel per user3.
        }
        dummy_scraper = DummyReelScraper(
            results=dummy_results,
        )
        multi_scraper = ReelMultiScraper(
            scraper=dummy_scraper,
            max_workers=3,
        )

        # Esegue lo scraping (restituirà un'unica lista di reels).
        results = multi_scraper.scrape_accounts(
            max_posts_per_profile=10,
            accounts_file=self.temp_file.name,
        )

        # Ci aspettiamo un totale di 3 reels: 1 (user1) + 2 (user2) + 0 (user3).
        self.assertEqual(len(results), 3, "Dovrebbero esserci 3 reels totali.")

        # Verifichiamo anche i 'code' dei reel ottenuti.
        codes = sorted(r["reel"]["code"] for r in results)
        self.assertEqual(codes, ["a1", "b1", "b2"])

    def test_scrape_accounts_with_errors(self):
        """
        Verifica che quando alcuni account generano errori durante lo scraping, l'errore viene
        catturato, che i risultati includano solo gli account senza errori e che venga registrato un log di errore.
        """
        # Simula risultati normali per user1 e user3 mentre per user2 viene lanciata un'eccezione.
        dummy_results = {
            "alice": [{"reel": {"code": "a1"}}],
            "charlie": [{"reel": {"code": "c1"}}],
        }
        dummy_errors = {"bob": Exception("Scraping failed for user2")}
        dummy_scraper = DummyReelScraper(
            results=dummy_results, errors=dummy_errors, logger_manager=self.dummy_logger
        )
        multi_scraper = ReelMultiScraper(
            scraper=dummy_scraper,
            max_workers=3,
        )

        results = multi_scraper.scrape_accounts(
            max_posts_per_profile=10,
            accounts_file=self.temp_file.name,
        )

        # Dal momento che user2 genera un errore, ci aspettiamo che i risultati contengano solo quelli di user1 e user3.
        # Non conosciamo l'ordine nella lista, per cui verifichiamo i conteggi.
        reel_counts = sorted([len(r) for r in results])
        expected_counts = sorted(
            [len(dummy_results["alice"]), len(dummy_results["charlie"])]
        )
        self.assertEqual(reel_counts, expected_counts)

        # Verifica che sia stato registrato un errore per user2.
        self.assertIn(("error", "bob"), self.dummy_logger.calls)

    def test_scrape_accounts_parallel_execution(self):
        """
        Verifica che lo scraping in parallelo venga eseguito per ogni account presente nel file.
        In questo test lo scraper dummy ritorna una lista vuota per ogni account.
        """
        dummy_scraper = DummyReelScraper(
            results={acc: [] for acc in self.usernames},
        )
        multi_scraper = ReelMultiScraper(
            scraper=dummy_scraper,
            max_workers=2,
        )

        results = multi_scraper.scrape_accounts(
            max_posts_per_profile=10,
            accounts_file=self.temp_file.name,
        )

        # Tutti gli account restituiscono 0 reels, dunque la lista finale è vuota.
        self.assertEqual(
            len(results), 0, "Dovrebbe essere una lista vuota, nessun reel disponibile."
        )

    def log_saving_scraping_results(self, reel_count: int, username: str):
        """
        Called when saving scraping results (like: log_saving_scraping_results(len(reels), username)).
        """
        self.calls.append(("save_scraping_results", reel_count, username))

    def test_scrape_accounts_no_db_manager_returns_results(self):
        """
        If db_manager is None, we gather all reels into a local list and return them.
        """
        dummy_scraper = DummyReelScraper(
            results={
                "alice": [{"code": "A1"}, {"code": "A2"}],
                "bob": [{"code": "B1"}],
                "charlie": [],
            }
        )
        multi_scraper = ReelMultiScraper(
            scraper=dummy_scraper,
            max_workers=2,  # just to test concurrency
            db_manager=None,
        )
        results = multi_scraper.scrape_accounts(
            self.temp_file.name, max_posts_per_profile=5, max_retires_per_profile=3
        )
        # We expect to see 3 total reels from alice (2) and bob (1), none from charlie
        self.assertEqual(len(results), 3)
        codes = sorted(item["code"] for item in results)
        self.assertEqual(codes, ["A1", "A2", "B1"])

    def test_scrape_accounts_with_db_manager(self):
        """
        If db_manager is provided, we do not aggregate results locally;
        instead, we call db_manager.store_reels(...) for each account.
        """
        dummy_scraper = DummyReelScraper(
            results={
                "alice": [{"code": "A1"}, {"code": "A2"}],
                "bob": [{"code": "B1"}],
                "charlie": [],
            }
        )
        mock_db = DummyDBManager()

        multi_scraper = ReelMultiScraper(
            scraper=dummy_scraper, max_workers=3, db_manager=mock_db
        )
        returned = multi_scraper.scrape_accounts(
            accounts_file=self.temp_file.name,
            max_posts_per_profile=10,
            max_retires_per_profile=5,
        )

        # Because db_manager != None, returned results is likely empty
        self.assertIsNone(returned)

        # But store_reels should have been called exactly 3 times
        # (once per user) with the correct data
        self.assertEqual(len(mock_db.calls), 3)
        # Each call looks like ("store_reels", username, [list_of_reels])
        actual_usernames = [
            call[1] for call in mock_db.calls if call[0] == "store_reels"
        ]
        self.assertCountEqual(actual_usernames, ["alice", "bob", "charlie"])

    def test_scrape_accounts_exception_handling(self):
        """
        If one or more accounts raise an exception, we skip them and do not crash.
        """
        dummy_scraper = DummyReelScraper(
            results={"alice": [{"code": "A1"}], "charlie": [{"code": "C1"}]},
            errors={"bob": Exception("Scraping error for Bob")},
        )
        multi_scraper = ReelMultiScraper(
            scraper=dummy_scraper, max_workers=3, db_manager=None
        )
        results = multi_scraper.scrape_accounts(
            accounts_file=self.temp_file.name,
            max_posts_per_profile=10,
            max_retires_per_profile=10,
        )
        # bob raises exception -> only alice and charlie produce reels
        self.assertEqual(len(results), 2)
        codes = sorted(item["code"] for item in results)
        self.assertEqual(codes, ["A1", "C1"])

    def test_scrape_accounts_with_logger_and_db_manager(self):
        """
        Tests code path for both db_manager and a logger_manager attached to the scraper.
        Ensures 'log_saving_scraping_results' and 'log_finish_multiscraping' are called.
        """
        dummy_logger = DummyLoggerManager()
        dummy_scraper = DummyReelScraper(
            results={"alice": [{"code": "A1"}], "bob": [], "charlie": []},
            logger_manager=dummy_logger,
        )
        mock_db = DummyDBManager()
        multi_scraper = ReelMultiScraper(
            scraper=dummy_scraper, max_workers=3, db_manager=mock_db
        )

        returned = multi_scraper.scrape_accounts(
            self.temp_file.name, max_posts_per_profile=5, max_retires_per_profile=5
        )
        # Because db_manager is present, we expect no local results
        self.assertIsNone(returned)

        # Check that store_reels was called for all accounts
        self.assertEqual(len(mock_db.calls), 3)  # alice, bob, charlie

        # Now ensure the logger was called to log saving results for 'alice' (since reels were found there),
        # plus a final finish call
        # "bob" and "charlie" have 0 reels, but code calls log_saving_scraping_results(0, 'bob/charlie') anyway
        # if it goes down that path. Let's see:
        self.assertIn(("finish", 1, 3), dummy_logger.calls)
        # The 'reels_count' increments by 1 for each account's future, not by the total # of reels.

        # Check the "save_scraping_results" calls if any reels were found
        # By default code calls: log_saving_scraping_results(len(reels), username)
        # in that snippet, it's only called if 'db_manager is not None' and reels > 0
        # or it might be called even if reels=0. Let's see the code:
        #
        # if self.db_manager is not None:
        #     self.db_manager.store_reels(username, reels)
        #     if self.scraper.logger_manager is not None:
        #         self.scraper.logger_manager.log_saving_scraping_results(len(reels), username)
        #
        # So it's always called, even if reels=0. So we should see 3 calls:
        self.assertIn(("save_scraping_results", 1, "alice"), dummy_logger.calls)
        self.assertIn(("save_scraping_results", 0, "bob"), dummy_logger.calls)
        self.assertIn(("save_scraping_results", 0, "charlie"), dummy_logger.calls)

    def test_scrape_with_nondefault_max_posts_and_retries(self):
        """
        Simply ensures coverage for the lines passing max_posts_per_profile and max_retires_per_profile
        to get_user_reels. We'll assert that our dummy scraper can see them (via an override).
        """

        class CheckingReelScraper(DummyReelScraper):
            def get_user_reels(
                self, username: str, max_posts: int = None, max_retries: int = 10
            ) -> List[Dict]:
                # Just store what we got in a dict for verification
                if not hasattr(self, "calls"):
                    self.calls = []
                self.calls.append((username, max_posts, max_retries))
                return super().get_user_reels(username, max_posts, max_retries)

        checking_scraper = CheckingReelScraper(
            results={
                "alice": [{"code": "A1"}],
                "bob": [{"code": "B1"}],
                "charlie": [{"code": "C1"}],
            }
        )
        multi_scraper = ReelMultiScraper(
            scraper=checking_scraper, max_workers=2, db_manager=None
        )
        multi_scraper.scrape_accounts(
            accounts_file=self.temp_file.name,
            max_posts_per_profile=99,
            max_retires_per_profile=77,
        )

        # The dummy captured the calls:
        self.assertEqual(len(checking_scraper.calls), 3)  # 3 accounts
        for username, mp, mr in checking_scraper.calls:
            self.assertIn(username, self.usernames)
            self.assertEqual(mp, 99)
            self.assertEqual(mr, 77)


if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
