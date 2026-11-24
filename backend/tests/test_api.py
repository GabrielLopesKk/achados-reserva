import io
import os
import sqlite3
import tempfile
import unittest
from datetime import date

from PIL import Image

from app import create_app

TOKEN = "teste-recepcao"


def make_photo(color=(10, 10, 10)):
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buf, "JPEG")
    buf.seek(0)
    return buf


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True, "STAFF_TOKEN": TOKEN, "ANTHROPIC_API_KEY": "",
            "DATABASE": os.path.join(self.tmp.name, "t.sqlite"),
            "UPLOAD_DIR": os.path.join(self.tmp.name, "up"),
        })
        os.makedirs(self.app.config["UPLOAD_DIR"], exist_ok=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def post_item(self, **over):
        data = {"item_type": "jaqueta", "color": "preto", "location": "Pátio",
                "found_date": date.today().isoformat(), "marks": "adesivo de gato",
                "description": "Jaqueta preta com capuz", "photo": (make_photo(), "a.jpg")}
        data.update(over)
        return self.client.post("/api/items", data=data, content_type="multipart/form-data")

    def staff(self):
        return {"X-Staff-Token": TOKEN}


class ItemFlowTests(ApiTestCase):
    def test_ai_describe_local_fallback_needs_review(self):
        r = self.client.post("/api/ai/describe", data={"photo": (make_photo((200, 30, 40)), "a.jpg")},
                             content_type="multipart/form-data")
        body = r.get_json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(body["source"], "local")
        self.assertEqual(body["color"], "vermelho")
        self.assertTrue(body["needs_review"])

    def test_rejects_non_image(self):
        r = self.client.post("/api/ai/describe", data={"photo": (io.BytesIO(b"nao"), "a.jpg")},
                             content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)

    def test_create_and_search_filters(self):
        self.assertEqual(self.post_item().status_code, 201)
        self.post_item(item_type="garrafa", color="azul", location="Cantina",
                       description="Garrafa azul amassada", marks="")
        total = self.client.get("/api/items").get_json()["items"]
        self.assertEqual(len(total), 2)
        by_type = self.client.get("/api/items?type=garrafa").get_json()["items"]
        self.assertEqual([i["item_type"] for i in by_type], ["garrafa"])
        by_text = self.client.get("/api/items?q=CAPUZ").get_json()["items"]
        self.assertEqual(len(by_text), 1)
        by_accent = self.client.get("/api/items?q=patio").get_json()["items"]
        self.assertEqual(by_accent, [])  # q busca descrição/marcas/tipo, não o local

    def test_future_date_rejected(self):
        self.assertEqual(self.post_item(found_date="2999-01-01").status_code, 400)

    def test_sensitive_photo_hidden_from_public(self):
        item = self.post_item(item_type="cartão", description="Carteirinha").get_json()
        self.assertIsNone(item["photo_url"])
        self.assertTrue(item["sensitive"])
        stored = self.app.test_client().get("/api/staff/items", headers=self.staff()).get_json()
        url = stored["items"][0]["photo_url"]
        self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.client.get(url, headers=self.staff()).status_code, 200)

    def test_public_photo_served(self):
        item = self.post_item().get_json()
        self.assertEqual(self.client.get(item["photo_url"]).status_code, 200)

    def test_old_items_expire_from_search(self):
        item = self.post_item().get_json()
        conn = sqlite3.connect(self.app.config["DATABASE"])
        conn.execute("UPDATE items SET created_at='2000-01-01T00:00:00+00:00' WHERE id=?", (item["id"],))
        conn.commit()
        conn.close()
        self.assertEqual(self.client.get("/api/items").get_json()["items"], [])


class ClaimAndReturnTests(ApiTestCase):
    def claim(self, item_id):
        return self.client.post(f"/api/items/{item_id}/claims", json={
            "name": "Ana Souza", "contact": "ana@mail.com", "message": "É minha, tem adesivo."})

    def test_full_flow_without_leaking_contact(self):
        item = self.post_item().get_json()
        r = self.claim(item["id"])
        self.assertEqual(r.status_code, 201)
        code = r.get_json()["pickup_code"]
        public = self.client.get("/api/items").get_json()
        self.assertNotIn("ana@mail.com", str(public))
        self.assertEqual(public["items"][0]["status"], "awaiting_pickup")

        claims = self.client.get(f"/api/staff/items/{item['id']}/claims", headers=self.staff())
        self.assertEqual(claims.get_json()["claims"][0]["contact_masked"], "a***@mail.com")

        bad = self.client.patch(f"/api/items/{item['id']}/status", headers=self.staff(),
                                json={"status": "returned", "code": "000000"})
        self.assertEqual(bad.status_code, 403)
        ok = self.client.patch(f"/api/items/{item['id']}/status", headers=self.staff(),
                               json={"status": "returned", "code": code})
        self.assertEqual(ok.get_json()["status"], "returned")
        self.assertEqual(self.client.get("/api/items").get_json()["items"], [])
        self.assertEqual(self.claim(item["id"]).status_code, 409)

    def test_status_requires_staff_token(self):
        item = self.post_item().get_json()
        r = self.client.patch(f"/api/items/{item['id']}/status", json={"status": "found"})
        self.assertEqual(r.status_code, 401)
        r = self.client.patch(f"/api/items/{item['id']}/status", headers=self.staff(),
                              json={"status": "found"})
        self.assertEqual(r.status_code, 200)

    def test_staff_disabled_without_token(self):
        self.app.config["STAFF_TOKEN"] = ""
        self.assertEqual(self.client.get("/api/staff/items").status_code, 503)


class ReportTests(ApiTestCase):
    def report(self, **over):
        body = {"description": "jaqueta preta com capuz", "item_type": "jaqueta", "color": "preto",
                "location": "Pátio", "lost_date": date.today().isoformat(), "contact": "bia@mail.com"}
        body.update(over)
        return self.client.post("/api/reports", json=body)

    def test_matches_require_token_and_return_candidates(self):
        self.post_item()
        created = self.report().get_json()
        url = f"/api/reports/{created['id']}/matches"
        self.assertEqual(self.client.get(url).status_code, 404)
        r = self.client.get(url, headers={"X-Report-Token": created["token"]})
        data = r.get_json()
        self.assertEqual(len(data["candidates"]), 1)
        self.assertNotIn("bia@mail.com", str(data))
        self.assertIn("confirme", data["note"])

    def test_invalid_report(self):
        self.assertEqual(self.report(description="x").status_code, 400)


class StaticTests(ApiTestCase):
    def test_meta_and_index(self):
        self.assertIn("jaqueta", self.client.get("/api/meta").get_json()["types"])
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/package.json").status_code, 404)


if __name__ == "__main__":
    unittest.main()
