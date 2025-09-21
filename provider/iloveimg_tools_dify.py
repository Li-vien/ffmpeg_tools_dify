from typing import Any
import os

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class IloveimgToolsDifyProvider(ToolProvider):
    
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            # 检查环境变量中是否配置了 LOVE_PUBLIC_KEY
            love_public_key = os.getenv('LOVE_PUBLIC_KEY')
            if not love_public_key:
                raise ToolProviderCredentialValidationError("LOVE_PUBLIC_KEY environment variable is not configured")
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))