#!/usr/bin/env python3
"""
Add test pages to an existing Confluence space.

This script adds sample pages to an existing space for testing.

Usage:
    python3 add_pages_to_space.py \
        --url http://localhost:8090 \
        --api-token YOUR_API_TOKEN \
        --space-key AIT
"""

import argparse
import sys

try:
    import requests
except ImportError:
    print("Error: requests library is required")
    print("Install with: pip install requests")
    sys.exit(1)


class ConfluencePageAdder:
    """Add pages to an existing Confluence space."""

    def __init__(self, url: str, api_token: str):
        """Initialize with Confluence credentials."""
        self.url = url.rstrip('/')
        self.api_token = api_token
        self.created_pages = []

    def _get_headers(self):
        """Get headers with Bearer token authorization."""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}'
        }

    def _check_space_exists(self, space_key: str) -> bool:
        """Check if space exists."""
        try:
            url = f"{self.url}/rest/api/space/{space_key}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error checking space: {e}")
            return False

    def create_page(self, space_key: str, title: str, content: str) -> bool:
        """Create a page in the space."""
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage",
                }
            },
        }

        try:
            url = f"{self.url}/rest/api/content"
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            page = response.json()
            self.created_pages.append(page)
            print(f"✅ Created page: {title}")
            return True
        except Exception as e:
            print(f"❌ Failed to create page '{title}': {e}")
            return False

    def add_pages(self, space_key: str) -> bool:
        """Add test pages to the space."""
        print(f"\n📄 Adding pages to {space_key} space...")

        # Check space exists
        if not self._check_space_exists(space_key):
            print(f"❌ Space {space_key} does not exist")
            return False

        # Page 1: Overview
        overview = """<ac:rich-text-body>
<h1>AI-Tech Overview</h1>
<p>Welcome to the AI-Tech documentation space. This space contains all information about our AI and machine learning initiatives.</p>

<h2>Table of Contents</h2>
<ul>
<li><a href="#getting-started">Getting Started</a></li>
<li><a href="#architecture">Architecture</a></li>
<li><a href="#models">Models</a></li>
<li><a href="#deployment">Deployment</a></li>
</ul>

<h2>Purpose</h2>
<p>This documentation serves as the central repository for:</p>
<ul>
<li>AI/ML project documentation</li>
<li>Model architecture and design</li>
<li>Training and deployment procedures</li>
<li>Best practices and guidelines</li>
<li>Research findings and experiments</li>
</ul>

<div data-macro-name="info">
<div class="confluence-information-macro-body">
<p>All team members should familiarize themselves with the content in this space.</p>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page(space_key, "Overview", overview)

        # Page 2: Getting Started
        getting_started = """<ac:rich-text-body>
<h1>Getting Started with AI-Tech</h1>
<p>This guide will help you get started with our AI and ML development environment.</p>

<h2>Prerequisites</h2>
<ul>
<li>Python 3.9 or higher</li>
<li>PyTorch or TensorFlow installed</li>
<li>CUDA toolkit (for GPU support)</li>
<li>Jupyter Notebook or JupyterLab</li>
</ul>

<h2>Installation</h2>
<pre><code class="language-bash"># Clone the repository
git clone https://github.com/company/ai-tech.git
cd ai-tech

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt</code></pre>

<h2>Setting Up Your Environment</h2>
<p>Create a <code>.env</code> file in the project root:</p>
<pre><code>PYTHONPATH=.
MODEL_PATH=/models
DATA_PATH=/data
LOG_LEVEL=INFO
CUDA_VISIBLE_DEVICES=0</code></pre>

<h2>Running Your First Model</h2>
<pre><code class="language-python">from ai_tech.models import load_model

# Load a pre-trained model
model = load_model('resnet50')

# Make predictions
predictions = model.predict(input_data)
print(predictions)</code></pre>

