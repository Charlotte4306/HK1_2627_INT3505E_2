URL = "/api/v1/books"

def get(client, **params):
    res = client.get(URL, query_string=params)
    return res.status_code, res.get_json()

#Đi hết các trang cursor, trả về danh sách id theo thứ tự
def walk_cursor(client, **params):
    ids, cursor = [], None
    while True:
        query = {**params, "strategy": "cursor"}
        if cursor:
            query["cursor"] = cursor
        status, body = get(client, **query)
        assert status == 200
        ids += [b["id"] for b in body["data"]]
        cursor = body["pagination"]["next_cursor"]
        if not body["pagination"]["has_more"]:
            assert cursor is None
            return ids


def test_default_strategy_is_offset(client):
    status, body = get(client)
    assert status == 200
    assert body["pagination"]["strategy"] == "offset"
    assert body["pagination"]["total"] == 8
    assert len(body["data"]) == 8

def test_offset_pages(client):
    _, page1 = get(client, strategy="offset", limit=3, offset=0)
    _, page3 = get(client, strategy="offset", limit=3, offset=6)
    assert [b["id"] for b in page1["data"]] == ["book_1", "book_2", "book_3"]
    assert page1["pagination"]["has_next"] is True
    assert len(page3["data"]) == 2
    assert page3["pagination"]["has_next"] is False

def test_offset_negative(client):
    status, _ = get(client, strategy="offset", offset=-1)
    assert status == 400


def test_cursor_walks_all_books_without_duplicates(client):
    ids = walk_cursor(client, limit=3)
    assert len(ids) == 8
    assert len(set(ids)) == 8

def test_cursor_matches_offset_order(client):
    sort = "-price,title"
    _, full = get(client, strategy="offset", sort=sort, limit=100)
    expected = [b["id"] for b in full["data"]]
    for limit in (1, 2, 3, 5):
        assert walk_cursor(client, sort=sort, limit=limit) == expected

def test_cursor_sort_changed(client):
    _, body = get(client, strategy="cursor", sort="price", limit=2)
    cursor = body["pagination"]["next_cursor"]
    status, body = get(client, strategy="cursor", sort="-price", cursor=cursor)
    assert status == 400
    assert body["error"] == "sort_changed"

def test_cursor_invalid(client):
    status, body = get(client, strategy="cursor", cursor="abc!!!")
    assert status == 400
    assert body["error"] == "invalid_cursor"


def test_genre_filter(client):
    _, body = get(client, genre="novel")
    assert body["pagination"]["total"] == 3
    assert all(b["category"]["slug"] == "novel" for b in body["data"])

def test_genre_multiple(client):
    _, body = get(client, genre="tech,novel")
    assert body["pagination"]["total"] == 8

def test_genre_unknown(client):
    _, body = get(client, genre="horror")
    assert body["data"] == []
    assert body["pagination"]["total"] == 0

def test_genre_with_cursor(client):
    ids = walk_cursor(client, genre="tech", sort="-price,title", limit=2)
    assert len(ids) == 5


def test_sort_multi_key(client):
    _, body = get(client, sort="-price,title", limit=100)
    rows = [(b["price"]["amount"], b["title"]) for b in body["data"]]
    #price giảm dần, cùng price thì title tăng dần
    assert rows == sorted(rows, key=lambda r: (-r[0], r[1]))
    assert rows[0] == (520000, "Design Patterns")
    assert rows[1] == (520000, "Refactoring")

def test_sort_mixed_direction(client):
    _, body = get(client, sort="price,-stock", limit=100)
    rows = [(b["price"]["amount"], b["inStock"]) for b in body["data"]]
    #60000: Chí Phèo (stock 25) đứng trước Dế Mèn (stock 0)
    assert rows[0] == (60000, True)
    assert rows[1] == (60000, False)

def test_sort_bad_field(client):
    status, body = get(client, sort="author")
    assert status == 400
    assert body["error"] == "bad_sort"

def test_sort_duplicate_field(client):
    status, _ = get(client, sort="price,-price")
    assert status == 400


def test_bad_strategy(client):
    status, body = get(client, strategy="page")
    assert status == 400
    assert body["error"] == "bad_strategy"

def test_limit_too_small(client):
    status, _ = get(client, limit=0)
    assert status == 400

def test_limit_capped(client):
    _, body = get(client, limit=1000)
    assert body["pagination"]["limit"] == 100
    
def test_cursor_sort_changed_different_keys(client):
    _, body = get(client, strategy="cursor", sort="-price,title", limit=3)
    cursor = body["pagination"]["next_cursor"]
    status, body = get(client, strategy="cursor", sort="price", cursor=cursor)
    assert status == 400
    assert body["error"] == "sort_changed"