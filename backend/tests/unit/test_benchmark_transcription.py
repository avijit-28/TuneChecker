import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import benchmark_transcription as bt  # noqa: E402


def test_cli_parse_defaults_and_flags():
    args = bt.parse_args([])
    assert args.dataset_slice == "2"
    assert args.models == "local,gemini"
    assert args.output_dir == "backend"
    assert args.language_mode == "english"
    assert args.gemini_model == bt.DEFAULT_GEMINI_MODEL
    assert args.mock is False
    assert args.local_files_only is False
    assert args.tier == "all"

    custom = bt.parse_args(
        [
            "--tier",
            "b",
            "--dataset-slice",
            "en_000001.mp3,en_000015.mp3",
            "--models",
            "local",
            "--output-dir",
            "custom_out",
            "--gemini-model",
            "gemini-3.5-transcribe",
            "--language-mode",
            "hinglish",
            "--local-files-only",
            "--mock",
        ]
    )
    assert custom.tier == "b"
    assert custom.dataset_slice == "en_000001.mp3,en_000015.mp3"
    assert custom.models == "local"
    assert custom.output_dir == "custom_out"
    assert custom.gemini_model == "gemini-3.5-transcribe"
    assert custom.language_mode == "hinglish"
    assert custom.local_files_only is True
    assert custom.mock is True


def test_deprecated_gemini_model_substitution():
    model, note = bt.resolve_gemini_model("gemini-2.5-flash")
    assert model == "gemini-4-hydrogen"
    assert note is not None and "deprecated" in note.lower()

    model2, note2 = bt.resolve_gemini_model("gemini-3.5-transcribe")
    assert model2 == "gemini-3.5-transcribe"
    assert note2 is None


def test_jiwer_metrics_known_synthetic_sentences():
    # Exact match ignoring case & punctuation
    exact = bt.compute_transcription_metrics(
        "Hello, world! Step-by-step.",
        "hello world step by step",
    )
    assert exact["wer_percent"] == 0.0
    assert exact["cer_percent"] == 0.0
    assert exact["accuracy_percent"] == 100.0
    assert exact["substitutions"] == 0
    assert exact["deletions"] == 0
    assert exact["insertions"] == 0
    assert exact["hits"] == 5

    # Known substitution, deletion, insertion with strong anchors:
    # Ref: "alpha beta gamma delta epsilon zeta" (6 words)
    # Hyp: "alpha x gamma epsilon zeta omega" (6 words: sub beta->x, del delta, ins omega -> 3 edits / 6 = 50% WER)
    mixed = bt.compute_transcription_metrics(
        "alpha beta gamma delta epsilon zeta",
        "alpha x gamma epsilon zeta omega",
    )
    assert mixed["substitutions"] == 1
    assert mixed["deletions"] == 1
    assert mixed["insertions"] == 1
    assert mixed["hits"] == 4
    assert mixed["wer_percent"] == 50.0
    assert mixed["cer_percent"] > 0.0
    assert mixed["accuracy_percent"] == 50.0


def test_compute_vocab_diff():
    diff = bt.compute_vocab_diff(
        "we provide dedicated onboarding specialists",
        "we provide amazing onboarding experts",
    )
    assert diff["only_in_reference"] == ["dedicated", "specialists"]
    assert diff["only_in_hypothesis"] == ["amazing", "experts"]
    assert diff["shared_vocab_count"] == 3
    assert 0.0 < diff["jaccard_similarity"] < 1.0
    assert len(diff["substitution_pairs"]) >= 1


def test_parse_dataset_slice_modes():
    items = [
        {"file_name": "en_000001.mp3"},
        {"file_name": "en_000002.mp3"},
        {"file_name": "en_000015.mp3"},
    ]
    assert [x["file_name"] for x in bt.parse_dataset_slice("2", items)] == [
        "en_000001.mp3",
        "en_000002.mp3",
    ]
    assert [x["file_name"] for x in bt.parse_dataset_slice("1:3", items)] == [
        "en_000002.mp3",
        "en_000015.mp3",
    ]
    assert [x["file_name"] for x in bt.parse_dataset_slice("en_000015,en_000001.mp3", items)] == [
        "en_000015.mp3",
        "en_000001.mp3",
    ]
    with pytest.raises(ValueError):
        bt.parse_dataset_slice("en_999999.mp3", items)


