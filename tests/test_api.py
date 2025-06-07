import unittest
import requests

BASE_URL = "http://localhost:5001"

class ApiTestCase(unittest.TestCase):

    def test_get_clubs(self):
        response = requests.get(f"{BASE_URL}/api/clubs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_contacts(self):
        response = requests.get(f"{BASE_URL}/api/contacts")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_events(self):
        response = requests.get(f"{BASE_URL}/api/events")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_faqs(self):
        response = requests.get(f"{BASE_URL}/api/faqs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_instructions(self):
        response = requests.get(f"{BASE_URL}/api/instructions")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

if __name__ == '__main__':
    unittest.main()
