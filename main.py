import os
import random
import sys
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sympy as sp
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# TODO: Refactor

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
# 例如：1.5 -> 01:30
def hours_to_time_str(hours):
    return f"{int(hours):02d}:{int(hours * 60 % 60):02d}"


# 格式化 excel 的日期数据
# 原始格式为 2024年12月31日 25:16
# 目标格式为 2025年1月1日 1:16
# 如果时间超过24小时，则日期加1天，时间减去24小时
def format_excel_date(date_str):
    try:
        date_part, time_part = date_str.split(" ")
        date_format = "%Y年%m月%d日"
        date_obj = datetime.strptime(date_part, date_format)
        hours, minutes = map(int, time_part.split(":"))

        if minutes >= 60:
            raise ValueError("分钟数超出范围")

        if hours >= 24:
            days_to_add = hours // 24
            hours_remaining = hours % 24
            date_obj += timedelta(days=days_to_add)
            hours = hours_remaining

        date_obj = date_obj.replace(hour=hours, minute=minutes)
        target_format = "%Y年%m月%d日 %H:%M"
        return date_obj.strftime(target_format)
    except Exception as e:
        return f"输入的日期时间格式不正确: {e}"


# 评估用户方程
def evaluate_temperature_equation(eq, t_value):
    t = sp.symbols("t")
    try:
        expr = sp.sympify(eq)
        return float(expr.subs(t, t_value))
    except Exception:
        messagebox.showerror("错误", f"无效的方程：{eq}")
        return None


# 修改文件名中的非法字符
def sanitize_filename(filename):
    illegal_chars = r'\/:*?"<>|'
    for char in illegal_chars:
        filename = filename.replace(char, "-")
    return filename


# 生成时间和温度、湿度数据
def generate_time_temperature_humidity_data(segments, time_interval=5):
    time_data = []
    temperature_data = []
    humidity_data = []
    excel_data = {"时间": [], "温度(℃)": [], "湿度(%)": []}

    for start, end, eq, temperature_error in segments:
        t_values = np.arange(start, end, time_interval / 60)
        for t in t_values:
            temperature = evaluate_temperature_equation(eq, t)
            if temperature is None:
                return None, None, None, None

            # 添加温度噪声
            temperature_noise = random.uniform(-temperature_error, temperature_error)
            temperature_with_noise = temperature + temperature_noise

            # 生成湿度数据（保持在 99.3% 到 99.5% 之间）
            humidity = random.uniform(99.3, 99.5)

            # 保留一位小数
            temperature_with_noise = round(temperature_with_noise, 1)
            humidity = round(humidity, 1)

            time_data.append(t)
            temperature_data.append(temperature_with_noise)
            humidity_data.append(humidity)

            excel_data["时间"].append(
                format_excel_date(date_entry.get() + " " + hours_to_time_str(t))
            )
            excel_data["温度(℃)"].append(temperature_with_noise)
            excel_data["湿度(%)"].append(humidity)

    return time_data, temperature_data, humidity_data, excel_data


# 保存图表
def save_plot(fig, output_dir, title):
    try:
        chart_path = os.path.join(output_dir, f"{title}.png")
        plt.savefig(chart_path)
        plt.close()
        return chart_path
    except Exception as e:
        messagebox.showerror("错误", f"保存图表失败：{e}")
        return None


# 保存 Excel 文件
def save_excel(excel_data, output_dir, title):
    try:
        excel_path = os.path.join(output_dir, f"{title}.xlsx")
        df = pd.DataFrame(excel_data)
        df.to_excel(excel_path, index=False)
        return excel_path
    except Exception as e:
        messagebox.showerror("错误", f"保存 Excel 文件失败：{e}")
        return None


def generate_plot(output_dir=os.path.dirname(__file__)):
    # 获取标题并处理非法字符
    title = title_entry.get() or datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    title = sanitize_filename(title)

    # 确保输出目录存在
    img_output_dir = os.path.join(output_dir, "img")
    excel_output_dir = os.path.join(output_dir, "excel")
    os.makedirs(img_output_dir, exist_ok=True)
    os.makedirs(excel_output_dir, exist_ok=True)

    # 获取时间段数据
    segments = []
    try:
        for entry in segment_entries:
            start = time_str_to_hours(entry["start"].get())
            end = time_str_to_hours(entry["end"].get())
            eq = entry["eq"].get()
            temperature_error = float(entry["error"].get())

            if start >= end:
                messagebox.showerror(
                    "错误",
                    f"开始时间必须小于结束时间：{entry['start'].get()} - {entry['end'].get()}",
                )
                return

            segments.append((start, end, eq, temperature_error))
    except ValueError as e:
        messagebox.showerror("错误", f"时间段输入无效：{e}")
        return

    # 生成时间和温度、湿度数据
    time_data, temperature_data, humidity_data, excel_data = (
        generate_time_temperature_humidity_data(segments)
    )
    if time_data is None:
        return

    # 将时间数据转换为datetime对象
    start_date = datetime(2024, 1, 1)
    datetime_data = [start_date + timedelta(hours=t) for t in time_data]
    datetime_data_num = mdates.date2num(datetime_data)

    if len(set(datetime_data)) <= 1:
        messagebox.showerror("错误", "时间段无效：所有时间点相同。")
        return

    # 生成图表
    chart_window = tk.Toplevel(root)
    chart_window.title("温湿度变化图")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(datetime_data_num, temperature_data, label="温度(℃)", color="red")
    ax.plot(datetime_data_num, humidity_data, label="湿度(%)", color="blue")

    # 设置x轴刻度值
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

    ax.set_xlabel("时间(24小时制)")
    ax.set_ylabel("温度(℃) / 湿度(%)")
    ax.set_title(title)
    ax.legend()

    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    canvas.draw()

    # 保存图表和 Excel 文件
    save_plot(fig, img_output_dir, title)
    save_excel(excel_data, excel_output_dir, title)

    # if chart_path and excel_path:
    #     messagebox.showinfo(
    #         "完成", f"图表已保存到：{chart_path}\n数据已保存到：{excel_path}"
    #     )


# GUI设置
root = tk.Tk()
root.title("温湿度绘图器")

top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

title_frame = tk.Frame(top_frame)
title_frame.pack(side=tk.TOP, pady=5)

title_label = tk.Label(title_frame, text="标题：")
title_label.pack(side=tk.LEFT)

title_entry = tk.Entry(title_frame, width=30)
title_entry.pack(side=tk.LEFT, padx=5)

date_label = tk.Label(title_frame, text="日期：")
date_label.pack(side=tk.LEFT)

date_entry = tk.Entry(title_frame, width=30)
date_entry.pack(side=tk.LEFT, padx=5)

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
    add_segment("08:00", "12:00", "10*t-55", "2")
    add_segment("12:00", "16:00", "65", "2")
    add_segment("16:00", "20:00", "-5*t+145", "2")

    root.geometry("600x400")
    root.mainloop()
