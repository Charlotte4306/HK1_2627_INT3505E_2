"""Demo handlers that return a simulated order without a database."""


def v1_create_order(body):
    return {"account_id": body["account_id"], "status": "created"}


def v2_create_order(body):
    return {"order": {"account_id": body["account_id"], "status": "created"}}
