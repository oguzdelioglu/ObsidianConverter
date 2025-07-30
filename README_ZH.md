<p align="center">
  <img src="logo.png" alt="ObsidianConverter Logo" width="200"/>
</p>

<h1 align="center">ObsidianConverter</h1>

<p align="center">
  一个强大的实用工具，可将纯文本文件转换为结构良好的 Obsidian 笔记，具有智能链接、标记和组织功能。
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README_TR.md">Türkçe</a> |
  <a href="README_ES.md">Español</a> |
  <a href="README_DE.md">Deutsch</a> |
  <a href="README_FR.md">Français</a> |
  <a href="README_ZH.md">中文</a>
</p>

## 功能特点

- **智能内容解析**：利用 LLM 识别自然内容分隔并组织信息
- **自动笔记链接**：使用语义相似性创建相关笔记之间的连接
- **递归目录处理**：处理目录及其子目录中的所有文本文件
- **Obsidian 优化输出**：创建具有适当前置元数据和格式的文件
- **智能标签生成**：基于笔记内容推荐相关标签
- **内容分类**：基于内容主题将笔记组织到逻辑文件夹中
- **增强 Obsidian 集成**：支持提示框、dataview 查询和目录表
- **并行处理**：同时处理多个文件以加快转换速度
- **配置系统**：通过 YAML 配置文件自定义行为
- **统计跟踪**：有关转换过程和笔记创建的详细统计信息
- **多 LLM 支持**：支持 Ollama、OpenAI 或 Anthropic 模型
- **交互式模式**：在保存前审核、编辑和完善笔记
- **Docker 支持**：使用 Docker 和 Docker Compose 轻松设置和运行

## 系统要求