<div data-macro-name="warning">
<div class="confluence-information-macro-body">
<p>Ensure CUDA is properly configured before running GPU-intensive models.</p>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page(space_key, "Getting Started", getting_started)

        # Page 3: Model Architecture
        architecture = """<ac:rich-text-body>
<h1>Model Architecture</h1>
<p>Overview of the AI-Tech model architecture and design patterns.</p>

<h2>Core Components</h2>
<table>
<tr><th>Component</th><th>Purpose</th><th>Technology</th></tr>
<tr><td>Feature Extractor</td><td>Extract features from raw data</td><td>PyTorch CNN</td></tr>
<tr><td>Encoder</td><td>Encode features to latent space</td><td>Transformer</td></tr>
<tr><td>Decoder</td><td>Decode from latent space</td><td>Transformer</td></tr>
<tr><td>Classifier</td><td>Classification head</td><td>MLP</td></tr>
</table>

<h2>Architecture Diagram</h2>
<pre><code>Input Data
    ↓
[Feature Extractor]
    ↓
Feature Vector
    ↓
[Encoder (Transformer)]
    ↓
Latent Representation
    ↓
[Decoder (Transformer)]
    ↓
[Classification Head]
    ↓
Output Predictions</code></pre>

<h2>Key Design Decisions</h2>
<ol>
<li><strong>Transformer-based</strong> - For better attention mechanisms</li>
<li><strong>Multi-head attention</strong> - Capture different feature aspects</li>
<li><strong>Layer normalization</strong> - Improve training stability</li>
<li><strong>Residual connections</strong> - Enable deeper networks</li>
</ol>

<h2>Hyperparameters</h2>
<pre><code class="language-python">CONFIG = {
    'hidden_size': 768,
    'num_hidden_layers': 12,
    'num_attention_heads': 12,
    'intermediate_size': 3072,
    'hidden_act': 'gelu',
    'hidden_dropout_prob': 0.1,
    'attention_probs_dropout_prob': 0.1,
    'max_position_embeddings': 512,
    'initializer_range': 0.02,
    'layer_norm_eps': 1e-12,
}</code></pre>

<div data-macro-name="tip">
<div class="confluence-information-macro-body">
<p>See the training guide for details on hyperparameter tuning.</p>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page(space_key, "Model Architecture", architecture)

        # Page 4: Training Guide
        training = """<ac:rich-text-body>
<h1>Training Guide</h1>
<p>Complete guide for training AI-Tech models.</p>

<h2>Dataset Preparation</h2>
<p>Before training, prepare your dataset:</p>
<pre><code class="language-bash">python scripts/prepare_dataset.py \\
  --input /raw/data \\
  --output /prepared/data \\
  --train-split 0.8 \\
  --val-split 0.1 \\
  --test-split 0.1</code></pre>

<h2>Training Configuration</h2>
<p>Create a training config file (YAML):</p>
<pre><code class="language-yaml">training:
  epochs: 100
  batch_size: 32
  learning_rate: 1e-4
  optimizer: adam
  loss_fn: cross_entropy

model:
  hidden_size: 768
  num_layers: 12
  num_heads: 12

validation:
  enabled: true
  freq: 1

logging:
  log_dir: ./logs
  log_level: info</code></pre>

<h2>Running Training</h2>
<pre><code class="language-bash">python train.py \\
  --config config.yaml \\
  --device cuda:0 \\
  --output ./checkpoints</code></pre>

<h2>Monitoring Training</h2>
<p>Monitor training progress with TensorBoard:</p>
<pre><code class="language-bash">tensorboard --logdir ./logs --port 6006</code></pre>

<h2>Common Issues</h2>

<div class="expand-container">
<span class="expand-control-text">Out of Memory (OOM) Error</span>
<div class="expand-content">
<p>Reduce batch size or model size:</p>
<pre><code>batch_size: 16  # Reduce from 32
hidden_size: 512  # Reduce from 768</code></pre>
</div>
</div>

<div class="expand-container">
<span class="expand-control-text">Training Loss Not Decreasing</span>
<div class="expand-content">
<p>Try adjusting learning rate or warmup:</p>
<pre><code>learning_rate: 5e-5  # Reduce learning rate
warmup_steps: 1000  # Add warmup period</code></pre>
</div>
</div>

