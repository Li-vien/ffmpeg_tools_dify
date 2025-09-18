## ffmpeg_tools_dify

**Author:** livien
**Version:** 0.0.1
**Type:** tool

### Description
A collection of ffmpeg tools that organizes common functionality


## Features
### 1. Get Video Frame
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| video | file | Yes | The video file |
| type | [start,end,time] | Yes | Frame extraction type: start (first frame), end (last frame), time (specified time) |
| time | string | No | Specific time to extract frame, effective when type is time (seconds) |


#### 2. Get Video Frames

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| video | file | Yes | The video file |
| gap_time | string | No | Interval in seconds (seconds) |
| count | string | No | Total number of frames to extract |


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


## License

[MIT](./LICENSE)

## Develop
```
python3 -m venv venv
source venv/bin/activate && pip install -r requirements.txt
source venv/bin/activate && python3 -m main
```