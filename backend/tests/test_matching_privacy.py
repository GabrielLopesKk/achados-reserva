import unittest

from app import matching, privacy


class MatchingTests(unittest.TestCase):
    item = {"item_type": "jaqueta", "color": "preto", "location": "Pátio",
            "description": "Jaqueta preta com capuz", "marks": "adesivo de gato",
            "found_date": "2026-11-20"}

    def test_strong_match(self):
        report = {"item_type": "jaqueta", "color": "preto", "location": "Pátio",
                  "description": "jaqueta preta com capuz", "lost_date": "2026-11-19"}
        s, reasons = matching.score(report, self.item)
        self.assertGreaterEqual(s, 0.8)
        self.assertIn("mesmo tipo", reasons)

    def test_weak_match_is_filtered(self):
        report = {"item_type": "garrafa", "color": "azul", "location": "Cantina",
                  "description": "garrafa azul", "lost_date": "2026-11-19"}
        self.assertEqual(matching.rank(report, [self.item]), [])

    def test_item_found_before_loss_is_penalised(self):
        report = {"item_type": "jaqueta", "color": "preto", "location": "Pátio",
                  "description": "jaqueta", "lost_date": "2026-11-22"}
        s, _ = matching.score(report, self.item)
        self.assertLess(s, 0.8)

    def test_accent_insensitive(self):
        self.assertEqual(matching.normalize("Cartão Ôculos"), "cartao oculos")


class PrivacyTests(unittest.TestCase):
    def test_mask_email_and_phone(self):
        self.assertEqual(privacy.mask_contact("ana@mail.com"), "a***@mail.com")
        self.assertEqual(privacy.mask_contact("(51) 99999-1234"), "••••-1234")

    def test_secret_roundtrip(self):
        code = privacy.new_secret()
        self.assertTrue(privacy.same_secret(code.lower(), privacy.hash_secret(code)))
        self.assertFalse(privacy.same_secret("ZZZZZZ", privacy.hash_secret(code)))


if __name__ == "__main__":
    unittest.main()
