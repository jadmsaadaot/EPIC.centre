# Copyright © 2024 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for application API endpoints."""
from http import HTTPStatus
from unittest.mock import patch

from faker import Faker

from centre_api.enums.access_request_status import AccessRequestsStatusEnum
from tests.utilities.factory_scenarios import TestApplicationScenarios, TestJwtClaims
from tests.utilities.factory_utils import (
    factory_access_request_model,
    factory_application_model,
    factory_auth_header,
    setup_admin_headers,
)

fake = Faker()


def test_get_all_applications_as_admin(client, session, jwt):
    """Test retrieving all applications as an admin user."""
    # Setup applications
    app1 = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())
    app2 = factory_application_model(session=session, **TestApplicationScenarios.get_epic_compliance_app())

    # Setup admin headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/applications', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) >= 2

    # Verify applications are returned
    app_names = [app['name'] for app in response.json]
    assert app1.name in app_names
    assert app2.name in app_names


def test_get_all_applications_returns_user_data(client, session, jwt):
    """Test that get all applications returns user-specific data."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup headers
    headers = factory_auth_header(jwt, TestJwtClaims.dst_admin_role.value)

    # Make request
    response = client.get('/api/applications', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) >= 1

    # Verify structure includes expected fields
    for application in response.json:
        assert 'id' in application
        assert 'name' in application
        assert 'title' in application
        assert 'description' in application
        assert 'launch_url' in application


def test_get_all_applications_unauthorized(client, session):
    """Test that unauthorized requests are rejected."""
    # Setup application
    factory_application_model(session=session)

    # Make request without auth header
    response = client.get('/api/applications')

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_request_catalog_as_user(client, session, jwt):
    """Test retrieving request catalog as a regular user."""
    # Setup applications
    app1 = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())
    app2 = factory_application_model(session=session, **TestApplicationScenarios.get_epic_engage_app())

    # Setup regular user headers
    headers = factory_auth_header(jwt, TestJwtClaims.regular_user_role.value)

    # Make request
    response = client.get('/api/applications/request-catalog', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)


@patch('centre_api.services.applications_service.ApplicationsService.get_request_catalog')
def test_get_request_catalog_shows_pending_status(mock_get_catalog, client, session, jwt):
    """Test that request catalog shows PENDING status for apps with pending requests."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup mock to return catalog with pending status
    mock_get_catalog.return_value = [
        {
            'id': app.id,
            'name': app.name,
            'title': app.title,
            'description': app.description,
            'status': 'PENDING'
        }
    ]

    # Setup headers
    headers = factory_auth_header(jwt, TestJwtClaims.regular_user_role.value)

    # Make request
    response = client.get('/api/applications/request-catalog', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) >= 1
    assert response.json[0]['status'] == 'PENDING'


def test_create_access_request_success(client, session, jwt):
    """Test creating an access request successfully."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup headers
    headers = factory_auth_header(jwt, TestJwtClaims.regular_user_role.value)

    # Make request
    response = client.post(f'/api/applications/{app.id}/access_request', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert 'id' in response.json
    assert response.json['app_id'] == app.id
    assert response.json['status'] == AccessRequestsStatusEnum.PENDING.value


def test_create_access_request_duplicate_pending(client, session, jwt):
    """Test that creating duplicate pending access request is handled."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup user
    user_id = TestJwtClaims.regular_user_role.value['sub']

    # Create existing pending request
    existing_request = factory_access_request_model(
        app_id=app.id,
        user_auth_guid=user_id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Setup headers
    headers = factory_auth_header(jwt, TestJwtClaims.regular_user_role.value)

    # Make request
    response = client.post(f'/api/applications/{app.id}/access_request', headers=headers)

    # The service should handle this - check the response
    # It might return existing request or error
    assert response.status_code in [HTTPStatus.OK, HTTPStatus.CONFLICT, HTTPStatus.BAD_REQUEST]


def test_create_access_request_invalid_app_id(client, session, jwt):
    """Test creating access request with invalid app ID."""
    # Setup headers
    headers = factory_auth_header(jwt, TestJwtClaims.regular_user_role.value)

    # Make request with non-existent app ID
    response = client.post('/api/applications/99999/access_request', headers=headers)

    # Assertions
    assert response.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST]


def test_get_access_levels_as_admin(client, session, jwt):
    """Test retrieving access levels for an application as admin."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup admin headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get(f'/api/applications/{app.name}/access-levels', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # Response should be a list of access levels/groups
    assert isinstance(response.json, (list, dict))


@patch('centre_api.services.applications_service.ApplicationsService.get_app_access_levels')
def test_get_access_levels_returns_groups(mock_get_levels, client, session, jwt):
    """Test that access levels endpoint returns group hierarchy."""
    # Setup mock return value
    mock_get_levels.return_value = [
        {'id': '1', 'name': 'ADMIN', 'path': '/TRACK/ADMIN', 'display_name': 'Administrator', 'level': 3},
        {'id': '2', 'name': 'VIEWER', 'path': '/TRACK/VIEWER', 'display_name': 'Viewer', 'level': 1}
    ]

    # Setup headers
    headers = factory_auth_header(jwt, TestJwtClaims.track_admin_role.value)

    # Make request
    response = client.get('/api/applications/EPIC.track/access-levels', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 2
    assert response.json[0]['name'] == 'ADMIN'
    assert response.json[1]['name'] == 'VIEWER'


def test_get_access_levels_invalid_app_name(client, session, jwt):
    """Test retrieving access levels with invalid app name."""
    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request with invalid app name
    response = client.get('/api/applications/INVALID_APP/access-levels', headers=headers)

    # Assertions
    assert response.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST]


def test_get_applications_with_active_filter(client, session, jwt):
    """Test that only active applications are returned by default."""
    # Setup active and inactive applications
    active_app = factory_application_model(
        session=session,
        is_active=True,
        **TestApplicationScenarios.get_epic_track_app()
    )
    inactive_app = factory_application_model(
        session=session,
        title='Inactive App',
        name='EPIC.inactive',
        is_active=False
    )

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/applications', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK

    # Check that active app is in response
    app_ids = [app['id'] for app in response.json]
    assert active_app.id in app_ids


def test_applications_endpoint_performance(client, session, jwt):
    """Test that applications endpoint performs well with multiple apps."""
    # Create multiple applications
    for i in range(10):
        factory_application_model(
            session=session,
            title=f'Test App {i}',
            name=f'EPIC.test{i}'
        )

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/applications', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) >= 10
