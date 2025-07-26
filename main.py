import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
import urllib.parse
import os
import threading
import time
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 결과 및 로그 파일 저장 디렉토리 설정
OUTPUT_DIR = './instagram_data'

# ────────────────────────── 전역 변수 추가 ──────────────────────────
# 프로필 조회 시 얻은 총 팔로워 수를 저장할 변수
global_total_followers_count = 0
global_user_id = None # 팔로워 추출 시 필요한 user_id도 저장

# ────────────────────────── GUI 요소 정의 및 초기화 ──────────────────────────
root = tk.Tk()
root.title("Instagram 프로필 정보 및 미디어 추출기")

# 인증 정보 프레임
auth_frame = tk.LabelFrame(root, text="인증 정보", padx=15, pady=15)
auth_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

tk.Label(auth_frame, text="닉네임 (username):").grid(row=0, column=0, sticky="e", pady=2)
username_entry = tk.Entry(auth_frame, width=40)
username_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

tk.Label(auth_frame, text="sessionid:").grid(row=1, column=0, sticky="e", pady=2)
sessionid_entry = tk.Entry(auth_frame, width=40)
sessionid_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

tk.Label(auth_frame, text="csrftoken:").grid(row=2, column=0, sticky="e", pady=2)
csrftoken_entry = tk.Entry(auth_frame, width=40)
csrftoken_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")


# 버튼 프레임
button_frame = tk.Frame(root, padx=10, pady=5)
button_frame.grid(row=1, column=0, columnspan=2, pady=5) # row 1로 변경

# 조회 버튼 (스레딩 처리)
fetch_button = tk.Button(button_frame, text="프로필 정보 조회", command=lambda: threading.Thread(target=fetch_instagram_data).start())
fetch_button.pack(side=tk.LEFT, padx=10)

# 모든 팔로워 추출 버튼 (초기에는 비활성화, 조회 후 활성화)
extract_all_followers_btn = tk.Button(button_frame, text="모든 팔로워 추출", state=tk.DISABLED,
                                      command=lambda: threading.Thread(target=extract_all_followers_wrapper).start())
extract_all_followers_btn.pack(side=tk.LEFT, padx=10)


# 결과 표시 및 하이라이트 목록 프레임
result_container = tk.LabelFrame(root, text="조회 결과 및 하이라이트", padx=5, pady=5)
result_container.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

# Canvas for scrollability
canvas = tk.Canvas(result_container)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Scrollbar
scrollbar = ttk.Scrollbar(result_container, orient="vertical", command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

canvas.configure(yscrollcommand=scrollbar.set)
# Canvas 크기 변경 시 scrollregion 업데이트
canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion = canvas.bbox("all")))

# Frame inside canvas where actual results will be
result_frame = tk.Frame(canvas)
# create_window에 width를 직접 지정하지 않고, inner frame의 pack/grid가 확장되도록 함
canvas_frame_id = canvas.create_window((0, 0), window=result_frame, anchor="nw")

# result_frame의 크기가 변경될 때 canvas의 scrollregion 업데이트
result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
# 캔버스 크기 변경 시 내부 프레임 너비 조절
canvas.bind('<Configure>', lambda e: canvas.itemconfigure(canvas_frame_id, width=e.width))


result_text = tk.StringVar()
initial_result_label = tk.Label(result_frame, textvariable=result_text, justify="left", anchor="nw", wraplength=480)
initial_result_label.pack(fill=tk.X, padx=5, pady=5)


# 진행률 표시줄
progress_label = tk.Label(root, text="준비 중...", anchor="w")
progress_label.grid(row=3, column=0, columnspan=2, padx=10, pady=2, sticky="ew")

progressbar = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
progressbar.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")


# 로그 출력 영역
log_output = tk.Text(root, width=80, height=15, wrap=tk.WORD, state=tk.DISABLED, bg="#f0f0f0")
log_output.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

