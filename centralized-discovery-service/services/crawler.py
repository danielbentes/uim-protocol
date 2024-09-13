# services/crawler.py

import aiohttp
import asyncio
import dns.resolver
from app.services.dns_utils import get_agents_json_url_from_dns
from app.schemas import AgentsJson
from app.database import SessionLocal
from app.crud import create_service, create_intent
from app.dependencies import get_db

async def fetch_agents_json(session, url):
    """Fetch agents.json from the given URL."""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
    return None

async def process_domain(domain):
    """Process a single domain to fetch agents.json."""
    agents_json_url = get_agents_json_url_from_dns(domain)
    if not agents_json_url:
        agents_json_url = f"https://{domain}/agents.json"
    async with aiohttp.ClientSession() as session:
        data = await fetch_agents_json(session, agents_json_url)
        if data:
            await save_agents_json(data)

async def save_agents_json(data):
    """Save agents.json data to the database."""
    agents_data = AgentsJson.parse_obj(data)
    db = SessionLocal()
    service = create_service(db, agents_data.service_info)
    for intent in agents_data.intents:
        create_intent(db, intent, service.id)
    db.close()

async def start_crawling():
    """Start the crawling process."""
    domains_to_crawl = ["example.com", "fakerealestate.com"]  # This should be dynamically discovered
    tasks = [process_domain(domain) for domain in domains_to_crawl]
    await asyncio.gather(*tasks)