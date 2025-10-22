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
        local_dir="/models/LivePortrait",
        ignore_patterns=["*.md", "*.txt"]
    )
    print("Models downloaded successfully!")


image = (
    modal.Image
    .from_registry("nvidia/cuda:12.1.1-devel-ubuntu22.04", add_python="3.10")
    .env({"DEBIAN_FRONTEND": "noninteractive"})
    .apt_install("git", "ffmpeg", "libgl1-mesa-glx", "libglib2.0-0", "libsm6", "libxext6", "libxrender-dev")
    .pip_install(
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "pillow>=10.0.0",
        "imageio>=2.31.0",
        "imageio-ffmpeg>=0.4.9",
        "safetensors>=0.3.1",
        "pydantic>=2.0.0",
        "scipy>=1.11.0",
        "scikit-image>=0.21.0",
        "tqdm>=4.65.0",
        "huggingface-hub>=0.19.0",
        "einops>=0.7.0",
        "omegaconf>=2.3.0",
        "tyro>=0.7.0"
    )
    .run_commands(
        "git clone https://github.com/KwaiVGI/LivePortrait /liveportrait"
    )
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
    
    @modal.enter()
    def load_model(self):
        """Load LivePortrait pipeline on container startup"""
        import sys
        sys.path.insert(0, "/liveportrait/src")
        
        print("Loading LivePortrait pipeline...")
        
        # Import after path is set
        from live_portrait_wrapper import LivePortraitWrapper
        
        self.pipeline = LivePortraitWrapper(
            cfg={
                'checkpoint_F': '/models/LivePortrait/appearance_feature_extractor.pth',
                'checkpoint_M': '/models/LivePortrait/motion_extractor.pth',
                'checkpoint_G': '/models/LivePortrait/spade_generator.pth',
                'checkpoint_W': '/models/LivePortrait/warping_module.pth',
                'flag_use_half_precision': True
            }
        )
        
        print("LivePortrait loaded successfully!")
    
    @modal.fastapi_endpoint(method="POST", requires_proxy_auth=True)
    def control_emotion(self, request: EmotionControlRequest) -> EmotionControlResponse:
        """
        Apply emotion controls to an input video
        """
        import cv2
        import numpy as np
        import torch
        
        print(f"Processing emotion control for video: {request.video_s3_key}")
        print(f"Controls: smile={request.smile_intensity}, pitch={request.head_pitch}, yaw={request.head_yaw}")
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Get input video from S3
            video_path = f"/s3-mount/{request.video_s3_key}"
            
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video not found at {video_path}")
            
            # Extract frames from video
            print("Extracting frames...")
            frames_dir = Path(temp_dir) / "input_frames"
            frames_dir.mkdir()
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            frames = []
            idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_path = frames_dir / f"frame_{idx:06d}.png"
                cv2.imwrite(str(frame_path), frame)
                frames.append(frame)
                idx += 1
            
            cap.release()
            print(f"Extracted {len(frames)} frames at {fps} FPS")
            
            # Process frames with LivePortrait
            print("Processing frames with emotion controls...")
            output_frames = []
            
            # Create emotion control parameters
            emotion_params = {
                'smile': request.smile_intensity,
                'eye_openness': request.eye_openness,
                'eyebrow': request.eyebrow_raise,
                'pitch': request.head_pitch,
                'yaw': request.head_yaw,
                'roll': request.head_roll,
                'eye_x': request.eye_gaze_x,
                'eye_y': request.eye_gaze_y,
                'mouth_open': request.mouth_open,
                'strength': request.expression_strength
            }
            
            for i, frame in enumerate(frames):
                if i % 10 == 0:
                    print(f"Processing frame {i}/{len(frames)}")
                
                # Apply emotion controls to frame
                # Note: Actual LivePortrait API will be different
                # This is a placeholder for the emotion control logic
                processed_frame = self._apply_emotion_controls(frame, emotion_params)
                output_frames.append(processed_frame)
            
            # Save processed frames back to video
            print("Reassembling video...")
            output_video_path = os.path.join(temp_dir, "output_video.mp4")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
            
            for frame in output_frames:
                out.write(frame)
            
            out.release()
            
            # Re-encode with ffmpeg for better compatibility
            final_video_path = os.path.join(temp_dir, "final_video.mp4")
            ffmpeg_command = [
                "ffmpeg",
                "-i", output_video_path,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                final_video_path
            ]
            subprocess.run(ffmpeg_command, check=True, capture_output=True)
            print("Video reassembled successfully!")
            
            # Upload result to S3
            video_uuid = str(uuid.uuid4())
            s3_key = f"emotion-control/{video_uuid}.mp4"
            s3_path = f"/s3-mount/{s3_key}"
            os.makedirs(os.path.dirname(s3_path), exist_ok=True)
            shutil.copy(final_video_path, s3_path)
            print(f"Saved video to S3: {s3_key}")
            
            # Save preview frame
            preview_s3_key = None
            if len(output_frames) > 0:
                preview_frame = output_frames[len(output_frames) // 2]
                preview_path = os.path.join(temp_dir, "preview.jpg")
                cv2.imwrite(preview_path, preview_frame)
                
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
    
    def _apply_emotion_controls(self, frame, params):
        """
        Apply emotion controls to a single frame using LivePortrait
        
        This is a placeholder - actual implementation will use LivePortrait's API
        """
        import cv2
        import numpy as np
        
        # TODO: Implement actual LivePortrait emotion control
        # For now, return the frame as-is
        # Real implementation will:
        # 1. Extract facial features
        # 2. Modify features based on params
        # 3. Render modified face back to frame
        
        return frame


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

