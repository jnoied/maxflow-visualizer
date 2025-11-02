import tkinter as tk
from tkinter import filedialog, messagebox
from collections import deque, defaultdict
import math, time, threading

# --------------------------
# BFS (증가경로 탐색)
# --------------------------
def bfs(capacity, flow, adj, s, t):
    parent = {}
    q = deque([(s, float('inf'))])
    while q:
        cur, cur_flow = q.popleft()
        for nxt in adj[cur]:
            residual = capacity[cur][nxt] - flow[cur][nxt]
            if residual > 0 and nxt not in parent and nxt != s:
                parent[nxt] = cur
                new_flow = min(cur_flow, residual)
                if nxt == t:
                    return parent, new_flow
                q.append((nxt, new_flow))
    return None, 0


# --------------------------
# GUI 클래스
# --------------------------
class FlowSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("💧 에드몬드-카프 최대유량 시각화 프로그램")
        self.root.geometry("1100x750")
        self.root.configure(bg="#F5F7FA")

        self.auto_running = False
        self.logs = []

        # ----------- UI 구성 -----------
        self.build_input_ui()
        self.build_canvas_ui()
        self.build_buttons()

        # ----------- 내부 상태 -----------
        self.capacity = defaultdict(lambda: defaultdict(int))
        self.flow = defaultdict(lambda: defaultdict(int))
        self.adj = defaultdict(list)
        self.nodes = {}
        self.edges = {}
        self.edge_texts = {}
        self.edges_data = []
        self.total_flow = 0
        self.finished = False

    # ---------------- UI 구성 함수 ----------------
    def build_input_ui(self):
        input_frame = tk.Frame(self.root, bg="#F5F7FA")
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="정점 이름(공백 구분):", bg="#F5F7FA").grid(row=0, column=0)
        self.node_names_entry = tk.Entry(input_frame, width=40)
        self.node_names_entry.grid(row=0, column=1, padx=5)

        tk.Label(input_frame, text="간선 정보 (예: A B 3):", bg="#F5F7FA").grid(row=1, column=0)
        self.edge_entry = tk.Text(input_frame, width=50, height=4)
        self.edge_entry.grid(row=1, column=1, padx=5)

        tk.Label(input_frame, text="시작 정점:", bg="#F5F7FA").grid(row=2, column=0)
        self.source_entry = tk.Entry(input_frame, width=8)
        self.source_entry.grid(row=2, column=1, sticky="w")

        tk.Label(input_frame, text="도착 정점:", bg="#F5F7FA").grid(row=2, column=1, sticky="e")
        self.sink_entry = tk.Entry(input_frame, width=8)
        self.sink_entry.grid(row=2, column=1, padx=80, sticky="e")

    def build_canvas_ui(self):
        self.canvas = tk.Canvas(self.root, bg="#FFFFFF", width=1050, height=500,
                                highlightthickness=1, highlightbackground="#CFD8DC")
        self.canvas.pack(pady=10)

        self.result_label = tk.Label(self.root,
                                     text="그래프를 입력하고 [📘 그래프 생성] 버튼을 누르세요.",
                                     bg="#F5F7FA", font=("맑은 고딕", 12))
        self.result_label.pack()

    def build_buttons(self):
        btn_frame = tk.Frame(self.root, bg="#F5F7FA")
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="📘 그래프 생성", command=self.create_graph,
                  font=("맑은 고딕", 11), bg="#BBDEFB").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="▶ 다음 단계", command=self.next_step,
                  font=("맑은 고딕", 11), bg="#C8E6C9").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="⏯ 자동 실행", command=self.toggle_auto_run,
                  font=("맑은 고딕", 11), bg="#B3E5FC").grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="💾 저장", command=self.save_graph,
                  font=("맑은 고딕", 11), bg="#FFE082").grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="📂 불러오기", command=self.load_graph,
                  font=("맑은 고딕", 11), bg="#FFD54F").grid(row=0, column=4, padx=5)
        tk.Button(btn_frame, text="🔄 초기화", command=self.reset_simulation,
                  font=("맑은 고딕", 11), bg="#FFCCBC").grid(row=0, column=5, padx=5)
        tk.Button(btn_frame, text="📊 레이아웃 변경", command=self.toggle_layout,
                  font=("맑은 고딕", 11), bg="#D1C4E9").grid(row=0, column=6, padx=5)

    # ---------------- 그래프 생성 ----------------
    def create_graph(self):
        self.canvas.delete("all")
        self.logs.clear()
        self.edges.clear()
        self.edge_texts.clear()
        self.capacity.clear()
        self.flow.clear()
        self.adj.clear()
        self.total_flow = 0
        self.finished = False

        node_names = self.node_names_entry.get().strip().split()
        if not node_names:
            self.result_label.config(text="⚠ 정점 이름을 입력하세요.")
            return

        edges_text = self.edge_entry.get("1.0", tk.END).strip().splitlines()
        self.edges_data = []
        for line in edges_text:
            parts = line.strip().split()
            if len(parts) == 3:
                u, v, c = parts[0], parts[1], int(parts[2])
                self.edges_data.append((u, v, c))
                self.capacity[u][v] += c
                self.adj[u].append(v)
                self.adj[v].append(u)

        self.node_layout = "circular"
        self.draw_nodes(node_names)
        self.draw_edges()
        self.result_label.config(text="✅ 그래프 생성 완료! [▶ 다음 단계] 또는 [⏯ 자동 실행] 버튼을 눌러보세요.")

    # ---------------- 노드 / 간선 시각화 ----------------
    def draw_nodes(self, node_names):
        self.nodes.clear()
        n = len(node_names)
        radius = 200
        cx, cy = 525, 250
        for i, name in enumerate(node_names):
            angle = 2 * math.pi * i / n
            if self.node_layout == "hierarchy":
                x, y = 200 + (i * 650 / (n - 1)), 250
            else:
                x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
            self.nodes[name] = (x, y)
            self.canvas.create_oval(x-25, y-25, x+25, y+25, fill="#BBDEFB", outline="#1976D2", width=2)
            self.canvas.create_text(x, y, text=name, font=("맑은 고딕", 10, "bold"))

    def draw_edges(self):
        offset_cycle = [0, -10, 10, -15, 15, -20, 20]
        for i, (u, v, c) in enumerate(self.edges_data):
            if u not in self.nodes or v not in self.nodes:
                continue
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]
            line = self.canvas.create_line(x1, y1, x2, y2, width=3, fill="#B0BEC5", arrow=tk.LAST)
            midx, midy = (x1 + x2) / 2, (y1 + y2) / 2
            offset_y = offset_cycle[i % len(offset_cycle)]
            txt = self.canvas.create_text(midx, midy + offset_y, text=f"0/{c}",
                                          font=("맑은 고딕", 10), fill="#424242")
            self.edges[(u, v)] = line
            self.edge_texts[(u, v)] = txt
            self.canvas.tag_bind(line, "<Button-1>", lambda e, u=u, v=v: self.show_edge_info(u, v))

    # ---------------- 애니메이션 / 단계 ----------------
    def animate_path(self, path_edges):
        for (u, v) in path_edges:
            if (u, v) in self.edges:
                self.canvas.itemconfig(self.edges[(u, v)], fill="#64B5F6", width=5)
                self.canvas.update()
                time.sleep(0.3)

    def next_step(self):
        if self.finished:
            self.show_summary()
            return

        s, t = self.source_entry.get().strip(), self.sink_entry.get().strip()
        if not s or not t:
            self.result_label.config(text="⚠ 시작/도착 정점을 입력하세요.")
            return

        parent, new_flow = bfs(self.capacity, self.flow, self.adj, s, t)
        if new_flow == 0:
            self.finished = True
            self.show_summary()
            return

        path = []
        v = t
        while v != s:
            u = parent[v]
            path.append((u, v))
            self.flow[u][v] += new_flow
            self.flow[v][u] -= new_flow
            v = u

        path_edges = list(reversed(path))
        self.animate_path(path_edges)
        for (u, v) in path_edges:
            if (u, v) in self.edge_texts:
                self.canvas.itemconfig(self.edge_texts[(u, v)],
                                       text=f"{self.flow[u][v]}/{self.capacity[u][v]}")

        self.logs.append(f"경로: {' → '.join([u for u, _ in path_edges] + [t])} (유량 {new_flow})")
        self.total_flow += new_flow
        self.result_label.config(text=f"현재 총 유량: {self.total_flow}")
        self.canvas.update()

    def show_summary(self):
        messagebox.showinfo("결과 요약",
                            "\n".join(self.logs + [f"\n💧 최대 유량 = {self.total_flow}"]))

    # ---------------- 기타 기능 ----------------
    def show_edge_info(self, u, v):
        info = f"{u} → {v}\n현재 유량: {self.flow[u][v]}\n용량: {self.capacity[u][v]}"
        messagebox.showinfo("간선 정보", info)

    def toggle_layout(self):
        self.node_layout = "hierarchy" if self.node_layout == "circular" else "circular"
        self.create_graph()

    def save_graph(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text files", "*.txt")])
        if not filename:
            return
        with open(filename, "w") as f:
            f.write(" ".join(self.nodes.keys()) + "\n")
            for u, v, c in self.edges_data:
                f.write(f"{u} {v} {c}\n")
        messagebox.showinfo("저장 완료", f"그래프를 저장했습니다.\n{filename}")

    def load_graph(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not filename:
            return
        with open(filename, "r") as f:
            lines = f.read().strip().splitlines()
        self.node_names_entry.delete(0, tk.END)
        self.node_names_entry.insert(0, lines[0])
        self.edge_entry.delete("1.0", tk.END)
        self.edge_entry.insert("1.0", "\n".join(lines[1:]))
        self.create_graph()

    def toggle_auto_run(self):
        if self.auto_running:
            self.auto_running = False
            self.result_label.config(text="⏸ 자동 실행 중지됨.")
        else:
            self.auto_running = True
            threading.Thread(target=self.auto_run_thread, daemon=True).start()

    def auto_run_thread(self):
        while self.auto_running and not self.finished:
            self.next_step()
            time.sleep(1)
        self.auto_running = False

    def reset_simulation(self):
        for u, v, c in self.edges_data:
            if (u, v) in self.edges:
                self.canvas.itemconfig(self.edges[(u, v)], fill="#B0BEC5", width=3)
                self.canvas.itemconfig(self.edge_texts[(u, v)], text=f"0/{c}")
        self.flow.clear()
        self.total_flow = 0
        self.finished = False
        self.logs.clear()
        self.result_label.config(text="시뮬레이션이 초기화되었습니다.")
        self.canvas.update()


# ---------------- 실행 ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = FlowSimulator(root)
    root.mainloop()
