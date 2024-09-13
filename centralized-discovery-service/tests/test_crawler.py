# tests/test_crawler.py

import unittest
from app.services.crawler import fetch_agents_json
import asyncio

class TestCrawler(unittest.TestCase):
    """Test cases for the crawler."""

    def setUp(self):
        """Set up test variables."""
        self.loop = asyncio.get_event_loop()

    def test_fetch_agents_json(self):
        """Test fetching agents.json."""
        async def test():
            url = "https://fakerealestate.com/agents.json"
            async with aiohttp.ClientSession() as session:
                data = await fetch_agents_json(session, url)
                self.assertIsNotNone(data)
        self.loop.run_until_complete(test())

# Additional test methods...