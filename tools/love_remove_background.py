from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from collections.abc import Generator
from typing import Any
import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from utils.love_helpers import remove_background_from_image

class LoveRemoveBackground(Tool):
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        uploaded_image_file = tool_parameters.get('image')
        
        if not uploaded_image_file:
            yield self.create_text_message("No image file provided")
            yield self.create_json_message({
                "status": "error",
                "message": "No image file provided"
            })
            return
        
        try:
            # 获取公钥
            public_key = self.runtime.credentials["love_public_key"]
            
            # 使用帮助函数处理图片背景移除
            result = remove_background_from_image(uploaded_image_file, public_key)
            
            if result["status"] == "success":
                # 返回成功结果
                yield self.create_text_message(result["message"])
                yield self.create_file_message(
                    filename=result["processed_filename"],
                    blob=result["data"],
                    mime_type="image/png"
                )
                yield self.create_json_message({
                    "status": "success",
                    "message": result["message"],
                    "original_filename": result["original_filename"],
                    "processed_filename": result["processed_filename"]
                })
            else:
                # 返回错误结果
                yield self.create_text_message(result["message"])
                yield self.create_json_message({
                    "status": "error",
                    "message": result["message"]
                })
            
        except Exception as processing_error:
            processing_error_message = f"Error processing image file: {str(processing_error)}"
            yield self.create_text_message(processing_error_message)
            yield self.create_json_message({
                "status": "error",
                "message": processing_error_message
            })