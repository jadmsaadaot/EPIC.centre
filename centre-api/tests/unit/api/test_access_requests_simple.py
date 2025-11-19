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
"""Tests for access requests API endpoints - simplified pattern."""
from http import HTTPStatus
from urllib.parse import urljoin

from centre_api.enums.access_request_status import AccessRequestsStatusEnum
from tests.utilities.factory_scenarios import TestApplicationScenarios, TestJwtClaims
from tests.utilities.factory_utils import (
    factory_access_request_model,
    factory_application_model,
    factory_auth_header,
)

API_BASE_URL = '/api/'


def test_get_all_access_requests(client, session, auth_header):
    """Test retrieving all access requests as admin."""
    # Setup applications and requests
    app1 = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())
    app2 = factory_application_model(session=session, **TestApplicationScenarios.get_epic_compliance_app())

    request1 = factory_access_request_model(app_id=app1.id, session=session)
    request2 = factory_access_request_model(app_id=app2.id, session=session)

    # Make request
    url = urljoin(API_BASE_URL, 'access-requests')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) >= 2


def test_get_access_requests_filtered_by_status(client, session, auth_header):
    """Test filtering access requests by status."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup access requests with different statuses
    pending_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )
    approved_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.APPROVED,
        session=session
    )

    # Make request for pending only
    url = urljoin(API_BASE_URL, 'access-requests?status=PENDING')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # All returned requests should be PENDING
    for request in response.json:
        if 'status' in request:
            assert request['status'] == AccessRequestsStatusEnum.PENDING.value


def test_get_user_access_requests(client, session, jwt):
    """Test retrieving access requests for a specific user."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup specific user
    user_id = TestJwtClaims.regular_user_role.value['sub']

    # Setup access requests for user
    request1 = factory_access_request_model(
        app_id=app.id,
        user_auth_guid=user_id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Setup headers for that user
    headers = factory_auth_header(jwt, TestJwtClaims.regular_user_role.value)

    # Make request
    url = urljoin(API_BASE_URL, f'access-requests/users/{user_id}')
    response = client.get(url, headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)


def test_update_access_request_approve(client, session, auth_header):
    """Test approving an access request."""
    # Setup application and pending request
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())
    access_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Make request to approve
    url = urljoin(API_BASE_URL, f'access-requests/{access_request.id}?status=APPROVED')
    response = client.put(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK


def test_update_access_request_reject(client, session, auth_header):
    """Test rejecting an access request."""
    # Setup application and pending request
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())
    access_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Make request to reject
    url = urljoin(API_BASE_URL, f'access-requests/{access_request.id}?status=REJECTED')
    response = client.put(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK


def test_update_access_request_invalid_status(client, session, auth_header):
    """Test updating access request with invalid status."""
    # Setup application and request
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())
    access_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Make request with invalid status
    url = urljoin(API_BASE_URL, f'access-requests/{access_request.id}?status=INVALID_STATUS')
    response = client.put(url, headers=auth_header)

    # Assertions
    assert response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY]


def test_update_access_request_not_found(client, auth_header):
    """Test updating non-existent access request."""
    # Make request with invalid request ID
    url = urljoin(API_BASE_URL, 'access-requests/99999?status=APPROVED')
    response = client.put(url, headers=auth_header)

    # Assertions
    assert response.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST]


def test_get_access_requests_without_auth(client):
    """Test that unauthorized requests are rejected."""
    # Make request without auth header
    url = urljoin(API_BASE_URL, 'access-requests')
    response = client.get(url)

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED
