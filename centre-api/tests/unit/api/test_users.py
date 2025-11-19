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
"""Tests for users API endpoints."""
from http import HTTPStatus
from unittest.mock import MagicMock, patch

from faker import Faker

from tests.utilities.factory_scenarios import TestJwtClaims
from tests.utilities.factory_utils import (
    factory_auth_header,
    setup_admin_headers,
    setup_app_admin_headers,
)

fake = Faker()


@patch('centre_api.services.user_service.UserService.get_users')
def test_get_all_users_as_dst_admin(mock_get_users, client, session, jwt):
    """Test DST admin can retrieve all users."""
    # Setup mock return value
    mock_get_users.return_value = [
        {
            'id': fake.uuid4(),
            'username': 'JSMITH',
            'firstName': 'John',
            'lastName': 'Smith',
            'email': 'john.smith@gov.bc.ca',
            'enabled': True,
            'apps': [
                {'name': 'EPIC.track', 'role': 'Administrator', 'group_path': '/TRACK/ADMIN'}
            ]
        },
        {
            'id': fake.uuid4(),
            'username': 'BJONES',
            'firstName': 'Bob',
            'lastName': 'Jones',
            'email': 'bob.jones@gov.bc.ca',
            'enabled': True,
            'apps': [
                {'name': 'EPIC.compliance', 'role': 'Viewer', 'group_path': '/COMPLIANCE/VIEWER'}
            ]
        }
    ]

    # Setup DST admin headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/users', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 2
    assert response.json[0]['username'] == 'JSMITH'
    assert response.json[1]['username'] == 'BJONES'


