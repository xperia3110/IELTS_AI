# IELTS AI

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini-purple.svg)](https://deepmind.google/technologies/gemini/)
[![spaCy](https://img.shields.io/badge/spaCy-NLP-blue.svg)](https://spacy.io/)
[![Whisper](https://img.shields.io/badge/Whisper-Speech-blue.svg)](https://github.com/openai/whisper)

IELTS AI is an intelligent, AI-driven web platform created to assist users in preparing for the IELTS exam. This system offers a personalized and adaptive learning environment that mimics real-world testing scenarios, helping learners improve a crucial IELTS component — Speaking.

Designed with both learners and educators in mind, the platform leverages advanced NLP models like OpenAI Whisper, spaCy, and Google Gemini to evaluate language proficiency, provide detailed feedback, and simulate actual test conditions. Whether you're targeting a higher band score or just getting started, IELTS AI supports your journey with real-time analysis and progress tracking.

## 🚀 Features

- 🗣️ Speaking practice with real-time pronunciation analysis
- 📊 Progress tracking and analytics dashboard
- 🤖 Multiple AI models for comprehensive evaluation

## 🛠 Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python
- **AI Modules**: 
  - Google Gemini for advanced analysis
  - spaCy for NLP tasks
  - Whisper for speech recognition

## ⚙️ Getting Started

### ✅ Prerequisites

- Python 3.x
- OpenAI API key
- Google Gemini API key
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space

### 🔧 Installation

1. **Clone the repository**
```bash
git clone https://github.com/xperia3110/IELTS_AI.git
cd IELTS_AI
```

2. **Set up environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Download NLP Models**
```bash
python -m spacy download en_core_web_sm
python -m whisper download base
```

4. **Configure API keys**
Create a `.env` file in the backend directory:
```env
GEMINI_API_KEY=your_gemini_api_key
```

5. **Run the App**
```bash
# Terminal 1 - Backend
cd backend && python3 app.py

# Terminal 2 - Frontend
cd frontend && python3 -m http.server 8000
```

Access the application at:
- Frontend: http://localhost:8000
- Backend API: http://localhost:4000 (Adjust it according to your system)

## 📝 Usage

1. Open your browser and navigate to http://localhost:8000
2. Follow the on-screen instructions to complete exercises
3. Review your performance and feedback

## 🤝 Contributing

We welcome all contributions! Here's how you can help:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## 📄 License

Licensed under the MIT License. See [LICENSE](LICENSE) for more info.

## 🙏 Acknowledgments

- OpenAI for GPT and Whisper models
- Google for Gemini API
- spaCy team for NLP tools
- All contributors and users of IELTS AI

## 📞 Support

If you encounter any issues or have questions, please:
1. Check the [Issues](https://github.com/xperia3110/IELTS_AI/issues) page
2. Create a new issue if your problem isn't already listed
---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/xperia3110">Collins Shibi</a></sub>
</div>
