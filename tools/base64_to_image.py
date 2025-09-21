
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from collections.abc import Generator
from typing import Any
import base64
import re

class Base64ToImage(Tool):
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        base64_image_string = tool_parameters.get('base64Image')
        
        # 验证输入
        if not base64_image_string:
            yield self.create_text_message("No base64 image string provided")
            yield self.create_json_message({
                "status": "error",
                "message": "No base64 image string provided"
            })
            return
        
        try:
            # 解析data URL格式: data:image/png;base64,iVBORw0KGgo...
            # 使用正则表达式提取MIME类型和base64数据
            data_url_pattern = r'data:image/([^;]+);base64,(.+)'
            match = re.match(data_url_pattern, base64_image_string)
            
            if not match:
                # 如果不是data URL格式，尝试直接解码base64
                try:
                    image_data = base64.b64decode(base64_image_string)
                    mime_type = "image/png"  # 默认类型
                    file_extension = "png"
                except Exception as decode_error:
                    error_msg = f"Invalid base64 string format: {str(decode_error)}"
                    yield self.create_text_message(error_msg)
                    yield self.create_json_message({
                        "status": "error",
                        "message": error_msg
                    })
                    return
            else:
                # 从data URL中提取信息
                image_format = match.group(1).lower()
                base64_data = match.group(2)
                
                # 确定MIME类型和文件扩展名
                mime_type_map = {
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'gif': 'image/gif',
                    'bmp': 'image/bmp',
                    'webp': 'image/webp'
                }
                
                mime_type = mime_type_map.get(image_format, 'image/png')
                file_extension = image_format if image_format in mime_type_map else 'png'
                
                # 解码base64数据
                try:
                    image_data = base64.b64decode(base64_data)
                except Exception as decode_error:
                    error_msg = f"Failed to decode base64 data: {str(decode_error)}"
                    yield self.create_text_message(error_msg)
                    yield self.create_json_message({
                        "status": "error",
                        "message": error_msg
                    })
                    return
            
            # 验证解码后的数据不为空
            if not image_data:
                error_msg = "Decoded image data is empty"
                yield self.create_text_message(error_msg)
                yield self.create_json_message({
                    "status": "error",
                    "message": error_msg
                })
                return
            
            # 生成输出文件名
            output_filename = f"converted_image.{file_extension}"
            
            # 创建blob消息返回图片数据
            yield self.create_blob_message(
                image_data,
                meta={
                    "filename": output_filename,
                    "mime_type": mime_type,
                }
            )
            
            yield self.create_json_message({
                "status": "success",
                "message": "Successfully converted base64 string to image",
                "output_filename": output_filename,
                "mime_type": mime_type,
                "image_size": len(image_data)
            })
            
            yield self.create_text_message(f"Successfully converted base64 string to {output_filename} ({len(image_data)} bytes)")
            
        except Exception as e:
            error_msg = f"Error processing base64 image: {str(e)}"
            yield self.create_text_message(error_msg)
            yield self.create_json_message({
                "status": "error",
                "message": error_msg
            })
        