
class DeploymentError(Exception):
    def __init__(self, message: str, provider: str = None, error_code: str = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(self.message)

class GitError(Exception):
    def __init__(self, message: str, repo_url: str = None):
        self.message = message
        self.repo_url = repo_url
        super().__init__(self.message)

class BuildError(Exception):
    def __init__(self, message: str, framework: str = None, command: str = None):
        self.message = message
        self.framework = framework
        self.command = command
        super().__init__(self.message)

class CredentialsError(Exception):
    def __init__(self, message: str, provider: str = None):
        self.message = message
        self.provider = provider
        super().__init__(self.message)

class AnalysisError(Exception):
    def __init__(self, message: str, project_path: str = None):
        self.message = message
        self.project_path = project_path
        super().__init__(self.message)

class ConfigurationError(Exception):
    def __init__(self, message: str, config_key: str = None):
        self.message = message
        self.config_key = config_key
        super().__init__(self.message)