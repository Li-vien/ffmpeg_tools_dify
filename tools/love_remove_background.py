from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from collections.abc import Generator
from typing import Any
import requests
import time

# iLoveImg API 端点
ILOVEIMG_AUTH_URL = "https://api.iloveimg.com/v1/auth"
ILOVEIMG_UPLOAD_URL = "https://api.iloveimg.com/v1/upload"
ILOVEIMG_TASK_URL = "https://api.iloveimg.com/v1/task"
ILOVEIMG_DOWNLOAD_URL = "https://api.iloveimg.com/v1/download"

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
            # 1. 获取 access token
            access_token = self._get_access_token()
            if not access_token:
                yield self.create_text_message("Failed to get access token")
                yield self.create_json_message({
                    "status": "error",
                    "message": "Failed to get access token"
                })
                return
            
            # 2. 上传图片文件
            upload_result = self._upload_image(uploaded_image_file, access_token)
            if not upload_result:
                yield self.create_text_message("Failed to upload image")
                yield self.create_json_message({
                    "status": "error",
                    "message": "Failed to upload image"
                })
                return
            
            # 3. 创建移除背景任务
            task_result = self._create_remove_background_task(upload_result, access_token)
            if not task_result:
                yield self.create_text_message("Failed to create remove background task")
                yield self.create_json_message({
                    "status": "error",
                    "message": "Failed to create remove background task"
                })
                return
            
            # 4. 轮询获取结果
            processed_result = self._poll_task_status(task_result, access_token)
            if not processed_result:
                yield self.create_text_message("Task processing failed or timeout")
                yield self.create_json_message({
                    "status": "error",
                    "message": "Task processing failed or timeout"
                })
                return
            
            # 5. 下载结果
            result_data = self._download_result(processed_result, access_token)
            if not result_data:
                yield self.create_text_message("Failed to download result")
                yield self.create_json_message({
                    "status": "error",
                    "message": "Failed to download result"
                })
                return
            
            # 6. 返回结果
            yield self.create_text_message("Background removal completed successfully")
            yield self.create_file_message(
                filename=f"removed_background_{uploaded_image_file.filename}",
                blob=result_data,
                mime_type="image/png"
            )
            yield self.create_json_message({
                "status": "success",
                "message": "Background removal completed successfully",
                "original_filename": uploaded_image_file.filename,
                "processed_filename": f"removed_background_{uploaded_image_file.filename}"
            })
            
        except Exception as processing_error:
            processing_error_message = f"Error processing image file: {str(processing_error)}"
            yield self.create_text_message(processing_error_message)
            yield self.create_json_message({
                "status": "error",
                "message": processing_error_message
            })
    
    def _get_access_token(self) -> str:
        """获取 iLoveImg API access token"""
        try:
            public_key = self.runtime.credentials["love_public_key"]
            
            response = requests.get(
                url=ILOVEIMG_AUTH_URL,
                params={"public_key": public_key},
                timeout=10
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                result = response.json()
                return result.get("access_token")
            
            return None
            
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def _upload_image(self, image_file, access_token: str) -> dict:
        """上传图片文件"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            files = {
                "file": (image_file.filename, image_file.blob, image_file.mime_type)
            }
            
            response = requests.post(
                url=ILOVEIMG_UPLOAD_URL,
                headers=headers,
                files=files,
                timeout=30
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            print(f"Error uploading image: {e}")
            return None
    
    def _create_remove_background_task(self, upload_result: dict, access_token: str) -> dict:
        """创建移除背景任务"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "server_filename": upload_result.get("server_filename"),
                "tool": "removebg"
            }
            
            response = requests.post(
                url=ILOVEIMG_TASK_URL,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
    
    def _poll_task_status(self, task_result: dict, access_token: str, max_attempts: int = 30) -> dict:
        """轮询任务状态直到完成"""
        try:
            task_id = task_result.get("task")
            if not task_id:
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            for attempt in range(max_attempts):
                response = requests.get(
                    url=f"{ILOVEIMG_TASK_URL}/{task_id}",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "Success":
                        return result
                    elif status == "Error":
                        print(f"Task failed: {result.get('message', 'Unknown error')}")
                        return None
                    
                    # 等待 2 秒后重试
                    time.sleep(2)
                else:
                    print(f"Unexpected status code: {response.status_code}")
                    return None
            
            print("Task polling timeout")
            return None
            
        except Exception as e:
            print(f"Error polling task status: {e}")
            return None
    
    def _download_result(self, processed_result: dict, access_token: str) -> bytes:
        """下载处理结果"""
        try:
            download_url = processed_result.get("download")
            if not download_url:
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            response = requests.get(
                url=download_url,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.content
            
            return None
            
        except Exception as e:
            print(f"Error downloading result: {e}")
            return None