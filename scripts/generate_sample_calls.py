import os
import shutil
import subprocess
import tempfile
from pathlib import Path

FFMPEG_BIN = shutil.which("ffmpeg") or r"C:\Users\avijitpakhira\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"

SAMPLES_DIR = Path("D:/avi/TuneChecker/samples")
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

RED_LINES = [
    ("Microsoft David Desktop", "Hello, thanks for taking my call today. Let's get right into the contract."),
    ("Microsoft Zira Desktop", "Hi David, thanks for calling. We reviewed your initial proposal, but the pricing feels quite high for our team size."),
    ("Microsoft David Desktop", "Look, if you cannot afford our standard enterprise pricing, you are frankly wasting both of our time. We don't give handouts to small shops."),
    ("Microsoft Zira Desktop", "That is quite an aggressive response. We just wanted to see if there is any flexibility on implementation fees."),
    ("Microsoft David Desktop", "Take it or leave it. I will email you the revised contract addendum by tomorrow at 5 PM, but the price is non-negotiable."),
    ("Microsoft Zira Desktop", "Okay, please send that over, though we will likely need to evaluate other vendors."),
    ("Microsoft David Desktop", "Fine. Maybe we could look into custom integrations next quarter, but do not count on it. Goodbye.")
]

GREEN_LINES = [
    ("Microsoft Zira Desktop", "Hello, thank you so much for taking the time to speak with me today. How are things going?"),
    ("Microsoft David Desktop", "Hi Sarah, things are going well. We looked through your platform demo and we really like the reporting features."),
    ("Microsoft Zira Desktop", "I am really glad to hear that. Our engineering team worked hard to make those dashboards intuitive for sales teams."),
    ("Microsoft David Desktop", "Our main question is around data migration from our existing CRM. How complicated is that process?"),
    ("Microsoft Zira Desktop", "That is completely understandable to be mindful of. We provide dedicated onboarding specialists to assist with the transition step-by-step."),
    ("Microsoft David Desktop", "That gives us a lot of peace of mind. Could you share some technical documentation on the API endpoints?"),
    ("Microsoft Zira Desktop", "Absolutely. Documentation will be shared with your team after this call, and we can schedule a technical deep-dive whenever you are ready.")
]

def synthesize_line(voice: str, text: str, output_wav: Path):
    escaped_text = text.replace("'", "''")
    ps_cmd = f"""
    Add-Type -AssemblyName System.Speech;
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
    $synth.SelectVoice('{voice}');
    $synth.SetOutputToWaveFile('{output_wav.as_posix()}');
    $synth.Speak('{escaped_text}');
    $synth.Dispose();
    """
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)

def build_call(lines, output_m4a: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        concat_list = tmp_path / "concat.txt"
        wav_files = []
        
        for idx, (voice, text) in enumerate(lines):
            line_wav = tmp_path / f"line_{idx:02d}.wav"
            synthesize_line(voice, text, line_wav)
            wav_files.append(line_wav)
            
        with open(concat_list, "w", encoding="utf-8") as f:
            for wav in wav_files:
                f.write(f"file '{wav.as_posix()}'\n")
                
        # Concat and encode to m4a (AAC)
        subprocess.run([
            FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c:a", "aac", "-b:a", "128k", "-ar", "16000",
            str(output_m4a)
        ], check=True)

if __name__ == "__main__":
    print("Generating samples/red_call_01.m4a...")
    build_call(RED_LINES, SAMPLES_DIR / "red_call_01.m4a")
    print("Generating samples/green_call_01.m4a...")
    build_call(GREEN_LINES, SAMPLES_DIR / "green_call_01.m4a")
    print("Done!")
