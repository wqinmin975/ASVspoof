"""Waveform-side feature extraction for the ASVspoof5 anchor experiment.

The vector is 50-dim and is derived only from the decoded waveform:
  1      log duration
  2-3    log-energy mean / std
  4-5    spectral centroid mean / std
  6-7    spectral flux mean (COMPUTED TWICE -- see note below)
  8      spectral roll-off mean
  9-10   ZCR mean / ZCR std
  11-35  25 log-mel band energies (mean over frames, 20-7600 Hz)
  36-50  15 MFCC coefficients (2..16, mean over frames)
         => 10 scalar statistics + 25 log-mel bands + 15 MFCC = 50 dimensions

Comment-only revision 2026-11-14 (P1-3, option A): the legacy docstring declared
"spectral centroid mean / std, spectral flux mean / std" for slots 4-7. No flux
std was ever implemented: slot 7 re-evaluates the same flux mean as slot 6, so
one of the 50 dimensions is duplicated. ONLY the documentation is corrected.
No feature value, no feats.npz content and no downstream csv/json was changed;
repairing the duplicate would require re-running the entire ASVspoof5 chain.

It is deliberately NOT the 4-channel 50-feature vector of the main synthetic
simulation (there is no signalling or semantic channel in a speech corpus);
it is the waveform-only anchor for the audio/semantic execution point.
"""

import numpy as np
import subprocess, tempfile, os, wave

SR = 16000
N_FFT = 512
HOP = 160
N_MELS = 40


def decode(path):
    """Decode to 16 kHz mono PCM through a temporary wav file.

    A pipe is avoided deliberately: on this host the pipe reader thread ran out
    of memory when ten workers decoded in parallel.
    """
    fd, wavp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(SR),
             "-f", "wav", "-acodec", "pcm_s16le", wavp],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with wave.open(wavp, "rb") as w:
            raw = w.readframes(w.getnframes())
    finally:
        try:
            os.remove(wavp)
        except OSError:
            pass
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def _mel_filterbank():
    n_bins = N_FFT // 2 + 1
    mel = lambda f: 2595.0 * np.log10(1.0 + f / 700.0)
    imel = lambda m: 700.0 * (10 ** (m / 2595.0) - 1.0)
    fmax = 7600.0
    pts = imel(np.linspace(mel(20.0), mel(fmax), N_MELS + 2))
    fb = np.zeros((N_MELS, n_bins), dtype=np.float32)
    for i in range(N_MELS):
        lo, ce, hi = pts[i], pts[i + 1], pts[i + 2]
        for k in range(n_bins):
            f = k * SR / N_FFT
            if lo <= f <= ce:
                fb[i, k] = (f - lo) / (ce - lo)
            elif ce < f <= hi:
                fb[i, k] = (hi - f) / (hi - ce)
    return fb


FB = _mel_filterbank()
# 15 of the 40 mel bands, evenly spaced, form the 25 log-mel summary via grouping
MEL_GROUPS = np.linspace(0, N_MELS, 26, dtype=int)


def _dct_matrix(n_out, n_in):
    k = np.arange(n_out)[:, None]
    n = np.arange(n_in)[None, :]
    return np.cos(np.pi * k * (2 * n + 1) / (2 * n_in)).astype(np.float32)


DCT = _dct_matrix(17, N_MELS)


def features(x):
    if len(x) < N_FFT * 2:
        x = np.pad(x, (0, N_FFT * 2 - len(x)))
    n_frames = 1 + (len(x) - N_FFT) // HOP
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(n_frames)[:, None]
    frames = x[idx] * np.hamming(N_FFT)[None, :]
    spec = np.abs(np.fft.rfft(frames, axis=1)) + 1e-8
    mel = spec @ FB.T
    logmel = np.log(mel)
    # cepstra
    mfcc = logmel @ DCT.T

    e = np.log(np.sum(frames ** 2, axis=1) + 1e-10)
    freqs = np.arange(spec.shape[1]) * SR / N_FFT
    p = spec / (spec.sum(axis=1, keepdims=True) + 1e-8)
    cent = (p * freqs[None, :]).sum(axis=1)
    flux = np.sqrt(np.sum(np.diff(spec, axis=0) ** 2, axis=1)).mean() if spec.shape[0] > 1 else 0.0
    roll = freqs[np.argmax(np.cumsum(p, axis=1) >= 0.85, axis=1)].mean()
    zcr = np.mean(np.abs(np.diff(np.sign(x))) > 0)
    zcr_std = np.std(np.abs(np.diff(np.sign(x))) > 0)

    # NOTE (2026-11-14, comment-only): slots 6 and 7 both evaluate the flux
    # mean. The legacy docstring advertised a "spectral flux std" here that was
    # never computed. Kept numerically UNCHANGED on purpose (P1-3 option A) so
    # feats.npz and every downstream result stay byte-identical.
    f = [np.log(len(x) / SR + 1e-6), e.mean(), e.std(),
         cent.mean(), cent.std(), flux, np.mean(np.sqrt(np.sum(np.diff(spec, axis=0) ** 2, axis=1)) if spec.shape[0] > 1 else 0.0),
         roll, zcr, zcr_std]
    f += [logmel[:, MEL_GROUPS[i]:MEL_GROUPS[i + 1]].mean() for i in range(25)]
    f += list(mfcc[:, 2:17].mean(axis=0))
    return np.asarray(f, dtype=np.float32)