def test_tier_a_ground_truth_matches_generate_sample_calls():
    spec = importlib.util.spec_from_file_location(
        "generate_sample_calls",
        REPO_ROOT / "scripts" / "generate_sample_calls.py",
    )
    gen_mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(gen_mod)

    gt_samples = {s["id"]: s for s in bt.load_tier_a_ground_truth()}
    assert "green_call_01" in gt_samples
    assert "red_call_01" in gt_samples

    green_expected = " ".join(text for _, text in gen_mod.GREEN_LINES)
    red_expected = " ".join(text for _, text in gen_mod.RED_LINES)
    assert gt_samples["green_call_01"]["reference_transcript"] == green_expected
    assert gt_samples["red_call_01"]["reference_transcript"] == red_expected


def test_tier_a_and_b_mock_execution_creates_reports(tmp_path):
    args = bt.parse_args(
        [
            "--tier",
            "all",
            "--dataset-slice",
            "2",
            "--models",
            "local,gemini",
            "--output-dir",
            str(tmp_path),
            "--mock",
        ]
    )
    results = bt.run_benchmark(args)

    report_path = tmp_path / "BENCHMARK_REPORT.md"
    json_path = tmp_path / "benchmark_results.json"
    assert report_path.exists()
    assert json_path.exists()

    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["metadata"]["mock_mode"] is True
    assert parsed["metadata"]["language_mode"] == "english"

    # Tier A checks
    assert len(parsed["tier_a"]["samples"]) == 2
    for sample in parsed["tier_a"]["samples"]:
        assert sample["local"]["status"] == "ok"
        assert sample["local"]["metrics"]["wer_percent"] >= 0.0
        assert sample["local"]["speed_factor"] > 0.0
        assert sample["local"]["throughput_wps"] > 0.0
        assert sample["gemini"]["status"] == "ok"

    # Tier B checks
    assert len(parsed["tier_b"]["samples"]) == 2
    for sample in parsed["tier_b"]["samples"]:
        assert sample["local"]["status"] == "ok"
        assert sample["gemini"]["status"] == "ok"
        comp = sample["cross_model_comparison"]
        assert comp["status"] == "ok"
        assert comp["wer_percent"] > 0.0  # non-identical mock transcripts verify real jiwer diff
        assert "vocab_diff" in comp

    md_text = report_path.read_text(encoding="utf-8")
    assert "Tier A: Faster-Whisper vs. Human/TTS Ground Truth" in md_text
    assert "Tier B: Cross-Model Benchmark" in md_text
    assert "Vocabulary Divergence" in md_text
    assert results["tier_a"]["aggregate"]["local"] is not None


