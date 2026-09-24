# ==========================================================
# 🐟 鲸鱼娘超链接管理工具
# 本鲸鱼娘特制注释版 V3.3
# 新增：
#   1. 自动合并 "自娱自乐🧑 - Wordle🎯" 这种被拍平的分组
#   2. 搜索框（只搜当前分类下的链接）
#   3. 撤销功能（操作前自动备份，Ctrl+Z 般的体验）
# ==========================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import re
import uuid
import copy
import tkinter.font as tkfont


def strip_js_comments(text):
    out = []
    i, n = 0, len(text)
    in_str = False
    str_ch = ''
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == str_ch:
                in_str = False
            i += 1
            continue
        if c == '"' or c == "'" or c == '`':
            in_str = True
            str_ch = c
            out.append(c)
            i += 1
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '/':
            while i < n and text[i] != '\n':
                i += 1
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '*':
            i += 2
            while i < n - 1 and not (text[i] == '*' and text[i + 1] == '/'):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def _strip_trailing_commas(text):
    out = []
    i, n = 0, len(text)
    in_str = False
    str_ch = ''
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == str_ch:
                in_str = False
            i += 1
            continue
        if c in ('"', "'", '`'):
            in_str = True
            str_ch = c
            out.append(c)
            i += 1
            continue
        if c == ',':
            j = i + 1
            while j < n and text[j].isspace():
                j += 1
            if j < n and text[j] in ']}':
                i = j
                continue
        out.append(c)
        i += 1
    return ''.join(out)


