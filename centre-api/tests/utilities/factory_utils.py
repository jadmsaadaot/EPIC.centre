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
"""Factory utilities for creating test data."""
from faker import Faker

from centre_api.config import get_named_config
from centre_api.enums.access_request_status import AccessRequestsStatusEnum
from centre_api.models.access_requests import AccessRequests
from centre_api.models.applications import Application
from centre_api.models.db import db

CONFIG = get_named_config('testing')
fake = Faker()

JWT_HEADER = {
    'typ': 'JWT',
    'kid': CONFIG.JWT_OIDC_TEST_AUDIENCE
}


def factory_auth_header(jwt, claims):
    """Produce JWT tokens for use in tests."""
    return {
        'Authorization': 'Bearer ' + jwt.create_jwt(claims=claims, header=JWT_HEADER)
    }


def factory_application_model(
    title=None,
    name=None,
    description=None,
    launch_url=None,
    is_active=True,
    session=None
):
    """Create an Application model instance for testing."""
    application = Application(
        title=title or fake.catch_phrase(),
        name=name or f"EPIC.{fake.word()}",
        description=description or fake.text(max_nb_chars=200),
        launch_url=launch_url or fake.url(),
        is_active=is_active,
        created_by=fake.user_name(),
        updated_by=fake.user_name()
    )

    if session:
        session.add(application)
        session.commit()
    else:
        db.session.add(application)
        db.session.commit()

    return application


def factory_access_request_model(
    app_id=None,
    user_auth_guid=None,
    status=AccessRequestsStatusEnum.PENDING,
    application=None,
    created_by=None,
    session=None
):
    """Create an AccessRequest model instance for testing."""
    # Create application if not provided and no app_id
    if not app_id and not application:
        application = factory_application_model(session=session)
        app_id = application.id
    elif application:
        app_id = application.id

    access_request = AccessRequests(
        app_id=app_id,
        user_auth_guid=user_auth_guid or fake.uuid4(),
        status=status,
        created_by=created_by or fake.user_name(),
        updated_by=fake.user_name()
    )

    if session:
        session.add(access_request)
        session.commit()
    else:
        db.session.add(access_request)
        db.session.commit()

    return access_request


def create_mock_jwt_claims(
    user_id=None,
    username=None,
    first_name=None,
    last_name=None,
    email=None,
    resource_access=None,
    groups=None
):
    """Create mock JWT claims for testing authentication."""
    return {
        'sub': user_id or fake.uuid4(),
        'preferred_username': username or fake.user_name().upper(),
        'given_name': first_name or fake.first_name(),
        'family_name': last_name or fake.last_name(),
        'email': email or fake.email(),
        'resource_access': resource_access or {
            'epic-centre': {'roles': ['manage_auth', 'manage_users']}
        },
        'groups': groups or ['/CENTRE/ADMIN']
    }


def setup_admin_headers(jwt, resource_access=None):
    """Set up authentication headers for an admin user."""
    claims = create_mock_jwt_claims(
        resource_access=resource_access or {
            'epic-centre': {'roles': ['manage_auth', 'manage_users']}
        }
    )
    token = jwt.create_jwt(claims, JWT_HEADER)
    headers = {'Authorization': f'Bearer {token}'}
    return headers, claims


def setup_regular_user_headers(jwt, user_id=None):
    """Set up authentication headers for a regular user (no admin roles)."""
    claims = create_mock_jwt_claims(
        user_id=user_id,
        resource_access={'epic-centre': {'roles': []}},
        groups=['/CENTRE/USER']
    )
    token = jwt.create_jwt(claims, JWT_HEADER)
    headers = {'Authorization': f'Bearer {token}'}
    return headers, claims


def setup_app_admin_headers(jwt, app_client_name='epictrack-web'):
    """Set up authentication headers for an app-specific admin."""
    claims = create_mock_jwt_claims(
        resource_access={
            app_client_name: {'roles': ['manage_users']}
        },
        groups=['/TRACK/ADMIN']
    )
    token = jwt.create_jwt(claims, JWT_HEADER)
    headers = {'Authorization': f'Bearer {token}'}
    return headers, claims
