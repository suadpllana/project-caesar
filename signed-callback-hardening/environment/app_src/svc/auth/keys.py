_entries = {
    "k-alpha-1": {
        "secret": "a1f4c0d2b98e47a6b31d5c8e0f27a94b6d3e15c7a08f2b4d6e9c1a3f5b7d0e28",
        "state": "retired",
        "subjects": ["pt-alpha"],
    },
    "k-alpha-2": {
        "secret": "3c7e91b5d04a2f68e1c93b7d5a0f426c8b1e3d5f7a9c0b2d4e6f8a1c3e5d7b90",
        "state": "active",
        "subjects": ["pt-alpha"],
    },
    "k-beta-1": {
        "secret": "77d1e3a5c9048b2f6e0d4a8c1b3f5d7e9a0c2b4d6f8e1a3c5b7d9f0e2a4c6b81",
        "state": "active",
        "subjects": ["pt-beta"],
    },
    "k-gamma-0": {
        "secret": "0b2d4f6a8c1e3b5d7f9a0c2e4b6d8f1a3c5e7b9d0f2a4c6e8b1d3f5a7c9e0b24",
        "state": "revoked",
        "subjects": ["pt-gamma"],
    },
    "k-relay-2": {
        "secret": "e5c3a1908f7d6b4a2c0e8d6b4f2a09c7e5d3b1f9a7c5e3d1b9f7a5c3e1d9b7f5",
        "state": "active",
        "subjects": ["pt-gamma", "pt-delta"],
    },
    "k-delta-1": {
        "secret": "62b0d8f4a6c2e0b8d6f4a2c0e8b6d4f2a0c8e6b4d2f0a8c6e4b2d0f8a6c4e2b0",
        "state": "pending",
        "subjects": ["pt-delta"],
    },
    "k-epsilon-1": {
        "secret": "d9f1b3c5a7e9d1f3b5c7a9e1d3f5b7c9a1e3d5f7b9c1a3e5d7f9b1c3a5e7d9f1",
        "state": "active",
        "subjects": ["pt-epsilon"],
    },
}


def lookup(key_id):
    return _entries.get(key_id)


def ids():
    return sorted(_entries)
