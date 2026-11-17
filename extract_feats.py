"""Extract the 50-d waveform feature vector for a stratified ASVspoof5 dev subset."""
import argparse, os, sys, json
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import featlib

PROTO = r"D:\ace\语义攻击\asvspoof5_check\protocols\ASVspoof5.dev.track_1.tsv"
AUDIO = r"D:\ace\语义攻击\asvspoof5_check\audio\flac_D"

# P1-1 (2026-11-14): the manuscript displays the shard name "flac_D_aa", while
# the on-disk directory is AUDIO (audio/flac_D). They denote the SAME local pool.
# Kept as a documented mapping; no sampling or file lookup uses the display name.
CORPUS_SHARD_NAME = "flac_D_aa"
AUDIO_DIR = AUDIO

# Full protocol corpus: 140,950 entries / 785 distinct speakers (corpus level).
# After sampling 2,000 utterances: 628 distinct speakers (subset level), and
# THIS subset-level population is what speaker-grouped folds are built on.
# The two counts are different levels and must not be conflated.
SEED = 2026
N_BONA = 1000
PER_ATTACK = 125


def load_proto():
    # ASVspoof5 track_1 protocol is WHITESPACE separated, >= 9 tokens:
    #   [0] spk  [1] fid  [2] gender  [3] codec  [4] q  [5] ttsvc
    #   [6] src  [7] attack (A09-A16 or "-")  [8] label (bonafide/spoof)
    # NOTE: fid is token 1, NOT token 0; attack is token 7, NOT token 2.
    # Sampling keys on fid, which must match the FLAC stems in AUDIO.
    meta = {}
    with open(PROTO, encoding="utf-8") as f:
        for line in f:
            r = line.split()
            if len(r) < 9:
                continue
            spk, fid, gender, codec, q, ttsvc, src, attack, label = r[:9]
            meta[fid] = dict(spk=spk, gender=gender, attack=attack, label=label)
    return meta


def _one(fid):
    path = os.path.join(AUDIO, fid + ".flac")
    try:
        x = featlib.decode(path)
        return fid, featlib.features(x).tolist()
    except Exception:
        return fid, None


def write_sampling_metadata(out="sampling_metadata.json", feats="feats.npz"):
    """P1-2: attach reproducibility metadata to an ALREADY EXISTING feats.npz.

    Read-only with respect to the released artifact: this function never
    re-samples, never decodes audio and never rewrites feats.npz. Every number
    is read back from the released npz / protocol / directory, so the sidecar
    cannot drift from the artifact it describes.
    """
    import numpy as np
    d = np.load(feats, allow_pickle=True)
    fid, spk, attack = d["fid"], d["spk"], d["attack"]
    meta = load_proto()
    files = {os.path.splitext(f)[0] for f in os.listdir(AUDIO) if f.endswith(".flac")}
    # The shuffle order in main() is sorted(by_attack.items()), i.e. ascending
    # attack label. Recover it from the released artifact, not from a guess.
    att_order = sorted({str(a) for a in set(attack.tolist()) if str(a) != "bonafide"})
    payload = {
        "generated_by": "extract_feats.py::write_sampling_metadata (metadata-only, no re-sampling)",
        "revision_date": "2026-11-14",
        "corpus_shard_display_name": CORPUS_SHARD_NAME,
        "local_audio_directory": AUDIO_DIR,
        "protocol_file": PROTO,
        "numpy_version": np.__version__,
        "random_seed": SEED,
        "n_bona": N_BONA,
        "per_attack": PER_ATTACK,
        "file_sort_rule": "sorted(set(local .flac stems))",
        "rng_consumption_order": (
            "one shared default_rng(2026): shuffle(bona) first, then "
            "shuffle(lst) once per attack in sorted(by_attack.items()) order"
        ),
        "attack_shuffle_order": att_order,
        "speaker_stratified": False,
        "full_protocol_line_count": sum(1 for _ in open(PROTO, encoding="utf-8")),
        "full_protocol_unique_speaker": len({m["spk"] for m in meta.values()}),
        "local_pool_flac_count": len(files),
        "sampled_utterance_count": int(len(fid)),
        "subset_unique_speaker": int(len(np.unique(spk))),
        "selected_ids_field": "feats.npz['fid'] (all 2,000 ids are stored)",
        "featlib_note": (
            "P1-3 option A: comment-only revision, numerical feature outputs "
            "unchanged; spectral-flux std was annotated but never implemented "
            "(slot 7 duplicates the slot-6 flux mean)."
        ),
        "reproduction_note": (
            "Downstream folds/training/evaluation reproduce from feats.npz['fid'] "
            "alone. Regenerating feats.npz FROM RAW protocol+flac additionally "
            "depends on numpy version, the sorted filename order, the shared "
            "default_rng(2026) state and the 8 attack-list shuffle order."
        ),
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("wrote", out)
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-bona", type=int, default=N_BONA)
    ap.add_argument("--per-attack", type=int, default=PER_ATTACK)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", default="feats.npz")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--metadata-only", action="store_true",
                    help="write sampling_metadata.json for the existing feats.npz; no sampling/decoding")
    ap.add_argument("--metadata-out", default="sampling_metadata.json")
    a = ap.parse_args()

    if a.metadata_only:
        # P1-2: attach the sidecar to the released artifact WITHOUT re-sampling.
        write_sampling_metadata(a.metadata_out, a.out)
        return

    meta = load_proto()
    files = {os.path.splitext(f)[0] for f in os.listdir(AUDIO) if f.endswith(".flac")}
    rng = np.random.default_rng(SEED)

    by_attack, bona = {}, []
    for fid in sorted(files):
        m = meta.get(fid)
        if not m:
            continue
        if m["label"] == "bonafide":
            bona.append(fid)
        else:
            by_attack.setdefault(m["attack"], []).append(fid)
    rng.shuffle(bona)
    sel_bona = bona[: a.n_bona]
    sel_spoof = []
    for att, lst in sorted(by_attack.items()):
        rng.shuffle(lst)
        sel_spoof += lst[: a.per_attack]
    ids = sel_bona + sel_spoof
    if a.limit:
        ids = ids[: a.limit]
    print(f"available {len(files)}; selecting {len(ids)} "
          f"(bona {len(sel_bona)}, spoof {len(sel_spoof)})", flush=True)

    X, Y, S, A, ID = [], [], [], [], []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        done = 0
        for fid, f in ex.map(_one, ids, chunksize=8):
            done += 1
            if f is None:
                continue
            X.append(f)
            m = meta[fid]
            Y.append(1 if m["label"] == "spoof" else 0)
            S.append(m["spk"])
            A.append(m["attack"])
            ID.append(fid)
            if done % 200 == 0:
                print(f"  {done}/{len(ids)}", flush=True)

    np.savez_compressed(a.out, X=np.asarray(X), y=np.asarray(Y), spk=np.asarray(S),
                        attack=np.asarray(A), fid=np.asarray(ID))
    print("saved", a.out, np.asarray(X).shape, "pos rate", float(np.mean(Y)))
    # P1-2: feats.npz and sampling_metadata.json are written as a pair.
    write_sampling_metadata("sampling_metadata.json", a.out)


if __name__ == "__main__":
    main()
