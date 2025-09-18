
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from collections.abc import Generator
from typing import Any
import tempfile
import subprocess
import json
import os

class GetVideoInfo(Tool):    
    def _create_error_response(self, error_message: str) -> Generator[ToolInvokeMessage, None, None]:
        yield self.create_text_message(error_message)
        yield self.create_json_message({
            "status": "error",
            "message": error_message
        })
    
    def _extract_stream_info(self, stream_metadata: dict) -> dict:
        stream_info = {
            "index": stream_metadata.get("index"),
            "codec_type": stream_metadata.get("codec_type"),
            "codec_name": stream_metadata.get("codec_name")
        }
        
        # 处理视频流特有信息
        if stream_metadata.get("codec_type") == "video":
            stream_info.update({
                "width": stream_metadata.get("width"),
                "height": stream_metadata.get("height"),
                "r_frame_rate": stream_metadata.get("r_frame_rate"),
                "display_aspect_ratio": stream_metadata.get("display_aspect_ratio", "unknown")
            })
        
        # 处理音频流特有信息
        elif stream_metadata.get("codec_type") == "audio":
            stream_info.update({
                "sample_rate": stream_metadata.get("sample_rate"),
                "channels": stream_metadata.get("channels"),
                "channel_layout": stream_metadata.get("channel_layout", "unknown")
            })
        
        return stream_info
    
    def _generate_summary_text(self, video_info_response: dict, filename: str) -> str:
        video_streams = [stream for stream in video_info_response["streams"] if stream["codec_type"] == "video"]
        audio_streams = [stream for stream in video_info_response["streams"] if stream["codec_type"] == "audio"]
        
        if not video_streams:
            return f"No video streams found in {filename}"
        
        primary_video_stream = video_streams[0]
        video_duration_seconds = video_info_response["format"]["duration"]
        duration_minutes = int(video_duration_seconds // 60)
        duration_seconds = int(video_duration_seconds % 60)
        
        summary_lines = [
            f"Video Information for {filename}:",
            "",
            f"Format: {video_info_response['format']['format_name']}",
            f"Duration: {duration_minutes}m {duration_seconds}s",
            f"Size: {video_info_response['format']['size'] / (1024*1024):.2f} MB",
        ]
        
        if "width" in primary_video_stream and "height" in primary_video_stream:
            summary_lines.append(f"Resolution: {primary_video_stream['width']}x{primary_video_stream['height']}")
            video_info_response["resolution"]["width"] = max(
                video_info_response["resolution"]["width"], 
                primary_video_stream["width"]
            )
            video_info_response["resolution"]["height"] = max(
                video_info_response["resolution"]["height"], 
                primary_video_stream["height"]
            )
        
        summary_lines.append(f"Video Codec: {primary_video_stream.get('codec_name', 'Unknown')}")
        
        if audio_streams:
            summary_lines.append(f"Audio Codec: {audio_streams[0].get('codec_name', 'Unknown')}")
        
        summary_lines.append(f"Bitrate: {video_info_response['format']['bit_rate'] / 1000:.2f} kbps")
        
        return "\n".join(summary_lines)
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        uploaded_video_file = tool_parameters.get('video')
        
        if not uploaded_video_file:
            yield from self._create_error_response("No video file provided")
            return
        
        try:
            # 创建临时文件
            video_file_extension = uploaded_video_file.extension if uploaded_video_file.extension else '.mp4'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=video_file_extension) as temp_video_file:
                temp_video_file.write(uploaded_video_file.blob)
                temporary_video_path = temp_video_file.name
            
            try:
                # 获取视频信息
                ffprobe_command = [
                    'ffprobe', 
                    '-v', 'error',  # 改为 error 级别，显示错误信息
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    temporary_video_path
                ]
                
                ffprobe_result = subprocess.run(
                    ffprobe_command, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                
                if ffprobe_result.returncode != 0:
                    analysis_error_message = f"Error analyzing video file: {ffprobe_result.stderr}"
                    yield from self._create_error_response(analysis_error_message)
                    return
                
                # 验证 ffprobe 输出是否为有效 JSON
                if not ffprobe_result.stdout.strip():
                    analysis_error_message = "ffprobe returned empty output"
                    yield from self._create_error_response(analysis_error_message)
                    return
                
                try:
                    video_metadata = json.loads(ffprobe_result.stdout)
                except json.JSONDecodeError as json_error:  
                    analysis_error_message = f"Failed to parse ffprobe output as JSON: {debug_info}"
                    yield from self._create_error_response(analysis_error_message)
                    return
                
                # 提取关键信息并构建结构化响应
                video_info_response = {
                    "status": "success",
                    "filename": uploaded_video_file.filename,
                    "format": {
                        "format_name": video_metadata.get("format", {}).get("format_name", "unknown"),
                        "duration": float(video_metadata.get("format", {}).get("duration", 0)),
                        "size": int(video_metadata.get("format", {}).get("size", 0)),
                        "bit_rate": int(video_metadata.get("format", {}).get("bit_rate", 0)),
                    },
                    "resolution": {
                        "width": 0,
                        "height": 0,
                    },
                    "streams": []
                }
                
                # 处理流信息
                for stream_metadata in video_metadata.get("streams", []):
                    stream_info = self._extract_stream_info(stream_metadata)
                    video_info_response["streams"].append(stream_info)
                
                # 生成摘要信息
                summary_text = self._generate_summary_text(video_info_response, uploaded_video_file.filename)
                
                # 返回处理结果
                yield self.create_text_message(summary_text)
                yield self.create_json_message(video_info_response)
                
            finally:
                # 清理临时文件
                if os.path.exists(temporary_video_path):
                    os.unlink(temporary_video_path)
                    
        except Exception as processing_error:
            processing_error_message = f"Error processing video file: {str(processing_error)}"
            yield from self._create_error_response(processing_error_message) 