def test_honest_handling_of_missing_gemini_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    from app.config import settings

    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)

    transcriber = bt.GeminiTranscriber("gemini-4-hydrogen")
    dummy_audio = tmp_path / "dummy.mp3"
    dummy_audio.write_bytes(b"fake-mp3-bytes")

    res = transcriber.transcribe(dummy_audio, audio_duration_sec=10.0)
    assert res.status == "skipped_missing_api_key"
    assert res.text is None
    assert res.error is not None

    # End-to-end Tier B with mocked LocalWhisperRunner + DataHive slice and missing API key
    fake_mp3 = tmp_path / "en_000001.mp3"
    fake_mp3.write_bytes(b"fake-audio")
    fake_items = [
        {
            "file_name": "en_000001.mp3",
            "topic": "finance",
            "duration_seconds": 60.0,
            "audio_path": fake_mp3,
        }
    ]
    fake_local_res = bt.EngineResult(
        engine="local",
        model="faster-whisper:large-v3-turbo",
        status="ok",
        text="hello world test transcript",
        audio_duration_seconds=60.0,
        processing_time_seconds=6.0,
        real_time_factor=0.1,
        speed_factor=10.0,
        throughput_wps=0.67,
        word_count=4,
        cost_usd=0.0,
        mode="live",
    )

    with (
        patch.object(bt, "load_datahive_slice", return_value=(fake_items, {"source": "test"})),
        patch.object(bt, "probe_audio_duration", return_value=60.0),
        patch.object(bt.LocalWhisperRunner, "transcribe", return_value=fake_local_res),
    ):
        args = bt.parse_args(
            [
                "--tier",
                "b",
                "--dataset-slice",
                "1",
                "--models",
                "local,gemini",
                "--output-dir",
                str(tmp_path),
            ]
        )
        bt.run_benchmark(args)

    parsed = json.loads((tmp_path / "benchmark_results.json").read_text(encoding="utf-8"))
    sample = parsed["tier_b"]["samples"][0]
    assert sample["gemini"]["status"] == "skipped_missing_api_key"
    assert sample["gemini"]["text"] is None
    assert sample["cross_model_comparison"]["status"] == "skipped_missing_api_key"
    assert sample["cross_model_comparison"]["wer_percent"] is None
    assert parsed["tier_b"]["aggregate"]["cross_model_comparison"] is None

    md_text = (tmp_path / "BENCHMARK_REPORT.md").read_text(encoding="utf-8")
    assert "skipped_missing_api_key" in md_text
    assert "| N/A |" in md_text


def test_gemini_transcriber_with_mocked_genai_client(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "test-fake-key")
    audio_file = tmp_path / "sample.mp3"
    audio_file.write_bytes(b"audio-data")

    mock_uploaded = SimpleNamespace(
        uri="https://generativelanguage.googleapis.com/v1/files/abc",
        name="files/abc",
        mime_type="audio/mpeg",
    )
    mock_interaction = SimpleNamespace(output_text="Hello from mocked Gemini.", steps=[])
    mock_client = MagicMock()
    mock_client.files.upload.return_value = mock_uploaded
    mock_client.interactions.create.return_value = mock_interaction

    with patch("google.genai.Client", return_value=mock_client):
        transcriber = bt.GeminiTranscriber("gemini-3.5-transcribe")
        res = transcriber.transcribe(audio_file, audio_duration_sec=12.0, language_mode="english")

    assert res.status == "ok"
    assert res.text == "Hello from mocked Gemini."
    assert res.word_count == 4
    mock_client.files.upload.assert_called_once()
    mock_client.interactions.create.assert_called_once()
    create_kwargs = mock_client.interactions.create.call_args.kwargs
    assert create_kwargs["model"] == "gemini-3.5-transcribe"
    assert create_kwargs["store"] is False
    assert "generation_config" in create_kwargs
    mock_client.files.delete.assert_called_once_with(name="files/abc")


def test_backend_shim_delegates_to_canonical_script(tmp_path):
    shim_path = REPO_ROOT / "backend" / "scripts" / "benchmark_transcription.py"
    spec = importlib.util.spec_from_file_location("backend_benchmark_shim", shim_path)
    shim_mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(shim_mod)
    assert shim_mod.main is bt.main


def test_parse_dataset_slice_rejects_negative_zero_and_multi_colon():
    items = [
        {"file_name": "en_000001.mp3"},
        {"file_name": "en_000002.mp3"},
    ]
    with pytest.raises(ValueError, match=r"--dataset-slice integer must be > 0"):
        bt.parse_dataset_slice("-1", items)

    with pytest.raises(ValueError, match=r"--dataset-slice integer must be > 0"):
        bt.parse_dataset_slice("0", items)

    with pytest.raises(ValueError, match=r"Invalid slice format: too many colons"):
        bt.parse_dataset_slice("1:2:3", items)

    with pytest.raises(ValueError, match=r"Invalid slice format: non-integer bounds"):
        bt.parse_dataset_slice("foo:bar", items)


