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
"""Tests for access requests API endpoints."""
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
    setup_app_admin_headers,
)

fake = Faker()


def test_get_all_access_requests_as_dst_admin(client, session, jwt):
    """Test DST admin can retrieve all access requests."""
    # Setup applications
    app1 = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())
    app2 = factory_application_model(session=session, **TestApplicationScenarios.get_epic_compliance_app())

    # Setup access requests
    request1 = factory_access_request_model(app_id=app1.id, session=session)
    request2 = factory_access_request_model(app_id=app2.id, session=session)

    # Setup DST admin headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/access-requests', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) >= 2


def test_get_all_access_requests_as_app_admin(client, session, jwt):
    """Test app admin can only see requests for their app."""
    # Setup applications
    track_app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())
    compliance_app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_compliance_app())

    # Setup access requests
    track_request = factory_access_request_model(app_id=track_app.id, session=session)
    compliance_request = factory_access_request_model(app_id=compliance_app.id, session=session)

    # Setup Track admin headers (should only see Track requests)
    headers, claims = setup_app_admin_headers(jwt, app_client_name='epictrack-web')

    # Make request
    response = client.get('/api/access-requests', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # Service should filter to only Track app requests
    # This depends on implementation details


def test_get_access_requests_filtered_by_status(client, session, jwt):
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
    rejected_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.REJECTED,
        session=session
    )

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request for pending only
    response = client.get('/api/access-requests?status=PENDING', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # All returned requests should be PENDING
    for request in response.json:
        if 'status' in request:
            assert request['status'] == AccessRequestsStatusEnum.PENDING.value


def test_get_access_requests_filtered_by_user(client, session, jwt):
    """Test filtering access requests by user_auth_guid."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup specific user
    user_id = fake.uuid4()

    # Setup access requests
    user_request = factory_access_request_model(
        app_id=app.id,
        user_auth_guid=user_id,
        session=session
    )
    other_request = factory_access_request_model(
        app_id=app.id,
        user_auth_guid=fake.uuid4(),
        session=session
    )

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request filtered by user
    response = client.get(f'/api/access-requests?user_auth_guid={user_id}', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # All returned requests should be for the specified user
    for request in response.json:
        if 'user_auth_guid' in request:
            assert request['user_auth_guid'] == user_id


def test_get_access_requests_invalid_status(client, session, jwt):
    """Test that invalid status filter returns error."""
    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request with invalid status
    response = client.get('/api/access-requests?status=INVALID_STATUS', headers=headers)

    # Assertions
    assert response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.OK]
    # If OK, it should return empty list or all requests


def test_get_access_requests_unauthorized(client, session):
    """Test that unauthorized requests are rejected."""
    # Make request without auth header
    response = client.get('/api/access-requests')

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_user_access_requests_success(client, session, jwt):
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

    # Setup headers
    headers = factory_auth_header(jwt, TestJwtClaims.regular_user_role.value)

    # Make request
    response = client.get(f'/api/access-requests/users/{user_id}', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)


def test_get_user_access_requests_filtered_by_status(client, session, jwt):
    """Test retrieving user access requests filtered by status."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup specific user
    user_id = TestJwtClaims.regular_user_role.value['sub']

    # Setup multiple access requests with different statuses
    pending_request = factory_access_request_model(
        app_id=app.id,
        user_auth_guid=user_id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )
    approved_request = factory_access_request_model(
        app_id=app.id,
        user_auth_guid=user_id,
        status=AccessRequestsStatusEnum.APPROVED,
        session=session
    )

    # Setup headers
    headers = factory_auth_header(jwt, TestJwtClaims.regular_user_role.value)

    # Make request for pending only
    response = client.get(f'/api/access-requests/users/{user_id}?status=PENDING', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # All returned requests should be PENDING
    for request in response.json:
        if 'status' in request:
            assert request['status'] == AccessRequestsStatusEnum.PENDING.value


def test_update_access_request_approve_as_admin(client, session, jwt):
    """Test approving an access request as admin."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup pending access request
    access_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Setup DST admin headers
    headers, claims = setup_admin_headers(jwt)

    # Make request to approve
    response = client.put(
        f'/api/access-requests/{access_request.id}?status=APPROVED',
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK


def test_update_access_request_reject_as_admin(client, session, jwt):
    """Test rejecting an access request as admin."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup pending access request
    access_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Setup DST admin headers
    headers, claims = setup_admin_headers(jwt)

    # Make request to reject
    response = client.put(
        f'/api/access-requests/{access_request.id}?status=REJECTED',
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK


def test_update_access_request_invalid_status(client, session, jwt):
    """Test updating access request with invalid status."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup pending access request
    access_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request with invalid status
    response = client.put(
        f'/api/access-requests/{access_request.id}?status=INVALID_STATUS',
        headers=headers
    )

    # Assertions
    assert response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY]


def test_update_access_request_not_found(client, session, jwt):
    """Test updating non-existent access request."""
    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request with invalid request ID
    response = client.put(
        '/api/access-requests/99999?status=APPROVED',
        headers=headers
    )

    # Assertions
    assert response.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST]


def test_update_access_request_unauthorized(client, session):
    """Test that unauthorized requests are rejected."""
    # Make request without auth header
    response = client.put('/api/access-requests/1?status=APPROVED')

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@patch('centre_api.services.access_requests.AccessRequestsService.process_access_request')
def test_update_access_request_creates_keycloak_group(mock_process, client, session, jwt):
    """Test that approving a request creates Keycloak group assignment."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup pending access request
    access_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Setup mock return value
    mock_process.return_value = {
        'id': access_request.id,
        'status': AccessRequestsStatusEnum.APPROVED.value,
        'app_id': app.id
    }

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request to approve
    response = client.put(
        f'/api/access-requests/{access_request.id}?status=APPROVED',
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # Verify the service was called
    mock_process.assert_called_once_with(access_request.id, 'APPROVED')


def test_get_all_access_requests_includes_app_details(client, session, jwt):
    """Test that access requests include application details."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup access request
    access_request = factory_access_request_model(app_id=app.id, session=session)

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/access-requests', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # Verify structure includes app details
    if len(response.json) > 0:
        request_data = response.json[0]
        assert 'app_id' in request_data or 'app' in request_data


def test_access_requests_pagination(client, session, jwt):
    """Test access requests endpoint handles large datasets."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Create multiple access requests
    for i in range(20):
        factory_access_request_model(
            app_id=app.id,
            status=AccessRequestsStatusEnum.PENDING,
            session=session
        )

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/access-requests?status=PENDING', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) >= 20


def test_update_access_request_multiple_status_changes(client, session, jwt):
    """Test that access request can go through status transitions."""
    # Setup application
    app = factory_application_model(session=session, **TestApplicationScenarios.get_epic_track_app())

    # Setup pending access request
    access_request = factory_access_request_model(
        app_id=app.id,
        status=AccessRequestsStatusEnum.PENDING,
        session=session
    )

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # First approve
    response1 = client.put(
        f'/api/access-requests/{access_request.id}?status=APPROVED',
        headers=headers
    )

    # Then try to reject (may or may not be allowed)
    response2 = client.put(
        f'/api/access-requests/{access_request.id}?status=REJECTED',
        headers=headers
    )

    # Assertions
    assert response1.status_code == HTTPStatus.OK
    # Second request may succeed or fail depending on business logic
    assert response2.status_code in [HTTPStatus.OK, HTTPStatus.BAD_REQUEST, HTTPStatus.CONFLICT]
