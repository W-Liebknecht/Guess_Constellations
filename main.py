import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import csv
import os
import sys
import argparse
from datetime import datetime

class CharacterMatchingTest:
    def __init__(self, root, test_mode=False, target_difficulty=0.7):
        self.root = root
        self.root.title("看星图猜星座")
        
        # 测试参数
        self.test_mode = test_mode
        self.target_difficulty = target_difficulty
        self.current_score = 0
        self.test_items = []  # 从CSV加载的所有项目
        self.selected_items = []  # 选中的3个项目
        self.current_item_index = 0
        self.test_start_time = None
        self.results = []  # 存储测试结果
        
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
        self.image_label = tk.Label(self.root)
        self.image_label.pack(pady=20)
        
        # 说明标签
        self.instruction_label = tk.Label(self.root, 
                                        text="请输入图片对应的中文名称(3-5个汉字):",
                                        font=('Arial', 12))
        self.instruction_label.pack(pady=10)
        
        # 文本输入区域
        self.text_entry = tk.Entry(self.root, width=30, font=('Arial', 14))
        self.text_entry.pack(pady=10)
        self.text_entry.bind("<Return>", lambda event: self.check_answer())
        
        # 提交按钮
        self.submit_btn = tk.Button(self.root, text="提交", 
                                   command=self.check_answer,
                                   font=('Arial', 12))
        self.submit_btn.pack(pady=10)
        
        # 状态显示
        self.status_label = tk.Label(self.root, text="", font=('Arial', 12))
        self.status_label.pack(pady=10)
        
        # 分数显示
        self.score_label = tk.Label(self.root, text="得分: 0/0", 
                                  font=('Arial', 14, 'bold'))
        self.score_label.pack(pady=10)
    
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
            
            # 如果不是测试模式，随机选择3个项目
            if not self.test_mode:
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
    
    def show_current_item(self):
        """显示当前测试项"""
        if self.current_item_index < len(self.selected_items):
            current_item = self.selected_items[self.current_item_index]
            img_name = f"{current_item['latin_name']}.png"
            img_path = os.path.join(os.path.dirname(__file__), 'stimuli_images', img_name)
            
            try:
                img = Image.open(img_path)
                img.thumbnail((400, 400))  # 调整图片大小
                photo = ImageTk.PhotoImage(img)
                
                self.image_label.config(image=photo)
                self.image_label.image = photo  # 保持引用
                
                # 更新状态
                self.status_label.config(
                    text=f"项目 {self.current_item_index + 1}/{len(self.selected_items)}")
                
                # 清空输入框并聚焦
                self.text_entry.delete(0, tk.END)
                self.text_entry.focus()
                
                # 记录开始时间
                if self.current_item_index == 0:
                    self.test_start_time = datetime.now()
                
            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片 {img_name}:\n{str(e)}")
                self.current_item_index += 1
                self.show_current_item()
        else:
            self.end_test()
    
    def check_answer(self):
        """检查用户输入是否正确"""
        user_input = self.text_entry.get().strip()
        current_item = self.selected_items[self.current_item_index]
        correct_answer = current_item['chinese_name']
       
        # 检查答案是否正确
        is_correct = (user_input == correct_answer)
        if is_correct:
            self.current_score += 1
        
        # 记录结果
        self.results.append({
            "image": current_item['latin_name'],
            "user_answer": user_input,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "difficulty": current_item['difficulty']
        })
        
        # 更新分数显示
        self.score_label.config(
            text=f"得分: {self.current_score}/{self.current_item_index + 1}")
        
        # 移动到下一项
        self.current_item_index += 1
        self.show_current_item()
    
    def end_test(self):
        """测试结束处理"""
        test_duration = datetime.now() - self.test_start_time
        accuracy = self.current_score / len(self.selected_items) * 100
        
        # 构建详细结果文本
        result_text = (f"测试完成!\n\n"
                      f"最终得分: {self.current_score}/{len(self.selected_items)}\n"
                      f"正确率: {accuracy:.1f}%\n"
                      f"用时: {test_duration.total_seconds():.1f}秒\n\n"
                      f"详细结果:\n")
        
        for i, result in enumerate(self.results, 1):
            result_text += (f"{i}. {result['image']}: "
                          f"您的答案: {result['user_answer']}, "
                          f"正确答案: {result['correct_answer']}, "
                          f"{'✓' if result['is_correct'] else '✗'}\n")
        
        messagebox.showinfo("测试结果", result_text)
        self.status_label.config(text="测试已完成")
        self.submit_btn.config(state=tk.DISABLED)
        
        # 3秒后退出程序
        self.root.after(3000, self.root.destroy)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='汉字匹配测试程序')
    parser.add_argument('-e', '--test', action='store_true', 
                       help='测试模式：验证所有图片是否能加载')
    parser.add_argument('-d', '--difficulty', type=float, default=0.6,
                       help='设置目标难度总和(默认0.6)')
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    # 启动GUI
    root = tk.Tk()
    app = CharacterMatchingTest(root, 
                              test_mode=args.test,
                              target_difficulty=args.difficulty)
    root.mainloop()
