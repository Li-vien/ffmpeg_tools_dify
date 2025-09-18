## ffmpeg_tools_dify

**Author:** livien
**Version:** 0.0.1
**Type:** tool

### Description
A collection of ffmpeg tools that organizes common functionality


## Features
### 1. Get Video Info
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| video | file | Yes | The video file |

### 2. Get Video Frame
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| video | file | Yes | The video file |
| type | [start,end,time] | Yes | Frame extraction type: start (first frame), end (last frame), time (specified time) |
| time | number | No | Specific time to extract frame, effective when type is time (seconds) |

#### 3. Get Video Frames

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| video | file | Yes | The video file |
| gap_time | number | No | Interval in seconds (seconds) |
| count | number | No | Total number of frames to extract |


## Examples
1. Extract first frame of video
```
{
    "video": [uploaded_video_file],
    "type": "start",
}
```
2. Extract last frame of video
```
{
    "video": [uploaded_video_file],
    "type": "end",
}
```
3. Extract frame at specified time
```
{
    "video": [uploaded_video_file],
    "type": "time",
    "time": "12"
}
```
4. Extract frames at 10-second intervals
{
    "video": [uploaded_video_file],
    "gap_time": "10",
}
```
5. Extract 10 frames
{
    "video": [uploaded_video_file],
    "count": "10",
}
```
6. Get video info
-- input
```
{
    "video": [uploaded_video_file],
}
```
-- output
```
{
  "text": "Video Information for video5.mp4:\n\nFormat: mov,mp4,m4a,3gp,3g2,mj2\nDuration: 0m 34s\nSize: 3.79 MB\nResolution: 394x852\nVideo Codec: h264\nAudio Codec: aac\nBitrate: 934.82 kbps\n",
  "files": [],
  "json": [
    {
      "filename": "video5.mp4",
      "format": {
        "bit_rate": 934823,
        "duration": 34.017007,
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "size": 3974987
      },
      "resolution": {
        "height": 852,
        "width": 394
      },
      "status": "success",
      "streams": [
        {
          "codec_name": "h264",
          "codec_type": "video",
          "display_aspect_ratio": "197:426",
          "height": 852,
          "index": 0,
          "r_frame_rate": "25/1",
          "width": 394
        },
        {
          "channel_layout": "stereo",
          "channels": 2,
          "codec_name": "aac",
          "codec_type": "audio",
          "index": 1,
          "sample_rate": "44100"
        }
      ]
    }
  ]
}
```

## License

[MIT](./LICENSE)

## Develop
```
python3 -m venv venv
source venv/bin/activate && pip install -r requirements.txt
source venv/bin/activate && python3 -m main

// publish
./dify-plugin-darwin-arm64 plugin package ./ffmpeg_tools_dify 
```