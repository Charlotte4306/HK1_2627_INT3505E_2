from itertools import count
from threading import Lock

USERS = {
    1: {"first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"},
    2: {"first_name": "Trang", "last_name": "Trần", "email": "b@vnu.vn"},
}
_next_id = count(max(USERS) + 1)
_users_lock = Lock()


def get_user(uid):
    return USERS.get(uid)


def create_user(first_name, last_name, email):
    user = {"first_name": first_name, "last_name": last_name, "email": email}
    with _users_lock:
        uid = next(_next_id)
        USERS[uid] = user
    return uid, user
