products = []

def list_products():
    return products, 200

def create_product(body):
    for product in products:
        if product["sku"] == body["sku"]:
            return {"error": "sku already exists"}, 409

    product = {"id": len(products) + 1, **body}
    products.append(product)
    return product, 201
