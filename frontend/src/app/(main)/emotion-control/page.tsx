"use client";

import { Loader2, UploadCloud, Sliders, Trash2 } from "lucide-react";
import { Input } from "~/components/ui/input";
import { useState } from "react";
import { Button } from "~/components/ui/button";
import { getPresignedUrl, controlEmotion } from "~/actions/generation";
import { toast } from "sonner";
import VideoDropzone from "~/components/video-dropzone";

export default function EmotionControlPage() {
  const [selectedVideoUrl, setSelectedVideoUrl] = useState<string | null>(null);
  const [selectedVideoFile, setSelectedVideoFile] = useState<File | null>(null);
  const [videoName, setVideoName] = useState<string>("");
  const [loading, setLoading] = useState(false);

  // Emotion control states
  const [smileIntensity, setSmileIntensity] = useState(0);
  const [eyeOpenness, setEyeOpenness] = useState(0);
  const [eyebrowRaise, setEyebrowRaise] = useState(0);
  const [headPitch, setHeadPitch] = useState(0);
  const [headYaw, setHeadYaw] = useState(0);
  const [headRoll, setHeadRoll] = useState(0);
  const [eyeGazeX, setEyeGazeX] = useState(0);
  const [eyeGazeY, setEyeGazeY] = useState(0);
  const [mouthOpen, setMouthOpen] = useState(0);
  const [expressionStrength, setExpressionStrength] = useState(1);

  const handleVideoFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedVideoUrl(URL.createObjectURL(file));
      setSelectedVideoFile(file);
      setVideoName(file.name.replace(/\.[^/.]+$/, ""));
    }
  };

  const handleGenerateVideo = async () => {
    if (!selectedVideoFile) {
      toast.error("Please upload a video first");
      return;
    }

    setLoading(true);

    try {
      // Upload video to S3
      const { url, key } = await getPresignedUrl(
        selectedVideoFile.name,
        selectedVideoFile.type,
        "emotionControlVideo",
      );

      await fetch(url, {
        method: "PUT",
        headers: {
          "Content-Type": selectedVideoFile.type,
        },
        body: selectedVideoFile,
      });

      // Submit emotion control job
      await controlEmotion({
        sourceVideoS3Key: key,
        videoName: videoName || "Emotion Controlled Video",
        smileIntensity: smileIntensity / 100,
        eyeOpenness: eyeOpenness / 100,
        eyebrowRaise: eyebrowRaise / 100,
        headPitch,
        headYaw,
        headRoll,
        eyeGazeX: eyeGazeX / 100,
        eyeGazeY: eyeGazeY / 100,
        mouthOpen: mouthOpen / 100,
        expressionStrength,
      });

      toast.success(
        "Emotion control job queued! You will see the result on the dashboard.",
      );

      // Reset form
      setSelectedVideoUrl(null);
      setSelectedVideoFile(null);
      setVideoName("");
      resetControls();
    } catch (error) {
      console.error("Error:", error);
      toast.error("Failed to submit emotion control job");
    } finally {
      setLoading(false);
    }
  };

  const resetControls = () => {
    setSmileIntensity(0);
    setEyeOpenness(0);
    setEyebrowRaise(0);
    setHeadPitch(0);
    setHeadYaw(0);
    setHeadRoll(0);
    setEyeGazeX(0);
    setEyeGazeY(0);
    setMouthOpen(0);
    setExpressionStrength(1);
  };

  return (
    <div className="container mx-auto max-w-7xl p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold">
          Real-Time <span className="text-purple-600">Emotion Control</span> &
          Expression Editing
        </h1>
        <p className="mt-2 text-base text-gray-600">
          Upload a video and control facial expressions, head pose, and emotions
          using AI-powered LivePortrait technology.
        </p>
      </div>

      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Left: Upload video */}
        <div className="flex w-full flex-col gap-4 lg:w-[400px]">
          {selectedVideoUrl ? (
            <div className="flex flex-col gap-4">
              <div className="relative">
                <video
                  src={selectedVideoUrl}
                  controls
                  className="w-full rounded-xl border"
                />
                <Button
                  variant="ghost"
                  onClick={() => {
                    setSelectedVideoFile(null);
                    setSelectedVideoUrl(null);
                  }}
                  className="absolute top-2 right-2 cursor-pointer rounded-full bg-white p-2 shadow"
                >
                  <Trash2 className="h-5 w-5 text-gray-600" />
                </Button>
              </div>
              <Input
                placeholder="Video name"
                value={videoName}
                onChange={(e) => setVideoName(e.target.value)}
              />
            </div>
          ) : (
            <div className="flex h-full min-h-[300px] flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 bg-gray-50 px-4 py-8">
              <UploadCloud className="mb-2 h-10 w-10 text-gray-400" />
              <label className="cursor-pointer font-medium underline">
                Upload video
                <Input
                  onChange={handleVideoFileChange}
                  type="file"
                  accept="video/*"
                  className="hidden"
                />
              </label>
              <div className="mt-2 text-xs text-gray-500">
                MP4, MOV, or WebM (max 100MB)
              </div>
            </div>
          )}
        </div>

        {/* Right: Emotion controls */}
        <div className="flex flex-1 flex-col gap-6">
          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <Sliders className="h-5 w-5 text-purple-600" />
              <h2 className="text-xl font-semibold">Emotion Controls</h2>
            </div>

            {/* Facial Expression Controls */}
            <div className="space-y-4">
              <div className="rounded-lg bg-gray-50 p-4">
                <h3 className="mb-3 text-sm font-semibold text-gray-700">
                  Facial Expressions
                </h3>
                <div className="space-y-3">
                  <div>
                    <label className="flex items-center justify-between text-sm">
                      <span>Smile Intensity</span>
                      <span className="text-purple-600">{smileIntensity}%</span>
                    </label>
                    <input
                      type="range"
                      min="-100"
                      max="100"
                      value={smileIntensity}
                      onChange={(e) => setSmileIntensity(Number(e.target.value))}
                      className="mt-1 w-full accent-purple-600"
                    />
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm">
                      <span>Eye Openness</span>
                      <span className="text-purple-600">{eyeOpenness}%</span>
                    </label>
                    <input
                      type="range"
                      min="-100"
                      max="100"
                      value={eyeOpenness}
                      onChange={(e) => setEyeOpenness(Number(e.target.value))}
                      className="mt-1 w-full accent-purple-600"
                    />
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm">
                      <span>Eyebrow Raise</span>
                      <span className="text-purple-600">{eyebrowRaise}%</span>
                    </label>
                    <input
                      type="range"
                      min="-100"
                      max="100"
                      value={eyebrowRaise}
                      onChange={(e) => setEyebrowRaise(Number(e.target.value))}
                      className="mt-1 w-full accent-purple-600"
                    />
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm">
                      <span>Mouth Opening</span>
                      <span className="text-purple-600">{mouthOpen}%</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={mouthOpen}
                      onChange={(e) => setMouthOpen(Number(e.target.value))}
                      className="mt-1 w-full accent-purple-600"
                    />
                  </div>
                </div>
              </div>

              {/* Head Pose Controls */}
              <div className="rounded-lg bg-gray-50 p-4">
                <h3 className="mb-3 text-sm font-semibold text-gray-700">
                  Head Pose
                </h3>
                <div className="space-y-3">
                  <div>
                    <label className="flex items-center justify-between text-sm">
                      <span>Pitch (Up/Down)</span>
                      <span className="text-purple-600">{headPitch}°</span>
                    </label>
                    <input
                      type="range"
                      min="-30"
                      max="30"
                      value={headPitch}
                      onChange={(e) => setHeadPitch(Number(e.target.value))}
                      className="mt-1 w-full accent-purple-600"
                    />
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm">
                      <span>Yaw (Left/Right)</span>
                      <span className="text-purple-600">{headYaw}°</span>
                    </label>
                    <input
                      type="range"
                      min="-30"
                      max="30"
                      value={headYaw}
                      onChange={(e) => setHeadYaw(Number(e.target.value))}
                      className="mt-1 w-full accent-purple-600"
                    />
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm">
                      <span>Roll (Tilt)</span>
                      <span className="text-purple-600">{headRoll}°</span>
                    </label>
                    <input
                      type="range"
                      min="-30"
                      max="30"
                      value={headRoll}
                      onChange={(e) => setHeadRoll(Number(e.target.value))}
                      className="mt-1 w-full accent-purple-600"
                    />
                  </div>
                </div>
              </div>

              {/* Eye Gaze Controls */}
              <div className="rounded-lg bg-gray-50 p-4">
                <h3 className="mb-3 text-sm font-semibold text-gray-700">
                  Eye Gaze
                </h3>
                <div className="space-y-3">
                  <div>
                    <label className="flex items-center justify-between text-sm">
                      <span>Horizontal (Left/Right)</span>
                      <span className="text-purple-600">{eyeGazeX}%</span>
                    </label>
                    <input
                      type="range"
                      min="-100"
                      max="100"
                      value={eyeGazeX}
                      onChange={(e) => setEyeGazeX(Number(e.target.value))}
                      className="mt-1 w-full accent-purple-600"
                    />
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm">
                      <span>Vertical (Up/Down)</span>
                      <span className="text-purple-600">{eyeGazeY}%</span>
                    </label>
                    <input
                      type="range"
                      min="-100"
                      max="100"
                      value={eyeGazeY}
                      onChange={(e) => setEyeGazeY(Number(e.target.value))}
                      className="mt-1 w-full accent-purple-600"
                    />
                  </div>
                </div>
              </div>

              {/* Expression Strength */}
              <div className="rounded-lg bg-gray-50 p-4">
                <h3 className="mb-3 text-sm font-semibold text-gray-700">
                  Overall Strength
                </h3>
                <div>
                  <label className="flex items-center justify-between text-sm">
                    <span>Expression Strength</span>
                    <span className="text-purple-600">
                      {expressionStrength.toFixed(1)}x
                    </span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={expressionStrength}
                    onChange={(e) =>
                      setExpressionStrength(Number(e.target.value))
                    }
                    className="mt-1 w-full accent-purple-600"
                  />
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 flex gap-3">
              <Button
                onClick={resetControls}
                variant="outline"
                className="flex-1"
                disabled={loading}
              >
                Reset Controls
              </Button>
              <Button
                onClick={handleGenerateVideo}
                className="flex-1 bg-purple-600 text-white hover:bg-purple-700"
                disabled={loading || !selectedVideoFile}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  "Generate Video"
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

