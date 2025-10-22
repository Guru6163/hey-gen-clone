"use client";

import { ArrowLeft, Loader2, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { getVideoDuration } from "~/utils/media";
import { Button } from "~/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import VideoDropzone from "~/components/video-dropzone";
import { getPresignedUrl, translateVideo } from "~/actions/generation";

const languages = [
  { value: "english", label: "🇺🇸 English" },
  { value: "hindi", label: "🇮🇳 Hindi" },
  { value: "turkish", label: "🇹🇷 Turkish" },
];

export default function TranslateVideoPage() {
  const [step, setStep] = useState(1);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [targetLanguage, setTargetLanguage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFileSelect = async (file: File) => {
    try {
      const fileUrl = URL.createObjectURL(file);
      const duration = await getVideoDuration(fileUrl);
      if (duration > 180) {
        toast.error("Video must be 3 minutes or less.");
        URL.revokeObjectURL(fileUrl);
        return;
      }
      setVideoFile(file);
      setVideoUrl(fileUrl);
      setStep(2);
    } catch {
      toast.error("Could not read the video file.");
    }
  };

  const handleTranslate = async () => {
    if (!videoFile || !targetLanguage) {
      toast.error("Please select a video and target language");
      return;
    }

    setLoading(true);

    const { url, key } = await getPresignedUrl(
      videoFile.name,
      videoFile.type,
      "videoTranslationSource",
    );

    await fetch(url, {
      method: "PUT",
      headers: { "Content-Type": videoFile.type },
      body: videoFile,
    });

    await translateVideo({
      sourceVideoS3Key: key,
      targetLanguage: targetLanguage,
    });

    toast.success(
      "Translation job queued! You will be notified upon completion.",
    );
    
    // Reset the form
    setStep(1);
    setVideoFile(null);
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
    }
    setVideoUrl(null);
    setTargetLanguage(null);
    setLoading(false);
  };

  return (
    <div className="container mx-auto max-w-7xl p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold">Video Translation</h1>
        <p className="mt-2 text-base text-gray-600">
          Translate with original voice and lip sync up to{" "}
          <span className="text-purple-600">3 minutes</span> in length
        </p>
      </div>

      {step === 1 && <VideoDropzone onFileSelect={handleFileSelect} />}

      {step === 2 && (
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          <div className="flex flex-col gap-4">
            <h3 className="font-semibold">Source Video</h3>
            <div className="relative">
              {videoUrl && (
                <video src={videoUrl} controls className="w-full rounded-lg" />
              )}
              <Button
                onClick={() => {
                  setStep(1);
                  setVideoFile(null);
                }}
                className="absolute top-2 right-2 cursor-pointer rounded-full bg-black/50 text-white hover:bg-black/70"
                variant="ghost"
                size="icon"
              >
                <Trash2 className="h-5 w-5 text-white" />
              </Button>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            <h3 className="font-semibold">Translation Settings</h3>
            <div>
              <label className="text-sm font-medium">Target language</label>
              <Select onValueChange={setTargetLanguage}>
                <SelectTrigger className="mt-1 w-full">
                  <SelectValue placeholder="Choose language" />
                </SelectTrigger>
                <SelectContent className="max-h-64">
                  {languages.map((lang) => (
                    <SelectItem key={lang.value} value={lang.value}>
                      {lang.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      )}

      <div className="mt-8 flex justify-between">
        <Button variant="outline" onClick={() => setStep(1)}>
          {step === 2 && <ArrowLeft className="mr-2 h-4 w-4" />}
          Back
        </Button>
        {step === 2 && (
          <Button
            onClick={handleTranslate}
            disabled={!targetLanguage || loading}
            className="cursor-pointer bg-purple-600 text-white hover:bg-purple-700"
          >
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Translate
          </Button>
        )}
      </div>
    </div>
  );
}