def js_obj_to_json(text):
    out = []
    i, n = 0, len(text)
    in_str = False
    str_ch = ''
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == str_ch:
                in_str = False
            i += 1
            continue
        if c == '"' or c == "'" or c == '`':
            in_str = True
            str_ch = c
            out.append(c)
            i += 1
            continue
        if c == '{' or c == ',':
            out.append(c)
            i += 1
            ws = []
            while i < n and text[i].isspace():
                ws.append(text[i])
                i += 1
            m = re.match(r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', text[i:])
            if m:
                out.extend(ws)
                out.append('"')
                out.append(m.group(1))
                out.append('"')
                out.append(':')
                i += m.end()
                continue
            else:
                out.extend(ws)
                continue
        out.append(c)
        i += 1
    result = ''.join(out)
    return _strip_trailing_commas(result)


def ensure_ids(data):
    seen_ids = set()

    def get_unique_id():
        while True:
            new_id = str(uuid.uuid4())
            if new_id not in seen_ids:
                seen_ids.add(new_id)
                return new_id

    for cat in data:
        if "id" not in cat or cat["id"] in seen_ids:
            cat["id"] = get_unique_id()
        else:
            seen_ids.add(cat["id"])
        for group in cat.get("groups", []):
            if "id" not in group or group["id"] in seen_ids:
                group["id"] = get_unique_id()
            else:
                seen_ids.add(group["id"])
            for sub in group.get("subgroups", []) or []:
                if "id" not in sub or sub["id"] in seen_ids:
                    sub["id"] = get_unique_id()
                else:
                    seen_ids.add(sub["id"])
                for link in sub.get("links", []) or []:
                    if "id" not in link or link["id"] in seen_ids:
                        link["id"] = get_unique_id()
                    else:
                        seen_ids.add(link["id"])
            for link in group.get("links", []) or []:
                if "id" not in link or link["id"] in seen_ids:
                    link["id"] = get_unique_id()
                else:
                    seen_ids.add(link["id"])
    return data


# ==========================================================
# 🐟 鲸鱼娘魔法：自动把 "自娱自乐🧑 - Wordle🎯" 这种被拍平的分组合并
# 规则：如果 group 名字里含有 " - "，就把 " - " 前面的当作父分组
# 后面的当作子分组名。同名的父分组自动合并。
# ==========================================================
def merge_flat_groups(data):
    """把 '自娱自乐🧑 - Wordle🎯' 这种被拍平的分组，还原成 subgroups 嵌套结构"""
    changed = False
    for cat in data:
        groups = cat.get("groups", [])
        if not groups:
            continue

        new_groups = []
        # 已经作为父分组处理过的名字 -> 它在 new_groups 里的位置
        merged_parents = {}
        # 用来记住父分组在 new_groups 里的下标
        parent_index = {}

        for group in groups:
            name = group.get("group") or ""
            # 只处理含 " - " 的、且还没被合并过的
            if " - " in name and "subgroups" not in group:
                parent_name, sub_name = name.split(" - ", 1)
                parent_name = parent_name.strip()
                sub_name = sub_name.strip()

                if parent_name not in parent_index:
                    # 新建一个父分组
                    parent_group = {
                        "id": group.get("id", str(uuid.uuid4())),
                        "group": parent_name,
                        "links": [],
                        "subgroups": []
                    }
                    parent_index[parent_name] = len(new_groups)
                    new_groups.append(parent_group)
                    changed = True
                else:
                    # 原有的 group id 已经被父分组用了，这边给一个全新的
                    changed = True

                new_groups[parent_index[parent_name]]["subgroups"].append({
                    "id": group.get("id", str(uuid.uuid4())) if "id" not in parent_group else str(uuid.uuid4()),
                    "name": sub_name,
                    "links": group.get("links", [])
                })
            else:
                new_groups.append(group)

        if changed:
            cat["groups"] = new_groups
    return data, changed


class LinkManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🐟 鲸鱼娘超链接管理工具")
        self.root.geometry("1200x820")

        self.set_fonts()

        self.data = []
        self.current_layout = "top"
        self.current_json_path = None
        self.current_js_path = None
        self.selected_link_id = None
        self._suppress_listbox_event = False
        self._status_after_id = None

        # 🐟 撤销栈
        self.undo_stack = []
        self.undo_depth = 20

        self.setup_ui()
        self.auto_load()

    def set_fonts(self):
        font_family = "Microsoft YaHei"
        font_size = 10
        for font_name in ["TkDefaultFont", "TkTextFont", "TkFixedFont",
                          "TkMenuFont", "TkHeadingFont", "TkCaptionFont",
                          "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"]:
            try:
                tkfont.nametofont(font_name).configure(family=font_family, size=font_size)
            except tk.TclError:
                pass
        self.root.option_add("*Font", f"{{{font_family}}} {font_size}")
        style = ttk.Style()
        style.configure(".", font=(font_family, font_size))
        style.configure("Treeview", font=(font_family, font_size), rowheight=25)
        style.configure("Treeview.Heading", font=(font_family, font_size, "bold"))

    def push_undo(self):
        """🐟 每次改动前，先把当前状态压进撤销栈"""
        try:
            snapshot = copy.deepcopy(self.data)
        except Exception:
            return
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > self.undo_depth:
            self.undo_stack.pop(0)

    def undo(self):
        """🐟 撤销上一步操作"""
        if not self.undo_stack:
            self.set_status("⚠️ 没有可以撤销的操作了！", "red")
            return
        self.data = self.undo_stack.pop()
        self.refresh_categories()
        self.auto_save()
        self.set_status("✅ 已撤销上一步操作！")

    def auto_load(self):
        if os.path.exists("website_data.json"):
            if self.load_file("website_data.json", silent=True): return
        if os.path.exists(os.path.join("js", "website_data.js")):
            if self.load_file(os.path.join("js", "website_data.js"), silent=True): return
        self.data = [{
            "layout": "top",
            "category": "AI类🤖",
            "groups": [{
                "group": "通用对话💬",
                "links": [{"name": "DeepSeek", "url": "https://www.deepseek.com/"}]
            }]
        }]
        ensure_ids(self.data)
        self.refresh_categories()

    def load_file(self, filepath, silent=False):
        if not filepath: return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            content = strip_js_comments(content)
            try:
                self.data = json.loads(content)
            except json.JSONDecodeError:
                start = content.find('[')
                end = content.rfind(']')
                if start == -1 or end == -1 or end < start:
                    if not silent: messagebox.showerror("错误", "文件中找不到数组数据 [ ... ]！")
                    return False
                json_str = content[start:end + 1]
                try:
                    self.data = json.loads(json_str)
                except json.JSONDecodeError:
                    cleaned = js_obj_to_json(json_str)
                    try:
                        self.data = json.loads(cleaned)
                    except json.JSONDecodeError as e:
                        if not silent:
                            messagebox.showerror("解析失败", f"尝试自动修复后仍无法解析该文件。\n错误：{str(e)}")
                        return False

            ensure_ids(self.data)
            # 🐟 自动合并被拍平的分组
            self.data, merged = merge_flat_groups(self.data)
            if merged and not silent:
                messagebox.showinfo("提示", "检测到被拍平的分组，已自动合并成子分组嵌套结构！")

            if filepath.endswith('.json'):
                self.current_json_path = filepath
                self.current_js_path = None
            else:
                self.current_js_path = filepath
                self.current_json_path = os.path.splitext(filepath)[0] + ".json"
            self.refresh_categories()
            if not silent: messagebox.showinfo("成功", f"成功读取并解析文件！\n路径：{filepath}")
            return True
        except Exception as e:
            if not silent: messagebox.showerror("错误", f"读取文件失败：{str(e)}")
            return False

    def auto_save(self):
        if not self.current_json_path and not self.current_js_path:
            default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js", "website_data.js")
            os.makedirs(os.path.dirname(default), exist_ok=True)
            self.current_js_path = default

        try:
            if self.current_js_path:
                js_content = self.build_js_text() + "\n"
                with open(self.current_js_path, "w", encoding="utf-8") as f:
                    f.write(js_content)
            elif self.current_json_path:
                with open(self.current_json_path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.set_status(f"❌ 自动保存失败：{e}", "red")
            print(f"自动保存失败: {e}")

    def build_js_text(self):
        lines = []
        lines.append("// 🐟 本文件由可爱的鲸鱼娘自动生成！主人不许手改哦，不然本鲸鱼就没收你的米饭！(๑•̀ㅂ•́)و✧")
        lines.append("var website_data = [")

        current_layout = None
        for i, item in enumerate(self.data):
            layout = item.get("layout", "top")
            if layout != current_layout:
                if current_layout is not None:
                    lines.append("")
                if layout == "top":
                    lines.append("  // ==========================================")
                    lines.append("  // 上半部分（large-box-up）")
                    lines.append("  // ==========================================")
                elif layout == "bottom":
                    lines.append("  // ==========================================")
                    lines.append("  // 下半部分（large-box 各种各样）")
                    lines.append("  // ==========================================")
                current_layout = layout

            obj_str = json.dumps(item, ensure_ascii=False, indent=2)
            obj_str = "\n".join("  " + line for line in obj_str.splitlines())
            if i < len(self.data) - 1:
                obj_str += ","
            lines.append(obj_str)
        lines.append("];")
        return "\n".join(lines)

    def save_file(self):
        filepath = filedialog.asksaveasfilename(
            title="另存为...",
            defaultextension=".js",
            initialfile="website_data.js",
            filetypes=[("JavaScript 文件", "*.js"), ("JSON 文件", "*.json")]
        )
        if not filepath: return
        try:
            if filepath.endswith('.json'):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                self.current_json_path = filepath
                self.current_js_path = None
                messagebox.showinfo("成功", f"JSON 备份保存成功！\n路径：{filepath}")
            else:
                js_content = self.build_js_text() + "\n"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(js_content)
                self.current_js_path = filepath
                self.current_json_path = None
                messagebox.showinfo("成功", f"JS 文件导出成功！\n路径：{filepath}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")

    def setup_ui(self):
        toolbar = tk.Frame(self.root, bg="#f0f0f0")
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        file_frame = tk.Frame(toolbar, bg="#f0f0f0")
        file_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
        tk.Button(file_frame, text="📂 导入文件", command=lambda: self.load_file(filedialog.askopenfilename()),
                  bg="#e0e0e0").pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="💾 另存为 (可存JS/JSON)", command=self.save_file, bg="#FFC107").pack(side=tk.LEFT,
                                                                                                        padx=2)
        tk.Button(file_frame, text="🚀 快速导出 website_data.js", command=self.quick_export_js, bg="#4CAF50",
                  fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="↩️ 撤销", command=self.undo, bg="#FF7043", fg="white").pack(side=tk.LEFT, padx=2)
        # 🐟 手动合并被拍平的分组
        tk.Button(file_frame, text="🧹 合并被拍平分组", command=self.manual_merge, bg="#9C27B0", fg="white").pack(
            side=tk.LEFT, padx=2)

        action_frame = tk.Frame(toolbar, bg="#f0f0f0")
        action_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
        tk.Button(action_frame, text="切换到上半部分 (top)", command=lambda: self.switch_layout("top"),
                  bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="切换到下半部分 (bottom)", command=lambda: self.switch_layout("bottom"),
                  bg="#e0e0e0").pack(side=tk.LEFT, padx=5)

        # 🐟 搜索框
        tk.Label(action_frame, text="🔎 搜索链接：", bg="#f0f0f0").pack(side=tk.LEFT, padx=(20, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.on_search())
        tk.Entry(action_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT)
        tk.Button(action_frame, text="清空", command=lambda: self.search_var.set("")).pack(side=tk.LEFT, padx=2)

        main_panel = tk.Frame(self.root)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = tk.Frame(main_panel, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(left_frame, text="📁 分类列表").pack()
        self.cat_listbox = tk.Listbox(left_frame, font=("Microsoft YaHei", 10))
        self.cat_listbox.pack(fill=tk.BOTH, expand=True)
        self.cat_listbox.bind('<<ListboxSelect>>', self.on_select_category)
        cat_btn_frame = tk.Frame(left_frame)
        cat_btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(cat_btn_frame, text="➕ 添加分类", command=self.add_category).pack(side=tk.LEFT, expand=True,
                                                                                    fill=tk.X)
        tk.Button(cat_btn_frame, text="❌ 删除分类", command=self.del_category).pack(side=tk.LEFT, expand=True,
                                                                                    fill=tk.X)

        cat_move_frame = tk.Frame(left_frame)
        cat_move_frame.pack(fill=tk.X, pady=2)
        tk.Button(cat_move_frame, text="⬆️ 上移分类", command=lambda: self.move_category(-1), bg="#E1BEE7").pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        tk.Button(cat_move_frame, text="⬇️ 下移分类", command=lambda: self.move_category(1), bg="#BBDEFB").pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        right_frame = tk.Frame(main_panel)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        tk.Label(right_frame, text="📂 分组 / 子分组 (右键菜单编辑/删除/移动)").pack(anchor="w")
        self.group_tree = ttk.Treeview(right_frame, columns=("type"), show="tree", height=6)
        self.group_tree.column("#0", width=300)
        self.group_tree.pack(fill=tk.X, pady=5)
        self.group_tree.bind('<<TreeviewSelect>>', self.on_select_group)

        self.group_menu = tk.Menu(self.root, tearoff=0)
        self.group_menu.add_command(label="⬆️ 上移", command=lambda: self.move_group(-1))
        self.group_menu.add_command(label="⬇️ 下移", command=lambda: self.move_group(1))
        self.group_menu.add_separator()
        self.group_menu.add_command(label="✏️ 重命名", command=self.rename_group)
        self.group_menu.add_command(label="❌ 删除分组/子组", command=self.del_group)
        self.group_tree.bind("<Button-3>", self.show_group_menu)

        group_btn_frame = tk.Frame(right_frame)
        group_btn_frame.pack(fill=tk.X)
        tk.Button(group_btn_frame, text="➕ 添加顶层分组", command=self.add_group).pack(side=tk.LEFT, expand=True,
                                                                                       fill=tk.X, padx=2)
        tk.Button(group_btn_frame, text="➕ 添加子分组", command=self.add_subgroup).pack(side=tk.LEFT, expand=True,
                                                                                        fill=tk.X, padx=2)

        tk.Label(right_frame, text="🔗 链接列表 (单击选中，直接在底部修改)").pack(anchor="w", pady=(10, 0))
        self.link_tree = ttk.Treeview(right_frame, columns=("name", "url"), show="headings", height=6)
        self.link_tree.heading("name", text="网站名称")
        self.link_tree.heading("url", text="网址")
        self.link_tree.column("name", width=200)
        self.link_tree.column("url", width=450)
        self.link_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.link_tree.bind('<<TreeviewSelect>>', self.on_link_select)

        link_move_frame = tk.Frame(right_frame)
        link_move_frame.pack(fill=tk.X, pady=2)
        tk.Button(link_move_frame, text="⬆️ 上移链接", command=lambda: self.move_link(-1), bg="#E1BEE7").pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        tk.Button(link_move_frame, text="⬇️ 下移链接", command=lambda: self.move_link(1), bg="#BBDEFB").pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        edit_frame = tk.LabelFrame(right_frame, text=" ⚡ 链接编辑区（不用弹窗啦！） ", padx=5, pady=5, bg="#f9f9f9")
        edit_frame.pack(fill=tk.X, pady=5)
        tk.Label(edit_frame, text="网站名称：", bg="#f9f9f9").grid(row=0, column=0, padx=2, pady=2, sticky="e")
        self.link_name_var = tk.StringVar()
        self.link_name_entry = tk.Entry(edit_frame, textvariable=self.link_name_var, width=30)
        self.link_name_entry.grid(row=0, column=1, padx=2, pady=2, sticky="we")
        tk.Label(edit_frame, text="网址：", bg="#f9f9f9").grid(row=0, column=2, padx=2, pady=2, sticky="e")
        self.link_url_var = tk.StringVar()
        self.link_url_entry = tk.Entry(edit_frame, textvariable=self.link_url_var, width=50)
        self.link_url_entry.grid(row=0, column=3, padx=2, pady=2, sticky="we")
        edit_frame.columnconfigure(1, weight=1)
        edit_frame.columnconfigure(3, weight=3)

        btn_frame = tk.Frame(edit_frame, bg="#f9f9f9")
        btn_frame.grid(row=0, column=4, padx=10)
        tk.Button(btn_frame, text="💾 保存修改", command=self.save_link_edit, bg="#2196F3", fg="white").pack(
            side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="➕ 添加到当前分组", command=self.add_link_from_entry, bg="#4CAF50", fg="white").pack(
            side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="❌ 删除选中", command=self.del_link, bg="#f44336", fg="white").pack(side=tk.LEFT,
                                                                                                      padx=2)

        self.status_label = tk.Label(self.root, text="", fg="#4CAF50", anchor="w", font=("Microsoft YaHei", 10, "bold"))
        self.status_label.pack(fill=tk.X, padx=10, pady=2)

    def set_status(self, text, color="#4CAF50"):
        self.status_label.config(text=text, fg=color)
        if self._status_after_id:
            self.root.after_cancel(self._status_after_id)
        self._status_after_id = self.root.after(2500, lambda: self.status_label.config(text=""))

    def manual_merge(self):
        """🐟 手动触发一次合并"""
        self.push_undo()
        self.data, changed = merge_flat_groups(self.data)
        if changed:
            self.refresh_categories()
            self.auto_save()
            self.set_status("✅ 已合并被拍平的分组！")
        else:
            self.set_status("ℹ️ 没有找到需要合并的分组。")

    def on_search(self):
        """🐟 搜索：输入关键字，过滤链接列表（在当前分组下）"""
        keyword = self.search_var.get().strip().lower()
        if not keyword:
            # 清空搜索时，重新显示当前选中分组的全部链接
            self.on_select_group(None)
            return
        # 在当前分类的所有分组里搜
        cat = self.get_current_category()
        if not cat: return
        self.link_tree.delete(*self.link_tree.get_children())
        found = []
        for group in cat.get("groups", []):
            # 分组自身链接
            for link in group.get("links", []) or []:
                name = (link.get("name") or "").lower()
                url = (link.get("url") or "").lower()
                if keyword in name or keyword in url:
                    found.append((group.get("group") or "（无分组名）", link))
            # 子分组
            for sub in group.get("subgroups", []) or []:
                for link in sub.get("links", []) or []:
                    name = (link.get("name") or "").lower()
                    url = (link.get("url") or "").lower()
                    if keyword in name or keyword in url:
                        found.append((f"{group.get('group') or ''} > {sub.get('name') or ''}", link))
        for container_name, link in found:
            self.link_tree.insert("", "end",
                                  values=(f"[{container_name}] {link.get('name', '')}", link.get("url", "")),
                                  tags=(link.get("id", ""),))
        self.set_status(f"🔎 找到 {len(found)} 条匹配的链接", "#2196F3")

    # ==========================================================
    # 🐟 查找辅助函数
    # ==========================================================
    def find_category(self, cat_id):
        for cat in self.data:
            if cat.get("id") == cat_id:
                return cat
        return None

    def find_group(self, cat, group_id):
        for group in cat.get("groups", []):
            if group.get("id") == group_id:
                return group
        return None

    def find_subgroup(self, group, sub_id):
        for sub in group.get("subgroups", []) or []:
            if sub.get("id") == sub_id:
                return sub
        return None

    def locate_link_container(self, link_id):
        for cat in self.data:
            for group in cat.get("groups", []):
                for link in group.get("links", []) or []:
                    if link.get("id") == link_id:
                        return group
                for sub in group.get("subgroups", []) or []:
                    for link in sub.get("links", []) or []:
                        if link.get("id") == link_id:
                            return sub
        return None

    # ==========================================================
    # 🐟 上下移动
    # ==========================================================
    def move_category(self, direction):
        cat = self.get_current_category()
        if not cat:
            self.set_status("⚠️ 请先选中一个分类！", "red")
            return
        filtered = self.get_filtered_categories()
        idx_in_filtered = filtered.index(cat)
        new_idx_in_filtered = idx_in_filtered + direction
        if new_idx_in_filtered < 0 or new_idx_in_filtered >= len(filtered):
            self.set_status("⚠️ 已经到头了，不能再移动！", "red")
            return
        self.push_undo()
        other_cat = filtered[new_idx_in_filtered]
        i1 = self.data.index(cat)
        i2 = self.data.index(other_cat)
        self.data[i1], self.data[i2] = self.data[i2], self.data[i1]
        self.refresh_categories()
        if self.cat_listbox.size() > 0:
            self._suppress_listbox_event = True
            self.cat_listbox.selection_set(new_idx_in_filtered)
            self._suppress_listbox_event = False
            self.on_select_category(None)
        self.auto_save()
        self.set_status("✅ 分类位置已调整！")

    def move_group(self, direction):
        selected = self.group_tree.selection()
        if not selected:
            self.set_status("⚠️ 请先选中一个分组或子分组！", "red")
            return
        item = selected[0]
        tags = self.group_tree.item(item, "tags")
        if not tags: return
        tag = tags[0]
        cat_id = self.group_tree.item(item, "values")[0]
        cat = self.find_category(cat_id)
        if not cat: return
        self.push_undo()

        if tag.startswith("g_"):
            group_id = tag.split("_", 1)[1]
            groups = cat.get("groups", [])
            idx = next((i for i, g in enumerate(groups) if g.get("id") == group_id), -1)
            if idx < 0: return
            new_idx = idx + direction
            if new_idx < 0 or new_idx >= len(groups):
                self.set_status("⚠️ 已经到头了，不能再移动！", "red")
                return
            groups[idx], groups[new_idx] = groups[new_idx], groups[idx]
            self.on_select_category(None)
            self._reselect_group(cat, "g", groups[new_idx].get("id", ""))
            self.auto_save()
            self.set_status("✅ 分组位置已调整！")
        elif tag.startswith("s_"):
            prefix, group_id, sub_id = tag.split("_", 2)
            group = self.find_group(cat, group_id)
            if not group: return
            subs = group.get("subgroups", []) or []
            idx = next((i for i, s in enumerate(subs) if s.get("id") == sub_id), -1)
            if idx < 0: return
            new_idx = idx + direction
            if new_idx < 0 or new_idx >= len(subs):
                self.set_status("⚠️ 已经到头了，不能再移动！", "red")
                return
            subs[idx], subs[new_idx] = subs[new_idx], subs[idx]
            self.on_select_category(None)
            self._reselect_group(cat, "s", group_id, subs[new_idx].get("id", ""))
            self.auto_save()
            self.set_status("✅ 子分组位置已调整！")

    def _reselect_group(self, cat, prefix, group_id, sub_id=None):
        for g_child in self.group_tree.get_children():
            tags = self.group_tree.item(g_child, "tags")
            if not tags: continue
            if prefix == "g" and tags[0] == f"g_{group_id}":
                self.group_tree.selection_set(g_child)
                self.group_tree.see(g_child)
                self.on_select_group(None)
                return
            if prefix == "s":
                for s_child in self.group_tree.get_children(g_child):
                    s_tags = self.group_tree.item(s_child, "tags")
                    if s_tags and s_tags[0] == f"s_{group_id}_{sub_id}":
                        self.group_tree.selection_set(s_child)
                        self.group_tree.see(s_child)
                        self.on_select_group(None)
                        return

    def move_link(self, direction):
        if not self.selected_link_id:
            self.set_status("⚠️ 请先选中一条链接！", "red")
            return
        container = self.locate_link_container(self.selected_link_id)
        if not container:
            self.set_status("❌ 找不到这条链接！", "red")
            return
        links = container.get("links", [])
        idx = next((i for i, l in enumerate(links) if l.get("id") == self.selected_link_id), -1)
        if idx < 0: return
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(links):
            self.set_status("⚠️ 已经到头了，不能再移动！", "red")
            return
        self.push_undo()
        links[idx], links[new_idx] = links[new_idx], links[idx]
        self.on_select_group(None)
        for item_id in self.link_tree.get_children():
            if self.link_tree.item(item_id, "tags") == (self.selected_link_id,):
                self.link_tree.selection_set(item_id)
                self.link_tree.see(item_id)
                break
        self.auto_save()
        self.set_status("✅ 链接位置已调整！")

    # ==========================================================
    # 其他功能
    # ==========================================================
    def show_group_menu(self, event):
        item = self.group_tree.identify_row(event.y)
        if item:
            self.group_tree.selection_set(item)
            self.group_menu.post(event.x_root, event.y_root)

    def rename_group(self):
        selected = self.group_tree.selection()
        if not selected: return
        item = selected[0]
        tags = self.group_tree.item(item, "tags")
        if not tags: return
        tag = tags[0]
        cat_id = self.group_tree.item(item, "values")[0]
        cat = self.find_category(cat_id)
        if not cat: return
        self.push_undo()

        if tag.startswith("g_"):
            group_id = tag.split("_", 1)[1]
            group = self.find_group(cat, group_id)
            if not group: return
            old = group.get("group") or ""
            new_name = simpledialog.askstring("编辑分组", "修改分组名称：", initialvalue=old, parent=self.root)
            self.root.focus_force()
            if new_name is not None:
                group["group"] = new_name if new_name else None
                self.on_select_category(None)
                self.auto_save()
        elif tag.startswith("s_"):
            prefix, group_id, sub_id = tag.split("_", 2)
            group = self.find_group(cat, group_id)
            if not group: return
            sub = self.find_subgroup(group, sub_id)
            if not sub: return
            old = sub.get("name", "")
            new_name = simpledialog.askstring("编辑子分组", "修改子分组名称：", initialvalue=old, parent=self.root)
            self.root.focus_force()
            if new_name:
                sub["name"] = new_name
                self.on_select_category(None)
                self.auto_save()

    def on_link_select(self, event):
        selected = self.link_tree.selection()
        if not selected:
            self.selected_link_id = None
            return
        item = selected[0]
        tags = self.link_tree.item(item, "tags")
        if not tags:
            self.selected_link_id = None
            return
        self.selected_link_id = tags[0]
        vals = self.link_tree.item(item, "values")
        if vals:
            self.link_name_var.set(vals[0])
            self.link_url_var.set(vals[1])
        self.status_label.config(text="")

    def save_link_edit(self):
        if not self.selected_link_id:
            self.set_status("⚠️ 请先在链接列表里选中一个链接！", "red")
            return
        sel = self.link_tree.selection()
        if not sel or self.link_tree.item(sel[0], "tags")[0] != self.selected_link_id:
            self.set_status("⚠️ 链接列表的选择已失效，请重新点一下要修改的链接。", "red")
            self.selected_link_id = None
            return
        name = self.link_name_var.get().strip()
        url = self.link_url_var.get().strip()
        if not name or not url:
            self.set_status("⚠️ 网站名称和网址都不能为空！", "red")
            return
        container = self.locate_link_container(self.selected_link_id)
        if not container:
            self.set_status("❌ 找不到这条链接，可能已经被删除了。", "red")
            return
        self.push_undo()
        for link in container.get("links", []):
            if link.get("id") == self.selected_link_id:
                link["name"] = name
                link["url"] = url
                break
        for item_id in self.link_tree.get_children():
            if self.link_tree.item(item_id, "tags") == (self.selected_link_id,):
                self.link_tree.item(item_id, values=(name, url))
                self.link_tree.selection_set(item_id)
                break
        self.auto_save()
        self.set_status("✅ 修改已保存到文件！")

    def add_link_from_entry(self):
        cat_data, container = self.get_current_link_target()
        if not cat_data or container is None:
            self.set_status("⚠️ 请先在中间列表选中一个分组或子分组！", "red")
            return
        name = self.link_name_var.get().strip()
        url = self.link_url_var.get().strip()
        if not name or not url:
            self.set_status("⚠️ 请先在输入框里填好网站名称和网址！", "red")
            return
        self.push_undo()
        container.setdefault("links", []).append({
            "id": str(uuid.uuid4()),
            "name": name,
            "url": url
        })
        self.link_name_var.set("")
        self.link_url_var.set("")
        self.selected_link_id = None
        self.on_select_group(None)
        self.auto_save()
        self.set_status("✅ 链接已添加并保存！")

    def quick_export_js(self):
        try:
            if self.current_json_path:
                base_dir = os.path.dirname(self.current_json_path)
            elif self.current_js_path:
                base_dir = os.path.dirname(self.current_js_path)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            if os.path.basename(base_dir) == "js":
                js_dir = base_dir
            else:
                js_dir = os.path.join(base_dir, "js")
            os.makedirs(js_dir, exist_ok=True)
            filepath = os.path.join(js_dir, "website_data.js")
            js_content = self.build_js_text() + "\n"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(js_content)
            self.current_js_path = filepath
            self.current_json_path = None
            messagebox.showinfo("成功", f"已导出到：\n{filepath}")
        except Exception as e:
            messagebox.showerror("错误", f"快速导出失败：{str(e)}")

    def switch_layout(self, layout):
        current_name = None
        sel = self.cat_listbox.curselection()
        if sel: current_name = self.cat_listbox.get(sel[0])
        self.current_layout = layout
        self.refresh_categories()
        if current_name:
            for i in range(self.cat_listbox.size()):
                if self.cat_listbox.get(i) == current_name:
                    self._suppress_listbox_event = True
                    self.cat_listbox.selection_clear(0, tk.END)
                    self.cat_listbox.selection_set(i)
                    self._suppress_listbox_event = False
                    self.on_select_category(None)
                    break

    def get_filtered_categories(self):
        return [cat for cat in self.data if cat.get("layout", "top") == self.current_layout]

    def refresh_categories(self):
        self._suppress_listbox_event = True
        self.cat_listbox.delete(0, tk.END)
        self.group_tree.delete(*self.group_tree.get_children())
        self.link_tree.delete(*self.link_tree.get_children())
        self.link_name_var.set("")
        self.link_url_var.set("")
        self.selected_link_id = None
        self.status_label.config(text="")
        for cat in self.get_filtered_categories():
            self.cat_listbox.insert(tk.END, cat.get("category", "（无名分类）"))
        self._suppress_listbox_event = False

    def get_current_category(self):
        selection = self.cat_listbox.curselection()
        if not selection: return None
        filtered = self.get_filtered_categories()
        if selection[0] >= len(filtered): return None
        return filtered[selection[0]]

    def on_select_category(self, event):
        if self._suppress_listbox_event:
            return
        cat = self.get_current_category()
        if not cat: return
        self.group_tree.delete(*self.group_tree.get_children())
        self.link_tree.delete(*self.link_tree.get_children())
        self.link_name_var.set("")
        self.link_url_var.set("")
        self.selected_link_id = None
        self.status_label.config(text="")
        for group in cat.get("groups", []):
            group_id = group.get("id", "")
            group_name = group.get("group") or "（无分组名/占位）"
            group_node = self.group_tree.insert("", "end", text=f"📁 {group_name}",
                                                values=(cat.get("id", ""),),
                                                tags=(f"g_{group_id}",))
            subgroups = group.get("subgroups") or []
            for sub in subgroups:
                sub_id = sub.get("id", "")
                self.group_tree.insert(group_node, "end",
                                       text=f"📂 {sub.get('name', '（无名）')}",
                                       values=(cat.get("id", ""),),
                                       tags=(f"s_{group_id}_{sub_id}",))

    def on_select_group(self, event):
        selected = self.group_tree.selection()
        if not selected: return
        item = selected[0]
        tags = self.group_tree.item(item, "tags")
        if not tags: return
        cat_id = self.group_tree.item(item, "values")[0]
        cat = self.find_category(cat_id)
        if not cat: return
        self.link_tree.delete(*self.link_tree.get_children())
        self.link_name_var.set("")
        self.link_url_var.set("")
        self.selected_link_id = None
        self.status_label.config(text="")
        tag = tags[0]
        if tag.startswith("g_"):
            group_id = tag.split("_", 1)[1]
            group = self.find_group(cat, group_id)
            if not group: return
            for link in group.get("links", []) or []:
                self.link_tree.insert("", "end",
                                      values=(link.get("name", ""), link.get("url", "")),
                                      tags=(link.get("id", ""),))
        elif tag.startswith("s_"):
            prefix, group_id, sub_id = tag.split("_", 2)
            group = self.find_group(cat, group_id)
            if not group: return
            sub = self.find_subgroup(group, sub_id)
            if not sub: return
            for link in sub.get("links", []) or []:
                self.link_tree.insert("", "end",
                                      values=(link.get("name", ""), link.get("url", "")),
                                      tags=(link.get("id", ""),))

    def add_category(self):
        name = simpledialog.askstring("添加分类", "请输入分类名称：", parent=self.root)
        self.root.focus_force()
        if name:
            self.push_undo()
            self.data.append({
                "id": str(uuid.uuid4()),
                "layout": self.current_layout,
                "category": name,
                "groups": []
            })
            self.refresh_categories()
            if self.cat_listbox.size() > 0:
                self._suppress_listbox_event = True
                self.cat_listbox.selection_set(self.cat_listbox.size() - 1)
                self._suppress_listbox_event = False
                self.on_select_category(None)
            self.auto_save()

    def del_category(self):
        cat = self.get_current_category()
        if not cat: return
        name = cat.get("category", "")
        if not messagebox.askyesno("确认", f"确定要删除分类「{name}」吗？"): return
        self.push_undo()
        self.data.remove(cat)
        self.refresh_categories()
        if self.cat_listbox.size() > 0:
            self._suppress_listbox_event = True
            self.cat_listbox.selection_set(self.cat_listbox.size() - 1)
            self._suppress_listbox_event = False
            self.on_select_category(None)
        self.auto_save()

    def add_group(self):
        cat = self.get_current_category()
        if not cat: return
        group_name = simpledialog.askstring("添加分组", "请输入分组名称（如：自娱自乐🧑）：", parent=self.root)
        self.root.focus_force()
        if group_name:
            self.push_undo()
            cat.setdefault("groups", []).append({
                "id": str(uuid.uuid4()),
                "group": group_name,
                "links": []
            })
            self.on_select_category(None)
            self.auto_save()

    def add_subgroup(self):
        selected = self.group_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先在分组列表里选择一个顶层分组！")
            return
        item = selected[0]
        tags = self.group_tree.item(item, "tags")
        if not tags or not tags[0].startswith("g_"):
            messagebox.showwarning("提示", "只能在顶层分组下添加子分组！")
            return
        cat_id = self.group_tree.item(item, "values")[0]
        cat = self.find_category(cat_id)
        if not cat: return
        group_id = tags[0].split("_", 1)[1]
        group = self.find_group(cat, group_id)
        if not group: return

        sub_name = simpledialog.askstring("添加子分组", "请输入子分组名称（如：Wordle🎯）：", parent=self.root)
        self.root.focus_force()
        if not sub_name:
            return
        self.push_undo()
        if "subgroups" not in group or group["subgroups"] is None:
            group["subgroups"] = []
        group["subgroups"].append({
            "id": str(uuid.uuid4()),
            "name": sub_name,
            "links": []
        })
        self.on_select_category(None)
        self.auto_save()

    def del_group(self):
        selected = self.group_tree.selection()
        if not selected: return
        item = selected[0]
        tags = self.group_tree.item(item, "tags")
        if not tags: return
        tag = tags[0]
        cat_id = self.group_tree.item(item, "values")[0]
        cat = self.find_category(cat_id)
        if not cat: return

        if tag.startswith("g_"):
            group_id = tag.split("_", 1)[1]
            group = self.find_group(cat, group_id)
            if not group: return
            link_count = len(group.get("links", []) or [])
            sub_count = len(group.get("subgroups", []) or [])
            msg = f"确定要删除分组「{group.get('group', '')}」吗？\n该分组包含 {sub_count} 个子分组和 {link_count} 个链接，删除后无法恢复。"
        elif tag.startswith("s_"):
            prefix, group_id, sub_id = tag.split("_", 2)
            group = self.find_group(cat, group_id)
            if not group: return
            sub = self.find_subgroup(group, sub_id)
            if not sub: return
            link_count = len(sub.get("links", []) or [])
            msg = f"确定要删除子分组「{sub.get('name', '')}」吗？\n该子分组包含 {link_count} 个链接，删除后无法恢复。"
        else:
            return

        if not messagebox.askyesno("确认", msg): return
        self.push_undo()

        if tag.startswith("g_"):
            group_id = tag.split("_", 1)[1]
            group = self.find_group(cat, group_id)
            if group: cat["groups"].remove(group)
        elif tag.startswith("s_"):
            prefix, group_id, sub_id = tag.split("_", 2)
            group = self.find_group(cat, group_id)
            if group:
                sub = self.find_subgroup(group, sub_id)
                if sub: group["subgroups"].remove(sub)

        self.on_select_category(None)
        self.link_tree.delete(*self.link_tree.get_children())
        self.auto_save()

    def get_current_link_target(self):
        selected = self.group_tree.selection()
        if not selected: return None, None
        item = selected[0]
        tags = self.group_tree.item(item, "tags")
        if not tags: return None, None
        tag = tags[0]
        cat_id = self.group_tree.item(item, "values")[0]
        cat = self.find_category(cat_id)
        if not cat: return None, None

        if tag.startswith("g_"):
            group_id = tag.split("_", 1)[1]
            group = self.find_group(cat, group_id)
            return cat, group
        elif tag.startswith("s_"):
            prefix, group_id, sub_id = tag.split("_", 2)
            group = self.find_group(cat, group_id)
            if not group: return None, None
            sub = self.find_subgroup(group, sub_id)
            return cat, sub
        return None, None

    def del_link(self):
        selected = self.link_tree.selection()
        if not selected: return
        item = selected[0]
        tags = self.link_tree.item(item, "tags")
        if not tags: return
        link_id = tags[0]
        if not messagebox.askyesno("确认", "确定要删除这个链接吗？"): return
        self.push_undo()

        container = self.locate_link_container(link_id)
        if container:
            for link in list(container.get("links", [])):
                if link.get("id") == link_id:
                    container["links"].remove(link)
                    self.link_name_var.set("")
                    self.link_url_var.set("")
                    self.selected_link_id = None
                    self.on_select_group(None)
                    self.auto_save()
                    return
        else:
            self.set_status("❌ 找不到这条链接，可能已经被删除。", "red")


if __name__ == "__main__":
    root = tk.Tk()
    app = LinkManagerApp(root)
    root.mainloop()