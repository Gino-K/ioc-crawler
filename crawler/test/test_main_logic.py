import unittest
import datetime
from crawler.main import filter_links_by_timestamp


class TestLinkFiltering(unittest.TestCase):

    def setUp(self):
        """Bereitet Daten vor, die für mehrere Tests nützlich sind."""
        self.now = datetime.datetime.now(datetime.timezone.utc)
        self.all_links = [
            "https://site.com/new_article",
            "https://site.com/recent_article",
            "https://site.com/old_article"
        ]

    def test_new_link_is_always_processed(self):
        """Testet, ob ein Link, der nicht in der DB ist, immer verarbeitet wird."""
        print("\n[Filter-Test] Szenario 1: Neuer Link")
        existing_map = {
            "https://site.com/some_other_article": self.now
        }

        result = filter_links_by_timestamp(["https://site.com/new_one"], existing_map)

        self.assertEqual(len(result), 1)
        self.assertIn("https://site.com/new_one", result)

    def test_recent_link_is_skipped(self):
        """Testet, ob ein Link, der erst vor Kurzem gesehen wurde, übersprungen wird."""
        print("\n[Filter-Test] Szenario 2: Kürzlich gesehener Link")
        recent_time = self.now - datetime.timedelta(days=2)
        existing_map = {
            "https://site.com/recent_article": recent_time
        }

        result = filter_links_by_timestamp(["https://site.com/recent_article"], existing_map, days_to_rescan=5)

        self.assertEqual(len(result), 0)

    def test_old_link_is_reprocessed(self):
        """Testet, ob ein alter Link (älter als der Schwellenwert) erneut verarbeitet wird."""
        print("\n[Filter-Test] Szenario 3: Alter Link")
        old_time = self.now - datetime.timedelta(days=10)
        existing_map = {
            "https://site.com/old_article": old_time
        }

        result = filter_links_by_timestamp(["https://site.com/old_article"], existing_map, days_to_rescan=5)

        self.assertEqual(len(result), 1)
        self.assertIn("https://site.com/old_article", result)

    def test_mixed_links_are_filtered_correctly(self):
        """Testet eine gemischte Liste aus neuen, alten und kürzlichen Links."""
        print("\n[Filter-Test] Szenario 4: Gemischte Liste")

        recent_time = self.now - datetime.timedelta(days=2)
        old_time = self.now - datetime.timedelta(days=10)

        existing_map = {
            "https://site.com/recent_article": recent_time,
            "https://site.com/old_article": old_time
        }

        # self.all_links ist ["/new_article", "/recent_article", "/old_article"]
        result = filter_links_by_timestamp(self.all_links, existing_map, days_to_rescan=5)

        expected_to_process = [
            "https://site.com/new_article",
            "https://site.com/old_article"
        ]

        self.assertEqual(len(result), 2)
        self.assertCountEqual(result,
                              expected_to_process)


if __name__ == '__main__':
    unittest.main()