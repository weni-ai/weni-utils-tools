"""
ProxyRequest - Class for making proxy requests to the VTEX API.
"""

from typing import Dict, Any, Optional

from weni.context import Context

import requests

RETAIL_URL = "https://retailsetup.weni.ai"

class ProxyRequest(Context):
    """
    Class for making proxy requests to the VTEX API.
    """
    def __init__(self, context: Context):
        super().__init__(
            parameters=context.parameters,
            globals=context.globals,
            contact=context.contact,
            project=context.project,
            constants=context.constants,
            credentials=context.credentials,
        )

    def make_proxy_request(
        self,
        path: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict:
        """
        Make a proxy request to the VTEX API.

        Args:
            path: VTEX API path
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to forward to VTEX API
            body: Request body data to send
            timeout: Request timeout in seconds (default: 30)

        Returns:
            Dictionary with the API response

        Raises:
            ValueError: If auth_token is not found in context
            requests.exceptions.HTTPError: If the API returns an error status
            requests.exceptions.Timeout: If the request times out
            requests.exceptions.RequestException: For other request failures

        Example:
            response = make_proxy_request(
                context=context,
                path="api/catalog/pvt/product/123",
                method="GET"
            )
        """
        jwt_token = self.project.get("auth_token")
        if not jwt_token:
            raise ValueError("auth_token not found in context.project")

        proxy_url = f"{RETAIL_URL}/vtex/proxy/"

        body_request = self._format_body_proxy_request(body=body, method=method, headers=headers, path=path)

        headers_request = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {jwt_token}",
        }

        response = requests.post(
            proxy_url,
            json=body_request,
            timeout=timeout,
            headers=headers_request
        )
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Include the response content in the error for easier debugging
            error_detail = {
                "status_code": response.status_code,
                "error": str(e),
                "response_text": response.text,
            }
            try:
                error_detail["response_json"] = response.json()
            except Exception:
                pass
            raise requests.exceptions.HTTPError(
                f"HTTP {response.status_code}: {error_detail}",
                response=response
            ) from e

        return response.json()

    def _format_body_proxy_request(
        self,
        body: Optional[Dict[str, Any]],
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Format the body of the proxy request.

        Args:
            body: Request body data
            method: HTTP method
            path: API path
            headers: Additional headers to forward

        Returns:
            Formatted body dictionary for the proxy request
        """
        body_request: Dict[str, Any] = {
            "method": method,
            "path": path,
        }

        if body:
            body_request["data"] = body

        if headers:
            body_request["headers"] = headers

        return body_request