# Grid row/column weights for resizing
root.grid_rowconfigure(2, weight=1) # Make result_container expand vertically
root.grid_rowconfigure(5, weight=1) # Make log_output expand vertically
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
auth_frame.grid_columnconfigure(1, weight=1) # Make entry fields expand

# ────────────────────────── 함수 정의 ──────────────────────────

# GUI 업데이트를 위한 헬퍼 함수 (메인 스레드에서 실행)
def update_gui_log(message):
    log_output.config(state=tk.NORMAL)
    log_output.insert(tk.END, message)
    log_output.see(tk.END) # 스크롤을 항상 최신 로그로
    log_output.config(state=tk.DISABLED)

def update_progress_bar(value, text=""):
    progressbar['value'] = value
    progress_label.config(text=text)
    root.update_idletasks() # GUI 업데이트 강제 적용

def reset_progress_bar():
    progressbar['value'] = 0
    progress_label.config(text="준비 중...")
    root.update_idletasks()

def clear_result_frame_content():
    # initial_result_label을 제외한 모든 위젯 삭제
    for widget in result_frame.winfo_children():
        if widget != initial_result_label:
            widget.destroy()
    # 캔버스 스크롤 영역 재설정
    canvas.yview_moveto(0) # 스크롤을 맨 위로
    result_frame.update_idletasks()
    canvas.configure(scrollregion = canvas.bbox("all"))

# 팔로워 추출 스레드 래퍼 함수 (매개변수 전달용)
def extract_all_followers_wrapper():
    global global_total_followers_count, global_user_id

    if global_user_id is None or global_total_followers_count == 0:
        root.after(0, messagebox.showerror, "오류", "먼저 '프로필 정보 조회'를 실행하여 팔로워 수를 확인해야 합니다.")
        return

    # GUI 입력 필드에서 값 가져오기
    username_from_gui = username_entry.get()
    sessionid_from_gui = sessionid_entry.get()
    csrftoken_from_gui = csrftoken_entry.get()

    # 세션 ID에서 ds_user_id 파싱
    try:
        ds_user_id_parsed = sessionid_from_gui.split('%')[0]
        if not ds_user_id_parsed.isdigit(): # ds_user_id는 숫자여야 함
            raise ValueError("Parsed ds_user_id is not a valid number.")
    except (IndexError, ValueError):
        root.after(0, messagebox.showerror, "오류", "sessionid에서 ds_user_id를 파싱할 수 없습니다. sessionid 형식을 확인하세요 (예: 123456789%abc...).")
        return

    follower_query_hash = os.getenv("INSTAGRAM_FOLLOWER_QUERY_HASH") # 이 값은 .env에서 가져옴

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Cookie": f"sessionid={sessionid_from_gui}; csrftoken={csrftoken_from_gui}; ds_user_id={ds_user_id_parsed};", # GUI 값 사용
        "X-CSRFToken": csrftoken_from_gui, # GUI 값 사용
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "DNT": "1",
    }
    # Pass stored user_id (target user's ID) and total_followers_count
    # Note: ds_user_id from .env is for authentication, user_id is the target profile's ID
    extract_all_followers(username_from_gui, global_user_id, global_total_followers_count, follower_query_hash, headers)