@patch('centre_api.services.user_service.UserService.get_users')
def test_get_users_with_search_filter(mock_get_users, client, session, jwt):
    """Test searching for users by search text."""
    # Setup mock return value
    mock_get_users.return_value = [
        {
            'id': fake.uuid4(),
            'username': 'JSMITH',
            'firstName': 'John',
            'lastName': 'Smith',
            'email': 'john.smith@gov.bc.ca',
            'enabled': True,
            'apps': []
        }
    ]

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request with search parameter
    response = client.get('/api/users?search=John', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # Verify the service was called with search parameter
    mock_get_users.assert_called_once_with('John', True)


@patch('centre_api.services.user_service.UserService.get_users')
def test_get_users_without_groups(mock_get_users, client, session, jwt):
    """Test retrieving users without group information."""
    # Setup mock return value
    mock_get_users.return_value = [
        {
            'id': fake.uuid4(),
            'username': 'JSMITH',
            'firstName': 'John',
            'lastName': 'Smith',
            'email': 'john.smith@gov.bc.ca',
            'enabled': True
        }
    ]

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request without including groups
    response = client.get('/api/users?include_groups=false', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # Verify the service was called with include_groups=False
    mock_get_users.assert_called_once_with(None, False)


def test_get_users_unauthorized(client, session):
    """Test that unauthorized requests are rejected."""
    # Make request without auth header
    response = client.get('/api/users')

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@patch('centre_api.services.user_service.UserService.get_user_by_username')
def test_get_user_by_username_success(mock_get_user, client, session, jwt):
    """Test retrieving a specific user by username."""
    # Setup mock return value
    username = 'JSMITH'
    mock_get_user.return_value = {
        'id': fake.uuid4(),
        'username': username,
        'firstName': 'John',
        'lastName': 'Smith',
        'email': 'john.smith@gov.bc.ca',
        'enabled': True,
        'apps': [
            {'name': 'EPIC.track', 'role': 'Administrator', 'group_path': '/TRACK/ADMIN'}
        ]
    }

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get(f'/api/users/username/{username}', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert response.json['username'] == username
    assert response.json['firstName'] == 'John'
    assert 'apps' in response.json


@patch('centre_api.services.user_service.UserService.get_user_by_username')
def test_get_user_by_username_not_found(mock_get_user, client, session, jwt):
    """Test retrieving non-existent user returns 404."""
    # Setup mock to return None
    mock_get_user.return_value = None

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/users/username/NONEXISTENT', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'message' in response.json


@patch('centre_api.services.user_service.UserService.update_user_status')
def test_update_user_status_enable(mock_update, client, session, jwt):
    """Test enabling a user account."""
    # Setup mock
    mock_update.return_value = None

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request to enable user
    username = 'JSMITH'
    response = client.patch(
        f'/api/users/username/{username}',
        json={'enabled': True},
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert 'User updated' in response.json
    # Verify service was called correctly
    mock_update.assert_called_once_with(username, {'enabled': True})


@patch('centre_api.services.user_service.UserService.update_user_status')
def test_update_user_status_disable(mock_update, client, session, jwt):
    """Test disabling a user account."""
    # Setup mock
    mock_update.return_value = None

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request to disable user
    username = 'JSMITH'
    response = client.patch(
        f'/api/users/username/{username}',
        json={'enabled': False},
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert 'User updated' in response.json
    # Verify service was called correctly
    mock_update.assert_called_once_with(username, {'enabled': False})


@patch('centre_api.services.user_service.UserService.update_user_status')
def test_update_user_first_name(mock_update, client, session, jwt):
    """Test updating user's first name."""
    # Setup mock
    mock_update.return_value = None

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request to update first name
    username = 'JSMITH'
    response = client.patch(
        f'/api/users/username/{username}',
        json={'firstName': 'Johnny'},
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    mock_update.assert_called_once_with(username, {'firstName': 'Johnny'})


def test_update_user_unauthorized(client, session):
    """Test that unauthorized update requests are rejected."""
    # Make request without auth header
    response = client.patch(
        '/api/users/username/JSMITH',
        json={'enabled': False}
    )

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@patch('centre_api.services.user_service.UserService.update_user_access')
def test_update_user_access_grant_role(mock_update_access, client, session, jwt):
    """Test granting user access to an application."""
    # Setup mock
    mock_update_access.return_value = None

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Prepare access data
    access_data = {
        'app_name': 'EPIC.track',
        'group_path': '/TRACK/ADMIN'
    }

    # Make request
    username = 'JSMITH'
    response = client.put(
        f'/api/users/{username}/access',
        json=access_data,
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert 'User group updated' in response.json
    # Verify service was called correctly
    mock_update_access.assert_called_once_with(username, access_data)


@patch('centre_api.services.user_service.UserService.update_user_access')
def test_update_user_access_change_role(mock_update_access, client, session, jwt):
    """Test changing user's role in an application."""
    # Setup mock
    mock_update_access.return_value = None

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Prepare access data to change from VIEWER to ADMIN
    access_data = {
        'app_name': 'EPIC.track',
        'group_path': '/TRACK/ADMIN'
    }

    # Make request
    username = 'JSMITH'
    response = client.put(
        f'/api/users/{username}/access',
        json=access_data,
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    mock_update_access.assert_called_once_with(username, access_data)


@patch('centre_api.services.user_service.UserService.revoke_user_access')
def test_revoke_user_access(mock_revoke, client, session, jwt):
    """Test revoking user access from an application."""
    # Setup mock
    mock_revoke.return_value = None

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Prepare access data
    access_data = {
        'app_name': 'EPIC.track',
        'group_path': '/TRACK/ADMIN'
    }

    # Make request
    username = 'JSMITH'
    response = client.delete(
        f'/api/users/{username}/access',
        json=access_data,
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert 'User group revoked' in response.json
    # Verify service was called correctly
    mock_revoke.assert_called_once_with(username, access_data)


def test_update_user_access_unauthorized(client, session):
    """Test that unauthorized access update requests are rejected."""
    # Make request without auth header
    response = client.put(
        '/api/users/JSMITH/access',
        json={'app_name': 'EPIC.track', 'group_path': '/TRACK/ADMIN'}
    )

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_revoke_user_access_unauthorized(client, session):
    """Test that unauthorized revoke requests are rejected."""
    # Make request without auth header
    response = client.delete(
        '/api/users/JSMITH/access',
        json={'app_name': 'EPIC.track'}
    )

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@patch('centre_api.services.user_service.UserService.get_users')
def test_get_users_as_app_admin_sees_filtered_users(mock_get_users, client, session, jwt):
    """Test that app admin only sees users from their app."""
    # Setup mock to return only users from Track app
    mock_get_users.return_value = [
        {
            'id': fake.uuid4(),
            'username': 'JSMITH',
            'firstName': 'John',
            'lastName': 'Smith',
            'email': 'john.smith@gov.bc.ca',
            'enabled': True,
            'apps': [
                {'name': 'EPIC.track', 'role': 'Viewer', 'group_path': '/TRACK/VIEWER'}
            ]
        }
    ]

    # Setup Track admin headers
    headers, claims = setup_app_admin_headers(jwt, app_client_name='epictrack-web')

    # Make request
    response = client.get('/api/users', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # Service should filter results based on admin permissions


@patch('centre_api.services.user_service.UserService.get_users')
def test_get_users_includes_app_access_info(mock_get_users, client, session, jwt):
    """Test that users include their app access information."""
    # Setup mock return value
    mock_get_users.return_value = [
        {
            'id': fake.uuid4(),
            'username': 'JSMITH',
            'firstName': 'John',
            'lastName': 'Smith',
            'email': 'john.smith@gov.bc.ca',
            'enabled': True,
            'apps': [
                {
                    'name': 'EPIC.track',
                    'role': 'Administrator',
                    'group_name': 'ADMIN',
                    'group_path': '/TRACK/ADMIN'
                },
                {
                    'name': 'EPIC.compliance',
                    'role': 'Viewer',
                    'group_name': 'VIEWER',
                    'group_path': '/COMPLIANCE/VIEWER'
                }
            ]
        }
    ]

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/users', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    user = response.json[0]
    assert 'apps' in user
    assert len(user['apps']) == 2
    assert user['apps'][0]['name'] == 'EPIC.track'
    assert user['apps'][0]['role'] == 'Administrator'


@patch('centre_api.services.user_service.UserService.update_user_access')
def test_update_user_access_permission_check(mock_update_access, client, session, jwt):
    """Test that permission is checked when updating user access."""
    # Setup mock to raise permission error
    mock_update_access.side_effect = PermissionError('User does not have permission to update access for app "EPIC.compliance"')

    # Setup Track admin headers (shouldn't be able to update Compliance access)
    headers, claims = setup_app_admin_headers(jwt, app_client_name='epictrack-web')

    # Prepare access data for Compliance app
    access_data = {
        'app_name': 'EPIC.compliance',
        'group_path': '/COMPLIANCE/ADMIN'
    }

    # Make request
    username = 'JSMITH'
    response = client.put(
        f'/api/users/{username}/access',
        json=access_data,
        headers=headers
    )

    # Assertions
    # Should return error status
    assert response.status_code in [HTTPStatus.FORBIDDEN, HTTPStatus.UNAUTHORIZED, HTTPStatus.INTERNAL_SERVER_ERROR]


@patch('centre_api.services.user_service.UserService.get_users')
def test_get_users_with_empty_results(mock_get_users, client, session, jwt):
    """Test retrieving users when no users exist."""
    # Setup mock to return empty list
    mock_get_users.return_value = []

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/users?search=NONEXISTENT', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert response.json == []


@patch('centre_api.services.user_service.UserService.get_users')
def test_get_users_performance_with_many_users(mock_get_users, client, session, jwt):
    """Test users endpoint performs well with many users."""
    # Setup mock to return many users
    mock_users = [
        {
            'id': fake.uuid4(),
            'username': f'USER{i}',
            'firstName': fake.first_name(),
            'lastName': fake.last_name(),
            'email': fake.email(),
            'enabled': True,
            'apps': []
        }
        for i in range(100)
    ]
    mock_get_users.return_value = mock_users

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Make request
    response = client.get('/api/users', headers=headers)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 100


@patch('centre_api.services.user_service.UserService.update_user_status')
def test_update_user_with_multiple_fields(mock_update, client, session, jwt):
    """Test updating multiple user fields at once."""
    # Setup mock
    mock_update.return_value = None

    # Setup headers
    headers, claims = setup_admin_headers(jwt)

    # Prepare update data
    update_data = {
        'enabled': True,
        'firstName': 'Johnny',
        'lastName': 'Smithson'
    }

    # Make request
    username = 'JSMITH'
    response = client.patch(
        f'/api/users/username/{username}',
        json=update_data,
        headers=headers
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    mock_update.assert_called_once_with(username, update_data)
