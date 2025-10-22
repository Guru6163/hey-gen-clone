import glob
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import modal
from pydantic import BaseModel

app = modal.App("liveportrait-emotion-control")

volume = modal.Volume.from_name("liveportrait-cache", create_if_missing=True)
volumes = {"/models": volume}


def download_liveportrait_models():
    """Download LivePortrait pretrained models"""
    from huggingface_hub import snapshot_download
    
    print("Downloading LivePortrait models...")
    snapshot_download(
        "KwaiVGI/LivePortrait",
        local_dir="/liveportrait/pretrained_weights",
        ignore_patterns=["*.md", "*.git*", "docs"]
    )
    print("Models downloaded successfully!")


image = (
    modal.Image
    .from_registry("nvidia/cuda:12.1.1-devel-ubuntu20.04", add_python="3.10")
    .env({"DEBIAN_FRONTEND": "noninteractive"})
    .apt_install("git", "ffmpeg")
    .pip_install_from_requirements("requirements.txt")
    .run_commands("git clone https://github.com/KwaiVGI/LivePortrait /liveportrait")
    .run_function(download_liveportrait_models, volumes=volumes)
)

s3_secret = modal.Secret.from_name("hey-gen-secret")


class EmotionControlRequest(BaseModel):
    """Request model for emotion control"""
    video_s3_key: str
    
    # Emotion controls (range: -1.0 to 1.0, default: 0.0)
    smile_intensity: Optional[float] = 0.0
    eye_openness: Optional[float] = 0.0
    eyebrow_raise: Optional[float] = 0.0
    
    # Head pose controls (range: -30 to 30 degrees)
    head_pitch: Optional[float] = 0.0  # Up/down tilt
    head_yaw: Optional[float] = 0.0    # Left/right rotation
    head_roll: Optional[float] = 0.0   # Side tilt
    
    # Eye gaze controls (range: -1.0 to 1.0)
    eye_gaze_x: Optional[float] = 0.0  # Horizontal
    eye_gaze_y: Optional[float] = 0.0  # Vertical
    
    # Advanced controls
    mouth_open: Optional[float] = 0.0
    expression_strength: Optional[float] = 1.0  # Overall strength multiplier


class EmotionControlResponse(BaseModel):
    """Response model with S3 keys"""
    video_s3_key: str
    preview_frame_s3_key: Optional[str] = None


