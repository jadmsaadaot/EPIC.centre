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
"""Tests for users API endpoints - simplified pattern."""
from http import HTTPStatus
from urllib.parse import urljoin
from unittest.mock import patch

from faker import Faker

API_BASE_URL = '/api/'

fake = Faker()


@patch('centre_api.services.user_service.UserService.get_users')
def test_get_all_users(mock_get_users, client, auth_header):
    """Test retrieving all users."""
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
            'apps': []
        }
    ]

    # Make request
    url = urljoin(API_BASE_URL, 'users')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 2
    assert response.json[0]['username'] == 'JSMITH'
    assert response.json[1]['username'] == 'BJONES'


@patch('centre_api.services.user_service.UserService.get_users')
def test_get_users_with_search(mock_get_users, client, auth_header):
    """Test searching for users."""
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

    # Make request with search parameter
    url = urljoin(API_BASE_URL, 'users?search=John')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    # Verify the service was called with search parameter
    mock_get_users.assert_called_once_with('John', True)


@patch('centre_api.services.user_service.UserService.get_user_by_username')
def test_get_user_by_username(mock_get_user, client, auth_header):
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

    # Make request
    url = urljoin(API_BASE_URL, f'users/username/{username}')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert response.json['username'] == username
    assert response.json['firstName'] == 'John'
    assert 'apps' in response.json


@patch('centre_api.services.user_service.UserService.get_user_by_username')
def test_get_user_by_username_not_found(mock_get_user, client, auth_header):
    """Test retrieving non-existent user."""
    # Setup mock to return None
    mock_get_user.return_value = None

    # Make request
    url = urljoin(API_BASE_URL, 'users/username/NONEXISTENT')
    response = client.get(url, headers=auth_header)

    # Assertions
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'message' in response.json


@patch('centre_api.services.user_service.UserService.update_user_status')
def test_update_user_status_disable(mock_update, client, auth_header):
    """Test disabling a user account."""
    # Setup mock
    mock_update.return_value = None

    # Make request to disable user
    username = 'JSMITH'
    url = urljoin(API_BASE_URL, f'users/username/{username}')
    response = client.patch(
        url,
        json={'enabled': False},
        headers=auth_header
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert 'User updated' in response.json
    # Verify service was called correctly
    mock_update.assert_called_once_with(username, {'enabled': False})


@patch('centre_api.services.user_service.UserService.update_user_status')
def test_update_user_status_enable(mock_update, client, auth_header):
    """Test enabling a user account."""
    # Setup mock
    mock_update.return_value = None

    # Make request to enable user
    username = 'JSMITH'
    url = urljoin(API_BASE_URL, f'users/username/{username}')
    response = client.patch(
        url,
        json={'enabled': True},
        headers=auth_header
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    mock_update.assert_called_once_with(username, {'enabled': True})


@patch('centre_api.services.user_service.UserService.update_user_access')
def test_update_user_access(mock_update_access, client, auth_header):
    """Test granting user access to an application."""
    # Setup mock
    mock_update_access.return_value = None

    # Prepare access data
    access_data = {
        'app_name': 'EPIC.track',
        'group_path': '/TRACK/ADMIN'
    }

    # Make request
    username = 'JSMITH'
    url = urljoin(API_BASE_URL, f'users/{username}/access')
    response = client.put(
        url,
        json=access_data,
        headers=auth_header
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert 'User group updated' in response.json
    mock_update_access.assert_called_once_with(username, access_data)


@patch('centre_api.services.user_service.UserService.revoke_user_access')
def test_revoke_user_access(mock_revoke, client, auth_header):
    """Test revoking user access from an application."""
    # Setup mock
    mock_revoke.return_value = None

    # Prepare access data
    access_data = {
        'app_name': 'EPIC.track',
        'group_path': '/TRACK/ADMIN'
    }

    # Make request
    username = 'JSMITH'
    url = urljoin(API_BASE_URL, f'users/{username}/access')
    response = client.delete(
        url,
        json=access_data,
        headers=auth_header
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert 'User group revoked' in response.json
    mock_revoke.assert_called_once_with(username, access_data)


def test_get_users_without_auth(client):
    """Test that unauthorized requests are rejected."""
    # Make request without auth header
    url = urljoin(API_BASE_URL, 'users')
    response = client.get(url)

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_update_user_without_auth(client):
    """Test that unauthorized update requests are rejected."""
    # Make request without auth header
    url = urljoin(API_BASE_URL, 'users/username/JSMITH')
    response = client.patch(
        url,
        json={'enabled': False}
    )

    # Assertions
    assert response.status_code == HTTPStatus.UNAUTHORIZED
