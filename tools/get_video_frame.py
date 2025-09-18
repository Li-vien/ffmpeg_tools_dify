from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from collections.abc import Generator
from typing import Any
import tempfile
import subprocess
import json
import os
import time

class GetVideoFrame(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        video_file = tool_parameters.get('video')
        frame_type = tool_parameters.get('type', 'start')
        time_seconds = tool_parameters.get('time', 1)
        
        # 验证输入
        if not video_file:
            yield self.create_text_message("No video file provided")
            yield self.create_json_message({
                "status": "error",
                "message": "No video file provided"
            })
            return
            
        if not frame_type:
            yield self.create_text_message("No frame type specified")
            yield self.create_json_message({
                "status": "error",
                "message": "No frame type specified"
            })
            return
        
        # 确保类型是合法的
        valid_types = ["start", "end", "time"]
        if frame_type not in valid_types:
            yield self.create_text_message(f"Unsupported frame type: {frame_type}. Supported types are: {', '.join(valid_types)}")
            yield self.create_json_message({
                "status": "error",
                "message": f"Unsupported frame type: {frame_type}. Supported types are: {', '.join(valid_types)}"
            })
            return
        
        # 验证时间参数
        if frame_type == 'time':
            try:
                time_seconds = float(time_seconds)
                if time_seconds < 0:
                    yield self.create_text_message("Time parameter must be non-negative")
                    yield self.create_json_message({
                        "status": "error",
                        "message": "Time parameter must be non-negative"
                    })
                    return
            except (ValueError, TypeError):
                yield self.create_text_message("Invalid time parameter. Must be a number")
                yield self.create_json_message({
                    "status": "error",
                    "message": "Invalid time parameter. Must be a number"
                })
                return
        
        try:
            # 设置临时文件
            input_file_extension = video_file.extension if video_file.extension else '.mp4'
            
            # 获取原始文件名（不带扩展名）
            orig_filename = os.path.splitext(video_file.filename)[0]
            output_filename = f"{orig_filename}_frame.jpg"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=input_file_extension) as in_temp_file:
                in_temp_file.write(video_file.blob)
                in_temp_path = in_temp_file.name
                
            out_temp_path = os.path.join(tempfile.gettempdir(), output_filename)
            
            try:
                # 根据类型确定提取时间点
                if frame_type == 'start':
                    seek_time = 0
                elif frame_type == 'end':
                    # 先获取视频时长
                    duration_command = [
                        'ffprobe', 
                        '-v', 'quiet',
                        '-print_format', 'json',
                        '-show_format',
                        in_temp_path
                    ]
                    duration_result = subprocess.run(duration_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    
                    if duration_result.returncode != 0:
                        error_msg = f"Failed to get video duration: {duration_result.stderr}"
                        yield self.create_text_message(error_msg)
                        yield self.create_json_message({
                            "status": "error",
                            "message": error_msg
                        })
                        return
                    
                    duration_info = json.loads(duration_result.stdout)
                    duration = float(duration_info.get("format", {}).get("duration", 0))
                    seek_time = max(0, duration - 1)  # 结束前1秒
                elif frame_type == 'time':
                    seek_time = float(time_seconds)
                
                # 执行帧提取
                yield self.create_text_message(f"Extracting frame from video...")
                
                # 使用ffmpeg提取帧
                command = [
                    'ffmpeg',
                    '-i', in_temp_path,
                    '-ss', str(seek_time),
                    '-vframes', '1',
                    '-q:v', '2',  # 高质量
                    '-y',  # 覆盖输出文件
                    out_temp_path
                ]
                
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if result.returncode != 0:
                    error_msg = f"Failed to extract video frame: {result.stderr}"
                    yield self.create_text_message(error_msg)
                    yield self.create_json_message({
                        "status": "error",
                        "message": error_msg
                    })
                    return
                
                # 读取提取的帧文件
                if os.path.exists(out_temp_path):
                    with open(out_temp_path, 'rb') as out_file:
                        frame_data = out_file.read()
                    
                    # 创建结果消息
                    yield self.create_blob_message(
                        frame_data,
                        meta={
                            "filename": output_filename,
                            "mime_type": "image/jpeg",
                        }
                    )
                    
                    yield self.create_json_message({
                        "status": "success",
                        "message": f"Successfully extracted frame from video",
                        "original_filename": video_file.filename,
                        "frame_filename": output_filename,
                        "frame_type": frame_type,
                        "seek_time": seek_time,
                        "frame_size": len(frame_data)
                    })
                    
                    yield self.create_text_message(f"Successfully extracted frame from {video_file.filename} at {seek_time:.2f}s.")
                    
                else:
                    error_msg = "Extracted frame file does not exist"
                    yield self.create_text_message(error_msg)
                    yield self.create_json_message({
                        "status": "error",
                        "message": error_msg
                    })
                
            finally:
                # 清理临时文件
                if os.path.exists(in_temp_path):
                    os.unlink(in_temp_path)
                if os.path.exists(out_temp_path):
                    os.unlink(out_temp_path)
                    
        except Exception as e:
            error_msg = f"Error processing video file: {str(e)}"
            yield self.create_text_message(error_msg)
            yield self.create_json_message({
                "status": "error",
                "message": error_msg
            })