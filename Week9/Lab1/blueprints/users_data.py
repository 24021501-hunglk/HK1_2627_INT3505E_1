users = [
    {
        "id": 1,
        "f": "A",
        "l": "B",
        "email": "abcd@example.com"
    },
    {
        "id": 2,
        "f": "C",
        "l": "D",
        "email": "cdef@example.com"
    },
    {
        "id": 3,
        "f": "E",
        "l": "F",
        "email": "efgh@example.com"
    }
]

def get_user(uid):
    return next((u for u in users if u["id"] == uid), None)