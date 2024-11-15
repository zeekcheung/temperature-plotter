import tkinter as tk
from tkinter import messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sympy as sp
from datetime import datetime, timedelta
import numpy as np
import matplotlib.dates as mdates
import random
import sys
import os

# 设置matplotlib字体为微软雅黑
plt.rcParams["font.family"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False


# 将时间字符串转换为小时数
def time_str_to_hours(time_str):
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours + minutes / 60
    except ValueError:
        raise ValueError("时间格式错误，应为HH:MM")


# 将小时数转换回时间字符串
def hours_to_time_str(hours):
    return f"{int(hours):02d}:{int(hours * 60 % 60):02d}"


# 评估用户方程
def evaluate_temperature_equation(eq, t_value):
    t = sp.symbols("t")
    try:
        expr = sp.sympify(eq)
        return float(expr.subs(t, t_value))
    except Exception:
        messagebox.showerror("错误", f"无效的方程：{eq}")
        return None


# 自定义格式化函数
def custom_formatter(x, pos):
    return hours_to_time_str(x)


# 生成温度图
def generate_plot(output_dir=os.path.join(os.path.dirname(__file__), "图片")):
    title = title_entry.get() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    segments = []

    try:
        for entry in segment_entries:
            start = time_str_to_hours(entry["start"].get())
            end = time_str_to_hours(entry["end"].get())
            eq = entry["eq"].get()
            error = float(entry["error"].get())

            # 检查时间段的有效性
            if start >= end:
                messagebox.showerror(
                    "错误",
                    f"开始时间必须小于结束时间：{entry['start'].get()} - {entry['end'].get()}",
                )
                return

            segments.append((start, end, eq, error))
    except ValueError as e:
        messagebox.showerror("错误", f"时间段输入无效：{e}")
        return

    time_data = []
    temp_data = []

    for start, end, eq, error in segments:
        t_values = np.linspace(start, end, 100)
        for t in t_values:
            temp = evaluate_temperature_equation(eq, t)
            if temp is None:
                return

            # 添加随机噪声，以便在指定误差范围内波动
            noise = random.uniform(-error, error)
            temp_data.append(temp + noise)  # 添加噪声
            time_data.append(t)

    # 将时间数据转换为datetime对象
    start_date = datetime(2024, 1, 1)  # 假设的开始日期
    datetime_data = [start_date + timedelta(hours=t) for t in time_data]
    datetime_data_num = mdates.date2num(datetime_data)

    if len(set(datetime_data)) <= 1:  # 检查所有时间点是否相同
        messagebox.showerror("错误", "时间段无效：所有时间点相同。")
        return

    chart_window = tk.Toplevel(root)
    chart_window.title("温度图")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(datetime_data_num, temp_data, label="温度(℃)")

    # 查找极值点
    temp_data_np = np.array(temp_data)
    maxima_indices = (
        np.argwhere(np.diff(np.sign(np.diff(temp_data_np))) == -1).flatten() + 1
    )
    minima_indices = (
        np.argwhere(np.diff(np.sign(np.diff(temp_data_np))) == 1).flatten() + 1
    )

    # 标记极值点
    for idx in maxima_indices:
        ax.annotate(
            f"极大值: {temp_data[idx]:.2f}",
            xy=(datetime_data[idx], temp_data[idx]),
            xytext=(5, 5),
            textcoords="offset points",
            arrowprops=dict(arrowstyle="->", color="red"),
            fontsize=8,
            color="red",
        )

    for idx in minima_indices:
        ax.annotate(
            f"极小值: {temp_data[idx]:.2f}",
            xy=(datetime_data[idx], temp_data[idx]),
            xytext=(5, -15),
            textcoords="offset points",
            arrowprops=dict(arrowstyle="->", color="blue"),
            fontsize=8,
            color="blue",
        )

    # 设置x轴刻度值
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))  # 每小时显示一个刻度值
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))  # 格式化x轴显示

    ax.set_xlabel("时间(24小时制)")
    ax.set_ylabel("温度(℃)")
    ax.set_title(title)
    ax.legend()

    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    canvas.draw()

    output_dir = os.path.abspath(output_dir)
    print(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, title))
    plt.close()


# GUI设置
root = tk.Tk()
root.title("温度绘图器")