def fetch_instagram_data():
    global global_total_followers_count, global_user_id

    root.after(0, reset_progress_bar) # 프로그레스 바 초기화
    root.after(0, clear_result_frame_content) # 기존 하이라이트 목록 초기화
    root.after(0, lambda: extract_all_followers_btn.config(state=tk.DISABLED)) # 조회 시작 시 팔로워 추출 버튼 비활성화

    # GUI 입력 필드에서 값 가져오기
    username_from_gui = username_entry.get()
    sessionid_from_gui = sessionid_entry.get()
    csrftoken_from_gui = csrftoken_entry.get()

    # 필수 값 확인 (GUI 입력값이 비어있는지)
    if not username_from_gui or not sessionid_from_gui or not csrftoken_from_gui:
        root.after(0, messagebox.showerror, "오류", "닉네임, sessionid, csrftoken을 입력해주세요.")
        return

    # 세션 ID에서 ds_user_id 파싱
    ds_user_id_parsed = ""
    try:
        ds_user_id_parsed = sessionid_from_gui.split('%')[0]
        if not ds_user_id_parsed.isdigit():
            raise ValueError("Parsed ds_user_id is not a valid number.")
    except (IndexError, ValueError):
        root.after(0, messagebox.showerror, "오류", "sessionid에서 ds_user_id를 파싱할 수 없습니다. sessionid 형식을 확인하세요 (예: 123456789%abc...).")
        return

    # 환경 변수에서 query_hash 값들은 계속 불러옴
    follower_query_hash = os.getenv("INSTAGRAM_FOLLOWER_QUERY_HASH")
    highlight_query_hash = os.getenv("INSTAGRAM_HIGHLIGHT_QUERY_HASH")
    highlight_media_query_hash = os.getenv("INSTAGRAM_HIGHLIGHT_MEDIA_QUERY_HASH")

    if not (follower_query_hash and highlight_query_hash and highlight_media_query_hash):
        root.after(0, messagebox.showerror, "오류", ".env 파일에서 모든 필수 환경 변수 (query_hash)를 불러오지 못했습니다. config.env 파일을 확인하세요.")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Cookie": f"sessionid={sessionid_from_gui}; csrftoken={csrftoken_from_gui}; ds_user_id={ds_user_id_parsed};", # GUI 값 사용
        "X-CSRFToken": csrftoken_from_gui, # GUI 값 사용
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "DNT": "1",
    }

    current_result_str = ""
    root.after(0, lambda: log_output.config(state=tk.NORMAL))
    root.after(0, update_gui_log, "\n[프로필 정보 조회 시작]\n")

    try:
        # 1. 유저 ID 조회 (username_from_gui 사용)
        search_url = f"https://www.instagram.com/web/search/topsearch/?query={username_from_gui}"
        root.after(0, update_gui_log, f" - 사용자 검색 요청 중: {username_from_gui}\n")
        res = requests.get(search_url, headers=headers)
        res.raise_for_status()

        user_data = res.json()

        # user_data['users']가 비어있을 경우 IndexError 방지
        if not user_data or "users" not in user_data or not user_data["users"]:
            root.after(0, messagebox.showerror, "오류", "유저를 찾을 수 없거나 검색 API 응답이 예상과 다릅니다.")
            root.after(0, lambda: extract_all_followers_btn.config(state=tk.DISABLED)) # 오류 시 버튼 비활성화
            return

        # user_data['users'][0]['user']가 None일 경우 KeyError 방지
        user_info = user_data["users"][0].get("user")
        if not user_info:
            root.after(0, messagebox.showerror, "오류", "유저 정보가 유효하지 않습니다. 응답 구조를 확인하세요.")
            root.after(0, lambda: extract_all_followers_btn.config(state=tk.DISABLED)) # 오류 시 버튼 비활성화
            return

        user_id = user_info.get("pk")
        if not user_id:
            root.after(0, messagebox.showerror, "오류", "유저 ID(pk)를 찾을 수 없습니다. 응답 구조를 확인하세요.")
            root.after(0, lambda: extract_all_followers_btn.config(state=tk.DISABLED)) # 오류 시 버튼 비활성화
            return

        # 전역 변수에 user_id 저장
        global_user_id = user_id

        current_result_str += f"✅ 유저 ID: {user_id}\n"
        root.after(0, update_gui_log, f"✅ 유저 ID: {user_id}\n")

        # 2. 총 팔로워 수 조회 (Graph QL 쿼리 해시 사용)
        # 팔로워 카운트 조회 시 user_id는 조회 대상 프로필의 ID입니다.
        follower_count_variables = {
            "id": user_id, "include_reel": True, "fetch_mutual": False, "first": 1, "after": None
        }
        encoded_follower_count_vars = urllib.parse.quote(json.dumps(follower_count_variables))
        follower_count_graphql_url = f"https://www.instagram.com/graphql/query/?query_hash={follower_query_hash}&variables={encoded_follower_count_vars}"

        root.after(0, update_gui_log, f"[총 팔로워 수 요청 중] {follower_count_graphql_url}\n")

        total_followers_display = "조회 실패" # GUI에 표시될 문자열
        try:
            follower_count_res = requests.get(follower_count_graphql_url, headers=headers)
            follower_count_res.raise_for_status()
            follower_count_data = follower_count_res.json()

            if "data" in follower_count_data and \
               "user" in follower_count_data["data"] and \
               "edge_followed_by" in follower_count_data["data"]["user"]:

                fetched_count = follower_count_data["data"]["user"]["edge_followed_by"].get("count", "0")
                total_followers_display = str(fetched_count) # GUI 표시용

                # 전역 변수에 총 팔로워 수 저장
                global_total_followers_count = int(fetched_count)

                current_result_str += f"👥 총 팔로워 수: {total_followers_display}\n"
                root.after(0, update_gui_log, f"👥 총 팔로워 수: {total_followers_display}\n")
                # 팔로워 추출 버튼 활성화
                root.after(0, lambda: extract_all_followers_btn.config(state=tk.NORMAL))
            else:
                current_result_str += "❌ 총 팔로워 데이터를 찾을 수 없습니다. API 응답 구조를 확인하세요.\n"
                root.after(0, update_gui_log, "❌ 총 팔로워 데이터를 찾을 수 없습니다. API 응답 구조를 확인하세요.\n")
                root.after(0, lambda: extract_all_followers_btn.config(state=tk.DISABLED)) # 실패 시 버튼 비활성화

        except Exception as e:
            current_result_str += f"❌ 총 팔로워 수 조회 실패: {e}\n"
            root.after(0, update_gui_log, f"❌ 총 팔로워 수 조회 실패: {e}\n")
            root.after(0, lambda: extract_all_followers_btn.config(state=tk.DISABLED)) # 실패 시 버튼 비활성화


        # 3. 하이라이트 조회 (기존 query_hash 사용)
        highlight_variables = {
            "user_id": user_id, "include_chaining": False, "include_reel": True,
            "include_suggested_users": False, "include_logged_out_extras": False,
            "include_highlight_reels": True, "include_live_status": True
        }
        encoded_highlight_vars = urllib.parse.quote(json.dumps(highlight_variables))
        highlight_graphql_url = f"https://www.instagram.com/graphql/query/?query_hash={highlight_query_hash}&variables={encoded_highlight_vars}"

        root.after(0, update_gui_log, f"[하이라이트 GraphQL 요청 중] {highlight_graphql_url}\n")

        highlight_data = None # 하이라이트 데이터를 저장할 변수
        try:
            highlight_res = requests.get(highlight_graphql_url, headers=headers)
            highlight_res.raise_for_status()
            highlight_data = highlight_res.json()

            if not highlight_data or "data" not in highlight_data or "user" not in highlight_data["data"]:
                current_result_str += "❌ 하이라이트 API 응답이 예상과 다릅니다. (data 또는 user 필드 없음)\n"
                root.after(0, update_gui_log, "❌ 하이라이트 API 응답이 예상과 다릅니다. (data 또는 user 필드 없음)\n")
            else:
                user_info_highlight = highlight_data["data"]["user"]
                highlight_edges = user_info_highlight.get("edge_highlight_reels", {}).get("edges", [])

                current_result_str += f"🎞️ 하이라이트: {len(highlight_edges)}개\n"
                root.after(0, update_gui_log, f"🎞️ 하이라이트: {len(highlight_edges)}개\n")

                if highlight_edges:
                    current_result_str += "     - 하이라이트 목록 (추출 버튼 클릭):\n"
                    root.after(0, update_gui_log, "     - 하이라이트 목록 (추출 버튼 클릭):\n")

                    # 하이라이트 목록을 GUI에 동적으로 추가
                    for i, edge in enumerate(highlight_edges):
                        node = edge.get("node", {})
                        highlight_id = node.get("id", "ID 없음")
                        highlight_title = node.get("title", "제목 없음")

                        # GUI 업데이트는 메인 스레드에서 해야 함
                        root.after(0, lambda h_id=highlight_id, h_title=highlight_title, current_idx=i: # current_idx로 현재 인덱스를 명시적으로 캡처
                            add_highlight_row_to_gui(h_id, h_title, user_id, sessionid_from_gui, csrftoken_from_gui, ds_user_id_parsed, highlight_media_query_hash, headers, current_idx)) # current_idx 전달
                else:
                    current_result_str += "     - 하이라이트 정보 없음.\n"
                    root.after(0, update_gui_log, "     - 하이라이트 정보 없음.\n")

        except Exception as e:
            current_result_str += f"❌ 하이라이트 조회 실패: {e}\n"
            root.after(0, update_gui_log, f"❌ 하이라이트 조회 실패: {e}\n")


    except requests.exceptions.HTTPError as errh:
        root.after(0, messagebox.showerror, "HTTP 오류", f"HTTP 오류 발생: {errh}")
        current_result_str += f"❌ HTTP 오류 발생: {errh}\n"
    except requests.exceptions.ConnectionError as errc:
        root.after(0, messagebox.showerror, "연결 오류", f"연결 오류 발생: {errc}")
        current_result_str += f"❌ 연결 오류 발생: {errc}\n"
    except requests.exceptions.Timeout as errt:
        root.after(0, messagebox.showerror, "타임아웃 오류", f"타임아웃 오류 발생: {errt}")
        current_result_str += f"❌ 타임아웃 오류 발생: {errt}\n"
    except requests.exceptions.RequestException as err:
        root.after(0, messagebox.showerror, "요청 오류", f"요청 오류 발생: {err}")
        current_result_str += f"❌ 요청 오류 발생: {err}\n"
    except json.JSONDecodeError:
        root.after(0, messagebox.showerror, "JSON 디코딩 오류", "응답을 JSON으로 디코딩할 수 없습니다. 유효하지 않은 응답입니다.")
        current_result_str += "❌ 응답을 JSON으로 디코딩할 수 없습니다. 유효하지 않은 응답입니다.\n"
    except IndexError: # users[0] 같은 인덱스 접근 시 발생
        root.after(0, messagebox.showerror, "유저 검색 오류", "검색 결과에서 유저 정보를 찾을 수 없습니다. 닉네임을 확인하세요.")
        current_result_str += "❌ 검색 결과에서 유저 정보를 찾을 수 없습니다. 닉네임을 확인하세요.\n"
    except KeyError as ke:
        root.after(0, messagebox.showerror, "API 응답 변경", f"JSON 응답에서 예상되는 키를 찾을 수 없습니다: {ke}. 인스타그램 API 변경 가능성.")
        current_result_str += f"❌ JSON 응답에서 예상되는 키를 찾을 수 없습니다: {ke}. 인스타그램 API 변경 가능성.\n"
    except Exception as e:
        root.after(0, messagebox.showerror, "예상치 못한 오류", f"예상치 못한 오류 발생:\n{e}")
        current_result_str += f"❌ 예상치 못한 오류 발생:\n{e}\n"
    finally:
        root.after(0, result_text.set, current_result_str)
        root.after(0, lambda: log_output.config(state=tk.DISABLED))
        root.after(0, lambda: canvas.configure(scrollregion=canvas.bbox("all"))) # 스크롤 영역 최종 업데이트