def test_parse_args_rejects_non_positive_max_audio_seconds(capsys):
    for bad_val in ("-5", "0"):
        with pytest.raises(SystemExit) as exc_info:
            bt.parse_args(["--max-audio-seconds", bad_val])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "--max-audio-seconds must be > 0" in captured.err


def test_main_catches_errors_without_unhandled_traceback(capsys, tmp_path):
    # Invalid --models
    rc_models = bt.main(["--mock", "--models", "unknown_engine", "--output-dir", str(tmp_path)])
    assert rc_models == 1
    err_models = capsys.readouterr().err
    assert err_models.startswith("Error: ")
    assert "Invalid --models" in err_models

    # Negative --dataset-slice integer
    rc_slice = bt.main(["--mock", "--tier", "b", "--dataset-slice", "-1", "--output-dir", str(tmp_path)])
    assert rc_slice == 1
    err_slice = capsys.readouterr().err
    assert err_slice.startswith("Error: ")
    assert "--dataset-slice integer must be > 0" in err_slice

    # Multi-colon --dataset-slice
    rc_colons = bt.main(["--mock", "--tier", "b", "--dataset-slice", "1:2:3", "--output-dir", str(tmp_path)])
    assert rc_colons == 1
    err_colons = capsys.readouterr().err
    assert err_colons.startswith("Error: ")
    assert "too many colons" in err_colons

    # Existing file passed as --output-dir (FileExistsError)
    existing_file = tmp_path / "already_a_file.txt"
    existing_file.write_text("occupied", encoding="utf-8")
    rc_file = bt.main(["--mock", "--output-dir", str(existing_file)])
    assert rc_file == 1
    err_file = capsys.readouterr().err
    assert err_file.startswith("Error: ")

    # RuntimeError / FileNotFoundError propagated from run_benchmark
    with patch.object(bt, "run_benchmark", side_effect=FileNotFoundError("sample missing")):
        rc_fnf = bt.main(["--mock", "--output-dir", str(tmp_path)])
    assert rc_fnf == 1
    err_fnf = capsys.readouterr().err
    assert err_fnf == "Error: sample missing\n"


def test_maybe_trim_audio_passes_loglevel_error_and_captures_stderr_tail(tmp_path):
    src = tmp_path / "corrupt.m4a"
    src.write_bytes(b"not-valid-audio")

    banner_prefix = "ffmpeg version banner " * 20  # > 200 chars before the real error
    real_err = "Invalid data found when processing input"
    fake_proc = SimpleNamespace(returncode=1, stderr=f"{banner_prefix}\n{real_err}\n")

    with patch("app.audio.ffmpeg.run_ffmpeg", return_value=fake_proc) as mock_ffmpeg:
        with pytest.raises(RuntimeError) as exc_info:
            bt.maybe_trim_audio(src, 3.0, tmp_path)

    called_args = mock_ffmpeg.call_args.args[0]
    assert called_args[:2] == ["-loglevel", "error"]
    assert real_err in str(exc_info.value)


