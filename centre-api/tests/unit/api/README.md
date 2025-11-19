# EPIC.centre API Tests

This directory contains comprehensive API tests for EPIC.centre backend endpoints.

## Test Files

### Comprehensive Test Suites (with extensive mocking)
- **`test_applications.py`** - 15 tests for applications endpoints
- **`test_access_requests.py`** - 19 tests for access requests endpoints
- **`test_users.py`** - 20 tests for users endpoints

These tests use extensive mocking to isolate API layer behavior and cover edge cases, error handling, and permission scenarios.

### Simplified Test Suites (EPIC.track pattern)
- **`test_applications_simple.py`** - 7 clean tests for applications endpoints
- **`test_access_requests_simple.py`** - 9 clean tests for access requests endpoints
- **`test_users_simple.py`** - 11 clean tests for users endpoints

These tests follow the EPIC.track pattern with minimal mocking, using the `auth_header` fixture and going end-to-end to the database.

## Running Tests

```bash
# Run all API tests
pytest tests/unit/api/ -v

# Run specific test file
pytest tests/unit/api/test_applications.py -v

# Run simplified tests only
pytest tests/unit/api/test_*_simple.py -v

# Run with coverage
pytest tests/unit/api/ --cov=centre_api --cov-report=html
```

## Test Patterns

### Pattern 1: Comprehensive Tests (Extensive Mocking)

```python
from unittest.mock import patch

@patch('centre_api.services.user_service.UserService.get_users')
def test_get_all_users_as_dst_admin(mock_get_users, client, session, jwt):
    """Test DST admin can retrieve all users."""
    mock_get_users.return_value = [...]
    headers, claims = setup_admin_headers(jwt)
    response = client.get('/api/users', headers=headers)
    assert response.status_code == HTTPStatus.OK
```

**Use when:**
- Testing complex permission logic
- Isolating API layer from service layer
- Need to test error conditions that are hard to reproduce
- Testing edge cases

### Pattern 2: Simplified Tests (Minimal Mocking)

```python
def test_get_all_applications(client, auth_header):
    """Test retrieving all applications."""
    app1 = factory_application_model(**TestApplicationScenarios.get_epic_track_app())
    url = urljoin(API_BASE_URL, 'applications')
    response = client.get(url, headers=auth_header)
    assert response.status_code == HTTPStatus.OK
```

**Use when:**
- Testing happy path scenarios
- Want end-to-end validation
- Following EPIC.track conventions
- Need cleaner, more readable tests

## Key Components

### Fixtures (in `tests/conftest.py`)

- **`client`** - Flask test client
- **`session`** - Database session with transaction rollback
- **`jwt`** - JWT manager for creating tokens
- **`auth_header`** - Configurable authentication headers (defaults to DST admin)
- **`dst_admin_header`** - DST admin authentication headers
- **`regular_user_header`** - Regular user authentication headers
- **`mock_auth_api_service`** - Autouse fixture that mocks all Auth API service calls

### Factory Utilities (in `tests/utilities/factory_utils.py`)

- `factory_application_model()` - Create Application instances
- `factory_access_request_model()` - Create AccessRequest instances
- `factory_auth_header()` - Generate JWT auth headers
- `setup_admin_headers()` - Setup DST admin authentication
- `setup_app_admin_headers()` - Setup app-specific admin authentication
- `setup_regular_user_headers()` - Setup regular user authentication

### Test Scenarios (in `tests/utilities/factory_scenarios.py`)

- `TestJwtClaims` - Pre-defined JWT claim scenarios for different user types
- `TestApplicationScenarios` - Helper methods for application test data
- `TestAccessRequestScenarios` - Helper methods for access request payloads

## Test Coverage

### Applications Endpoints
- ✅ GET `/api/applications` - Retrieve all applications
- ✅ GET `/api/applications/request-catalog` - Request catalog with status
- ✅ POST `/api/applications/<app_id>/access_request` - Create access request
- ✅ GET `/api/applications/<app_name>/access-levels` - Get access levels

