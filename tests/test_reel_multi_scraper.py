import os
import tempfile
import unittest
from typing import Dict, List

# Import della classe sotto test.
from reelscraper import ReelMultiScraper


# -----------------------------------------------------------------------------
# Dummy implementations per il testing:
# -----------------------------------------------------------------------------
class DummyDataSaver:
    def __init__(self, full_path):
        self.full_path = full_path
        self.saved_results = None

    def save(self, results):
        self.saved_results = results


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

    def log_saving_scraping_results(self, full_path: str):
        """
        Registra il salvataggio dei risultati di scraping.
        """
        self.calls.append(("save", full_path))

    def log_finish_multiscraping(self, total_reels: int, total_accounts: int):
        """
        Registra il completamento dello scraping in parallelo.
        """
        self.calls.append(("finish", total_reels, total_accounts))

    def log_reels_scraped(self, message_or_value):
        self.calls.append(("reels_scraped", message_or_value))


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
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            max_workers=3,
        )

        # Esegue lo scraping (restituirà un'unica lista di reels).
        results = multi_scraper.scrape_accounts(
            max_posts_per_profile=10,
            accounts_file=self.temp_accounts_file.name,
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
            "user1": [{"reel": {"code": "a1"}}],
            "user3": [{"reel": {"code": "c1"}}],
        }
        dummy_errors = {"user2": Exception("Scraping failed for user2")}
        dummy_scraper = DummyReelScraper(results=dummy_results, errors=dummy_errors)
        multi_scraper = ReelMultiScraper(
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            max_workers=3,
        )

        results = multi_scraper.scrape_accounts(
            max_posts_per_profile=10,
            accounts_file=self.temp_accounts_file.name,
        )

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
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            max_workers=2,
        )

        results = multi_scraper.scrape_accounts(
            max_posts_per_profile=10,
            accounts_file=self.temp_accounts_file.name,
        )

        # Tutti gli account restituiscono 0 reels, dunque la lista finale è vuota.
        self.assertEqual(
            len(results), 0, "Dovrebbe essere una lista vuota, nessun reel disponibile."
        )

    def test_scrape_accounts_with_data_saver(self):
        """
        Verifica che, se viene passato un data_saver, vengano salvati i risultati e che
        venga registrato il log del salvataggio.
        """
        # Prepara alcuni risultati dummy per ogni account.
        dummy_results = {
            "user1": [{"reel": {"code": "a1"}}],
            "user2": [{"reel": {"code": "b1"}}, {"reel": {"code": "b2"}}],
            "user3": [{"reel": {"code": "c1"}}],
        }
        dummy_scraper = DummyReelScraper(results=dummy_results)
        # Crea un dummy data saver con un percorso fittizio.
        dummy_data_saver = DummyDataSaver(full_path="/fake/path/results.json")

        # Crea l'istanza del multi-scraper passando sia il logger che il data saver.
        # Assumiamo che ReelMultiScraper accetti un parametro 'data_saver'.
        multi_scraper = ReelMultiScraper(
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            data_saver=dummy_data_saver,
            max_workers=3,
        )

        # Eseguire lo scraping.
        results = multi_scraper.scrape_accounts(
            max_posts_per_profile=10,
            accounts_file=self.temp_accounts_file.name,
        )

        # Verifica che il data saver abbia salvato i risultati ottenuti.
        self.assertEqual(
            dummy_data_saver.saved_results,
            results,
            "I risultati dello scraping dovrebbero essere salvati tramite data_saver.save.",
        )

        # Verifica che il logger abbia registrato il salvataggio usando il percorso completo del data saver.
        self.assertIn(
            ("save", dummy_data_saver.full_path),
            self.dummy_logger.calls,
            "Il logger dovrebbe registrare l'azione di salvataggio con il percorso completo.",
        )


if __name__ == "__main__":
    unittest.main()
