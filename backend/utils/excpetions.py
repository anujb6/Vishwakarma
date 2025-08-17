"""Custom exceptions for the deployment application"""

class DeploymentError(Exception):
    """Base exception for deployment-related errors"""
    
    def __init__(self, message: str, provider: str = None, error_code: str = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(self.message)

class GitError(Exception):
    """Exception for Git-related operations"""
    
    def __init__(self, message: str, repo_url: str = None):
        self.message = message
        self.repo_url = repo_url
        super().__init__(self.message)

class BuildError(Exception):
    """Exception for build-related errors"""
    
    def __init__(self, message: str, framework: str = None, command: str = None):
        self.message = message
        self.framework = framework
        self.command = command
        super().__init__(self.message)

class CredentialsError(Exception):
    """Exception for credential validation errors"""
    
    def __init__(self, message: str, provider: str = None):
        self.message = message
        self.provider = provider
        super().__init__(self.message)

class AnalysisError(Exception):
    """Exception for code analysis errors"""
    
    def __init__(self, message: str, project_path: str = None):
        self.message = message
        self.project_path = project_path
        super().__init__(self.message)

class ConfigurationError(Exception):
    """Exception for configuration-related errors"""
    
    def __init__(self, message: str, config_key: str = None):
        self.message = message
        self.config_key = config_key
        super().__init__(self.message)