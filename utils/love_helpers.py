import requests
import time
from typing import Optional, Dict, Any

# iLoveImg API 端点
ILOVEIMG_AUTH_URL = "https://api.iloveimg.com/v1/auth"
ILOVEIMG_UPLOAD_URL = "https://api.iloveimg.com/v1/upload"
ILOVEIMG_TASK_URL = "https://api.iloveimg.com/v1/task"
ILOVEIMG_DOWNLOAD_URL = "https://api.iloveimg.com/v1/download"


class ILoveImgClient:
    """iLoveImg API 客户端"""
    
    def __init__(self, public_key: str):
        self.public_key = public_key
        self.access_token: Optional[str] = None
    
    def get_access_token(self) -> Optional[str]:
        """获取 iLoveImg API access token"""
        try:
            response = requests.get(
                url=ILOVEIMG_AUTH_URL,
                params={"public_key": self.public_key},
                timeout=10
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                return self.access_token
            
            return None
            
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def upload_image(self, image_file) -> Optional[Dict[str, Any]]:
        """上传图片文件"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}"
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
    
    def create_remove_background_task(self, upload_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建移除背景任务"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
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
    
    def poll_task_status(self, task_result: Dict[str, Any], max_attempts: int = 30) -> Optional[Dict[str, Any]]:
        """轮询任务状态直到完成"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        try:
            task_id = task_result.get("task")
            if not task_id:
                return None
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
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
    
    def download_result(self, processed_result: Dict[str, Any]) -> Optional[bytes]:
        """下载处理结果"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        try:
            download_url = processed_result.get("download")
            if not download_url:
                return None
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
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


def remove_background_from_image(image_file, public_key: str) -> Dict[str, Any]:
    """
    完整的图片背景移除流程
    
    Args:
        image_file: 上传的图片文件对象
        public_key: iLoveImg API 公钥
    
    Returns:
        Dict[str, Any]: 包含处理结果的字典
    """
    client = ILoveImgClient(public_key)
    
    # 1. 获取 access token
    if not client.get_access_token():
        return {
            "status": "error",
            "message": "Failed to get access token"
        }
    
    # 2. 上传图片文件
    upload_result = client.upload_image(image_file)
    if not upload_result:
        return {
            "status": "error",
            "message": "Failed to upload image"
        }
    
    # 3. 创建移除背景任务
    task_result = client.create_remove_background_task(upload_result)
    if not task_result:
        return {
            "status": "error",
            "message": "Failed to create remove background task"
        }
    
    # 4. 轮询获取结果
    processed_result = client.poll_task_status(task_result)
    if not processed_result:
        return {
            "status": "error",
            "message": "Task processing failed or timeout"
        }
    
    # 5. 下载结果
    result_data = client.download_result(processed_result)
    if not result_data:
        return {
            "status": "error",
            "message": "Failed to download result"
        }
    
    # 6. 返回成功结果
    return {
        "status": "success",
        "message": "Background removal completed successfully",
        "data": result_data,
        "original_filename": image_file.filename,
        "processed_filename": f"removed_background_{image_file.filename}"
    }