<div class="expand-container">
<span class="expand-control-text">Validation Metrics Plateau</span>
<div class="expand-content">
<p>Try data augmentation or regularization:</p>
<pre><code>dropout: 0.2  # Increase dropout
augmentation: true  # Enable augmentation</code></pre>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page(space_key, "Training Guide", training)

        # Page 5: Deployment
        deployment = """<ac:rich-text-body>
<h1>Deployment</h1>
<p>Guide for deploying trained models to production.</p>

<h2>Export Model</h2>
<p>Export trained model to ONNX format:</p>
<pre><code class="language-python">import torch
from ai_tech.models import load_model

# Load trained model
model = load_model('checkpoint.pt')
model.eval()

# Create dummy input
dummy_input = torch.randn(1, 3, 224, 224)

# Export to ONNX
torch.onnx.export(
    model,
    dummy_input,
    'model.onnx',
    input_names=['input'],
    output_names=['output'],
    opset_version=12
)</code></pre>

<h2>Docker Deployment</h2>
<p>Create Dockerfile for containerization:</p>
<pre><code class="language-dockerfile">FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run inference server
CMD ["python", "-m", "ai_tech.server"]</code></pre>

<h2>Kubernetes Deployment</h2>
<pre><code class="language-yaml">apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-tech-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-tech
  template:
    metadata:
      labels:
        app: ai-tech
    spec:
      containers:
      - name: inference
        image: company/ai-tech:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            memory: "2Gi"
            cpu: "1"</code></pre>

<h2>Performance Metrics</h2>
<table>
<tr><th>Metric</th><th>Target</th><th>Current</th></tr>
<tr><td>Latency (p99)</td><td>&lt; 100ms</td><td>85ms</td></tr>
<tr><td>Throughput</td><td>&gt; 100 req/s</td><td>120 req/s</td></tr>
<tr><td>Accuracy</td><td>&gt; 95%</td><td>96.2%</td></tr>
<tr><td>Availability</td><td>&gt; 99.9%</td><td>99.95%</td></tr>
</table>

<div data-macro-name="note">
<div class="confluence-information-macro-body">
<p>Always run smoke tests before deploying to production.</p>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page(space_key, "Deployment", deployment)

        # Page 6: Best Practices
        best_practices = """<ac:rich-text-body>
<h1>Best Practices</h1>
<p>Guidelines and best practices for AI-Tech development.</p>

<h2>Code Organization</h2>
<ul>
<li>Keep models in <code>models/</code> directory</li>
<li>Data processing in <code>data/</code> directory</li>
<li>Training scripts in <code>train/</code> directory</li>
<li>Utilities in <code>utils/</code> directory</li>
</ul>

<h2>Version Control</h2>
<p>Always commit important checkpoints:</p>
<pre><code class="language-bash">git add model_checkpoint.pt
git commit -m "feat: add improved resnet50 with 96.2% accuracy"</code></pre>

<h2>Documentation</h2>
<p>Document all models and experiments:</p>
<ul>
<li>Model card with architecture and performance</li>
<li>Training logs and metrics</li>
<li>Dataset information and splits</li>
<li>Hyperparameter configurations</li>
</ul>

<h2>Testing</h2>
<p>Write unit tests for critical functions:</p>
<pre><code class="language-python">import unittest
from ai_tech.models import load_model

class TestModelInference(unittest.TestCase):
    def setUp(self):
        self.model = load_model('model.pt')

    def test_output_shape(self):
        output = self.model.predict(input_data)
        self.assertEqual(output.shape, expected_shape)

    def test_output_range(self):
        output = self.model.predict(input_data)
        self.assertTrue((output >= 0).all())
        self.assertTrue((output <= 1).all())</code></pre>

<h2>Performance Optimization</h2>
<ol>
<li><strong>Model Quantization</strong> - Reduce model size</li>
<li><strong>Knowledge Distillation</strong> - Transfer to smaller model</li>
<li><strong>Pruning</strong> - Remove unnecessary weights</li>
<li><strong>Caching</strong> - Cache frequent computations</li>
</ol>

<div data-macro-name="tip">
<div class="confluence-information-macro-body">
<p>Profile your code regularly to identify bottlenecks.</p>
</div>
</div>
</ac:rich-text-body>"""

        self.create_page(space_key, "Best Practices", best_practices)

    def run(self, space_key: str) -> bool:
        """Run the page addition process."""
        print("\n🚀 Adding Pages to Confluence Space")
        print("=" * 50)

        success = self.add_pages(space_key)

        # Summary
        print("\n" + "=" * 50)
        print("📊 Summary")
        print(f"  Pages created: {len(self.created_pages)}")

        if success:
            print(f"\n✅ Successfully added {len(self.created_pages)} pages to {space_key} space!")
            print("\nPages created:")
            for page in self.created_pages:
                print(f"  • {page.get('title', 'Unknown')}")
            return True
        else:
            print(f"\n⚠️  Some pages failed to create")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add test pages to an existing Confluence space"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8090",
        help="Confluence URL"
    )
    parser.add_argument(
        "--api-token",
        required=True,
        help="Confluence API token"
    )
    parser.add_argument(
        "--space-key",
        required=True,
        help="Space key (e.g., AIT)"
    )

    args = parser.parse_args()

    # Create adder and run
    adder = ConfluencePageAdder(args.url, args.api_token)
    success = adder.run(args.space_key)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