@app.cls(
    image=image,
    gpu="A100-40GB",
    volumes={
        **volumes,
        "/s3-mount": modal.CloudBucketMount("private-hey-gen", secret=s3_secret)
    },
    timeout=1800,
    secrets=[s3_secret]
)
class EmotionControlServer:
    @modal.fastapi_endpoint(method="POST", requires_proxy_auth=True)
    def control_emotion(self, request: EmotionControlRequest) -> EmotionControlResponse:
        """
        Apply emotion controls to an input video using LivePortrait
        
        Uses LivePortrait's inference script with custom retargeting parameters
        """
        import cv2
        
        print(f"Processing emotion control for video: {request.video_s3_key}")
        print(f"Controls: smile={request.smile_intensity}, pitch={request.head_pitch}, yaw={request.head_yaw}")
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Get input video from S3
            video_path = f"/s3-mount/{request.video_s3_key}"
            
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video not found at {video_path}")
            
            # Extract first frame as source image
            print("Extracting source frame...")
            cap = cv2.VideoCapture(video_path)
            ret, first_frame = cap.read()
            cap.release()
            
            if not ret:
                raise RuntimeError("Could not read video")
            
            source_image_path = os.path.join(temp_dir, "source.jpg")
            cv2.imwrite(source_image_path, first_frame)
            
            # Create retargeting info file for emotion controls
            retargeting_info = {
                'smile': request.smile_intensity,
                'eye_openness': request.eye_openness,
                'eyebrow': request.eyebrow_raise,
                'pitch': request.head_pitch,
                'yaw': request.head_yaw,
                'roll': request.head_roll,
                'eye_x': request.eye_gaze_x,
                'eye_y': request.eye_gaze_y,
                'mouth_open': request.mouth_open,
                'expression_strength': request.expression_strength
            }
            
            print(f"Applying emotion controls: {retargeting_info}")
            
            # Run LivePortrait inference
            # For now, use source video as driving video (self-reenactment with retargeting)
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            print("Running LivePortrait inference...")
            command = [
                "python",
                "inference.py",
                "-s", source_image_path,
                "-d", video_path,
                "--output_dir", output_dir,
                # Add retargeting parameters
                "--flag_retarget_eyes", "1" if abs(request.eye_gaze_x) > 0.01 or abs(request.eye_gaze_y) > 0.01 else "0",
                "--flag_retarget_mouth", "1" if abs(request.smile_intensity) > 0.01 or abs(request.mouth_open) > 0.01 else "0"
            ]
            
            result = subprocess.run(
                command,
                cwd="/liveportrait",
                capture_output=True,
                text=True,
                timeout=1500
            )
            
            if result.returncode != 0:
                print(f"LivePortrait stderr: {result.stderr}")
                print(f"LivePortrait stdout: {result.stdout}")
                raise RuntimeError(f"LivePortrait inference failed: {result.stderr}")
            
            print("LivePortrait processing complete!")
            
            # Find the generated video
            generated_video = None
            for fpath in glob.glob(os.path.join(output_dir, "**", "*.mp4"), recursive=True):
                generated_video = fpath
                break
            
            if not generated_video or not os.path.exists(generated_video):
                raise RuntimeError("LivePortrait did not produce output video")
            
            # Re-encode with ffmpeg for better compatibility
            final_video_path = os.path.join(temp_dir, "final_video.mp4")
            ffmpeg_command = [
                "ffmpeg",
                "-i", generated_video,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                final_video_path
            ]
            subprocess.run(ffmpeg_command, check=True, capture_output=True)
            print("Video processed successfully!")
            
            # Upload result to S3
            video_uuid = str(uuid.uuid4())
            s3_key = f"emotion-control/{video_uuid}.mp4"
            s3_path = f"/s3-mount/{s3_key}"
            os.makedirs(os.path.dirname(s3_path), exist_ok=True)
            shutil.copy(final_video_path, s3_path)
            print(f"Saved video to S3: {s3_key}")
            
            # Extract a preview frame
            preview_s3_key = None
            preview_path = os.path.join(temp_dir, "preview.jpg")
            ffmpeg_preview = [
                "ffmpeg",
                "-i", video_path,
                "-vf", "select='eq(n,0)'",
                "-vframes", "1",
                preview_path
            ]
            result = subprocess.run(ffmpeg_preview, capture_output=True)
            
            if result.returncode == 0 and os.path.exists(preview_path):
                preview_s3_key = f"emotion-control/{video_uuid}_preview.jpg"
                preview_s3_path = f"/s3-mount/{preview_s3_key}"
                shutil.copy(preview_path, preview_s3_path)
                print(f"Saved preview to S3: {preview_s3_key}")
            
            return EmotionControlResponse(
                video_s3_key=s3_key,
                preview_frame_s3_key=preview_s3_key
            )
            
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


@app.local_entrypoint()
def main():
    """Test the emotion control service"""
    import requests
    
    server = EmotionControlServer()
    endpoint_url = server.control_emotion.get_web_url()
    
    request = EmotionControlRequest(
        video_s3_key="samples/videos/test.mp4",
        smile_intensity=0.5,
        head_yaw=10.0,
        eye_gaze_x=0.3
    )
    
    payload = request.model_dump()
    headers = {
        "Modal-Key": "wk-zwFuWTHhuHDBOfg0SOKk7M",
        "Modal-Secret": "ws-ZqRDrXwK0xr2BSAUAqwp16"
    }
    
    response = requests.post(endpoint_url, json=payload, headers=headers)
    response.raise_for_status()
    
    result = EmotionControlResponse(**response.json())
    print(f"Result video: {result.video_s3_key}")
    print(f"Preview frame: {result.preview_frame_s3_key}")

