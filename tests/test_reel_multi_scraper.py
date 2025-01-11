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
        self, results: Dict[str, List[Dict]], errors: Dict[str, Exception] = None
    ):
        """
        :param results: Dizionario che mappa lo username a una lista di dizionari (reels).
        :param errors: Dizionario che mappa lo username a un'eccezione da lanciare.
        """
        self.results = results
        self.errors = errors if errors is not None else {}

    def get_user_reels(
        self, username: str, max_posts: int = None, max_retries: int = 10
    ) -> List[Dict]:
        # Se per lo username è prevista un'eccezione, la lancia.
        if username in self.errors:
            raise self.errors[username]
        # Se non è specificato niente viene ritornata la lista (vuota se non presente).
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


# -----------------------------------------------------------------------------
# Test Suite per ReelMultiScraper
# -----------------------------------------------------------------------------


class TestReelMultiScraper(unittest.TestCase):

    def setUp(self):
        # Crea un file temporaneo contenente una lista di username.
        self.temp_accounts_file = tempfile.NamedTemporaryFile("w+", delete=False)
        self.accounts = ["user1", "user2", "user3"]
        self.temp_accounts_file.write("\n".join(self.accounts))
        self.temp_accounts_file.flush()
        self.temp_accounts_file.close()
        # Crea un'istanza del dummy logger.
        self.dummy_logger = DummyLoggerManager()

    def tearDown(self):
        # Rimuove il file temporaneo degli account.
        os.unlink(self.temp_accounts_file.name)

    def test_scrape_accounts_all_successful(self):
        """
        Verifica che lo scraping di tutti gli account, eseguito in parallelo, restituisca
        i risultati attesi quando non si verificano errori, e che vengano registrati i log di successo.
        """
        # Prepara i risultati dummy per ogni account.
        dummy_results = {
            "user1": [{"reel": {"code": "a1"}}],
            "user2": [{"reel": {"code": "b1"}}, {"reel": {"code": "b2"}}],
            "user3": [],  # Nessun reel per user3.
        }
        dummy_scraper = DummyReelScraper(results=dummy_results)
        multi_scraper = ReelMultiScraper(
            accounts_file=self.temp_accounts_file.name,
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            max_workers=3,
        )

        # Esegue lo scraping.
        results = multi_scraper.scrape_accounts(max_posts=10)

        # Poiché il risultato è una lista (l'ordine non è garantito), verifichiamo:
        # - Il numero totale di successi (dei log) deve essere uguale al numero di account.
        success_logs = [
            call for call in self.dummy_logger.calls if call[0] == "success"
        ]
        self.assertEqual(len(success_logs), len(self.accounts))

        # Controlla che, per ogni risultato, il numero di reels corrisponda a quanto atteso.
        # Poiché non abbiamo la mapping username → risultato, verifichiamo solo i conteggi.
        reel_counts = sorted([len(r) for r in results])
        expected_counts = sorted(
            [len(dummy_results[username]) for username in self.accounts]
        )
        self.assertEqual(reel_counts, expected_counts)

    def test_scrape_accounts_with_errors(self):
        """
        Verifica che quando alcuni account generano errori durante lo scraping, l'errore viene
        catturato, che i risultati includano solo gli account senza errori e che venga registrato un log di errore.
        """
        # Simula risultati normali per user1 e user3 mentre per user2 viene lanciata un'eccezione.
        dummy_results = {
            "user1": [{"reel": {"code": "a1"}}],
            "user3": [{"reel": {"code": "c1"}}],
        }
        dummy_errors = {"user2": Exception("Scraping failed for user2")}
        dummy_scraper = DummyReelScraper(results=dummy_results, errors=dummy_errors)
        multi_scraper = ReelMultiScraper(
            accounts_file=self.temp_accounts_file.name,
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            max_workers=3,
        )

        results = multi_scraper.scrape_accounts(max_posts=10)

        # Dal momento che user2 genera un errore, ci aspettiamo che i risultati contengano solo quelli di user1 e user3.
        # Non conosciamo l'ordine nella lista, per cui verifichiamo i conteggi.
        reel_counts = sorted([len(r) for r in results])
        expected_counts = sorted(
            [len(dummy_results["user1"]), len(dummy_results["user3"])]
        )
        self.assertEqual(reel_counts, expected_counts)

        # Verifica che sia stato registrato un errore per user2.
        self.assertIn(("error", "user2"), self.dummy_logger.calls)

    def test_scrape_accounts_parallel_execution(self):
        """
        Verifica che lo scraping in parallelo venga eseguito per ogni account presente nel file.
        In questo test lo scraper dummy ritorna una lista vuota per ogni account.
        """
        dummy_scraper = DummyReelScraper(results={acc: [] for acc in self.accounts})
        multi_scraper = ReelMultiScraper(
            accounts_file=self.temp_accounts_file.name,
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            max_workers=2,
        )

        results = multi_scraper.scrape_accounts(max_posts=10)

        # Controlla che il numero di risultati ottenuti corrisponda al numero di account.
        self.assertEqual(len(results), len(self.accounts))
        # Verifica che ogni risultato sia una lista vuota.
        for reels in results:
            self.assertEqual(reels, [])
        # Verifica che per ogni account sia stato registrato un log di successo.
        success_logs = [
            call for call in self.dummy_logger.calls if call[0] == "success"
        ]
        self.assertEqual(len(success_logs), len(self.accounts))


if __name__ == "__main__":
    unittest.main()
