import os
import sys
import time
import json
import re
import requests
from base64 import b64decode
from openai import OpenAI

# ==============================================================================
# 配置文件区域 - 使用前请按需修改
# ==============================================================================

# 1. 大模型 API 配置区域 (默认留空，供用户自己配置)
API_URL = " "  # 替换为你的大模型 API 地址 (如果是官方 OpenAI 可留空或填默认)
API_KEY = "YOUR_API_KEY_HERE"  # 替换为你的大模型 API_KEY
MODEL_NAME = " "  # 替换为你使用的模型名称

# 2. 考试目标 配置区域
COURSE_ID = ""  # 替换为你要考试的 COURSE_ID

# 3. 试卷列表 (请根据抓包结果替换对应的 test_id 和 paper_id)
EXAM_LIST = [
    {"chapter": "第一章", "test_id": " ", "paper_id": " "},
    # 根据需要在此处继续添加其他章节...
]


class ZhiHuiShuQRLogin:
    """智慧树扫码登录模块"""

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/134.0.0.0 Safari/537.36"
        }
        self.session.headers.update(self.headers)

    def _open_image(self, file_path):
        """跨平台自动打开二维码图片"""
        try:
            if sys.platform.startswith('darwin'):  # macOS
                os.system(f'open "{file_path}"')
            elif os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # Linux
                os.system(f'xdg-open "{file_path}"')
        except Exception:
            pass

    def login(self):
        print("\n▶️ 开始获取登录二维码...")
        qr_page = "https://passport.zhihuishu.com/qrCodeLogin/getLoginQrImg"
        query_page = "https://passport.zhihuishu.com/qrCodeLogin/getLoginQrInfo"
        login_page = "https://passport.zhihuishu.com/login?service=https://onlineservice-api.zhihuishu.com/login/gologin"

        try:
            # 1. 获取二维码图片与 Token
            res = self.session.get(qr_page, timeout=10).json()
            qr_token = res.get("qrToken")
            img_data = b64decode(res.get("img"))

            qr_file = "login_qr.png"
            with open(qr_file, "wb") as f:
                f.write(img_data)

            print(f"✅ 二维码已保存至当前目录：{qr_file}")
            self._open_image(qr_file)
            print("⏳ 请使用手机【知到APP】或【微信】扫码登录...")

            # 2. 轮询扫码状态
            scanned = False
            while True:
                time.sleep(1.5)
                status_res = self.session.get(query_page, params={"qrToken": qr_token}, timeout=10).json()
                status = status_res.get("status")

                if status == -1:
                    pass  # 尚未扫码
                elif status == 0:
                    if not scanned:
                        print("👀 已扫码，请在手机上点击确认！")
                        scanned = True
                elif status == 1:
                    print("🎉 登录成功！正在获取身份凭证...")
                    once_pwd = status_res.get("oncePassword")

                    # 3. 换取最终的 Cookie
                    self.session.get(login_page, params={"pwd": once_pwd}, timeout=10)
                    cookie_str = "; ".join([f"{k}={v}" for k, v in self.session.cookies.get_dict().items()])
                    return cookie_str
                elif status == 2:
                    print("❌ 二维码已过期，请重新运行脚本。")
                    return None
                elif status == 3:
                    print("❌ 登录已取消。")
                    return None

        except Exception as e:
            print(f"❌ 登录请求出现异常: {e}")
            return None