top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

title_frame = tk.Frame(top_frame)
title_frame.pack(side=tk.TOP, pady=5)

title_label = tk.Label(title_frame, text="图表标题：")
title_label.pack(side=tk.LEFT)

title_entry = tk.Entry(title_frame, width=30)
title_entry.pack(side=tk.LEFT, padx=5)

button_frame = tk.Frame(root)
button_frame.pack(side=tk.TOP, pady=5)

add_segment_button = tk.Button(
    button_frame, text="添加时间段", command=lambda: add_segment()
)
add_segment_button.pack(side=tk.LEFT, padx=5)

generate_plot_button = tk.Button(button_frame, text="生成图表", command=generate_plot)
generate_plot_button.pack(side=tk.LEFT, padx=5)

segment_frame = tk.Frame(root)
segment_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=10, pady=5)

canvas_scroll = tk.Canvas(segment_frame)
scrollbar = ttk.Scrollbar(segment_frame, orient="vertical", command=canvas_scroll.yview)
scrollable_frame = tk.Frame(canvas_scroll)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")),
)

canvas_scroll.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas_scroll.configure(yscrollcommand=scrollbar.set)

canvas_scroll.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

segment_entries = []


def add_segment(start="", end="", eq="", error=""):
    row = len(segment_entries)

    start_entry = tk.Entry(scrollable_frame, width=10)
    start_entry.grid(row=row + 1, column=1, padx=5, pady=2)

    end_entry = tk.Entry(scrollable_frame, width=10)
    end_entry.grid(row=row + 1, column=2, padx=5, pady=2)

    eq_entry = tk.Entry(scrollable_frame, width=15)
    eq_entry.grid(row=row + 1, column=3, padx=5, pady=2)

    error_entry = tk.Entry(scrollable_frame, width=10)
    error_entry.grid(row=row + 1, column=4, padx=5, pady=2)

    delete_button = tk.Button(
        scrollable_frame, text="删除", command=lambda: delete_segment(row)
    )
    delete_button.grid(row=row + 1, column=5, padx=5, pady=2)

    segment_entries.append(
        {
            "start": start_entry,
            "end": end_entry,
            "eq": eq_entry,
            "error": error_entry,
            "delete": delete_button,
        }
    )

    if row == 0:
        tk.Label(scrollable_frame, text="开始时间").grid(row=row, column=1)
        tk.Label(scrollable_frame, text="结束时间").grid(row=row, column=2)
        tk.Label(scrollable_frame, text="温度变化函数").grid(row=row, column=3)
        tk.Label(scrollable_frame, text="误差").grid(row=row, column=4)
        tk.Label(scrollable_frame, text="操作").grid(row=row, column=5)

    start_entry.insert(0, start)
    end_entry.insert(0, end)
    eq_entry.insert(0, eq)
    error_entry.insert(0, error)


def delete_segment(index):
    entry = segment_entries[index]
    entry["start"].grid_remove()
    entry["end"].grid_remove()
    entry["eq"].grid_remove()
    entry["error"].grid_remove()
    entry["delete"].grid_remove()

    segment_entries.pop(index)
    for i, entry in enumerate(segment_entries):
        entry["start"].grid(row=i + 1, column=1)
        entry["end"].grid(row=i + 1, column=2)
        entry["eq"].grid(row=i + 1, column=3)
        entry["error"].grid(row=i + 1, column=4)
        entry["delete"].grid(row=i + 1, column=5)


# 处理命令行参数 "title start end equation error"
if len(sys.argv) > 1:
    title = sys.argv[1]
    title_entry.insert(0, title)

    output_dir = sys.argv[2]

    for arg in sys.argv[3:]:
        try:
            parts = arg.split()
            if len(parts) != 4:
                raise ValueError("每个参数组必须包含4个部分")
            start, end, eq, error = parts
            add_segment(start, end, eq, error)
        except ValueError as e:
            messagebox.showerror("错误", f"参数格式错误: {arg} - {str(e)}")

    generate_plot(output_dir)
else:
    add_segment("08:00", "12:00", "10*t-55", "1")
    add_segment("12:00", "16:00", "65", "0.5")
    add_segment("16:00", "20:00", "-5*t+145", "1")

    root.geometry("600x400")
    root.mainloop()
