import os

from dotenv import load_dotenv
from weni.context import Context

from weni_utils.tools.proxy import ProxyRequest

load_dotenv()

context = Context(
    parameters={"document": "12345678900"},
    globals={},
    contact={},
    project={"auth_token": os.getenv("AUTH_TOKEN", "mock-token")},
    constants={},
    credentials={},
)

proxy = ProxyRequest(context)

document = context.parameters.get("document")
response = proxy.make_proxy_request(
    path=f"api/oms/pvt/orders?q={document}",
    method="GET",
)

print(response)