class ZhiHuiShuAutoExam:
    """智慧树全自动答题模块"""

    def __init__(self, cookie_string):
        self.headers = {
            "Cookie": cookie_string,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/134.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*"
        }
        self.ai_client = OpenAI(api_key=API_KEY, base_url=API_URL)

    def call_llm_for_answer(self, question_type, question_content, options):
        options_text = "\n".join([f"{opt['letter']}. {opt['content']}" for opt in options])

        prompt = f"""你是一个专业的学术助手，请解答这道大学考试题目。
题目类型：{question_type}
题目内容：{question_content}
选项：
{options_text}

请严格遵守以下规则：
1. 如果是单选题，只输出一个字母，例如：A
2. 如果是多选题，只输出多个字母的组合，例如：ABC
3. 如果是判断题，只输出“对”或“错”的对应选项字母
绝对不要输出任何其他解释、标点符号或前缀。"""

        print(f"\n[AI 思考中] 题目: {question_content}")
        try:
            response = self.ai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            raw_answer = response.choices[0].message.content.strip()
            letters = re.findall(r'[A-Z]', raw_answer.upper())
            print(f"[AI 回复] {raw_answer} -> 提取答案: {''.join(letters)}")
            return letters
        except Exception as e:
            print(f"[❌ AI 请求失败] {e}")
            return []

    def get_exam_sheet(self, test_id, paper_id):
        url = "https://studentexamtest.zhihuishu.com/gateway/t/v1/exam/user/getExamSheetInfo"
        params = {
            "examTestId": test_id,
            "examPaperId": paper_id,
            "courseId": COURSE_ID
        }
        try:
            res = requests.get(url, params=params, headers=self.headers).json()
            code = res.get('code')
            if code == 0 or code == 200:
                data_node = res.get('data', {})
                if not data_node:
                    return []
                parts = data_node.get('partSheetVos', [])
                if not parts:
                    return []
                return parts[0].get('questionSheetVos', [])
            else:
                print(f"[Debug-获取试卷] ❌ 接口被拒绝，返回: {res}")
        except Exception as e:
            print(f"[Debug-获取试卷] ❌ 请求异常: {e}")
        return []

    def get_question_detail(self, test_id, paper_id, question_id):
        url = f"https://studentexamtest.zhihuishu.com/gateway/t/v1/question/getExamQuestionInfo?examTestId={test_id}&examPaperId={paper_id}&questionId={question_id}&courseId={COURSE_ID}"
        try:
            res = requests.get(url, headers=self.headers).json()
            if res.get('code') == 0 or res.get('code') == 200:
                return res.get('data')
        except Exception as e:
            print(f"[Debug-题目详情] ❌ 请求异常: {e}")
        return None

    def save_answer(self, test_id, paper_id, question_id, answer_option_ids):
        url = "https://studentexamtest.zhihuishu.com/gateway/t/v1/answer/saveAnswer"
        data = {
            "examTestId": test_id,
            "examPaperId": paper_id,
            "questionId": question_id,
            "courseId": COURSE_ID,
            "answer": '#@#'.join(str(aid) for aid in answer_option_ids)
        }
        try:
            res = requests.post(url, json=data, headers=self.headers).json()
            if res.get('code') == 0 or res.get('code') == 200 or res.get('rt'):
                return True
        except Exception as e:
            print(f"[Debug-提交答案] ❌ 请求异常: {e}")
        return False

    def submit_exam(self, test_id, paper_id):
        url = "https://studentexamtest.zhihuishu.com/gateway/t/v1/exam/user/submitExam"
        data = {
            "examTestId": test_id,
            "examPaperId": paper_id,
            "courseId": COURSE_ID
        }
        try:
            res = requests.post(url, json=data, headers=self.headers).json()
            code = res.get('code')
            if code == 0 or code == 200 or res.get('rt'):
                return True
            return False
        except Exception:
            return False

    def run(self):
        print("\n▶️ 开始全自动答题任务...")

        for exam in EXAM_LIST:
            chapter_name = exam["chapter"]
            test_id = exam["test_id"]
            paper_id = exam["paper_id"]

            print(f"\n================ 正在处理：{chapter_name} ================")
            questions = self.get_exam_sheet(test_id, paper_id)
            if not questions:
                print(f"⚠️ {chapter_name} 未获取到题目，可能已交卷，跳过。")
                continue

            print(f"📋 共获取到 {len(questions)} 道题目。")

            for index, q_brief in enumerate(questions):
                q_id = q_brief['questionId']
                q_detail = self.get_question_detail(test_id, paper_id, q_id)
                if not q_detail:
                    continue

                q_content = re.sub(r'<[^>]+>', '', q_detail.get('content', ''))
                q_type_num = q_detail.get('questionType')
                q_type = "单选题" if q_type_num == 1 else "多选题" if q_type_num == 2 else "判断题"

                letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
                options = []
                option_id_map = {}
                for i, opt in enumerate(q_detail.get('optionVos', [])):
                    if i < len(letters):
                        letter = letters[i]
                        clean_opt = re.sub(r'<[^>]+>', '', opt.get('content', ''))
                        options.append({'letter': letter, 'content': clean_opt, 'id': opt['id']})
                        option_id_map[letter] = opt['id']

                ai_letters = self.call_llm_for_answer(q_type, q_content, options)
                answer_ids = [option_id_map[letter] for letter in ai_letters if letter in option_id_map]

                if answer_ids:
                    success = self.save_answer(test_id, paper_id, q_id, answer_ids)
                    status = "✅ 提交成功" if success else "❌ 提交失败"
                    print(f"[{index + 1}/{len(questions)}] {status}")
                else:
                    print(f"[{index + 1}/{len(questions)}] ⚠️ AI未给出有效答案，跳过本题。")

                time.sleep(3.5)  # 题目间隔防风控

            # 执行自动交卷
            print(f"\n⏳ 正在自动提交 {chapter_name} 的作业...")
            success = self.submit_exam(test_id, paper_id)
            if success:
                print(f"🎉 {chapter_name} 自动交卷成功！")
            else:
                print(f"⚠️ {chapter_name} 自动交卷失败，请前往网页端确认。")

            time.sleep(5)  # 章节之间休眠防风控

        print("\n⏹️ 所有章节执行完毕，脚本退出。")


if __name__ == "__main__":
    print("=" * 55)
    print(" 🎓 智慧树全自动考试 ")
    print("=" * 55)

    # 步骤 1：扫码获取 Cookie
    login_module = ZhiHuiShuQRLogin()
    cookie = login_module.login()

    if cookie:
        # 清理登录过程中产生的二维码图片
        try:
            if os.path.exists("login_qr.png"):
                os.remove("login_qr.png")
        except Exception:
            pass

        # 步骤 2：启动答题引擎
        bot = ZhiHuiShuAutoExam(cookie)
        bot.run()
    else:
        print("\n⏹️ 未能获取身份凭证，程序已退出。")