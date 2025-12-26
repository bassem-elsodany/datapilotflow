#!/usr/bin/env python3
"""
Confluence Test Data Setup Script

This script creates sample spaces and pages in a local Confluence instance
for testing the DataPilotFlow Confluence integration.

Prerequisites:
1. Confluence must be running (via docker-compose)
2. Admin account must be created (from setup wizard)
3. API token must be generated from admin panel

Usage:
    python3 confluence_test_data_setup.py \\
        --url http://localhost:8090 \\
        --username admin@example.com \\
        --api-token YOUR_API_TOKEN

Or set environment variables:
    export CONFLUENCE_URL=http://localhost:8090
    export CONFLUENCE_USERNAME=admin@example.com
    export CONFLUENCE_API_TOKEN=YOUR_API_TOKEN
    python3 confluence_test_data_setup.py
"""

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: requests library is required")
    print("Install with: pip install requests")
    sys.exit(1)


@dataclass
class ConfluenceCredentials:
    """Confluence API credentials."""
    url: str
    username: str
    api_token: str

    @property
    def auth(self):
        """Return tuple for basic auth."""
        return (self.username, self.api_token)

    @property
    def headers(self):
        """Return common headers for API requests."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


class ConfluenceTestDataSetup:
    """Create test spaces and pages in Confluence."""

    def __init__(self, credentials: ConfluenceCredentials):
        """Initialize with Confluence credentials."""
        self.creds = credentials
        self.session = requests.Session()
        self.session.auth = self.creds.auth
        self.session.headers.update(self.creds.headers)
        self.created_spaces = []
        self.created_pages = []

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make authenticated request to Confluence API."""
        url = f"{self.creds.url}/rest/api/space" if "space" in endpoint else \
              f"{self.creds.url}/rest/api/content" if "content" in endpoint else \
              f"{self.creds.url}/{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs, timeout=30)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.RequestException as e:
            print(f"Error: {method} {url} - {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def _check_confluence_running(self) -> bool:
        """Check if Confluence is running and accessible."""
        try:
            response = self.session.get(
                f"{self.creds.url}/status",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error: Cannot connect to Confluence at {self.creds.url}")
            print(f"Details: {e}")
            return False

    def _check_authentication(self) -> bool:
        """Check if authentication credentials are valid."""
        try:
            response = self.session.get(
                f"{self.creds.url}/rest/api/user/current",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error: Authentication failed")
            print(f"Check that your API token is valid")
            return False

    def create_space(self, key: str, name: str, description: str = "") -> Optional[dict]:
        """
        Create a Confluence space.

        Args:
            key: Space key (e.g., 'TECH')
            name: Space name (e.g., 'Technical Documentation')
            description: Space description

        Returns:
            Space data dict or None if failed
        """
        payload = {
            "key": key,
            "name": name,
            "description": {"plain": {"value": description or f"{name} space"}},
        }

        try:
            url = f"{self.creds.url}/rest/api/space"
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            space = response.json()
            self.created_spaces.append(space)
            print(f"✓ Created space: {name} ({key})")
            return space
        except Exception as e:
            print(f"✗ Failed to create space {key}: {e}")
            return None

    def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_page_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Create a Confluence page.

        Args:
            space_key: Space key where page will be created
            title: Page title
            content: Page content in storage format (XHTML)
            parent_page_id: Optional parent page ID for nested pages

        Returns:
            Page data dict or None if failed
        """
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage",
                }
            },
        }

        if parent_page_id:
            payload["ancestors"] = [{"id": parent_page_id}]

        try:
            url = f"{self.creds.url}/rest/api/content"
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            page = response.json()
            self.created_pages.append(page)
            print(f"  ✓ Created page: {title}")
            return page
        except Exception as e:
            print(f"  ✗ Failed to create page {title}: {e}")
            return None

    def setup_tech_space(self) -> bool:
        """Set up TECH space with sample pages."""
        print("\n📚 Setting up TECH space...")
        space = self.create_space(
            "TECH",
            "Technical Documentation",
            "Technical documentation and architecture guides"
        )
        if not space:
            return False

        # Getting Started page
        getting_started = """<ac:rich-text-body>
<h1>Getting Started with Our Platform</h1>
<p>Welcome to the technical documentation. This guide will help you get started quickly.</p>

<h2>Prerequisites</h2>
<ul>
<li>Python 3.11 or higher</li>
<li>Docker and Docker Compose</li>
<li>Git for version control</li>
</ul>

<h2>Installation</h2>
<pre><code class="language-bash">git clone https://github.com/example/project.git
cd project
docker-compose up -d</code></pre>

<h2>Configuration</h2>
<p>Create a <code>.env</code> file with the following variables:</p>
<pre><code>API_URL=http://localhost:8000
DEBUG=true
LOG_LEVEL=info</code></pre>

<h2>Next Steps</h2>
<ul>
<li>Read <a href="#advanced">Advanced Topics</a></li>
<li>Check the <a href="#api">REST API Reference</a></li>
<li>Review <a href="#deployment">Deployment Guide</a></li>
</ul>

<div data-macro-name="info">
<div class="confluence-information-macro-body">
<p>For support, visit our Slack channel or email support@example.com</p>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page("TECH", "Getting Started", getting_started)

        # Advanced Topics page
        advanced_topics = """<ac:rich-text-body>
<h1>Advanced Topics</h1>
<p>This section covers advanced features and configurations.</p>

<h2>Architecture Overview</h2>
<table>
<tr><th>Component</th><th>Purpose</th><th>Technology</th></tr>
<tr><td>API Server</td><td>HTTP API endpoints</td><td>Python FastAPI</td></tr>
<tr><td>Database</td><td>Data persistence</td><td>PostgreSQL 15</td></tr>
<tr><td>Cache Layer</td><td>Performance optimization</td><td>Redis</td></tr>
<tr><td>Message Queue</td><td>Async processing</td><td>RabbitMQ</td></tr>
</table>

<h2>Performance Tuning</h2>
<p>Here are key performance optimization strategies:</p>
<ol>
<li><strong>Database Indexing</strong> - Create indexes on frequently queried columns</li>
<li><strong>Caching Strategy</strong> - Use Redis for hot data</li>
<li><strong>Connection Pooling</strong> - Reuse database connections</li>
<li><strong>Load Balancing</strong> - Distribute traffic across multiple instances</li>
</ol>

<h2>Security Best Practices</h2>
<ul>
<li>Always use HTTPS in production</li>
<li>Implement proper authentication and authorization</li>
<li>Validate and sanitize all user inputs</li>
<li>Keep dependencies updated</li>
<li>Use environment variables for sensitive data</li>
</ul>

<div data-macro-name="warning">
<div class="confluence-information-macro-body">
<p>Never commit credentials or API keys to version control</p>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page("TECH", "Advanced Topics", advanced_topics)

        return True

    def setup_docs_space(self) -> bool:
        """Set up DOCS space with user documentation."""
        print("\n📖 Setting up DOCS space...")
        space = self.create_space(
            "DOCS",
            "User Documentation",
            "End-user guides and tutorials"
        )
        if not space:
            return False

        # User Guide page
        user_guide = """<ac:rich-text-body>
<h1>User Guide</h1>
<p>Complete guide for end users of the platform.</p>

<h2>Account Management</h2>
<p>Learn how to manage your account and profile settings.</p>

<h3>Creating an Account</h3>
<ol>
<li>Visit the login page</li>
<li>Click "Sign Up"</li>
<li>Enter your email address</li>
<li>Create a secure password</li>
<li>Verify your email address</li>
</ol>

<h3>Profile Settings</h3>
<p>Update your profile information:</p>
<ul>
<li>Display name</li>
<li>Avatar/Profile picture</li>
<li>Notification preferences</li>
<li>Language preferences</li>
<li>Time zone</li>
</ul>

<h2>Common Tasks</h2>

<h3>Creating a Project</h3>
<pre><code>1. Go to Dashboard
2. Click "New Project"
3. Fill in project details
4. Invite team members
5. Click "Create"</code></pre>

<h3>Sharing Documents</h3>
<p>To share a document with others:</p>
<ol>
<li>Open the document</li>
<li>Click the "Share" button</li>
<li>Enter email addresses of team members</li>
<li>Set permissions (view/edit/admin)</li>
<li>Send invitations</li>
</ol>

<div data-macro-name="tip">
<div class="confluence-information-macro-body">
<p>You can use keyboard shortcuts to speed up your workflow. Press <code>?</code> to view all shortcuts.</p>
</div>
</div>

<h2>Troubleshooting</h2>
<p>Common issues and solutions:</p>

<div class="expand-container">
<span class="expand-control-text">I forgot my password</span>
<div class="expand-content">
<p>Click "Forgot Password" on the login page and follow the email instructions to reset it.</p>
</div>
</div>

<div class="expand-container">
<span class="expand-control-text">I can't access a shared document</span>
<div class="expand-content">
<p>Check that you're logged in with the correct account. Contact the document owner to ensure you have the right permissions.</p>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page("DOCS", "User Guide", user_guide)

        return True

    def setup_api_space(self) -> bool:
        """Set up API space with REST API documentation."""
        print("\n🔌 Setting up API space...")
        space = self.create_space(
            "API",
            "REST API Reference",
            "Complete REST API documentation"
        )
        if not space:
            return False

        # REST API Reference page
        api_reference = """<ac:rich-text-body>
<h1>REST API Reference</h1>
<p>Complete reference for the REST API.</p>

<h2>Authentication</h2>
<p>All API requests require authentication using an API token:</p>
<pre><code class="language-bash">curl -H "Authorization: Bearer YOUR_API_TOKEN" \\
     https://api.example.com/v1/users</code></pre>

<h2>Base URL</h2>
<p><code>https://api.example.com/v1</code></p>

<h2>Common HTTP Status Codes</h2>
<table>
<tr><th>Code</th><th>Meaning</th><th>Example</th></tr>
<tr><td>200</td><td>Success</td><td>GET request completed successfully</td></tr>
<tr><td>201</td><td>Created</td><td>New resource created</td></tr>
<tr><td>400</td><td>Bad Request</td><td>Invalid parameters</td></tr>
<tr><td>401</td><td>Unauthorized</td><td>Invalid or missing API token</td></tr>
<tr><td>403</td><td>Forbidden</td><td>Insufficient permissions</td></tr>
<tr><td>404</td><td>Not Found</td><td>Resource does not exist</td></tr>
<tr><td>500</td><td>Server Error</td><td>Internal server error</td></tr>
</table>

<h2>Endpoints</h2>

<h3>Users Endpoint</h3>
<p><strong>GET</strong> <code>/users</code> - List all users</p>
<pre><code class="language-bash">curl -H "Authorization: Bearer TOKEN" \\
     https://api.example.com/v1/users</code></pre>

<p><strong>POST</strong> <code>/users</code> - Create a new user</p>
<pre><code class="language-bash">curl -X POST \\
     -H "Authorization: Bearer TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{"name":"John","email":"john@example.com"}' \\
     https://api.example.com/v1/users</code></pre>

<p><strong>GET</strong> <code>/users/:id</code> - Get a specific user</p>
<pre><code class="language-bash">curl -H "Authorization: Bearer TOKEN" \\
     https://api.example.com/v1/users/123</code></pre>

<h2>Error Responses</h2>
<p>Errors are returned in JSON format:</p>
<pre><code class="language-json">{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required parameter: email",
    "details": {
      "parameter": "email"
    }
  }
}</code></pre>

<div data-macro-name="note">
<div class="confluence-information-macro-body">
<p>API rate limits: 1000 requests per hour. Check the <code>X-RateLimit-*</code> headers in responses.</p>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page("API", "REST API Reference", api_reference)

        return True

    def run(self) -> bool:
        """Run the complete setup process."""
        print("🚀 Confluence Test Data Setup")
        print("=" * 50)

        # Check connectivity
        print("\nChecking Confluence connectivity...")
        if not self._check_confluence_running():
            print("✗ Confluence is not running or not accessible")
            return False
        print("✓ Confluence is running")

        # Check authentication
        print("\nChecking authentication...")
        if not self._check_authentication():
            print("✗ Authentication failed")
            return False
        print("✓ Authentication successful")

        # Create spaces
        success = True
        success = self.setup_tech_space() and success
        success = self.setup_docs_space() and success
        success = self.setup_api_space() and success

        # Summary
        print("\n" + "=" * 50)
        print("📊 Setup Summary")
        print(f"  Spaces created: {len(self.created_spaces)}")
        print(f"  Pages created: {len(self.created_pages)}")

        if success:
            print("\n✅ Setup completed successfully!")
            print("\nYou can now:")
            print("1. Log in to Confluence at http://localhost:8090")
            print("2. Browse the created spaces: TECH, DOCS, API")
            print("3. Test the DataPilotFlow Confluence integration")
            print("\nTo test with DataPilotFlow:")
            print("1. Create a Confluence credential with:")
            print("   - URL: http://localhost:8090 (or http://confluence:8090 from Docker)")
            print("   - Username: your admin email")
            print("   - API Token: from Confluence admin panel")
            print("2. Create a knowledge source with:")
            print("   - Content Source: Confluence")
            print("   - Extraction Mode: space_pages")
            print("   - Spaces: TECH, DOCS, API")
            print("   - Output Format: Markdown")
            return True
        else:
            print("\n⚠️  Setup completed with some errors")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create test data in Confluence for DataPilotFlow integration testing"
    )
    parser.add_argument(
        "--url",
        default=os.getenv("CONFLUENCE_URL", "http://localhost:8090"),
        help="Confluence URL (default: http://localhost:8090)"
    )
    parser.add_argument(
        "--username",
        default=os.getenv("CONFLUENCE_USERNAME", ""),
        help="Confluence username/email (from environment or arg)"
    )
    parser.add_argument(
        "--api-token",
        default=os.getenv("CONFLUENCE_API_TOKEN", ""),
        help="Confluence API token (from environment or arg)"
    )

    args = parser.parse_args()

    # Validate required parameters
    if not args.username:
        print("Error: --username is required (or set CONFLUENCE_USERNAME)")
        sys.exit(1)

    if not args.api_token:
        print("Error: --api-token is required (or set CONFLUENCE_API_TOKEN)")
        sys.exit(1)

    # Create credentials and run setup
    credentials = ConfluenceCredentials(
        url=args.url,
        username=args.username,
        api_token=args.api_token
    )

    setup = ConfluenceTestDataSetup(credentials)
    success = setup.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