- Python 3.8+
- 以下 LLM 提供者之一：
  - [Ollama](https://ollama.ai/)（默认，本地 LLM 服务）
  - OpenAI API 密钥（适用于 GPT 模型）
  - Anthropic API 密钥（适用于 Claude 模型）
- 所需的 Python 包（参见 `requirements.txt`）
- Docker（可选，用于容器化使用）

## 安装方法

### 方法 1：开发设置
1. 克隆此仓库
2. 创建虚拟环境：`python -m venv venv`
3. 激活环境：
   - 在 macOS/Linux 上：`source venv/bin/activate`
   - 在 Windows 上：`venv\Scripts\activate`
4. 以开发模式安装：`pip install -e .`

### 方法 2：常规安装
1. 克隆此仓库
2. 运行：`pip install .`

### 方法 3：Docker 安装
1. 构建 Docker 镜像：`docker build -t obsidian-converter .`
2. 使用 Docker 运行：`docker run -v $(pwd)/txt:/data/input -v $(pwd)/vault:/data/output obsidian-converter`
3. 或使用 Docker Compose：`docker-compose up`

详细 Docker 说明请参阅 [README_DOCKER.md](README_DOCKER.md)。

### 前提条件
- 对于 Ollama：确保已安装并使用所需模型运行（默认："mistral"）
  - 使用以下命令安装模型：`ollama pull mistral`
- 对于 OpenAI：通过 `--openai-key` 参数或 `OPENAI_API_KEY` 环境变量设置 API 密钥
- 对于 Anthropic：通过 `--anthropic-key` 参数或 `ANTHROPIC_API_KEY` 环境变量设置 API 密钥

## 使用方法

```bash
# 显示帮助信息
obsidian-converter --help

# 基本用法（处理 txt/ 目录中的所有 .txt 文件）
obsidian-converter

# 处理特定文件
obsidian-converter files example.txt subdir/notes.txt

# 清理输出目录
obsidian-converter clean

# 列出所有生成的笔记
obsidian-converter list

# 列出特定类别的笔记
obsidian-converter list --category technical

# 创建配置文件
obsidian-converter config --create --file my_config.yaml

# 查看当前配置
obsidian-converter config --file my_config.yaml

# 使用配置文件
obsidian-converter --config my_config.yaml

# 自定义目录
obsidian-converter --input /path/to/input --output /path/to/output

# 启用并行处理
obsidian-converter --parallel --workers 4

# 在转换前清理输出目录
obsidian-converter --clean

# 使用特定模型
obsidian-converter --model llama2

# 详细日志记录
obsidian-converter --verbose

# 交互式审核模式
obsidian-converter --interactive

# 为交互式模式指定编辑器
obsidian-converter --interactive --editor vim

# 使用不同的 LLM 提供者
obsidian-converter --provider ollama --model llama2
obsidian-converter --provider openai --model gpt-3.5-turbo --openai-key YOUR_API_KEY
obsidian-converter --provider anthropic --model claude-3-sonnet-20240229 --anthropic-key YOUR_API_KEY

# 所有选项组合
obsidian-converter --input /path/to/input --output /path/to/output --model llama2 \
  --similarity 0.4 --max-links 10 --clean --verbose --parallel --workers 8 --interactive
```

## 配置

可以通过命令行参数或 YAML 配置文件配置该工具：

```bash
# 创建默认配置文件
obsidian-converter config --create --file my_config.yaml
```

配置文件示例：

```yaml
# 核心设置
input_dir: txt
output_dir: vault
model: mistral

# LLM 提供者设置
provider: ollama      # ollama, openai, 或 anthropic
openai_api_key: null  # 您的 OpenAI API 密钥（或使用环境变量）
anthropic_api_key: null  # 您的 Anthropic API 密钥（或使用环境变量）
llm_temperature: 0.7  # LLM 响应的温度

# 处理设置
similarity_threshold: 0.3
max_links: 5
use_cache: true
cache_file: .llm_cache.json

# 性能设置
parallel_processing: true
max_workers: 4
chunk_size: 1000000  # 大文件的 1MB 块大小

# Obsidian 特定设置
obsidian_features:
  callouts: true
  dataview: true
  toc: true
  graph_metadata: true

# 包含/排除的文件模式
include_patterns:
  - '*.txt'
  - '*.md'
exclude_patterns:
  - '*.tmp'
  - '~*'
```

您可以使用此配置文件：

```bash
obsidian-converter --config my_config.yaml
```

## 高级功能

### 统计和报告

该工具生成有关转换过程的统计信息，包括：

- 处理的文件数和创建的笔记数
- 类别和标签分布
- 单词和字符计数
- LLM 性能指标
- 处理时间

JSON 报告会自动保存在输出文件夹内的 `.stats` 目录中。

### 并行处理

对于大型文档集，启用并行处理以加快转换速度：

```bash
obsidian-converter --parallel --workers 4
```

### 内存优化

自动分块处理大文件以减少内存使用。您可以在配置文件中自定义块大小。

### 自定义文件模式

默认情况下，该工具处理 `.txt` 文件，但您可以在配置文件中自定义模式：

```yaml
include_patterns:
  - '*.txt'  # 文本文件
  - '*.md'   # Markdown 文件
  - 'notes_*.log'  # 特定命名的日志文件
```

### 交互式模式

通过交互式模式在保存前审核和编辑每个笔记：

```bash
obsidian-converter --interactive
```

在交互式模式中，您可以：
- 在您偏好的文本编辑器中编辑笔记
- 丢弃不想保留的笔记
- 更改笔记类别
- 在决定前查看完整内容
- 审核元数据和建议的链接

要指定自定义编辑器（而不是使用系统默认编辑器）：

```bash
obsidian-converter --interactive --editor vim
```

## 输出示例

对于包含混合笔记的文本文件，ObsidianConverter 将生成多个结构良好的 Markdown 文件：

```markdown
---
title: 项目规划
date: 2023-06-15
tags: [规划, 项目管理, 工作流]
category: 工作
---

## 项目规划

这里是提取出的关于项目规划的内容...

## 相关笔记
- [[会议笔记 - Q2 审查]]
- [[任务优先级方法]]
```

## 工作原理

1. 读取输入目录及其子目录中的所有 `.txt` 文件
2. 使用 LLM 分析并将内容分解为逻辑部分
3. 为每个笔记创建适当的元数据（前置数据）
4. 建立相关笔记之间的连接
5. 在清晰的文件夹结构中组织笔记
6. 生成完整的 Obsidian 知识库

## 许可证

MIT