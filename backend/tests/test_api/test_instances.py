"""Integration tests for instances API."""
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import status

from main import app
from models.database import get_db


@pytest.mark.integration
@pytest.mark.asyncio
class TestInstancesAPI:
    """Test suite for /api/instances endpoints."""

    async def test_create_instance(self, db_session):
        """Test creating a new instance."""
        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/instances/",
                json={
                    "name": "Test Instance",
                    "url": "https://test.magento.com",
                    "api_token": "test_token_123",
                    "is_active": True
                }
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Instance"
        assert data["url"] == "https://test.magento.com/"
        assert data["is_active"] is True
        assert "id" in data

        app.dependency_overrides.clear()

    async def test_create_instance_invalid_url(self, db_session):
        """Test creating instance with invalid URL fails."""
        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/instances/",
                json={
                    "name": "Test Instance",
                    "url": "not-a-url",
                    "api_token": "test_token_123"
                }
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        app.dependency_overrides.clear()

    async def test_get_instances(self, db_session, sample_instance):
        """Test getting all instances."""
        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/instances/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(instance["name"] == "Test Instance" for instance in data)

        app.dependency_overrides.clear()

    async def test_get_instance_by_id(self, db_session, sample_instance):
        """Test getting a specific instance."""
        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/instances/{sample_instance.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_instance.id
        assert data["name"] == sample_instance.name

        app.dependency_overrides.clear()

    async def test_update_instance(self, db_session, sample_instance):
        """Test updating an instance."""
        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/api/instances/{sample_instance.id}",
                json={"name": "Updated Name"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"

        app.dependency_overrides.clear()

    async def test_delete_instance(self, db_session, sample_instance):
        """Test deleting an instance."""
        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        instance_id = sample_instance.id

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Delete
            response = await client.delete(f"/api/instances/{instance_id}")
            assert response.status_code == status.HTTP_204_NO_CONTENT

            # Verify deleted
            response = await client.get(f"/api/instances/{instance_id}")
            assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()
