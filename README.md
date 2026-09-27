# Local Qwen Deployment on vLLM

Run a private, self-hosted LLM chat interface on your own GPU — no API keys, no per-token costs, no data leaving your machine. This project deploys **Qwen2-1.5B-Instruct** (or any compatible HuggingFace model) using **vLLM** as the inference engine and **Streamlit** as the chat frontend, packaged in a single Docker container.

📊 **[Visual Walkthrough — Slides](./slides/vllm-deployment-docker.pdf)**

---

## Self-Hosted Model vs API-Deployed Model

| | Self-Hosted (this project) | API-Based (OpenAI, Anthropic) |
|---|---|---|
| Cost | One-time GPU cost | Per-token billing |
| Privacy | Data stays on your machine | Data sent to third party |
| Control | Full — model, params, context length | Limited to what the API exposes |
| Setup | Requires GPU + Docker | Just an API key |
| Best for | Private data, cost at scale, learning | Quick prototyping, production apps |

---

## Architecture

```
Browser
  └── Port 80  →  nginx (auth gateway)
                      ├── /login, /logout  →  FastAPI auth service (JWT cookie)
                      └── /  (auth_request check)  →  Streamlit UI (app.py, internal :8501)
                                                            └── vLLM API (internal :8000)
                                                                    └── NVIDIA GPU (Tesla T4 / local)
```

All services run inside a **single Docker container**; only port 80 is exposed externally. The entrypoint script starts vLLM first, polls `/health` until the model is loaded, then starts the FastAPI auth service, Streamlit, and finally nginx — which gates every request behind a valid JWT session cookie before proxying to Streamlit.

---

## Key Component Workflow

---

## Project Structure

```
llm-deployment-demo/
├── app.py                  # Streamlit chat frontend
├── auth_app.py             # FastAPI login/JWT verification service
├── nginx.conf              # Auth-gated reverse proxy (port 80)
├── entrypoint.sh           # Starts vLLM, auth service, Streamlit, then nginx
├── Dockerfile              # CUDA + PyTorch + vLLM + Streamlit + nginx image
├── requirements.txt        # Python dependencies
├── g4-instance-setup.md    # AWS EC2 g4dn.xlarge provisioning guide (manual/console)
├── terraform/              # Terraform for EC2 provisioning (instance + security group)
└── README.md
```

---

## Quick Start

### Step 1 — Provision the EC2 Instance with Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # set your key_name and ssh_cidr
terraform init
terraform apply
```

This provisions a `g4dn.xlarge` on AWS's Deep Learning Base GPU AMI (Ubuntu 22.04) — driver, Docker, and NVIDIA Container Toolkit are already baked in, no manual driver install/reboot needed. Outputs the instance's public IP and an SSH command.

Prefer the AWS Console instead? Manual steps are in **[g4-instance-setup.md](./g4-instance-setup.md)**.

---

### Step 2 — SSH into the Instance

Once the instance is running, grab the IP from Terraform's output (or the AWS Console) and connect:

```bash
terraform output public_ip
```

```bash
ssh -i your-key.pem ubuntu@<ec2-public-ip>
```

---

### Step 3 — Clone the Repo

```bash
git clone https://github.com/vishakhasadhwani/llm-deployment-demo.git
cd llm-deployment-demo
```

---

### Step 4 — Build the Docker Image

```bash
docker build -t vllm-nexus .
```

> First build takes 10–20 minutes. Subsequent builds use the layer cache.

---

### Step 5 — Run the Container

```bash
docker run --gpus all \
    -p 80:80 \
    -e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    -e JWT_SECRET=$(openssl rand -hex 32) \
    -e AUTH_USER=admin \
    -e AUTH_PASSWORD=change-me \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm-nexus
```

**Run in background:**

```bash
docker run -d --gpus all \
    -p 80:80 \
    -e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    -e JWT_SECRET=$(openssl rand -hex 32) \
    -e AUTH_USER=admin \
    -e AUTH_PASSWORD=change-me \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --restart unless-stopped \
    --name vllm-nexus \
    vllm-nexus

docker logs -f vllm-nexus                        # watch logs
docker stop vllm-nexus && docker rm vllm-nexus   # stop and clean up
```

> Only port 80 is exposed. vLLM's API (:8000) and Streamlit (:8501) are internal-only, reached exclusively through the nginx auth gateway.

---

### Step 6 — Open the UI

```
http://<your-ec2-public-ip>
```

You'll land on a login page — sign in with `AUTH_USER` / `AUTH_PASSWORD`. After login, the UI shows **SERVER OFFLINE** for 1–3 minutes while the model loads — hit **REFRESH** in the sidebar once ready.

---

## Supported Models

Confirmed to work on Tesla T4 (16 GB VRAM):

| Model | HuggingFace ID | VRAM | Quality |
|---|---|---|---|
| Qwen2 1.5B Instruct ✅ recommended | `Qwen/Qwen2-1.5B-Instruct` | ~3 GB | Good |
| TinyLlama 1.1B Chat | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | ~2 GB | Basic |
| Gemma 2B Instruct | `google/gemma-2b-it` | ~5 GB | Good |
| Phi-3 Mini Instruct | `microsoft/Phi-3-mini-4k-instruct` | ~8 GB | Very good |

Switch models by changing `MODEL_ID`:

```bash
-e MODEL_ID=microsoft/Phi-3-mini-4k-instruct
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODEL_ID` | `Qwen/Qwen2-1.5B-Instruct` | HuggingFace model ID to load |
| `GPU_UTIL` | `0.85` | Fraction of GPU VRAM to use (0.0–1.0) |
| `MAX_MODEL_LEN` | `2048` | Maximum context length in tokens |
| `VLLM_HOST` | `http://localhost:8000` | vLLM server URL (used by Streamlit) |
| `JWT_SECRET` | *(required)* | Signing secret for session JWTs — generate with `openssl rand -hex 32` |
| `AUTH_USER` | `admin` | Login username |
| `AUTH_PASSWORD` | `changeme` | Login password — set a real value in production |

---

## Troubleshooting

**`could not select device driver "" with capabilities: [[gpu]]`**
NVIDIA Container Toolkit is not installed or Docker wasn't restarted after install.

**`CUDA out of memory`**
Model too large for available VRAM. Reduce `MAX_MODEL_LEN` or switch to a smaller model.

**`ValueError: chat template not found`**
Use a model with `instruct` or `chat` in the name.

**UI shows SERVER OFFLINE after startup**
Wait 2–3 minutes for the model to load, then click **REFRESH** in the sidebar.

**Container exits immediately with `JWT_SECRET must be set`**
Pass `-e JWT_SECRET=$(openssl rand -hex 32)` on `docker run` — it's required, no default.

**Stuck redirecting to `/login` even with correct credentials**
Cookies are `httponly`/`samesite=lax` over plain HTTP — this is fine for `http://<ip>` access but browsers may block them behind an HTTPS-terminating proxy sending mixed content. Access the UI directly over `http://`, or add TLS termination in front of nginx.

---

## Tech Stack

| Component | Technology |
|---|---|
| Inference Engine | vLLM 0.6.3 |
| Frontend | Streamlit 1.58 |
| Deep Learning | PyTorch 2.4.0 + CUDA 12.1 |
| Containerization | Docker + NVIDIA Container Toolkit |
| GPU | NVIDIA Tesla T4 (16 GB VRAM) |
