# 版权属于全世界无产阶级者

# 交互式发散思维单词记忆工具 (Interactive Sentence Generator)

这是一个基于 Gradio 和 AI 的交互式 Web 应用，旨在通过“发散式思维”帮助用户学习和记忆英语单词。用户输入一个单词，应用会生成一个包含该单词的例句。例句中的每个单词都可以点击，点击后该单词将成为新的输入，从而开启一轮新的“头脑风暴”，帮助用户在语境中建立单词之间的联系。

<img width="1905" height="841" alt="Image" src="https://github.com/user-attachments/assets/59daf721-2532-429d-952f-61eb950ee56e" />
*(请将上面的链接替换为您的应用截图)*

## ✨ 功能亮点

- **🤖 AI 驱动的智能造句**：利用强大的 AI 模型（默认为 DeepSeek）为任意单词生成自然、贴切的例句。
- **🗣️ 交互式例句学习**：生成的例句中每个单词都是一个可点击的按钮，点击即可围绕新单词进行发散学习，探索词汇网络。
- **🔊 真人发音**：集成有道词典的单词发音功能，帮助用户掌握正确读音。音频文件会自动缓存，节省加载时间。
- **📖 详细释义**：除了例句，应用还会提供单词的国际音标（IPA）和多条中文释义（含词性）。
- **📂 历史记录与导航**：所有查询过的单词都会被自动保存。您可以通过“上一个”和“下一个”按钮轻松回顾学习历史。
- **🔧 高度可定制**：您可以在应用的 UI 界面中轻松设置 API Key、修改提示词（Prompt）模板以及界面引导文案，以满足个性化需求。

## 🚀 安装与运行

按照以下步骤在您的本地计算机上运行此应用。

### 1. 克隆仓库

```bash
git clone https://github.com/kungful/Interactive-Sentence-Generator.git
cd Interactive-Sentence-Generator
```


### 2. 安装依赖

建议在虚拟环境中安装，以避免包版本冲突。

```bash
# 创建虚拟环境 (可选)
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 安装所需的包
pip install -r requirements.txt
```

### 3. 配置 API 密钥

此应用需要一个 DeepSeek API 密钥才能工作。

- **方式一（推荐）**：在应用启动后，在网页的 "API Settings" 部分输入您的密钥并保存。密钥将保存在本地的 `.api_key` 文件中。
- **方式二**：创建一个名为 `.api_key` 的文件，并将您的密钥粘贴到文件中。
- **方式三**：设置一个名为 `DEEPSEEK_API_KEY` 的环境变量。

### 4. 运行应用

```bash
python app.py
```

应用启动后，您会在终端看到一个本地 URL (通常是 `http://127.0.0.1:7860`)。在浏览器中打开此链接即可开始使用。

## 🛠️ 配置

您可以在应用的 "UI Settings" 和 "API Settings" 折叠面板中进行自定义配置：

- **API Settings**:
  - **DeepSeek API Base URL**: 默认为 `https://api.deepseek.com`。如果需要，可以更改为其他兼容的 API 端点。
  - **DeepSeek API Key**: 在此处输入和保存您的 API 密钥。
- **UI Settings**:
  - **Instruction Text**: 修改主界面上方的引导性文字。
  - **Prompt Template**: 自定义发送给 AI 的用户提示模板。`{word}` 是单词占位符。
  - **System Prompt**: 自定义发送给 AI 的系统级指令，用于设定 AI 的角色和行为。

所有配置都会自动保存在项目根目录下的相应文件（如 `.instruction_text`, `.prompt_template`）中。

## 💻 技术栈

- **后端**: Python
- **Web 框架**: Gradio
- **AI 模型**: DeepSeek API (可替换为其他兼容 OpenAI 接口的模型)
- **HTTP 请求**: httpx
- **音频服务**: 有道词典

## 🤝 如何贡献

欢迎任何形式的贡献！如果您有好的想法或发现了 Bug，请随时提交 Pull Request 或创建 Issue。

1.  Fork 本仓库
2.  创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4.  推送到分支 (`git push origin feature/AmazingFeature`)
5.  打开一个 Pull Request

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。
