# Caption timing fixtures (A99)

`te.opus`, `hi.opus`, `en.opus`: 1.0 s silence + FLEURS clip 1 + 2.0 s silence + FLEURS clip 2, mono 16 kHz, Opus 32 kbps.
Clip ids, transcripts and lengths are in `fleurs.json`. Used only by `social/test_captions_timing.py`.

Source: **Google FLEURS** (validation split, configs `te_in`, `hi_in`, `en_us`), https://huggingface.co/datasets/google/fleurs,
licensed **CC BY 4.0** (https://creativecommons.org/licenses/by/4.0/). Changes: silence added, two clips joined, re-encoded.
Paper: Conneau et al., "FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech", 2022.
