# TashkeelAgent
**An AI-Powered Agent for Automatic Arabic Text Diacritization**

TashkeelAgent is an open-source tool designed to automatically add diacritics (*tashkeel*) to Arabic text using large language models (LLMs).
It tackles one of the most challenging problems in Arabic NLP — producing accurate diacritization while preserving the original text exactly.

---

## 📖 What is *Tashkeel*?
*Tashkeel* refers to the system of diacritical marks in the Arabic language.
Arabic text is usually written without these marks, relying on context for correct pronunciation and meaning. While fluent readers can interpret text without diacritics, they are essential in:

- Historical manuscripts
- Religious scriptures
- Educational material for children or language learners
- Cases where ambiguity must be resolved

Manual diacritization is typically performed by linguistic experts. Existing automated tools often fall short in accuracy, especially for nuanced texts.

---

## 🚀 Why Agentic *Tashkeel*?
With recent advances in LLMs, diacritization can now be performed without specialized neural models or manual annotation.
Modern LLMs are:

- **Highly multilingual** — with deep semantic understanding.
- **Context-aware** — capable of processing extended text to select the correct diacritics.

However, applying LLMs to *tashkeel* introduces challenges:

1. **Preserving Original Text**
   LLMs excel at generating new text but are less reliable at precisely reproducing existing text. Diacritization is fundamentally a “copy-with-modification” task, and unintended alterations to the base content can occur.

2. **Tokenization Limitations**
   Arabic morphology requires precise letter-level handling, which general-purpose LLMs do not natively provide as they operate at token level (a token is a sequence of commonly co-occurring characters).

**TashkeelAgent** overcomes these issues by combining LLM reasoning power with strict safeguards to preserve the integrity of the original text.

> 📌 To the best of our knowledge, TashkeelAgent is the first implementation of *agentic diacritization*, leveraging general-purpose LLMs rather than syntax-based systems or domain-specific neural models.

---

## 🛠 Installation

1. **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/TashkeelAgent.git
    cd TashkeelAgent
    ```

2. **Install `uv` and create a virtual environment**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3. **Install dependencies**
    ```bash
    uv pip install .
    ```
4. **Set API keys**
- Store your LLM provider API key as an environment variable:
    ```bash
    export OPENAI_API_KEY="your_api_key"
    ```
- Or place it in a .env file in the project root.

## 📦 Usage
To diacritize text:
```bash
uv run tashkeel_agent.py <path/to/source.txt> <path/to/target.txt>
```
- <`source.txt`>: Input file containing Arabic text (UTF-8 plain text).
- <`target.txt`>: Output file where diacritized text will be saved.

To run tests:
```bash
uv run pytest
```
> File extensions can be anything, as long as the content is UTF-8 encoded plain text.

## ⚠ Limitations
- Diacritics may not always be accurate.
- No benchmark comparison with other diacritization tools is currently included.

## 📜 License
This project is released under the MIT License.

## 🤝 Contributing
Contributions are welcome!
Feel free to open issues or submit pull requests to improve accuracy, efficiency, or functionality.

## 🙏 Thanks
- [OpenAI](https://openai.com)
