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
"""Test scenarios for EPIC.centre tests."""
from enum import Enum

from faker import Faker

from centre_api.config import get_named_config

fake = Faker()
CONFIG = get_named_config('testing')


class TestJwtClaims(dict, Enum):
    """Test scenarios of JWT claims."""

    dst_admin_role = {
        'iss': CONFIG.JWT_OIDC_TEST_ISSUER,
        'sub': 'f7a4a1d4-73a8-4cbc-a40f-bb1145302065',
        'preferred_username': f'{fake.user_name()}@idir',
        'given_name': fake.first_name(),
        'family_name': fake.last_name(),
        'email': 'dst.admin@gov.bc.ca',
        'resource_access': {
            'epic-centre': {'roles': ['manage_auth', 'manage_users']}
        },
        'groups': ['/CENTRE/ADMIN']
    }

    track_admin_role = {
        'iss': CONFIG.JWT_OIDC_TEST_ISSUER,
        'sub': '12345678-aaaa-bbbb-cccc-1234567890ab',
        'preferred_username': f'{fake.user_name()}@idir',
        'given_name': fake.first_name(),
        'family_name': fake.last_name(),
        'email': 'track.admin@gov.bc.ca',
        'resource_access': {
            'epictrack-web': {'roles': ['manage_users']}
        },
        'groups': ['/TRACK/ADMIN']
    }

    compliance_admin_role = {
        'iss': CONFIG.JWT_OIDC_TEST_ISSUER,
        'sub': '22345678-bbbb-cccc-dddd-2234567890bc',
        'preferred_username': f'{fake.user_name()}@idir',
        'given_name': fake.first_name(),
        'family_name': fake.last_name(),
        'email': 'compliance.admin@gov.bc.ca',
        'resource_access': {
            'epic-compliance': {'roles': ['super_user']}
        },
        'groups': ['/COMPLIANCE/SUPER_USER']
    }

    regular_user_role = {
        'iss': CONFIG.JWT_OIDC_TEST_ISSUER,
        'sub': '33345678-cccc-dddd-eeee-3334567890cd',
        'preferred_username': f'{fake.user_name()}@idir',
        'given_name': fake.first_name(),
        'family_name': fake.last_name(),
        'email': 'regular.user@gov.bc.ca',
        'resource_access': {},
        'groups': ['/CENTRE/USER']
    }


class TestApplicationScenarios:
    """Common test scenarios for applications."""

    @staticmethod
    def get_epic_track_app():
        """Return EPIC.track application data."""
        return {
            'title': 'EPIC.track',
            'name': 'EPIC.track',
            'description': 'Project tracking and workflow management system',
            'launch_url': 'https://epic-track.gov.bc.ca',
            'is_active': True
        }

    @staticmethod
    def get_epic_compliance_app():
        """Return EPIC.compliance application data."""
        return {
            'title': 'EPIC.compliance',
            'name': 'EPIC.compliance',
            'description': 'Compliance monitoring and reporting system',
            'launch_url': 'https://epic-compliance.gov.bc.ca',
            'is_active': True
        }

    @staticmethod
    def get_epic_engage_app():
        """Return EPIC.engage application data."""
        return {
            'title': 'EPIC.engage',
            'name': 'EPIC.engage',
            'description': 'Public engagement platform',
            'launch_url': 'https://epic-engage.gov.bc.ca',
            'is_active': True
        }


class TestAccessRequestScenarios:
    """Common test scenarios for access requests."""

    @staticmethod
    def get_access_request_payload(app_id: int):
        """Return a standard access request payload."""
        return {
            'app_id': app_id
        }

    @staticmethod
    def get_update_request_payload(status: str):
        """Return payload for updating an access request."""
        return {
            'status': status
        }
