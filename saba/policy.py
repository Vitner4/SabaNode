

class Policy:
    def __init__(self, policy: dict = None):
        self.policy = policy if policy is not None else self.default()

    @staticmethod
    def default() -> dict:
        return {
            "sync": {
                "source": "child",
                "destination": "main"
            },
            "actions": [
                "add",
                "update"
            ]
        }