def add_highlight_row_to_gui(highlight_id, highlight_title, user_id, sessionid, csrftoken, ds_user_id, highlight_media_query_hash, headers, idx):
    highlight_row = tk.Frame(result_frame)
    highlight_row.pack(fill=tk.X, padx=5, pady=2)

    tk.Label(highlight_row, text=f"         {idx+1}. ID: {highlight_id}, 제목: {highlight_title}", justify="left", anchor="w", wraplength=400).pack(side=tk.LEFT, fill=tk.X, expand=True) # wraplength 추가하여 텍스트가 잘리지 않도록 함

    extract_btn = tk.Button(highlight_row, text="추출",
                            command=lambda h_id=highlight_id, h_title=highlight_title:
                            threading.Thread(target=extract_highlight_media,
                                            args=(h_id, h_title, user_id, sessionid, csrftoken, ds_user_id, highlight_media_query_hash, headers)).start())
    extract_btn.pack(side=tk.RIGHT)
    canvas.configure(scrollregion = canvas.bbox("all")) # 새 위젯이 추가될 때마다 스크롤 영역 업데이트

# 모든 팔로워를 추출하여 TXT 파일로 저장하는 함수
# total_followers_count_param은 fetch_instagram_data에서 미리 조회된 값입니다.
def extract_all_followers(username_env, target_user_id, total_followers_count_param, follower_query_hash, headers):
    root.after(0, update_gui_log, f"\n[모든 팔로워 추출 시작] 사용자 ID: {target_user_id}\n")

    # 이미 조회된 총 팔로워 수를 사용합니다.
    total_followers_count = total_followers_count_param
    root.after(0, update_gui_log, f"미리 조회된 총 팔로워 수: {total_followers_count}명.\n")
    root.after(0, update_progress_bar, 0, f"팔로워 {total_followers_count}명 수집 준비 중...")


    all_followers = []
    has_next_page = True
    after_cursor = None
    page_num = 0

    # total_followers_count가 0이면 더 이상 진행할 필요 없음
    if total_followers_count == 0:
        root.after(0, update_gui_log, "총 팔로워 수가 0이므로 추출을 종료합니다.\n")
        root.after(0, update_progress_bar, 100, "팔로워 추출 완료 (0명)!")
        root.after(2000, reset_progress_bar)
        root.after(0, lambda: extract_all_followers_btn.config(state=tk.NORMAL))
        return

    while has_next_page:
        page_num += 1
        current_progress_text = f"팔로워 수집 진행 중... (페이지 {page_num}, 현재 {len(all_followers)}/{total_followers_count}명)"
        progress_val = (len(all_followers) / max(1, total_followers_count)) * 90
        root.after(0, update_progress_bar, progress_val, current_progress_text)

        follower_variables = {
            "id": target_user_id, # 조회 대상 프로필의 ID
            "include_reel": True,
            "fetch_mutual": False,
            "first": 50, # 한 번에 가져올 팔로워 수
            "after": after_cursor
        }
        encoded_follower_vars = urllib.parse.quote(json.dumps(follower_variables))
        follower_graphql_url = f"https://www.instagram.com/graphql/query/?query_hash={follower_query_hash}&variables={encoded_follower_vars}"

        try:
            res = requests.get(follower_graphql_url, headers=headers)
            res.raise_for_status()
            data = res.json()

            if "data" in data and "user" in data["data"] and "edge_followed_by" in data["data"]["user"]:
                edges = data["data"]["user"]["edge_followed_by"]["edges"]
                page_info = data["data"]["user"]["edge_followed_by"]["page_info"]

                for edge in edges:
                    node = edge.get("node", {})
                    all_followers.append({
                        "id": node.get("id", "N/A"),
                        "username": node.get("username", "N/A"),
                        "full_name": node.get("full_name", "N/A")
                    })

                has_next_page = page_info.get("has_next_page", False)
                after_cursor = page_info.get("end_cursor")

                root.after(0, update_gui_log, f" - 페이지 {page_num} 완료. 현재까지 {len(all_followers)}명 수집. 다음 페이지: {has_next_page}\n")

                if has_next_page and len(all_followers) < total_followers_count: # 예상 팔로워 수보다 적을 때만 다음 페이지 진행
                    time.sleep(2)
                else: # 모든 팔로워를 수집했거나 더 이상 다음 페이지가 없을 때
                    has_next_page = False # 루프 종료
            else:
                root.after(0, update_gui_log, "❌ 팔로워 데이터 응답 구조가 예상과 다릅니다. 페이지네이션 중단.\n")
                break

        except Exception as e:
            root.after(0, update_gui_log, f"❌ 팔로워 페이지 {page_num} 조회 실패: {e}\n")
            break

    # 파일 저장 (진행률 90% 이후)
    root.after(0, update_progress_bar, 90, "팔로워 데이터 파일 저장 중...")

    # 저장 경로 설정
    # username_for_dir = os.getenv("INSTAGRAM_USERNAME") # GUI 입력값 사용
    username_for_dir = username_entry.get()
    username_dir_path = os.path.join(OUTPUT_DIR, username_for_dir)
    os.makedirs(username_dir_path, exist_ok=True)
    followers_filename = os.path.join(username_dir_path, f"{username_for_dir}_followers.txt") # 변수명 통일
    try:
        with open(followers_filename, 'w', encoding='utf-8') as f:
            for follower in all_followers:
                f.write(f"ID: {follower['id']}, Username: {follower['username']}, Full Name: {follower['full_name']}\n")
        root.after(0, update_gui_log, f"✅ 모든 팔로워 ({len(all_followers)}명) 저장 완료: {followers_filename}\n")
    except Exception as e:
        root.after(0, update_gui_log, f"❌ 팔로워 파일 저장 실패: {e}\n")
    finally:
        root.after(0, update_progress_bar, 100, "팔로워 추출 완료!")
        root.after(2000, reset_progress_bar)
        root.after(0, lambda: extract_all_followers_btn.config(state=tk.NORMAL)) # 작업 완료 후 다시 활성화

