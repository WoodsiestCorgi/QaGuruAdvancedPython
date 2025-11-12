class Server:
    def __init__(self, env: str):
        self.base_url = {
                'dev':  'http://localhost:8002',
                'test': 'http://localhost:8002',
                'prod': 'http://localhost:8002'
                }[env]
