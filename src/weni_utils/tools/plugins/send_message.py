"""
Send Message Plugin - WhatsApp Broadcast Message Sending

Plugin for sending messages through Weni's WhatsApp Broadcast API.
Supports sending text messages, templates, attachments, quick replies and footers.
"""

from typing import Any, Dict, List, Optional, Union

import requests
import json

from .base import PluginBase


class SendMessage(PluginBase):
    """
    Message sending plugin using Weni's WhatsApp Broadcast API.

    This plugin allows sending messages through Weni's broadcast API,
    supporting different types of content and formatting.

    Features:
        - Simple text message sending
        - Template sending with dynamic variables
        - Attachments (images, PDFs, documents)
        - Quick replies (quick response buttons)
        - Custom footers
        - Flexible authentication (Token or JWT)

    Args:
        weni_token: Weni authentication token for external API
        weni_jwt_token: JWT authentication token for internal API
        weni_api_url_external: External broadcast API URL
        weni_api_url_internal: Internal broadcast API URL
        timeout: HTTP request timeout in seconds (default: 30)
        channel_uuid: WhatsApp channel UUID for sending messages

    """

    name = "send_message"

    def __init__(
        self,
        weni_token: Optional[str] = None,
        weni_jwt_token: Optional[str] = None,
        weni_api_url_external: str = "https://flows.weni.ai/api/v2/whatsapp_broadcasts.json",
        weni_api_url_internal: str = "https://flows.weni.ai/api/v2/internals/whatsapp_broadcasts",
        timeout: int = 30,
        channel_uuid: Optional[str] = "",
    ):
        """
        Initialize the message sending plugin.

        Args:
            weni_token: Weni authentication token for external API.
                       If provided, will be used for external API authentication.
            weni_jwt_token: JWT authentication token for internal API.
                           If provided with weni_token=None, will be used for internal API.
            weni_api_url_external: Weni's external broadcast API URL.
            weni_api_url_internal: Weni's internal broadcast API URL.
            timeout: HTTP request timeout in seconds (default: 30).
            channel_uuid: WhatsApp channel UUID where messages will be sent.
                         Must be provided for messages to be sent correctly.

        Note:
            At least one token (weni_token or weni_jwt_token) must be provided.
            channel_uuid is required for sending messages.
        """
        if not weni_token and not weni_jwt_token:
            raise ValueError(
                "At least one authentication token must be provided "
                "(weni_token or weni_jwt_token)"
            )

        self.weni_token = weni_token
        self.weni_jwt_token = weni_jwt_token
        self.weni_api_url_external = weni_api_url_external
        self.weni_api_url_internal = weni_api_url_internal
        self.channel_uuid = channel_uuid or ""
        self.timeout = timeout

    def send_message(
        self,
        message: str,
        contact_urn: str,
        variables: List[str],
        attachments: Optional[List[Union[str, Dict[str, Any]]]] = None,
        footer: Optional[str] = None,
        quick_replies: Optional[List[Union[str, Dict[str, Any]]]] = None,
        template_uuid: Optional[str] = None,
        locale: str = "pt_BR",
    ) -> Dict[str, Any]:
        """
        Send a message via WhatsApp Broadcast.

        Main method for sending messages. Supports different content types:
        text messages, templates, attachments, quick replies and footers.

        Args:
            message: Message text to be sent. Can be empty if using template.
            contact_urn: Contact URN in format "whatsapp:5511999999999".
            variables: List of variables for template substitution.
                      Example: ["John", "$100.00"] for template "Hello {{1}}, your order {{2}}".
            attachments: Optional list of attachments. Can be list of URLs (str) or
                        list of dictionaries with attachment info.
            footer: Optional footer text for the message.
            quick_replies: Optional list of quick replies (quick response buttons).
                          Can be list of strings or list of dictionaries.
            template_uuid: Optional template UUID to use. If provided,
                          message will be sent as template.
            locale: Template locale (default: "pt_BR").

        Returns:
            Dict containing API response with possible fields:
                - success: bool indicating success (when there's an error)
                - error: str with error message (when there's an error)
                - status_code: int with HTTP code (when there's HTTP error)
                - response: str with API response (when there's HTTP error)
                - url: str with request URL (when there's an error)
                - API JSON response data (when successful)

        Raises:
            ValueError: If contact_urn is empty or channel_uuid is not configured.
        """
        if not contact_urn:
            raise ValueError("contact_urn cannot be empty")

        if not self.channel_uuid:
            raise ValueError("channel_uuid must be configured in __init__ to send messages")

        return self.send_broadcast_external(
            message,
            contact_urn,
            variables,
            attachments,
            footer,
            quick_replies,
            template_uuid,
            locale,
        )

    def send_broadcast_external(
        self,
        message: str,
        contact_urn: str,
        variables: List[str],
        attachments: Optional[List[Union[str, Dict[str, Any]]]] = None,
        footer: Optional[str] = None,
        quick_replies: Optional[List[Union[str, Dict[str, Any]]]] = None,
        template_uuid: Optional[str] = None,
        locale: str = "pt_BR",
    ) -> Dict[str, Any]:
        """
        Send message using WhatsApp Broadcast API (internal method).

        This method processes and formats data before sending
        to Weni's API.

        Args:
            message: Message text.
            contact_urn: Contact URN.
            variables: List of variables for templates.
            attachments: Optional list of attachments.
            footer: Optional footer text.
            quick_replies: Optional list of quick replies.
            template_uuid: Optional template UUID.
            locale: Template locale.

        Returns:
            Dict with API response or error information.
        """
        # Format attachments if provided
        formatted_attachments = []
        if attachments:
            formatted_attachments = self.format_attachments(attachments)

        # Format template if provided
        template = None
        if template_uuid:
            template = self.format_template(template_uuid, variables, locale)

        # Format complete payload
        payload = self.format_payload(
            message=message,
            template=template,
            attachments=formatted_attachments,
            contact_urn=contact_urn,
            footer=footer,
            quick_replies=quick_replies,
        )

        # Send request and return response
        response = self.request_broadcast(payload)
        return response

    def format_payload(
        self,
        message: Optional[str] = "",
        attachments: Optional[List[str]] = None,
        contact_urn: Optional[str] = "",
        footer: Optional[str] = None,
        quick_replies: Optional[List[Union[str, Dict[str, Any]]]] = None,
        template: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Format the payload for message sending.

        Creates the data structure in the format expected by WhatsApp Broadcast API.

        Args:
            message: Message text.
            attachments: List of formatted attachments.
            contact_urn: Contact URN.
            footer: Footer text.
            quick_replies: List of quick replies.
            template: Dictionary with template information.

        Returns:
            Dict with formatted payload in API expected format.

        Note:
            The returned payload is a Python dictionary, not a JSON string.
            JSON serialization is done in the request_broadcast method.
        """
        if attachments is None:
            attachments = []

        payload = {
            "urns": [contact_urn],
            "channel": self.channel_uuid,
            "msg": {
                "text": message or "",
                "attachments": attachments,
            },
        }

        # Add optional fields only if provided
        if template:
            payload["msg"]["template"] = template

        if footer:
            payload["msg"]["footer"] = footer

        if quick_replies:
            payload["msg"]["quick_replies"] = quick_replies

        return payload

    def format_template(
        self, template_uuid: str, variables: List[str], locale: str = "pt_BR"
    ) -> Dict[str, Any]:
        """
        Format template for message sending.

        Creates the template data structure in the format expected by the API.

        Args:
            template_uuid: Template UUID registered in Weni.
            variables: List of variables for template substitution.
                      Variable order must match template order.
            locale: Template locale (default: "pt_BR").
                   Examples: "pt_BR", "en_US", "es_ES".

        Returns:
            Dict with formatted template structure:
                {
                    "uuid": str,
                    "variables": List[str],
                    "locale": str
                }

        """
        return {"uuid": template_uuid, "variables": variables, "locale": locale}

    def format_attachments(self, attachments: List[Union[str, Dict[str, Any]]]) -> List[str]:
        """
        Format attachments for message sending.

        Converts URLs or attachment dictionaries to the format expected by API:
        "mime/type:url". Automatically detects MIME type based on file extension
        or uses type provided in dictionary.

        Args:
            attachments: List of attachments. Can contain:
                       - Strings with file URLs
                       - Dictionaries with format {"url": str, "mime_type": str, ...}

        Returns:
            List of strings in format "mime/type:url" for each valid attachment.

        Supported MIME Types:
            - Images: image/png, image/jpg, image/jpeg, image/gif
            - Documents: application/pdf, application/doc, application/docx
            - Spreadsheets: application/xls, application/xlsx
        """
        formatted_attachments = []

        # Extension to MIME type mapping
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        for attachment in attachments:
            # If dictionary, extract URL and MIME type
            if isinstance(attachment, dict):
                url = attachment.get("url", "")
                mime_type = attachment.get("mime_type", "")
                if not url:
                    continue
                if mime_type:
                    formatted_attachments.append(f"{mime_type}:{url}")
                    continue
                # If no mime_type, try to detect by extension
                attachment = url

            # Convert to string and normalize
            url = str(attachment).strip()
            if not url:
                continue

            # Detect MIME type by extension (case-insensitive)
            url_lower = url.lower()
            mime_type = None

            for ext, mime in mime_types.items():
                if url_lower.endswith(ext):
                    mime_type = mime
                    break

            if mime_type:
                formatted_attachments.append(f"{mime_type}:{url}")
            else:
                # If can't detect, use as generic link
                # or can throw a warning (commented for compatibility)
                formatted_attachments.append(f"application/octet-stream:{url}")

        return formatted_attachments

    def request_broadcast(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send request to WhatsApp Broadcast API with error handling.

        Performs HTTP POST request to Weni's API and handles different types
        of errors that can occur during communication.

        Args:
            payload: Dictionary with formatted payload for sending.
                   Will be serialized to JSON automatically by requests.

        Returns:
            Dict with API response. On success, returns response JSON.
            On error, returns a dict with:
                - success: False
                - error: str with error message
                - status_code: int (only for HTTP errors)
                - response: str (only for HTTP errors, contains API response)
                - url: str with request URL

        """
        # Determine URL and headers based on available token
        if self.weni_token:
            url = self.weni_api_url_external
            headers = {
                "Authorization": f"Token {self.weni_token}",
                "Content-Type": "application/json",
            }
        elif self.weni_jwt_token:
            url = self.weni_api_url_internal
            headers = {
                "Authorization": f"Bearer {self.weni_jwt_token}",
                "Content-Type": "application/json",
            }
        else:
            # This case shouldn't happen due to validation in __init__
            return {
                "success": False,
                "error": "No authentication token configured",
                "url": "",
            }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Timeout trying to connect to API after {self.timeout}s",
                "url": url,
            }

        except requests.exceptions.HTTPError as http_err:
            status_code = None
            response_text = None

            if hasattr(http_err, "response") and http_err.response is not None:
                status_code = http_err.response.status_code
                try:
                    response_text = http_err.response.text
                except Exception:
                    response_text = "Could not read response"

            return {
                "success": False,
                "error": f"HTTP Error {status_code}: {str(http_err)}",
                "status_code": status_code,
                "response": response_text,
                "url": url,
            }

        except requests.exceptions.RequestException as err:
            return {
                "success": False,
                "error": f"Request error: {str(err)}",
                "url": url,
            }

        except json.JSONDecodeError as json_err:
            return {
                "success": False,
                "error": f"Error decoding JSON response: {str(json_err)}",
                "url": url,
            }

        except Exception as ex:
            return {
                "success": False,
                "error": f"Unexpected error: {str(ex)}",
                "url": url,
            }
