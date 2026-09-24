🎓 智慧树全自动满分考试 (ZhiHuiShu Auto Exam Bot)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![OpenAI Compatible](https://img.shields.io/badge/LLM-OpenAI_API-orange.svg)
结合大语言模型 (LLM) 的智慧树（知到）全自动考试与作业助手。只需一次扫码，即可全自动获取课程列表、拉取考试任务，并调用 AI 完成作答与提交。

---
✨ 核心特性  
🔒 扫码一键登录：内置获取二维码与轮询接口，跨平台自动调用系统自带看图软件打开二维码。使用知到 APP 扫码。  
🤖 AI 智能赋能：完美兼容 OpenAI 标准 API 格式。可自由接入各类大语言模型（如 GPT-4, DeepSeek, Kimi 等），单选、多选。  
🚀 全自动交互：自动拉取当前账号下所有课程，终端交互式选择目标课程，自动分析待考清单。  
🕵️‍♂️ 纯本地运行：代码完全开源，不收集、不上传任何个人隐私数据（学号、姓名、密码等）。  
  
🛠️ 快速开始
1. 环境准备
请确保你的电脑上已安装 Python 3.8 或更高版本。
2. 克隆项目与安装依赖
```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名
pip install requests openai
```
3. 配置大模型 API
在使用前，你需要拥有一个支持 OpenAI 接口格式的大模型 API Key。
使用任意文本编辑器打开 `main.py`（或你主程序的名字），找到代码开头的配置区域：
```python
# ==============================================================================
# 大模型 API 配置区域
# ==============================================================================
API_URL = "https://api.longcat.chat/v1"  # 替换为你的大模型 API 地址
API_KEY = "YOUR_API_KEY_HERE"            # 替换为你的大模型 API_KEY
MODEL_NAME = "Long-Cat"                  # 替换为你使用的模型名称
```
4. 运行脚本
```bash
python main.py
```
运行后，按照终端提示操作即可：
等待系统弹出二维码图片。
手机扫码确认登录。
在终端选择你想刷的课程序号。

---
⚠️ 免责声明 (Disclaimer)
仅供学习交流：本项目属于学术探讨与自动化技术研究，初衷是为了演示 Python 爬虫技术与 LLM API 结合的工程实践。
禁止违规使用：请勿将本脚本用于期末考试等任何违反学校纪律和平台规则的作弊行为。任何因滥用本项目导致的账号封禁、学分清零、违纪处分等后果，均由使用者本人自行承担，项目作者概不负责。
开源协议：本项目遵循 MIT 开源许可证。

---
> 觉得好用的话，别忘了给个 ⭐ **Star** 鼓励一下作者！
