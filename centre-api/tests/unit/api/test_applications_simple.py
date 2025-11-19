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
"""Tests for application API endpoints - simplified pattern."""
from http import HTTPStatus
from urllib.parse import urljoin

from centre_api.enums.access_request_status import AccessRequestsStatusEnum
from tests.utilities.factory_scenarios import TestApplicationScenarios
from tests.utilities.factory_utils import factory_application_model

API_BASE_URL = '/api/'


def test_get_all_applications(client, auth_header):
    """Test retrieving all applications."""
    # Setup applications
    app1 = factory_application_model(**TestApplicationScenarios.get_epic_track_app())
    app2 = factory_application_model(**TestApplicationScenarios.get_epic_compliance_app())

    # Make request
    url = urljoin(API_BASE_URL, 'applications')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) >= 1

    # Verify applications are returned
    app_names = [app['name'] for app in response.json]
    assert app1.name in app_names
    assert app2.name in app_names


def test_get_application_includes_required_fields(client, auth_header):
    """Test that applications include all required fields."""
    # Setup application
    factory_application_model(**TestApplicationScenarios.get_epic_track_app())

    # Make request
    url = urljoin(API_BASE_URL, 'applications')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) >= 1

    # Verify structure
    app = response.json[0]
    assert 'id' in app
    assert 'name' in app
    assert 'title' in app
    assert 'description' in app
    assert 'launch_url' in app


def test_get_request_catalog(client, auth_header):
    """Test retrieving request catalog."""
    # Setup applications
    factory_application_model(**TestApplicationScenarios.get_epic_track_app())

    # Make request
    url = urljoin(API_BASE_URL, 'applications/request-catalog')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)


def test_create_access_request(client, session, auth_header):
    """Test creating an access request for an application."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Make request
    url = urljoin(API_BASE_URL, f'applications/{app.id}/access_request')
    response = client.post(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert 'id' in response.json
    assert response.json['app_id'] == app.id
    assert response.json['status'] == AccessRequestsStatusEnum.PENDING.value


def test_get_access_levels_for_application(client, auth_header):
    """Test retrieving access levels for an application."""
    # Setup application
    app = factory_application_model(**TestApplicationScenarios.get_epic_track_app())

    # Make request
    url = urljoin(API_BASE_URL, f'applications/{app.name}/access-levels')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # Response should be a list of access levels/groups
    assert isinstance(response.json, (list, dict))


def test_get_applications_without_auth(client):
    """Test that unauthorized requests are rejected."""
    # Make request without auth header
    url = urljoin(API_BASE_URL, 'applications')
    response = client.get(url)

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED
