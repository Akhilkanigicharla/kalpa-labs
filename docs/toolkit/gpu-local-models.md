# Local models on Windows: Ollama, ds4, OpenJev / llama.cpp

**Answer first:** don't install anything yet. **First run `nvidia-smi`** (step 1) and send Claude the output. On a low-RAM PC with no NVIDIA GPU, the only realistic local option is a **tiny model (about 1 to 4B parameters) in Ollama**, and even that is optional. n8n's free OpenRouter and Hugging Face models are faster and cost nothing. **ds4 and OpenJev do not fit this PC** (numbers below).

> Kalpa hard rule 2 says nothing gets installed on Akhil's PC. This page is a **reference for a CEO decision**. Install Ollama only if Akhil explicitly decides to make an exception after the check in step 1.

## Step 1: check the hardware (2 minutes, installs nothing)

Open **PowerShell** and run each line. Copy the output to Claude.

```powershell
nvidia-smi
```

- If you see a table with a GPU name and "Memory-Usage" (for example `8192MiB`), you have an NVIDIA GPU. Note the **total memory (VRAM)** and the **Driver Version**.
- If you see `'nvidia-smi' is not recognized…`, there is **no NVIDIA GPU or no driver**. Treat the PC as CPU-only.

```powershell
# RAM in GB, free disk on C:, CPU name
[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
Get-PSDrive C | Select-Object @{n='FreeGB';e={[math]::Round($_.Free/1GB,1)}}
(Get-CimInstance Win32_Processor).Name
# Windows version (Ollama needs Windows 10 22H2 or newer)
(Get-ComputerInfo).OsName; (Get-ComputerInfo).OsDisplayVersion
```

## Step 2: what fits (decision table)

Rule of thumb, **an estimate and not a vendor number**: a GGUF model needs about its file size plus 1–2 GB of free RAM or VRAM to run.

| Your PC after step 1 | What to do | Model file sizes (Hugging Face, checked 17 Oct 2026) |
|---|---|---|
| Under 8 GB RAM, no NVIDIA GPU | **Don't run local models.** Use OpenRouter free and Hugging Face in n8n | — |
| 8 GB RAM, no GPU | Optional: one ~1B model in Ollama for offline drafts, which will be slow | Gemma 3 1B Q4_K_M = 0.81 GB ([ggml-org/gemma-3-1b-it-GGUF](https://huggingface.co/ggml-org/gemma-3-1b-it-GGUF)). Licence: Gemma Terms of Use (see the model card) |
| 16 GB RAM, or an NVIDIA GPU with 4–6 GB VRAM | A ~4B model is usable | Qwen3-4B Q4_K_M = 2.50 GB ([Qwen/Qwen3-4B-GGUF](https://huggingface.co/Qwen/Qwen3-4B-GGUF)). Licence file in that repo |
| 24 GB+ VRAM, or 32 GB+ RAM | Only then could OpenJev Q4 run, and only for **non-commercial** tests | OpenJev Q4_K_M = **19.4 GB** ([ggml-org/OpenJev-GGUF](https://huggingface.co/ggml-org/OpenJev-GGUF)) |
| Mac with 96 GB+ unified memory, DGX Spark, or Ada-class (L40S) GPUs | The only class ds4 targets | ds4's Qwen3.8 Q2 download is one 137.10 GiB file ([antirez/ds4](https://github.com/antirez/ds4)) |

## Ollama on Windows (only after step 1 and a CEO "yes")

Source: [Ollama Windows docs](https://github.com/ollama/ollama/blob/main/docs/windows.mdx), MIT ([repo](https://github.com/ollama/ollama)).

- **Needs:** Windows 10 22H2 or newer (Home or Pro). NVIDIA driver **551.61 or newer** if you have an NVIDIA GPU. At least **4 GB of disk** for the program, plus the model files.
- **Install:** download `OllamaSetup.exe` from the official Ollama download page (linked in the [README](https://github.com/ollama/ollama)). It installs in your user account, with **no Administrator needed**, and runs in the tray in the background.
- **Small C: drive?** Put models elsewhere before downloading any:

```powershell
# Example: store models on D: (change the path to a drive that has space)
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\ollama-models", "User")
# Quit Ollama from the tray, start it again from the Start menu, open a new PowerShell
```

- **Run a tiny model** (Ollama library names; `ollama pull` prints the real size before downloading):

```powershell
ollama pull gemma3:1b
ollama run gemma3:1b "Write a 2-line WhatsApp reminder for a salon appointment in Telugu."
```

- **Remove it later:** `ollama rm gemma3:1b`, then uninstall Ollama from Windows Settings → Apps.
- **n8n link:** n8n Cloud **cannot reach** `localhost:11434` on your PC, and opening that port to the internet is unsafe. Local Ollama is only for use on the PC itself (for example Presenton running locally with `LLM=ollama`). n8n agents keep using OpenRouter free.

## llama.cpp and OpenJev (reference only)

- **llama.cpp:** MIT, 131,513 stars, pushed 17 Oct 2026 ([ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)). Windows builds are the zip files on its Releases page: a CPU build, or a CUDA build if `nvidia-smi` showed a GPU. Unzip to a folder, open PowerShell there, and the usual server command is:

```powershell
# Downloads from Hugging Face on first run and serves an OpenAI-style API on port 8080
.\llama-server.exe -hf ggml-org/gemma-3-1b-it-GGUF:Q4_K_M --port 8080
```

  Check the flag names against the current llama.cpp README before use. The OpenJev model card shows a newer launcher, `llama serve -hf ggml-org/OpenJev-GGUF`, and says the model is served through a `/v1/systemone` decision API added in a llama.cpp pull request ([OpenJev-GGUF card](https://huggingface.co/ggml-org/OpenJev-GGUF)).

- **OpenJev:** a 27.4B-parameter "decision" model (classifies and decides; it does not write text) based on Qwen3.5 ([openjev/openjev](https://huggingface.co/openjev/openjev)).
  - Weights are **CC BY-NC 4.0, non-commercial only**. Kalpa sells products, so **SKIP** for any business stream.
  - Files: Q4_K_M 19.4 GB, Q8_0 28.6 GB, BF16 53.8 GB, plus a 0.6–0.9 GB vision projector.
  - A small Apache-2.0 alternative with a similar "decision model" idea exists: [chaoliangUNSW/Jev-Style-0.8B-Decision-v3-GGUF](https://huggingface.co/chaoliangUNSW/Jev-Style-0.8B-Decision-v3-GGUF) (Q4_K_M 0.53 GB). It is untested by us and is a community model, so treat it as TRY LATER. Its repo also ships `.py` and `.cpp` helper files, so read them before running anything.

## ds4 (antirez): not for this PC

- **What it is:** a local inference engine for DeepSeek V4 Flash/PRO (and a Qwen3.8 build), MIT ([repo](https://github.com/antirez/ds4)).
- **Hardware:** Metal is "the primary target, on Macs with 96 GB or more". The CUDA builds target a DGX Spark or "one or more CUDA cards, including Ada/L40S". **Windows is not mentioned** in the README.
- **Verdict:** SKIP. If Kalpa ever needs a big open model, rent a GPU by the hour or use a hosted free model. That is a CEO budget decision.

**Next step:** run the 2 commands in step 1 (2 minutes) and paste the output to Claude. Claude will then say "no local model" or name exactly one model to try.
