#!/usr/bin/env python3
"""
Create 30 hierarchical AI documentation pages in Confluence.

This script creates a comprehensive AI knowledge base with parent-child page relationships.

Usage:
    python3 create_ai_content.py \
        --url http://localhost:8090 \
        --api-token YOUR_API_TOKEN \
        --space-key AIT
"""

import argparse
import sys
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: requests library is required")
    print("Install with: pip install requests")
    sys.exit(1)


class AIContentCreator:
    """Create hierarchical AI documentation in Confluence."""

    def __init__(self, url: str, api_token: str):
        """Initialize with Confluence credentials."""
        self.url = url.rstrip('/')
        self.api_token = api_token
        self.created_pages = {}

    def _get_headers(self):
        """Get headers with Bearer token authorization."""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}'
        }

    def create_page(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> Optional[str]:
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

        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]

        try:
            url = f"{self.url}/rest/api/content"
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            page = response.json()
            page_id = page.get('id')
            self.created_pages[title] = page_id
            print(f"✅ Created: {title} (ID: {page_id})")
            return page_id
        except Exception as e:
            print(f"❌ Failed to create '{title}': {e}")
            return None

    def create_ai_content(self, space_key: str) -> bool:
        """Create all AI documentation pages."""
        print(f"\n🚀 Creating 30 AI documentation pages in {space_key} space...\n")

        # Root page
        root_id = self.create_page(space_key, "AI Knowledge Base", """<ac:rich-text-body>
<h1>AI Knowledge Base</h1>
<p>Comprehensive documentation covering all aspects of Artificial Intelligence, from fundamentals to advanced applications.</p>

<h2>Topics Covered</h2>
<ul>
<li>Fundamentals of AI</li>
<li>Machine Learning</li>
<li>Deep Learning</li>
<li>Natural Language Processing</li>
<li>Computer Vision</li>
<li>Reinforcement Learning</li>
<li>AI Ethics & Society</li>
</ul>

<div data-macro-name="info">
<div class="confluence-information-macro-body">
<p>This knowledge base contains 30+ pages of AI documentation organized hierarchically by topic and subtopic.</p>
</div>
</div>
</ac:rich-text-body>""")

        # SECTION 1: Fundamentals
        fund_id = self.create_page(space_key, "1. AI Fundamentals", """<ac:rich-text-body>
<h1>AI Fundamentals</h1>
<p>Core concepts and history of Artificial Intelligence.</p>
<h2>What You'll Learn</h2>
<ul>
<li>Definition and scope of AI</li>
<li>Historical development</li>
<li>AI vs Machine Learning vs Deep Learning</li>
<li>Key concepts and terminology</li>
</ul>
</ac:rich-text-body>""", root_id)

        self.create_page(space_key, "1.1 History of AI", """<ac:rich-text-body>
<h1>History of AI</h1>
<table>
<tr><th>Period</th><th>Key Developments</th><th>Notable Researchers</th></tr>
<tr><td>1950s</td><td>Turing Test, Dartmouth Conference</td><td>Turing, McCarthy, Minsky</td></tr>
<tr><td>1960s-70s</td><td>Expert Systems</td><td>Feigenbaum, Buchanan</td></tr>
<tr><td>1980s-90s</td><td>AI Winter, Rise of Machine Learning</td><td>Hinton, LeCun</td></tr>
<tr><td>2000s-2010s</td><td>Deep Learning Revolution</td><td>Bengio, LeCun, Hinton</td></tr>
<tr><td>2020s</td><td>Large Language Models, Foundation Models</td><td>OpenAI, DeepMind, Meta</td></tr>
</table>
</ac:rich-text-body>""", fund_id)

        self.create_page(space_key, "1.2 Core AI Concepts", """<ac:rich-text-body>
<h1>Core AI Concepts</h1>
<h2>Intelligence</h2>
<p>The ability to learn, reason, and solve problems.</p>
<h2>Agents</h2>
<p>Systems that perceive environment and take actions.</p>
<h2>Knowledge Representation</h2>
<p>How information is stored and used by AI systems.</p>
<h2>Search Algorithms</h2>
<pre><code class="language-python">def depth_first_search(graph, node, visited=None):
    if visited is None:
        visited = set()
    visited.add(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            depth_first_search(graph, neighbor, visited)
    return visited</code></pre>
</ac:rich-text-body>""", fund_id)

        self.create_page(space_key, "1.3 AI vs ML vs DL", """<ac:rich-text-body>
<h1>AI vs Machine Learning vs Deep Learning</h1>
<h2>Hierarchy</h2>
<pre><code>Artificial Intelligence (Broad)
    ├─ Symbolic AI (Rule-based)
    ├─ Machine Learning (Data-driven)
    │   ├─ Supervised Learning
    │   ├─ Unsupervised Learning
    │   ├─ Reinforcement Learning
    │   └─ Deep Learning (Neural Networks)
    │       ├─ CNNs (Computer Vision)
    │       ├─ RNNs (Sequences)
    │       ├─ Transformers (NLP)
    │       └─ GANs (Generation)
    └─ Robotics</code></pre>
</ac:rich-text-body>""", fund_id)

        # SECTION 2: Machine Learning
        ml_id = self.create_page(space_key, "2. Machine Learning", """<ac:rich-text-body>
<h1>Machine Learning</h1>
<p>Learn how systems improve from data without explicit programming.</p>
<h2>Key Topics</h2>
<ul>
<li>Supervised Learning</li>
<li>Unsupervised Learning</li>
<li>Reinforcement Learning</li>
<li>Evaluation Metrics</li>
</ul>
</ac:rich-text-body>""", root_id)

        self.create_page(space_key, "2.1 Supervised Learning", """<ac:rich-text-body>
<h1>Supervised Learning</h1>
<h2>Regression</h2>
<p>Predicting continuous values:</p>
<pre><code class="language-python">from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X_train, y_train)
predictions = model.predict(X_test)</code></pre>
<h2>Classification</h2>
<pre><code class="language-python">from sklearn.ensemble import RandomForestClassifier
classifier = RandomForestClassifier(n_estimators=100)
classifier.fit(X_train, y_train)</code></pre>
</ac:rich-text-body>""", ml_id)

        self.create_page(space_key, "2.2 Unsupervised Learning", """<ac:rich-text-body>
<h1>Unsupervised Learning</h1>
<h2>Clustering</h2>
<pre><code class="language-python">from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=3)
clusters = kmeans.fit_predict(data)</code></pre>
<h2>Dimensionality Reduction</h2>
<pre><code class="language-python">from sklearn.decomposition import PCA
pca = PCA(n_components=2)
reduced = pca.fit_transform(data)</code></pre>
</ac:rich-text-body>""", ml_id)

        self.create_page(space_key, "2.3 Model Evaluation", """<ac:rich-text-body>
<h1>Model Evaluation Metrics</h1>
<table>
<tr><th>Metric</th><th>Use Case</th><th>Formula</th></tr>
<tr><td>Accuracy</td><td>Classification</td><td>(TP+TN)/(TP+TN+FP+FN)</td></tr>
<tr><td>Precision</td><td>Positive Predictions</td><td>TP/(TP+FP)</td></tr>
<tr><td>Recall</td><td>Actual Positives</td><td>TP/(TP+FN)</td></tr>
<tr><td>F1-Score</td><td>Balanced Metric</td><td>2*(Precision*Recall)/(Precision+Recall)</td></tr>
<tr><td>RMSE</td><td>Regression</td><td>√(1/n Σ(y-ŷ)²)</td></tr>
</table>
</ac:rich-text-body>""", ml_id)

        # SECTION 3: Deep Learning
        dl_id = self.create_page(space_key, "3. Deep Learning", """<ac:rich-text-body>
<h1>Deep Learning</h1>
<p>Neural networks with multiple layers for complex pattern recognition.</p>
<h2>Architectures</h2>
<ul>
<li>Convolutional Neural Networks (CNN)</li>
<li>Recurrent Neural Networks (RNN)</li>
<li>Transformer Models</li>
<li>Generative Models</li>
</ul>
</ac:rich-text-body>""", root_id)

        self.create_page(space_key, "3.1 Neural Networks Basics", """<ac:rich-text-body>
<h1>Neural Networks Basics</h1>
<h2>Components</h2>
<ul>
<li>Neurons (Perceptrons)</li>
<li>Layers (Input, Hidden, Output)</li>
<li>Activation Functions (ReLU, Sigmoid, Tanh)</li>
<li>Backpropagation Algorithm</li>
</ul>
<h2>Training</h2>
<pre><code class="language-python">import torch.nn as nn
model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters())</code></pre>
</ac:rich-text-body>""", dl_id)

        self.create_page(space_key, "3.2 Convolutional Neural Networks", """<ac:rich-text-body>
<h1>Convolutional Neural Networks (CNN)</h1>
<h2>Architecture</h2>
<pre><code>Input Image
    ↓
[Convolution] - Detect features
    ↓
[ReLU] - Non-linearity
    ↓
[Pooling] - Reduce dimensions
    ↓
[Flatten]
    ↓
[Fully Connected Layers]
    ↓
Output (Classification)</code></pre>
<h2>Popular Models</h2>
<ul>
<li>LeNet (1998)</li>
<li>AlexNet (2012)</li>
<li>VGGNet (2014)</li>
<li>ResNet (2015)</li>
<li>DenseNet (2016)</li>
</ul>
</ac:rich-text-body>""", dl_id)

        self.create_page(space_key, "3.3 Recurrent Neural Networks", """<ac:rich-text-body>
<h1>Recurrent Neural Networks (RNN)</h1>
<h2>Variants</h2>
<ul>
<li><strong>LSTM</strong> (Long Short-Term Memory) - Handles long-term dependencies</li>
<li><strong>GRU</strong> (Gated Recurrent Unit) - Simpler LSTM variant</li>
<li><strong>Bidirectional RNN</strong> - Process sequences both directions</li>
</ul>
<h2>Applications</h2>
<ul>
<li>Machine Translation</li>
<li>Sentiment Analysis</li>
<li>Time Series Forecasting</li>
<li>Speech Recognition</li>
</ul>
</ac:rich-text-body>""", dl_id)

        self.create_page(space_key, "3.4 Transformer Models", """<ac:rich-text-body>
<h1>Transformer Models</h1>
<h2>Key Components</h2>
<ul>
<li>Self-Attention Mechanism</li>
<li>Multi-Head Attention</li>
<li>Positional Encoding</li>
<li>Feed-Forward Networks</li>
</ul>
<h2>Famous Models</h2>
<pre><code>BERT (2018) - Bidirectional Encoder
GPT (2018) - Generative Pre-trained Transformer
ELECTRA (2020) - Efficient Learning
RoBERTa (2019) - Robustly Optimized BERT
T5 (2019) - Text-to-Text Transfer Transformer
ALBERT (2019) - A Lite BERT</code></pre>
</ac:rich-text-body>""", dl_id)

        # SECTION 4: NLP
        nlp_id = self.create_page(space_key, "4. Natural Language Processing", """<ac:rich-text-body>
<h1>Natural Language Processing (NLP)</h1>
<p>Teaching computers to understand and generate human language.</p>
<h2>Core Tasks</h2>
<ul>
<li>Tokenization</li>
<li>Sentiment Analysis</li>
<li>Named Entity Recognition</li>
<li>Machine Translation</li>
<li>Question Answering</li>
</ul>
</ac:rich-text-body>""", root_id)

        self.create_page(space_key, "4.1 Text Preprocessing", """<ac:rich-text-body>
<h1>Text Preprocessing</h1>
<h2>Steps</h2>
<ul>
<li>Lowercasing</li>
<li>Tokenization</li>
<li>Removing Stopwords</li>
<li>Stemming/Lemmatization</li>
<li>Vectorization</li>
</ul>
<h2>Implementation</h2>
<pre><code class="language-python">from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
tokens = word_tokenize(text.lower())
stop_words = set(stopwords.words('english'))
filtered = [t for t in tokens if t not in stop_words]</code></pre>
</ac:rich-text-body>""", nlp_id)

        self.create_page(space_key, "4.2 Sentiment Analysis", """<ac:rich-text-body>
<h1>Sentiment Analysis</h1>
<h2>Approaches</h2>
<ul>
<li><strong>Lexicon-based</strong> - Use word sentiment scores</li>
<li><strong>Machine Learning</strong> - Train classifiers</li>
<li><strong>Deep Learning</strong> - Neural networks</li>
<li><strong>Pre-trained Models</strong> - BERT, RoBERTa</li>
</ul>
<h2>Example</h2>
<pre><code class="language-python">from transformers import pipeline
sentiment_pipeline = pipeline("sentiment-analysis")
result = sentiment_pipeline("I love this product!")
# Output: {'label': 'POSITIVE', 'score': 0.99}</code></pre>
</ac:rich-text-body>""", nlp_id)

        self.create_page(space_key, "4.3 Named Entity Recognition", """<ac:rich-text-body>
<h1>Named Entity Recognition (NER)</h1>
<h2>Entity Types</h2>
<ul>
<li>Person</li>
<li>Organization</li>
<li>Location</li>
<li>Date</li>
<li>Money</li>
<li>Product</li>
</ul>
<h2>Tools</h2>
<ul>
<li>spaCy</li>
<li>NLTK</li>
<li>Hugging Face Transformers</li>
<li>Stanford NER</li>
</ul>
</ac:rich-text-body>""", nlp_id)

        # SECTION 5: Computer Vision
        cv_id = self.create_page(space_key, "5. Computer Vision", """<ac:rich-text-body>
<h1>Computer Vision</h1>
<p>Enabling machines to interpret and understand visual information.</p>
<h2>Main Tasks</h2>
<ul>
<li>Image Classification</li>
<li>Object Detection</li>
<li>Semantic Segmentation</li>
<li>Image Generation</li>
</ul>
</ac:rich-text-body>""", root_id)

        self.create_page(space_key, "5.1 Image Classification", """<ac:rich-text-body>
<h1>Image Classification</h1>
<h2>Popular Datasets</h2>
<ul>
<li>ImageNet (1000 classes)</li>
<li>CIFAR-10 (10 classes)</li>
<li>MNIST (Handwritten digits)</li>
<li>Fashion-MNIST (Clothing items)</li>
</ul>
<h2>Benchmarks</h2>
<table>
<tr><th>Model</th><th>ImageNet Top-1 Accuracy</th><th>Parameters</th></tr>
<tr><td>ResNet-50</td><td>76.1%</td><td>25.5M</td></tr>
<tr><td>EfficientNet-B7</td><td>84.4%</td><td>66M</td></tr>
<tr><td>Vision Transformer</td><td>85.1%</td><td>307M</td></tr>
</table>
</ac:rich-text-body>""", cv_id)

        self.create_page(space_key, "5.2 Object Detection", """<ac:rich-text-body>
<h1>Object Detection</h1>
<h2>Algorithms</h2>
<ul>
<li><strong>YOLO</strong> (You Only Look Once) - Real-time detection</li>
<li><strong>R-CNN</strong> (Region-based CNN) - Accurate detection</li>
<li><strong>SSD</strong> (Single Shot MultiBox Detector) - Balance speed/accuracy</li>
<li><strong>Faster R-CNN</strong> - Improved R-CNN</li>
</ul>
</ac:rich-text-body>""", cv_id)

        self.create_page(space_key, "5.3 Semantic Segmentation", """<ac:rich-text-body>
<h1>Semantic Segmentation</h1>
<h2>Architectures</h2>
<ul>
<li>FCN (Fully Convolutional Networks)</li>
<li>U-Net</li>
<li>DeepLab</li>
<li>SegNet</li>
</ul>
<h2>Applications</h2>
<ul>
<li>Medical Image Analysis</li>
<li>Autonomous Driving</li>
<li>Scene Understanding</li>
<li>Satellite Imagery</li>
</ul>
</ac:rich-text-body>""", cv_id)

        # SECTION 6: Reinforcement Learning
        rl_id = self.create_page(space_key, "6. Reinforcement Learning", """<ac:rich-text-body>
<h1>Reinforcement Learning</h1>
<p>Training agents to make optimal decisions through interaction with environment.</p>
<h2>Core Concepts</h2>
<ul>
<li>Markov Decision Process (MDP)</li>
<li>Value Functions</li>
<li>Policy Gradient</li>
<li>Q-Learning</li>
</ul>
</ac:rich-text-body>""", root_id)

        self.create_page(space_key, "6.1 Q-Learning", """<ac:rich-text-body>
<h1>Q-Learning</h1>
<h2>Algorithm</h2>
<pre><code class="language-python">import numpy as np
Q = np.zeros((states, actions))
for episode in range(episodes):
    state = env.reset()
    for step in range(max_steps):
        action = select_action(state, Q)
        next_state, reward = env.step(action)
        Q[state, action] += alpha * (reward + gamma * max(Q[next_state]) - Q[state, action])
        state = next_state</code></pre>
<h2>Applications</h2>
<ul>
<li>Game Playing (Atari)</li>
<li>Robot Control</li>
<li>Resource Allocation</li>
</ul>
</ac:rich-text-body>""", rl_id)

        self.create_page(space_key, "6.2 Policy Gradient Methods", """<ac:rich-text-body>
<h1>Policy Gradient Methods</h1>
<h2>Algorithms</h2>
<ul>
<li>REINFORCE</li>
<li>Actor-Critic</li>
<li>PPO (Proximal Policy Optimization)</li>
<li>A3C (Asynchronous Advantage Actor-Critic)</li>
</ul>
<h2>Advantages</h2>
<ul>
<li>Direct policy optimization</li>
<li>Works with continuous actions</li>
<li>Better convergence properties</li>
</ul>
</ac:rich-text-body>""", rl_id)

        # SECTION 7: AI Ethics & Society
        ethics_id = self.create_page(space_key, "7. AI Ethics & Society", """<ac:rich-text-body>
<h1>AI Ethics and Society</h1>
<p>Responsible development and deployment of AI systems.</p>
<h2>Key Issues</h2>
<ul>
<li>Fairness and Bias</li>
<li>Transparency and Explainability</li>
<li>Privacy</li>
<li>Accountability</li>
<li>Job Impact</li>
</ul>
</ac:rich-text-body>""", root_id)

        self.create_page(space_key, "7.1 Bias and Fairness", """<ac:rich-text-body>
<h1>Bias and Fairness in AI</h1>
<h2>Types of Bias</h2>
<ul>
<li><strong>Data Bias</strong> - Skewed training data</li>
<li><strong>Algorithmic Bias</strong> - Flawed algorithms</li>
<li><strong>Human Bias</strong> - Designer assumptions</li>
<li><strong>Measurement Bias</strong> - Metric selection</li>
</ul>
<h2>Mitigation Strategies</h2>
<ul>
<li>Diverse training data</li>
<li>Bias detection tools</li>
<li>Fair representation</li>
<li>Regular audits</li>
</ul>
</ac:rich-text-body>""", ethics_id)

        self.create_page(space_key, "7.2 Explainability and Interpretability", """<ac:rich-text-body>
<h1>Explainability and Interpretability</h1>
<h2>Methods</h2>
<ul>
<li>LIME (Local Interpretable Model-agnostic Explanations)</li>
<li>SHAP (SHapley Additive exPlanations)</li>
<li>Feature Importance</li>
<li>Attention Visualization</li>
</ul>
<h2>Tools</h2>
<pre><code class="language-python">import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)
shap.summary_plot(shap_values, X)</code></pre>
</ac:rich-text-body>""", ethics_id)

        self.create_page(space_key, "7.3 Privacy and Data Protection", """<ac:rich-text-body>
<h1>Privacy and Data Protection</h1>
<h2>Techniques</h2>
<ul>
<li>Differential Privacy</li>
<li>Federated Learning</li>
<li>Data Anonymization</li>
<li>Encryption</li>
</ul>
<h2>Regulations</h2>
<ul>
<li>GDPR (General Data Protection Regulation)</li>
<li>CCPA (California Consumer Privacy Act)</li>
<li>AI Act (EU)</li>
</ul>
</ac:rich-text-body>""", ethics_id)

        # SECTION 8: Advanced Topics
        adv_id = self.create_page(space_key, "8. Advanced Topics", """<ac:rich-text-body>
<h1>Advanced AI Topics</h1>
<p>Cutting-edge research and emerging areas in AI.</p>
<h2>Topics</h2>
<ul>
<li>Meta-Learning</li>
<li>Transfer Learning</li>
<li>Few-Shot Learning</li>
<li>Multimodal Learning</li>
</ul>
</ac:rich-text-body>""", root_id)

        self.create_page(space_key, "8.1 Transfer Learning", """<ac:rich-text-body>
<h1>Transfer Learning</h1>
<h2>Concept</h2>
<p>Leverage knowledge from one task to improve another task.</p>
<h2>Strategies</h2>
<ul>
<li>Feature Extraction - Use pre-trained features</li>
<li>Fine-tuning - Adapt pre-trained model</li>
<li>Domain Adaptation - Reduce domain gap</li>
</ul>
<h2>Benefits</h2>
<ul>
<li>Reduced training time</li>
<li>Better performance with limited data</li>
<li>Lower computational cost</li>
</ul>
</ac:rich-text-body>""", adv_id)

        self.create_page(space_key, "8.2 Few-Shot Learning", """<ac:rich-text-body>
<h1>Few-Shot Learning</h1>
<h2>Approaches</h2>
<ul>
<li>Prototypical Networks</li>
<li>Matching Networks</li>
<li>Model-Agnostic Meta-Learning (MAML)</li>
<li>Siamese Networks</li>
</ul>
<h2>Applications</h2>
<ul>
<li>One-shot learning</li>
<li>Zero-shot learning</li>
<li>Domain adaptation</li>
</ul>
</ac:rich-text-body>""", adv_id)

        self.create_page(space_key, "8.3 Multimodal Learning", """<ac:rich-text-body>
<h1>Multimodal Learning</h1>
<h2>Modalities</h2>
<ul>
<li>Vision (Images, Videos)</li>
<li>Language (Text)</li>
<li>Audio (Speech, Music)</li>
<li>Time Series (Sensor Data)</li>
</ul>
<h2>Models</h2>
<ul>
<li>CLIP (Contrastive Language-Image)</li>
<li>ViLBERT (Vision Language BERT)</li>
<li>DALL-E (Text-to-Image)</li>
<li>GPT-4V (Multimodal GPT)</li>
</ul>
</ac:rich-text-body>""", adv_id)

        # SECTION 9: Practical Implementation
        impl_id = self.create_page(space_key, "9. Practical Implementation", """<ac:rich-text-body>
<h1>Practical AI Implementation</h1>
<p>Best practices for building production AI systems.</p>
<h2>Workflows</h2>
<ul>
<li>Data Pipeline</li>
<li>Model Training</li>
<li>Evaluation</li>
<li>Deployment</li>
<li>Monitoring</li>
</ul>
</ac:rich-text-body>""", root_id)

        self.create_page(space_key, "9.1 Data Pipeline", """<ac:rich-text-body>
<h1>Building Data Pipelines</h1>
<h2>Steps</h2>
<ol>
<li>Data Collection</li>
<li>Data Cleaning</li>
<li>Feature Engineering</li>
<li>Data Validation</li>
<li>Data Storage</li>
</ol>
<h2>Tools</h2>
<ul>
<li>Apache Spark</li>
<li>Apache Airflow</li>
<li>Pandas</li>
<li>DVC (Data Version Control)</li>
</ul>
</ac:rich-text-body>""", impl_id)

        self.create_page(space_key, "9.2 Model Training Pipeline", """<ac:rich-text-body>
<h1>Model Training Pipeline</h1>
<h2>Components</h2>
<ul>
<li>Hyperparameter Tuning</li>
<li>Cross-Validation</li>
<li>Model Selection</li>
<li>Regularization</li>
<li>Checkpointing</li>
</ul>
<h2>Tools</h2>
<ul>
<li>MLflow</li>
<li>Weights & Biases</li>
<li>Kubeflow</li>
<li>Ray Tune</li>
</ul>
</ac:rich-text-body>""", impl_id)

        self.create_page(space_key, "9.3 Production Deployment", """<ac:rich-text-body>
<h1>Deploying Models to Production</h1>
<h2>Considerations</h2>
<ul>
<li>Scalability</li>
<li>Latency</li>
<li>Reliability</li>
<li>Monitoring</li>
<li>Version Control</li>
</ul>
<h2>Deployment Options</h2>
<ul>
<li>REST API (Flask, FastAPI)</li>
<li>Cloud Platforms (AWS SageMaker, GCP Vertex AI)</li>
<li>Edge Deployment (TensorFlow Lite, ONNX)</li>
<li>Kubernetes</li>
</ul>
</ac:rich-text-body>""", impl_id)

        return True

    def run(self, space_key: str) -> bool:
        """Run the content creation process."""
        try:
            success = self.create_ai_content(space_key)

            print("\n" + "=" * 60)
            print(f"📊 Summary: {len(self.created_pages)} pages created")
            print("=" * 60)

            if success:
                print(f"\n✅ Successfully created {len(self.created_pages)} AI documentation pages!")
                return True
            else:
                print(f"\n⚠️  Some pages failed to create")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create 30 hierarchical AI documentation pages"
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

    creator = AIContentCreator(args.url, args.api_token)
    success = creator.run(args.space_key)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
