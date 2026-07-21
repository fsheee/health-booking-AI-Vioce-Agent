"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Mic, Square, AlertTriangle, Volume2 } from "lucide-react";

export default function VoiceAssistantPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isEmergency, setIsEmergency] = useState(false);
  const [patientId, setPatientId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    api.patients.getMe().then((patient) => {
      setPatientId(patient.id);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function startRecording() {
    try {
      setError("");
      setTranscript("");
      setResponse("");
      setAudioUrl(null);
      setIsEmergency(false);

      if (!patientId) {
        setError("Could not identify patient. Please login again.");
        return;
      }

      const session = await api.voice.startSession(patientId);
      setSessionId(session.id);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      audioChunks.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.current.push(e.data);
      };

      recorder.onstop = async () => {
        setIsProcessing(true);
        try {
          const blob = new Blob(audioChunks.current, { type: "audio/webm" });
          const base64 = await blobToBase64(blob);

          const data = await api.voice.process(session.id, base64);
          setTranscript(data.transcript || "Audio processed");
          setResponse(data.response);
          setIsEmergency(data.is_emergency || false);

          if (data.audio) {
            const audioBlob = base64ToBlob(data.audio);
            const url = URL.createObjectURL(audioBlob);
            setAudioUrl(url);
          }
        } catch (err: any) {
          setError(err.message || "Failed to process voice");
        } finally {
          setIsProcessing(false);
        }

        stream.getTracks().forEach((t) => t.stop());
      };

      recorder.start();
      mediaRecorder.current = recorder;
      setIsRecording(true);
    } catch (err: any) {
      setError(err.name === "NotAllowedError" ? "Microphone access denied. Please allow microphone access." : err.message);
    }
  }

  function stopRecording() {
    mediaRecorder.current?.stop();
    setIsRecording(false);
  }

  function blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        const base64 = result.split(",")[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  function base64ToBlob(base64: string): Blob {
    const byteChars = atob(base64);
    const byteNums = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
      byteNums[i] = byteChars.charCodeAt(i);
    }
    return new Blob([new Uint8Array(byteNums)], { type: "audio/mp3" });
  }

  function playAudio() {
    audioRef.current?.play();
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AI Voice Assistant</h1>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Speak with the AI Assistant</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {isEmergency && (
            <div className="rounded-lg border-2 border-red-500 bg-red-50 p-4">
              <div className="flex items-center gap-2 text-red-700 font-semibold">
                <AlertTriangle className="h-5 w-5" />
                Emergency Detected
              </div>
              <p className="mt-1 text-sm text-red-600">
                Your conversation has been escalated to a human staff member.
                If this is a medical emergency, please call 911 immediately.
              </p>
            </div>
          )}

          <div className="flex justify-center">
            <Button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isProcessing}
              size="lg"
              className={`h-16 w-16 rounded-full ${
                isRecording ? "bg-red-600 hover:bg-red-700 animate-pulse" : ""
              }`}
            >
              {isRecording ? <Square className="h-6 w-6" /> : <Mic className="h-6 w-6" />}
            </Button>
          </div>

          <p className="text-center text-sm text-muted-foreground">
            {isProcessing ? "Processing your request..." : isRecording ? "Recording... tap to stop" : "Tap to start speaking"}
          </p>

          {error && (
            <div className="rounded bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
          )}

          {transcript && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">You said:</p>
              <div className="rounded-lg bg-muted p-3 text-sm">{transcript}</div>
            </div>
          )}

          {response && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">Assistant:</p>
              <div className="rounded-lg bg-blue-50 p-3 text-sm">{response}</div>
            </div>
          )}

          {audioUrl && (
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={playAudio}>
                <Volume2 className="h-4 w-4 mr-1" /> Play Response
              </Button>
              <audio ref={audioRef} src={audioUrl} className="hidden" />
            </div>
          )}
        </CardContent>
      </Card>

      <div className="max-w-2xl text-xs text-muted-foreground space-y-1">
        <p>This AI assistant can help you book appointments, check availability, and answer questions about your care.</p>
        <p className="font-semibold text-destructive">
          It cannot diagnose or treat medical conditions. If you have a medical emergency, call 911 immediately.
        </p>
      </div>
    </div>
  );
}
