USERS = {
    1: {
        "first_name": "Van",
        "last_name": "Nguyen",
        "email": "a@vnu.vn"
    },
    2: {
        "first_name": "Trang",
        "last_name": "Tran",
        "email": "b@vnu.vn"
    }
}

def get_user(uid):
    return USERS.get(uid)

def create_user(first_name, last_name, email):
    uid = max(USERS.keys(), default=0) + 1

    USERS[uid] = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email
    }

    return {
        "id": uid,
        **USERS[uid]
    }


def email_exists(email):
    return any(
        user["email"].lower() == email.lower()
        for user in USERS.values()
    )