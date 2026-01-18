"""Mock source adapter for testing."""

import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from src.schemas.lead import CompanySize, LeadSource
from src.services.sources.base import (
    AdapterResult,
    BaseSourceAdapter,
    RateLimitStatus,
    RawLead,
    SearchQuery,
    SourceStatus,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Mock data generators
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
]

COMPANIES = [
    "TechCorp", "InnovateLabs", "DataDrive", "CloudNine", "ByteWorks", "CodeStream",
    "PixelPerfect", "AgileMinds", "DevOps Pro", "SaaS Solutions", "StartupHub",
    "GrowthEngine", "ScaleUp Inc", "Venture Labs", "Digital Dynamics", "FutureTech",
]

INDUSTRIES = [
    "software", "technology", "finance", "healthcare", "retail", "marketing",
    "consulting", "manufacturing", "real estate", "education",
]

HIGH_INTENT_TITLES = [
    "Looking for {service} developer for urgent project",
    "Hiring: {service} expert needed ASAP",
    "Budget: ${budget}k - Need {service} specialist",
    "Seeking experienced {service} team",
    "{service} project - Ready to start immediately",
]

MEDIUM_INTENT_TITLES = [
    "Interested in {service} services",
    "Exploring options for {service} development",
    "Considering {service} implementation",
    "Looking for {service} recommendations",
]

LOW_INTENT_TITLES = [
    "Learning about {service} - any resources?",
    "Student project: {service} help needed",
    "Free {service} advice wanted",
    "Hobby project using {service}",
]


class MockSourceAdapter(BaseSourceAdapter):
    """
    Mock adapter for testing without external API calls.

    Generates realistic-looking lead data with configurable
    parameters for response time and data quality.
    """

    def __init__(
        self,
        source: LeadSource = LeadSource.MANUAL,
        config: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize mock adapter.

        Args:
            source: Source type to simulate.
            config: Configuration options:
                - min_delay_ms: Minimum response delay (default 100)
                - max_delay_ms: Maximum response delay (default 500)
                - success_rate: Probability of success (default 0.95)
                - min_leads: Minimum leads to return (default 5)
                - max_leads: Maximum leads to return (default 20)
                - high_intent_ratio: Ratio of high-intent leads (default 0.3)
        """
        super().__init__(config)
        self._source = source
        self._remaining_requests = 100
        self._request_count = 0

    @property
    def source_type(self) -> LeadSource:
        """Get source type."""
        return self._source

    @property
    def name(self) -> str:
        """Get adapter name."""
        return f"Mock{self._source.value.title()}Adapter"

    async def search(self, query: SearchQuery) -> AdapterResult:
        """
        Execute mock search.

        Args:
            query: Search parameters.

        Returns:
            AdapterResult with generated mock leads.
        """
        start_time = datetime.now(timezone.utc)
        self._request_count += 1

        # Simulate network delay
        min_delay = self.config.get("min_delay_ms", 100)
        max_delay = self.config.get("max_delay_ms", 500)
        delay_ms = random.randint(min_delay, max_delay)
        await asyncio.sleep(delay_ms / 1000)

        # Simulate occasional failures
        success_rate = self.config.get("success_rate", 0.95)
        if random.random() > success_rate:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return AdapterResult(
                source=self._source,
                status=SourceStatus.FAILED,
                error_message="Simulated API failure",
                execution_time_ms=execution_time,
            )

        # Generate leads
        min_leads = self.config.get("min_leads", 5)
        max_leads = min(self.config.get("max_leads", 20), query.max_results)
        num_leads = random.randint(min_leads, max_leads)

        leads = []
        high_intent_ratio = self.config.get("high_intent_ratio", 0.3)

        for i in range(num_leads):
            lead = self._generate_mock_lead(query, i < num_leads * high_intent_ratio)
            leads.append(lead)

        self._remaining_requests -= 1
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        logger.info(
            "mock_search_completed",
            source=self._source.value,
            leads_found=len(leads),
            execution_time_ms=execution_time,
        )

        return AdapterResult(
            source=self._source,
            status=SourceStatus.SUCCESS,
            leads=leads,
            execution_time_ms=execution_time,
            rate_limit_status=self.get_rate_limit_status(),
        )

    async def check_availability(self) -> bool:
        """Check if mock source is available."""
        return self._is_available and self._remaining_requests > 0

    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get rate limit status."""
        return RateLimitStatus(
            remaining_requests=max(0, self._remaining_requests),
            reset_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_limited=self._remaining_requests <= 0,
        )

    def _generate_mock_lead(self, query: SearchQuery, high_intent: bool) -> RawLead:
        """
        Generate a realistic mock lead.

        Args:
            query: Search query for context.
            high_intent: Whether to generate high-intent signals.

        Returns:
            RawLead with mock data.
        """
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        company = random.choice(COMPANIES)
        industry = random.choice(INDUSTRIES)

        # Generate email with some missing to simulate incomplete data
        email = None
        if random.random() > 0.2:  # 80% have email
            domain = company.lower().replace(" ", "") + ".com"
            email = f"{first_name.lower()}.{last_name.lower()}@{domain}"

        # Generate phone with some missing
        phone = None
        if random.random() > 0.4:  # 60% have phone
            phone = f"+1{random.randint(200, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"

        # Company size
        sizes = [
            (CompanySize.SOLO, 0.1),
            (CompanySize.SMALL, 0.3),
            (CompanySize.MEDIUM, 0.35),
            (CompanySize.ENTERPRISE, 0.15),
            (CompanySize.UNKNOWN, 0.1),
        ]
        company_size = random.choices(
            [s[0] for s in sizes],
            weights=[s[1] for s in sizes],
        )[0]

        # Generate title based on intent level
        service = query.keywords[0] if query.keywords else "software"
        budget = random.randint(5, 50)

        if high_intent:
            if random.random() > 0.5:
                title = random.choice(HIGH_INTENT_TITLES).format(service=service, budget=budget)
            else:
                title = random.choice(MEDIUM_INTENT_TITLES).format(service=service)
        else:
            if random.random() > 0.7:
                title = random.choice(MEDIUM_INTENT_TITLES).format(service=service)
            else:
                title = random.choice(LOW_INTENT_TITLES).format(service=service)

        # Generate description
        description = f"We are looking for expertise in {service}. "
        if high_intent:
            description += f"Our budget is approximately ${budget * 1000}. "
            description += "We need to start as soon as possible. "
        description += f"Industry: {industry}. Company size: {company_size.value}."

        # Budget amount (only for high intent)
        budget_amount = None
        if high_intent and random.random() > 0.3:
            budget_amount = float(budget * 1000)

        # Random creation time within last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        created_at = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)

        return RawLead(
            name=f"{first_name} {last_name}",
            company=company,
            source=self._source,
            source_url=f"https://{self._source.value}.example.com/post/{random.randint(10000, 99999)}",
            email=email,
            phone=phone,
            company_size=company_size,
            industry=industry,
            budget=budget_amount,
            created_at=created_at,
            title=title,
            description=description,
            raw_data={
                "mock_id": random.randint(100000, 999999),
                "high_intent": high_intent,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def reset_rate_limit(self) -> None:
        """Reset rate limit for testing."""
        self._remaining_requests = 100
        self._request_count = 0
