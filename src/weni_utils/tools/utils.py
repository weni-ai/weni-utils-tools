from typing import Optional
from urllib.parse import urlencode




class Utils:
    """Backward-compatible namespace. Prefer create_path_order_id()."""

    @staticmethod
    def create_path_order_id(
        order_id: Optional[str] = None,
        document: Optional[str | int] = None,
        email: Optional[str] = None,
        per_page: Optional[int] = None,
        seller_name: Optional[str] = None,
        sales_channel: Optional[int] = None,
    ) -> str:
        """Build VTEX OMS orders API path by order id, document or email.

        Only one of order_id, document or email should be provided.
        per_page, seller_name and sales_channel apply only to list endpoints (document/email).
        """
        if order_id:
            path = f"/api/oms/pvt/orders/{order_id}"
            return path

        if document is not None:
            doc_str = str(document).replace("-", "").replace(".", "").strip()
            path = f"/api/oms/pvt/orders/?q={doc_str}"
        elif email:
            if "@" not in email or "." not in email:
                raise ValueError("Invalid email.")
            path = f"/api/oms/pvt/orders/?q={email}"
        else:
            return ""

        # Query params only for list endpoint (path already contains ?)
        params = {}
        if per_page is not None:
            params["per_page"] = per_page
        if seller_name:
            params["seller_name"] = seller_name
        if sales_channel is not None:
            params["sales_channel"] = sales_channel

        if params:
            path += ("&" if "?" in path else "?") + urlencode(params)

        return path

