from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from collections.abc import Generator
from typing import Any
import tempfile
import subprocess
import json
import os
import time

class GetVideoFrameList(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        video_file = tool_parameters.get('video')
        gap_time = tool_parameters.get('gap_time', 1)
        count = tool_parameters.get('count', 1)
        
        # 验证输入
        if not video_file:
            yield self.create_text_message("No video file provided")
            yield self.create_json_message({
                "status": "error",
                "message": "No video file provided"
            })
            return
            
        # 验证间隔时间参数
        try:
            gap_time = float(gap_time)
            if gap_time <= 0:
                yield self.create_text_message("Gap time must be positive")
                yield self.create_json_message({
                    "status": "error",
                    "message": "Gap time must be positive"
                })
                return
        except (ValueError, TypeError):
            yield self.create_text_message("Invalid gap time parameter. Must be a number")
            yield self.create_json_message({
                "status": "error",
                "message": "Invalid gap time parameter. Must be a number"
            })
            return
        
        # 验证数量参数
        try:
            count = int(count)
            if count <= 0:
                yield self.create_text_message("Count must be positive")
                yield self.create_json_message({
                    "status": "error",
                    "message": "Count must be positive"
                })
                return
            if count > 100:  # 限制最大数量避免过多文件
                yield self.create_text_message("Count cannot exceed 100")
                yield self.create_json_message({
                    "status": "error",
                    "message": "Count cannot exceed 100"
                })
                return
        except (ValueError, TypeError):
            yield self.create_text_message("Invalid count parameter. Must be an integer")
            yield self.create_json_message({
                "status": "error",
                "message": "Invalid count parameter. Must be an integer"
            })
            return
        
        try:
            # 设置临时文件
            input_file_extension = video_file.extension if video_file.extension else '.mp4'
            
            # 获取原始文件名（不带扩展名）
            orig_filename = os.path.splitext(video_file.filename)[0]
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=input_file_extension) as in_temp_file:
                in_temp_file.write(video_file.blob)
                in_temp_path = in_temp_file.name
                
            try:
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
                
                if duration <= 0:
                    error_msg = "Invalid video duration"
                    yield self.create_text_message(error_msg)
                    yield self.create_json_message({
                        "status": "error",
                        "message": error_msg
                    })
                    return
                
                # 计算提取时间点
                if count == 1:
                    # 如果只要1帧，提取中间帧
                    seek_times = [duration / 2]
                else:
                    # 计算多个时间点
                    if count * gap_time > duration:
                        # 如果间隔时间太大，调整间隔时间
                        gap_time = duration / count
                    
                    seek_times = []
                    for i in range(count):
                        seek_time = i * gap_time
                        if seek_time < duration:
                            seek_times.append(seek_time)
                
                # 执行批量帧提取
                yield self.create_text_message(f"Extracting {len(seek_times)} frames from video...")
                
                extracted_frames = []
                temp_dir = tempfile.gettempdir()
                
                for i, seek_time in enumerate(seek_times):
                    output_filename = f"{orig_filename}_frame_{i+1:03d}.jpg"
                    out_temp_path = os.path.join(temp_dir, output_filename)
                    
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
                    
                    if result.returncode == 0 and os.path.exists(out_temp_path):
                        with open(out_temp_path, 'rb') as out_file:
                            frame_data = out_file.read()
                        
                        # 创建帧消息
                        yield self.create_blob_message(
                            frame_data,
                            meta={
                                "filename": output_filename,
                                "mime_type": "image/jpeg",
                            }
                        )
                        
                        extracted_frames.append({
                            "frame_number": i + 1,
                            "filename": output_filename,
                            "seek_time": seek_time,
                            "frame_size": len(frame_data)
                        })
                        
                        # 清理临时帧文件
                        os.unlink(out_temp_path)
                    else:
                        error_msg = f"Failed to extract frame at {seek_time:.2f}s: {result.stderr}"
                        yield self.create_text_message(error_msg)
                
                # 创建结果消息
                yield self.create_json_message({
                    "status": "success",
                    "message": f"Successfully extracted {len(extracted_frames)} frames from video",
                    "original_filename": video_file.filename,
                    "video_duration": duration,
                    "gap_time": gap_time,
                    "requested_count": count,
                    "extracted_count": len(extracted_frames),
                    "frames": extracted_frames
                })
                
                yield self.create_text_message(f"Successfully extracted {len(extracted_frames)} frames from {video_file.filename}.")
                
            finally:
                # 清理临时文件
                if os.path.exists(in_temp_path):
                    os.unlink(in_temp_path)
                    
        except Exception as e:
            error_msg = f"Error processing video file: {str(e)}"
            yield self.create_text_message(error_msg)
            yield self.create_json_message({
                "status": "error",
                "message": error_msg
            })