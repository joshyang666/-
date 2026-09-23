import os
import sys
import time
import json
import re
import requests
from base64 import b64decode
from openai import OpenAI

# ==============================================================================
# 大模型 API 配置区域 (用户填入自己的 key)
# ==============================================================================
API_URL = " "  # 替换为你的大模型 API 地址
API_KEY = "YOUR_API_KEY_HERE"  # 替换为你的大模型 API_KEY
MODEL_NAME = ""  # 替换为你使用的模型名称


class ZhiHuiShuQRLogin:
    """智慧树扫码登录模块 (无缝获取 Cookie)"""

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/134.0.0.0 Safari/537.36"
        }
        self.session.headers.update(self.headers)

    def _open_image(self, file_path):
        """跨平台自动打开二维码图片"""
        try:
            if sys.platform.startswith('darwin'):
                os.system(f'open "{file_path}"')
            elif os.name == 'nt':
                os.startfile(file_path)
            elif os.name == 'posix':
                os.system(f'xdg-open "{file_path}"')
        except Exception:
            pass

    def login(self):
        print("\n▶️ 开始获取登录二维码...")
        qr_page = "https://passport.zhihuishu.com/qrCodeLogin/getLoginQrImg"
        query_page = "https://passport.zhihuishu.com/qrCodeLogin/getLoginQrInfo"
        login_page = "https://passport.zhihuishu.com/login?service=https://onlineservice-api.zhihuishu.com/login/gologin"

        try:
            res = self.session.get(qr_page, timeout=10).json()
            qr_token = res.get("qrToken")
            img_data = b64decode(res.get("img"))

            qr_file = "login_qr.png"
            with open(qr_file, "wb") as f:
                f.write(img_data)

            print(f"✅ 二维码已保存至当前目录：{qr_file}")
            self._open_image(qr_file)
            print("⏳ 请使用手机【知到APP】或【微信】扫码登录...")

            scanned = False
            while True:
                time.sleep(1.5)
                status_res = self.session.get(query_page, params={"qrToken": qr_token}, timeout=10).json()
                status = status_res.get("status")

                if status == -1:
                    pass
                elif status == 0:
                    if not scanned:
                        print("👀 已扫码，请在手机上点击确认！")
                        scanned = True
                elif status == 1:
                    print("🎉 登录成功！正在获取身份凭证...")
                    once_pwd = status_res.get("oncePassword")
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
        self.course_id = None
        self.exam_list = []

    # ========================================================================
    # 核心突破：单接口双重解析 (获取课程列表 + 考试列表)
    # ========================================================================
    def init_tasks(self):
        """调用接口自动拉取并分类所有作业和考试"""
        print(f"\n🔍 正在扫描当前账号下的所有作业与考试...")

        url = "https://studentexam-api.zhihuishu.com/studentExam/gateway/t/v1/student/getStudentHomework"
        req_headers = self.headers.copy()
        req_headers["Content-Type"] = "application/x-www-form-urlencoded"

        try:
            # 提交空表单以获取该账号下的全部未完成/已完成作业
            res = requests.post(url, data={}, headers=req_headers).json()
            if res.get("status") != "200" and res.get("msg") != "请求成功":
                print(f"❌ 获取列表失败，服务器返回: {res}")
                return False

            homework_list = res.get("rt", {}).get("studentHomeworkList", [])
            if not homework_list:
                print("⚠️ 恭喜！当前账号下未找到任何待处理的作业或考试。")
                return False

            # 1. 解析数据：提取所有包含的课程信息
            courses = {}
            for hw in homework_list:
                cid = str(hw.get("courseId", ""))
                cname = hw.get("courseName", "未知课程")
                if cid and cid not in courses:
                    courses[cid] = cname

            if not courses:
                print("⚠️ 未能在数据中提取到有效的课程信息。")
                return False

            # 2. 交互环节：让用户选择课程
            course_ids = list(courses.keys())
            if len(course_ids) == 1:
                self.course_id = course_ids[0]
                print(f"✅ 自动锁定唯一待考课程: {courses[self.course_id]} (ID: {self.course_id})")
            else:
                print("\n📚 发现以下课程有作业/考试，请选择（输入对应数字）：")
                for i, cid in enumerate(course_ids):
                    print(f"[{i + 1}] {courses[cid]} (ID: {cid})")

                try:
                    choice = int(input("\n👉 你的选择是: ")) - 1
                    if choice < 0 or choice >= len(course_ids):
                        raise ValueError
                    self.course_id = course_ids[choice]
                except ValueError:
                    print("❌ 输入无效，程序退出。")
                    return False

            # 3. 提取环节：过滤并构建所选课程的考试列表
            for hw in homework_list:
                if str(hw.get("courseId")) == self.course_id:
                    hw_name = hw.get("examName", "未知测试")
                    test_id = hw.get("id")  # 试题 ID
                    paper_id = hw.get("examId")  # 试卷 ID

                    if test_id and paper_id:
                        self.exam_list.append({
                            "chapter": hw_name,
                            "test_id": test_id,
                            "paper_id": paper_id
                        })

            print(f"✅ 成功加载 {len(self.exam_list)} 个考试/作业任务！")
            return True

        except Exception as e:
            print(f"❌ 请求考试列表异常: {e}")
            return False

    # ========================================================================
    # 答题与提交流程
    # ========================================================================
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
            "courseId": self.course_id
        }
        try:
            res = requests.get(url, params=params, headers=self.headers).json()
            if res.get('code') in [0, 200]:
                data_node = res.get('data', {})
                parts = data_node.get('partSheetVos', [])
                if parts:
                    return parts[0].get('questionSheetVos', [])
        except Exception as e:
            print(f"[Debug-获取试卷] ❌ 请求异常: {e}")
        return []

    def get_question_detail(self, test_id, paper_id, question_id):
        url = f"https://studentexamtest.zhihuishu.com/gateway/t/v1/question/getExamQuestionInfo?examTestId={test_id}&examPaperId={paper_id}&questionId={question_id}&courseId={self.course_id}"
        try:
            res = requests.get(url, headers=self.headers).json()
            if res.get('code') in [0, 200]:
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
            "courseId": self.course_id,
            "answer": '#@#'.join(str(aid) for aid in answer_option_ids)
        }
        try:
            res = requests.post(url, json=data, headers=self.headers).json()
            if res.get('code') in [0, 200] or res.get('rt'):
                return True
        except Exception as e:
            print(f"[Debug-提交答案] ❌ 请求异常: {e}")
        return False

    def submit_exam(self, test_id, paper_id):
        url = "https://studentexamtest.zhihuishu.com/gateway/t/v1/exam/user/submitExam"
        data = {
            "examTestId": test_id,
            "examPaperId": paper_id,
            "courseId": self.course_id
        }
        try:
            res = requests.post(url, json=data, headers=self.headers).json()
            if res.get('code') in [0, 200] or res.get('rt'):
                return True
        except Exception:
            pass
        return False

    def run(self):
        # 1. 自动初始化并让用户选择课程
        if not self.init_tasks():
            return

        print(f"\n▶️ 开始全自动答题任务！")

        # 2. 循环执行任务
        for exam in self.exam_list:
            chapter_name = exam.get("chapter", "未知章节")
            test_id = exam.get("test_id")
            paper_id = exam.get("paper_id")

            print(f"\n================ 正在处理：{chapter_name} ================")
            questions = self.get_exam_sheet(test_id, paper_id)
            if not questions:
                print(f"⚠️ {chapter_name} 未获取到题目，可能已完成并交卷，跳过。")
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

            print(f"\n⏳ 正在自动提交 {chapter_name} ...")
            success = self.submit_exam(test_id, paper_id)
            if success:
                print(f"🎉 {chapter_name} 自动交卷成功！")
            else:
                print(f"⚠️ {chapter_name} 自动交卷失败，请前往网页端确认。")

            time.sleep(5)  # 章节之间休眠防风控

        print("\n⏹️ 选定课程所有考试执行完毕，脚本退出。")


if __name__ == "__main__":
    print("=" * 55)
    print(" 🎓 智慧树全自动满分助手 (终极开源一键版) ")
    print("=" * 55)

    # 步骤 1: 扫码登录拿 Cookie
    login_module = ZhiHuiShuQRLogin()
    cookie = login_module.login()

    if cookie:
        # 清除二维码残余图片
        try:
            if os.path.exists("login_qr.png"):
                os.remove("login_qr.png")
        except Exception:
            pass

        # 步骤 2: 全自动执行 (解析列表 + 作答)
        bot = ZhiHuiShuAutoExam(cookie)
        bot.run()

    else:
        print("\n⏹️ 未能获取身份凭证，程序已退出。")
