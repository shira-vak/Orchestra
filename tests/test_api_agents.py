import httpx

from tests.consts import EXPECTED_AGENT_NAMES


async def test_list_agents_returns_all_four_seeded_agents(client: httpx.AsyncClient) -> None:
    response = await client.get("/agents")

    assert response.status_code == 200
    names = {agent["name"] for agent in response.json()}
    assert names == EXPECTED_AGENT_NAMES
