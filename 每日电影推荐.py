import tkinter as tk
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
import datetime
import hashlib
from PIL import Image, ImageTk
import io
import webbrowser

DOUBAN_CHART_URL = "https://movie.douban.com/chart"

def fetch_chart_movies():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(DOUBAN_CHART_URL, headers=headers, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    movies = []
    for item in soup.select("div.indent table tr"):
        title_tag = item.select_one("div.pl2 a")
        if not title_tag:
            continue
        title = title_tag.text.strip().replace("\n", "").replace(" ", "")
        link = title_tag["href"]
        rating_tag = item.select_one("span.rating_nums")
        rating = rating_tag.text.strip() if rating_tag else "暂无评分"
        info_tag = item.select_one("p.pl")
        info = info_tag.text.strip() if info_tag else ""
        img_tag = item.select_one("a.nbg img")
        img_url = img_tag["src"] if img_tag else ""
        movies.append({"title": title, "rating": rating, "info": info, "link": link, "img_url": img_url})
    return movies

def fetch_comments(movie_url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        resp = requests.get(movie_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        comments = []
        for c in soup.select(".comment span.short"):
            comments.append(c.text.strip())
        return comments[:5] if comments else ["暂无短评"]
    except Exception as e:
        return [f"获取评论失败: {e}"]

def fetch_summary(movie_url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        resp = requests.get(movie_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        summary_tag = soup.select_one('span[property="v:summary"]')
        if summary_tag:
            summary = summary_tag.text.strip().replace("\n", " ").replace("  ", " ")
            return summary
        else:
            return "暂无简介"
    except Exception as e:
        return f"获取简介失败: {e}"

def get_today_index(movies):
    today = datetime.date.today().isoformat()
    idx = int(hashlib.md5(today.encode()).hexdigest(), 16) % len(movies)
    return idx

def show_movie(idx):
    movie = movies[idx]
    comments = fetch_comments(movie["link"])
    summary = fetch_summary(movie["link"])
    text.delete("1.0", tk.END)

    # 插入电影名并添加tag
    title_info = f"片名：{movie['title']}\n"
    text.insert(tk.END, title_info)
    title_start = "1.3"  # "片名："后第4个字符
    title_end = f"1.{3+len(movie['title'])}"
    text.tag_add("douban_link", title_start, title_end)
    text.tag_config("douban_link", foreground="#1a73e8", underline=True)
    def open_link(event, url=movie["link"]):
        webbrowser.open(url)
    text.tag_bind("douban_link", "<Button-1>", open_link)

    # 其余信息
    text.insert(tk.END, f"评分：{movie['rating']}\n简介：{summary}\n\n短评：\n")
    for i, c in enumerate(comments, 1):
        text.insert(tk.END, f"{i}. {c}\n")

    # 显示图片（保持原有逻辑）
    if movie.get("img_url"):
        try:
            img_resp = requests.get(movie["img_url"], timeout=10)
            img_data = img_resp.content
            pil_img = Image.open(io.BytesIO(img_data)).resize((120, 160))
            tk_img = ImageTk.PhotoImage(pil_img)
            img_label.config(image=tk_img, text="")
            img_label.image = tk_img
        except Exception as e:
            img_label.config(image="", text="图片加载失败")
            img_label.image = None
    else:
        img_label.config(image="", text="无图片")
        img_label.image = None

def next_movie():
    global current_idx
    current_idx = (current_idx + 1) % len(movies)
    show_movie(current_idx)

def prev_movie():
    global current_idx
    current_idx = (current_idx - 1) % len(movies)
    show_movie(current_idx)

def refresh_movies():
    global movies, current_idx
    text.delete("1.0", tk.END)
    text.insert(tk.END, "正在抓取豆瓣电影榜单，请稍候...")
    root.update()
    try:
        movies = fetch_chart_movies()
        if not movies:
            raise Exception("未抓取到电影数据，可能页面结构有变。")
        current_idx = get_today_index(movies)
        show_movie(current_idx)
    except Exception as e:
        messagebox.showerror("错误", f"抓取失败：{e}")

# 主窗口
root = tk.Tk()
root.title("今日电影推荐")
root.geometry("540x1000")  # 增大窗口尺寸
root.configure(bg="#f7f7f7")  # 浅灰背景

# 顶部标题栏
header = tk.Label(root, text="今日电影推荐", font=("微软雅黑", 20, "bold"), fg="#42bd56", bg="#f7f7f7")
header.pack(pady=(18, 6))

# 图片显示控件
img_label = tk.Label(root, bg="#f7f7f7")
img_label.pack(pady=(0, 8))

text = tk.Text(root, font=("微软雅黑", 15), wrap="word", bg="white", fg="#222", bd=0, relief="flat", highlightthickness=1, highlightbackground="#e0e0e0")
text.pack(fill="both", expand=True, padx=28, pady=16)  # 增大内边距

frame = tk.Frame(root, bg="#f7f7f7")
frame.pack(pady=8)

btn_style = {"font": ("微软雅黑", 12, "bold"), "bg": "#42bd56", "fg": "white", "activebackground": "#388e3c", "activeforeground": "white", "bd": 0, "relief": "flat", "width": 10, "height": 1, "cursor": "hand2"}

btn_prev = tk.Button(frame, text="上一部", command=prev_movie, **btn_style)
btn_prev.pack(side="left", padx=8)
btn_next = tk.Button(frame, text="下一部", command=next_movie, **btn_style)
btn_next.pack(side="left", padx=8)
btn_refresh = tk.Button(frame, text="刷新榜单", command=refresh_movies, **btn_style)
btn_refresh.pack(side="left", padx=8)

movies = []
current_idx = 0

refresh_movies()

root.mainloop()