# 하이라이트 미디어를 추출하여 저장하는 함수
def extract_highlight_media(highlight_id, highlight_title, user_id, sessionid, csrftoken, ds_user_id, highlight_media_query_hash, headers):
    root.after(0, reset_progress_bar)
    root.after(0, update_gui_log, f"\n[하이라이트 미디어 추출 시작] ID: {highlight_id}, 제목: {highlight_title}\n")
    root.after(0, update_progress_bar, 0, f"'{highlight_title}' 미디어 정보 가져오는 중...")

    highlight_media_variables = {
        "reel_ids": [],
        "tag_names": [],
        "location_ids": [],
        "highlight_reel_ids": [highlight_id],
        "precomposed_overlay": False,
        "show_story_viewer_list": True,
        "story_viewer_fetch_count": 50,
        "story_viewer_cursor": ""
    }
    encoded_media_vars = urllib.parse.quote(json.dumps(highlight_media_variables))
    highlight_media_graphql_url = f"https://www.instagram.com/graphql/query/?query_hash={highlight_media_query_hash}&variables={encoded_media_vars}"

    root.after(0, update_gui_log, f" - 미디어 요청 URL: {highlight_media_graphql_url}\n")

    try:
        res = requests.get(highlight_media_graphql_url, headers=headers)
        res.raise_for_status()
        data = res.json()

        media_items = data.get('data', {}).get('reels_media', [])

        reels = []
        if media_items:
            for media_reel in media_items:
                reels.extend(media_reel.get('items', []))

        if not reels:
            root.after(0, update_gui_log, " - 해당 하이라이트에 미디어 항목이 없거나 응답 구조가 예상과 다릅니다.\n")
            root.after(0, reset_progress_bar)
            return

        media_dict = {}
        for reel in reels:
            is_video = reel.get('is_video', False)
            media_url = None

            if is_video:
                video_resources = reel.get('video_resources')
                if video_resources and len(video_resources) > 0:
                    media_url = video_resources[-1]['src']
                else:
                    # 비디오인데 video_resources가 없으면 display_resources에서 이미지 URL을 시도
                    display_resources = reel.get('display_resources')
                    if display_resources and len(display_resources) > 0:
                        media_url = display_resources[-1]['src']
                        root.after(0, update_gui_log, f" - 경고: {reel['id']} (비디오)에 비디오 URL 없음. 대신 이미지 URL 사용.\n")
            else: # 이미지인 경우
                display_resources = reel.get('display_resources')
                if display_resources and len(display_resources) > 0:
                    media_url = display_resources[-1]['src']

            if media_url: # URL을 찾았으면 저장
                media_dict[reel['id']] = media_url
            else:
                root.after(0, update_gui_log, f" - [건너뛰기] {reel['id']}: 유효한 미디어 URL을 찾을 수 없습니다.\n")

        # 저장 경로 설정
        # username_for_dir = os.getenv("INSTAGRAM_USERNAME") # GUI 입력값 사용
        username_for_dir = username_entry.get() # GUI에서 현재 입력된 닉네임 사용
        clean_highlight_title = "".join([c for c in highlight_title if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
        if not clean_highlight_title:
            clean_highlight_title = f"Highlight_{highlight_id}"

        # OUTPUT_DIR/사용자닉네임/하이라이트제목 형식으로 폴더 생성
        highlight_subdir = os.path.join(OUTPUT_DIR, username_for_dir, clean_highlight_title)
        os.makedirs(highlight_subdir, exist_ok=True)

        downloaded_count = 0
        total_media_to_download = len(media_dict)

        for media_id, url in media_dict.items():
            if not url:
                root.after(0, update_gui_log, f" - [건너뛰기] {media_id}: 유효한 URL 없음.\n")
                continue

            try:
                from urllib.parse import urlparse
                url_path = urlparse(url).path
                ext = os.path.splitext(url_path)[-1]
                filename = f"{media_id}{ext}"
                save_path = os.path.join(highlight_subdir, filename)

                root.after(0, update_gui_log, f" - 다운로드 중: {filename}...\n")

                r = requests.get(url, stream=True)
                r.raise_for_status()

                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)

                downloaded_count += 1
                current_progress = (downloaded_count / total_media_to_download) * 100
                root.after(0, update_progress_bar, current_progress,
                           f"'{highlight_title}' 미디어 다운로드 진행: {downloaded_count}/{total_media_to_download} ({current_progress:.1f}%)")
                root.after(0, update_gui_log, f" - [완료] {filename}\n")

            except Exception as e:
                root.after(0, update_gui_log, f" - [실패] {media_id} 다운로드 오류: {e}\n")

        root.after(0, update_gui_log, f"✅ 하이라이트 '{highlight_title}' 미디어 {downloaded_count}개 저장 완료: {highlight_subdir}\n")
        root.after(0, update_progress_bar, 100, f"하이라이트 '{highlight_title}' 추출 완료!")
        root.after(2000, reset_progress_bar)

    except Exception as e:
        root.after(0, update_gui_log, f"❌ 하이라이트 미디어 조회/다운로드 실패: {e}\n")
        root.after(0, reset_progress_bar)

# .env 변수를 GUI에 로드하는 함수
def load_env_vars_into_gui():
    username = os.getenv("INSTAGRAM_USERNAME")
    sessionid = os.getenv("INSTAGRAM_SESSIONID")
    csrftoken = os.getenv("INSTAGRAM_CSRFTOKEN")

    if username:
        username_entry.insert(0, username)
    if sessionid:
        sessionid_entry.insert(0, sessionid)
    if csrftoken:
        csrftoken_entry.insert(0, csrftoken)

root.after(100, load_env_vars_into_gui) # GUI가 로드된 후 환경 변수 자동 채우기

root.mainloop()