def test_run_benchmark_isolates_maybe_trim_audio_failures_per_sample(tmp_path):
    bad_audio = tmp_path / "corrupt.m4a"
    bad_audio.write_bytes(b"corrupt")
    good_audio = tmp_path / "good.m4a"
    good_audio.write_bytes(b"good")

    tier_a_samples = [
        {
            "id": "bad_sample",
            "audio_path": str(bad_audio),
            "expected_verdict": "GREEN",
            "reference_transcript": "hello world",
        },
        {
            "id": "good_sample",
            "audio_path": str(good_audio),
            "expected_verdict": "GREEN",
            "reference_transcript": "hello world",
        },
    ]
    good_local_res = bt.EngineResult(
        engine="local",
        model="faster-whisper:base",
        status="ok",
        text="hello world",
        audio_duration_seconds=3.0,
        processing_time_seconds=0.5,
        real_time_factor=0.1667,
        speed_factor=6.0,
        throughput_wps=4.0,
        word_count=2,
        cost_usd=0.0,
        mode="live",
    )

    def fake_trim(audio_path, max_sec, workdir):
        if Path(audio_path) == bad_audio:
            raise RuntimeError("Failed to trim audio corrupt.m4a: Invalid data found")
        return Path(audio_path)

    with (
        patch.object(bt, "load_tier_a_ground_truth", return_value=tier_a_samples),
        patch.object(bt, "maybe_trim_audio", side_effect=fake_trim),
        patch.object(bt, "probe_audio_duration", return_value=3.0),
        patch.object(bt.LocalWhisperRunner, "transcribe", return_value=good_local_res),
    ):
        args = bt.parse_args(
            [
                "--tier",
                "a",
                "--models",
                "local",
                "--max-audio-seconds",
                "3.0",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
        results = bt.run_benchmark(args)

    samples = results["tier_a"]["samples"]
    assert len(samples) == 2
    assert samples[0]["id"] == "bad_sample"
    assert samples[0]["status"] == "failed"
    assert "Invalid data found" in samples[0]["error"]
    assert samples[0]["local"]["status"] == "failed"
    assert "Invalid data found" in samples[0]["local"]["error"]

    assert samples[1]["id"] == "good_sample"
    assert samples[1]["local"]["status"] == "ok"
    assert results["tier_a"]["aggregate"]["local"]["evaluated_samples"] == 1

    md_text = (tmp_path / "out" / "BENCHMARK_REPORT.md").read_text(encoding="utf-8")
    assert "Sample Processing Errors" in md_text
    assert "Invalid data found" in md_text


def test_run_benchmark_tier_b_isolates_maybe_trim_audio_failures_per_sample(tmp_path):
    bad_audio = tmp_path / "bad.mp3"
    bad_audio.write_bytes(b"corrupt")
    good_audio = tmp_path / "good.mp3"
    good_audio.write_bytes(b"good")

    dh_items = [
        {"file_name": "bad.mp3", "topic": "finance", "duration_seconds": 10.0, "audio_path": bad_audio},
        {"file_name": "good.mp3", "topic": "finance", "duration_seconds": 12.0, "audio_path": good_audio},
    ]
    good_local_res = bt.EngineResult(
        engine="local",
        model="faster-whisper:base",
        status="ok",
        text="hello world",
        audio_duration_seconds=3.0,
        processing_time_seconds=0.5,
        real_time_factor=0.1667,
        speed_factor=6.0,
        throughput_wps=4.0,
        word_count=2,
        cost_usd=0.0,
        mode="live",
    )

    def fake_trim(audio_path, max_sec, workdir):
        if Path(audio_path) == bad_audio:
            raise RuntimeError("Failed to trim audio bad.mp3: Invalid data found")
        return Path(audio_path)

    with (
        patch.object(bt, "load_datahive_slice", return_value=(dh_items, {"source": "test"})),
        patch.object(bt, "maybe_trim_audio", side_effect=fake_trim),
        patch.object(bt, "probe_audio_duration", return_value=3.0),
        patch.object(bt.LocalWhisperRunner, "transcribe", return_value=good_local_res),
    ):
        args = bt.parse_args(
            [
                "--tier",
                "b",
                "--models",
                "local",
                "--max-audio-seconds",
                "3.0",
                "--output-dir",
                str(tmp_path / "out_b"),
            ]
        )
        results = bt.run_benchmark(args)

    samples = results["tier_b"]["samples"]
    assert len(samples) == 2
    assert samples[0]["file_name"] == "bad.mp3"
    assert samples[0]["status"] == "failed"
    assert "Invalid data found" in samples[0]["error"]
    assert samples[0]["local"]["status"] == "failed"
    assert samples[1]["file_name"] == "good.mp3"
    assert samples[1]["local"]["status"] == "ok"
    assert results["tier_b"]["aggregate"]["local"]["evaluated_files"] == 1