### Access Requests Endpoints
- ✅ GET `/api/access-requests` - Retrieve all requests (filtered by admin role)
- ✅ GET `/api/access-requests?status=<status>` - Filter by status
- ✅ GET `/api/access-requests/users/<user_guid>` - Get user's requests
- ✅ PUT `/api/access-requests/<id>?status=<status>` - Approve/reject requests

### Users Endpoints
- ✅ GET `/api/users` - Retrieve users (with search)
- ✅ GET `/api/users/username/<username>` - Get specific user
- ✅ PATCH `/api/users/username/<username>` - Update user status
- ✅ PUT `/api/users/<username>/access` - Grant/update user access
- ✅ DELETE `/api/users/<username>/access` - Revoke user access

## Authentication

All tests use JWT-based authentication with role-based access control:

- **DST Admin** - `epic-centre` client with `manage_auth` or `manage_users` roles
- **App Admin** - App-specific client with admin roles (e.g., `epictrack-web` with `manage_users`)
- **Regular User** - No admin roles, limited permissions

## Best Practices

1. **Use factory functions** to create test data
2. **Use descriptive test names** that explain what is being tested
3. **Follow AAA pattern** - Arrange, Act, Assert
4. **Test both success and failure cases**
5. **Verify authentication/authorization** is enforced
6. **Use appropriate mocking** - mock external services (Keycloak), not your own code
7. **Clean up after tests** - use session fixture with rollback

## Examples

### Testing a new endpoint

```python
def test_my_new_endpoint(client, auth_header):
    """Test description."""
    # Arrange - set up test data
    app = factory_application_model(**TestApplicationScenarios.get_epic_track_app())

    # Act - make the request
    url = urljoin(API_BASE_URL, f'my-endpoint/{app.id}')
    response = client.get(url, headers=auth_header)

    # Assert - verify the response
    assert response.status_code == HTTPStatus.OK
    assert 'id' in response.json
```

### Testing with different user roles

There are multiple ways to test with different user roles:

**Option 1: Use specific role fixtures**
```python
def test_with_regular_user(client, regular_user_header):
    """Test regular user permissions."""
    url = urljoin(API_BASE_URL, 'applications')
    response = client.get(url, headers=regular_user_header)
    assert response.status_code == HTTPStatus.OK

def test_with_dst_admin(client, dst_admin_header):
    """Test DST admin permissions."""
    url = urljoin(API_BASE_URL, 'users')
    response = client.get(url, headers=dst_admin_header)
    assert response.status_code == HTTPStatus.OK
```

**Option 2: Use pytest markers to override default role**
```python
import pytest
from tests.utilities.factory_scenarios import TestJwtClaims

@pytest.mark.token_info(TestJwtClaims.regular_user_role.value)
def test_regular_user_cannot_access_admin_endpoint(client, auth_header):
    """Test that regular users get 403 on admin endpoints."""
    url = urljoin(API_BASE_URL, 'admin/users')
    response = client.get(url, headers=auth_header)
    assert response.status_code == HTTPStatus.FORBIDDEN
```

**Option 3: Use parametrized auth_header fixture**
```python
@pytest.mark.parametrize('auth_header', [TestJwtClaims.regular_user_role], indirect=True)
def test_with_parametrized_role(client, auth_header):
    """Test using parametrized auth_header."""
    url = urljoin(API_BASE_URL, 'applications')
    response = client.get(url, headers=auth_header)
    assert response.status_code == HTTPStatus.OK
```

**Option 4: Setup custom headers in test (for complex scenarios)**
```python
def test_with_app_admin(client, jwt):
    """Test app admin can only see their app data."""
    headers, claims = setup_app_admin_headers(jwt, app_client_name='epictrack-web')

    url = urljoin(API_BASE_URL, 'users')
    response = client.get(url, headers=headers)
    assert response.status_code == HTTPStatus.OK
```

## References

- **EPIC.submit tests**: `C:\Users\jadms\OneDrive\Desktop\epic-submit\EPIC.submit\submit-api\tests`
- **EPIC.track tests**: `C:\Users\jadms\OneDrive\Desktop\Epic-Track\EPIC.track\epictrack-api\tests`
- **Architecture docs**: `EPIC_CENTRE_ARCHITECTURE.md`
