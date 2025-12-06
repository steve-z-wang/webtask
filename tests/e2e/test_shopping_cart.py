"""E2E test for shopping cart automation."""

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_shopping_cart(agent):
    """Test adding items to cart and verifying total."""
    await agent.goto("https://practicesoftwaretesting.com/")
    await agent.wait(3)

    await agent.do("add 2 Flat-Head Wood Screws to the cart")

    verdict = await agent.verify("the cart contains 2 items")
    assert verdict.passed, f"Verification failed: {verdict.feedback}"
