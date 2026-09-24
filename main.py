import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import random
import csv
import os
import sys
import argparse
from datetime import datetime

# 图片在窗口里的逻辑显示尺寸(不随屏幕缩放变化)。
# 原始星图是 800x800 ~ 1200x1200，所以 DISPLAY_SIZE * MAX_SCALE 不应超过原图分辨率，
# 否则 CTkImage 只能靠放大来填满，画面就会发虚。
DISPLAY_SIZE = (1200, 1200)
MAX_SCALE = 2.0


def enable_high_dpi():
    """在创建任何窗口之前声明进程 DPI 感知。

    customtkinter 自己也会调用 SetProcessDpiAwareness(2)，但那是在 CTk() 内部、
    Tk 窗口已经创建之后才调用的。Windows 要求在任何窗口创建之前调用才生效，
    否则整个窗口会被系统按位图拉伸，文字和图片都会发虚。
    """
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            pass


enable_high_dpi()


class CharacterMatchingTest:
    def __init__(self, root, test_mode=False, infty_mode=False, target_difficulty=0.7):
        self.root = root

        # 测试参数
        self.test_mode = test_mode
        self.infty_mode = infty_mode
        self.target_difficulty = target_difficulty
        self.current_score = 0
        self.test_items = []  # 从CSV加载的所有项目
        self.selected_items = []  # 固定模式下选中的3个项目
        self.current_item = None  # 当前正在作答的题目
        self.current_item_index = 0
        self.answered_count = 0  # 已作答题数
        self.test_start_time = None
        self.results = []  # 存储测试结果

        self.root.title("看星图猜星座 - 无限模式" if self.infty_mode else "看星图猜星座")

        # 创建GUI界面
        self.create_widgets()

        # 加载配置
        self.load_configuration()

        # 如果是测试模式，直接验证所有图片
        if self.test_mode:
            self.test_all_images()

    def create_widgets(self):
        """创建程序界面组件"""
        # 图片显示区域
        self.image_label = ctk.CTkLabel(self.root, text="")
        self.image_label.pack(pady=20)

        # 说明标签
        self.instruction_label = ctk.CTkLabel(self.root,
                                        text="请输入图片对应的中文名称(3-5个汉字):",
                                        font=ctk.CTkFont(family='Arial', size=30))
        self.instruction_label.pack(pady=20)

        # 文本输入区域
        self.text_entry = ctk.CTkEntry(self.root, width=300,
                                       font=ctk.CTkFont(family='Arial', size=30))
        self.text_entry.pack(pady=10)
        self.text_entry.bind("<Return>", lambda event: self.check_answer())

        # 提交按钮
        self.submit_btn = ctk.CTkButton(self.root, text="提交",
                                   command=self.check_answer,
                                   width=140, height=36,
                                   font=ctk.CTkFont(family='Arial', size=20))
        self.submit_btn.pack(pady=10)

        # 状态显示
        self.status_label = ctk.CTkLabel(self.root, text="",
                                         font=ctk.CTkFont(family='Arial', size=30))
        self.status_label.pack(pady=10)

        # 分数显示
        self.score_label = ctk.CTkLabel(self.root, text="得分: 0/0",
                                  font=ctk.CTkFont(family='Arial', size=30, weight='bold'))
        self.score_label.pack(pady=10)

    def log(self, message):
        """把信息打印到控制台。

        打包成窗口程序(main.spec 里 console=False)时 stdout 可能为 None，
        这时直接跳过，避免打印本身让程序崩溃。
        """
        if sys.stdout is None:
            return
        try:
            print(message, flush=True)
        except Exception:
            pass

    def load_configuration(self):
        """加载CSV配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'stimuli_config.csv')
            with open(config_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.test_items = list(reader)
                # 确保所有难度值都是浮点数
                for item in self.test_items:
                    item['difficulty'] = float(item['difficulty'])

            # 如果不是测试模式，准备题目
            if not self.test_mode:
                if self.infty_mode:
                    # 无限模式：不预选题目，每一题都从全部星座里随机抽取
                    self.test_start_time = datetime.now()
                    self.log(f"[无限模式] 已加载 {len(self.test_items)} 个星座，"
                             f"每题随机出现；输入中文名后回车提交，关闭窗口即可退出。")
                else:
                    # 固定模式：随机选择3个项目
                    self.select_test_items()
                self.show_current_item()

        except Exception as e:
            messagebox.showerror("错误", f"无法加载配置文件:\n{str(e)}")
            self.root.destroy()

    def select_test_items(self):
        """改进的随机选择算法，确保能找到合适的难度组合"""
        # 先尝试精确匹配
        for _ in range(1000):
            selected = random.sample(self.test_items, 3)
            total_diff = sum(item['difficulty'] for item in selected)
            if abs(total_diff - self.target_difficulty) < 0.05:  # 更严格的容差
                self.selected_items = selected
                return

        # 如果找不到精确匹配，放宽条件
        best_diff = float('inf')
        best_combination = None

        # 随机尝试1000次，找最接近的组合
        for _ in range(1000):
            selected = random.sample(self.test_items, 3)
            total_diff = sum(item['difficulty'] for item in selected)
            current_diff = abs(total_diff - self.target_difficulty)

            if current_diff < best_diff:
                best_diff = current_diff
                best_combination = selected

                # 如果找到足够好的组合就停止
                if best_diff < 0.1:
                    break

        self.selected_items = best_combination
        messagebox.showinfo("提示",
                          f"使用最接近的难度组合: {sum(item['difficulty'] for item in self.selected_items):.2f} " +
                          f"(目标: {self.target_difficulty})")

    def test_all_images(self):
        """测试模式：验证所有图片是否能正确加载"""
        failed_items = []

        for item in self.test_items:
            img_name = f"{item['latin_name']}.png"
            img_path = os.path.join(os.path.dirname(__file__), 'stimuli_images', img_name)

            try:
                img = Image.open(img_path)
                img.verify()  # 验证图片完整性
                img.close()
            except Exception as e:
                failed_items.append(f"{img_name} ({str(e)})")

        if failed_items:
            messagebox.showerror("测试失败",
                               f"以下图片加载失败:\n\n" + "\n".join(failed_items))
        else:
            messagebox.showinfo("测试通过", "所有图片加载成功!")

        self.root.destroy()

    def pick_current_item(self):
        """取出当前要显示的题目；返回 None 表示没有题目可出了"""
        if self.infty_mode:
            # 无限模式：每次都从全部星座里随机抽，只是避免和上一题连续重复
            pool = [item for item in self.test_items if item is not self.current_item]
            if not pool:
                pool = self.test_items
            return random.choice(pool) if pool else None

        if self.current_item_index < len(self.selected_items):
            return self.selected_items[self.current_item_index]
        return None

    def show_current_item(self):
        """显示当前测试项"""
        # 图片有可能损坏，失败时换一题重试；最多10次，避免无限递归
        for _ in range(10):
            current_item = self.pick_current_item()
            if current_item is None:
                self.end_test()
                return

            img_name = f"{current_item['latin_name']}.png"
            img_path = os.path.join(os.path.dirname(__file__), 'stimuli_images', img_name)

            try:
                with Image.open(img_path) as raw:
                    # convert 会立刻读出全部像素，之后文件就不再需要。
                    # 用 with 让句柄确定性地关闭，而不是依赖垃圾回收。
                    img = raw.convert("RGBA")

                # 用 LANCZOS 高质量重采样，并且只缩到「显示尺寸 × 最大超采样倍数」，
                # 把多余的像素留给高分屏 —— 让 CTkImage 之后是「缩小」而不是「放大」。
                img.thumbnail((round(DISPLAY_SIZE[0] * MAX_SCALE),
                               round(DISPLAY_SIZE[1] * MAX_SCALE)),
                              Image.Resampling.LANCZOS)

                # CTkImage 内部还会按 size × 屏幕缩放 再缩放一次，
                # 所以这里的 size 要换算回等比逻辑尺寸，避免非正方形原图被拉伸。
                display_size = (max(1, round(img.width / MAX_SCALE)),
                                max(1, round(img.height / MAX_SCALE)))
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=display_size)

                self.image_label.configure(image=photo)
                self.image_label.image = photo  # 保持引用

                self.current_item = current_item

                # 更新状态
                if self.infty_mode:
                    self.status_label.configure(
                        text=f"无限模式 - 第 {self.answered_count + 1} 题")
                else:
                    self.status_label.configure(
                        text=f"项目 {self.current_item_index + 1}/{len(self.selected_items)}")

                # 更新分数显示
                self.score_label.configure(
                    text=f"得分: {self.current_score}/{self.answered_count}")

                # 清空输入框并聚焦
                self.text_entry.delete(0, "end")
                self.text_entry.focus()

                # 记录开始时间
                if self.test_start_time is None:
                    self.test_start_time = datetime.now()

                return

            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片 {img_name}:\n{str(e)}")
                self.current_item = None
                self.current_item_index += 1

        self.end_test()

    def check_answer(self):
        """检查用户输入是否正确"""
        current_item = self.current_item
        if current_item is None:  # 当前没有题目可答
            return

        user_input = self.text_entry.get().strip()
        correct_answer = current_item['chinese_name']

        # 检查答案是否正确
        is_correct = (user_input == correct_answer)
        if is_correct:
            self.current_score += 1
        self.answered_count += 1

        # 记录结果
        self.results.append({
            "image": current_item['latin_name'],
            "user_answer": user_input,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "difficulty": current_item['difficulty']
        })

        # 在控制台打印对错
        self.log(f"[{self.answered_count}] {current_item['latin_name']} "
                 f"答案={correct_answer} 输入={user_input or '(空)'} "
                 f"-> {'CORRECT' if is_correct else 'WRONG'} "
                 f"(得分 {self.current_score}/{self.answered_count})")

        # 更新分数显示
        self.score_label.configure(
            text=f"得分: {self.current_score}/{self.answered_count}")

        # 移动到下一项
        self.current_item_index += 1
        self.show_current_item()

    def end_test(self):
        """测试结束处理（只用于固定模式，无限模式不会结束）"""
        if self.infty_mode:
            return

        total = len(self.selected_items)
        if total == 0 or self.test_start_time is None:
            return

        test_duration = datetime.now() - self.test_start_time
        accuracy = self.current_score / total * 100

        # 构建详细结果文本
        result_text = (f"测试完成!\n\n"
                      f"最终得分: {self.current_score}/{total}\n"
                      f"正确率: {accuracy:.1f}%\n"
                      f"用时: {test_duration.total_seconds():.1f}秒\n\n"
                      f"详细结果:\n")

        for i, result in enumerate(self.results, 1):
            result_text += (f"{i}. {result['image']}: "
                          f"您的答案: {result['user_answer']}, "
                          f"正确答案: {result['correct_answer']}, "
                          f"{'✓' if result['is_correct'] else '✗'}\n")

        messagebox.showinfo("测试结果", result_text)
        self.status_label.configure(text="测试已完成")
        self.submit_btn.configure(state="disabled")

        # 3秒后退出程序
        self.root.after(3000, self.root.destroy)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='汉字匹配测试程序')
    parser.add_argument('-t', '--test', action='store_true',
                       help='测试模式：验证所有图片是否能加载')
    parser.add_argument('-d', '--difficulty', type=float, default=0.6,
                       help='设置目标难度总和(默认0.6)')
    parser.add_argument('-i', '--infty', action='store_true',
                       help='无限模式：连续随机出题，不设题数上限，并在控制台打印每题对错')
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()

    # 设置外观
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    # 启动GUI
    root = ctk.CTk()
    app = CharacterMatchingTest(root,
                                test_mode=args.test,
                                infty_mode=args.infty,
                                target_difficulty=args.difficulty)
    root.mainloop()
