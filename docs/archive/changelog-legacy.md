# Boundary Circle - Legacy Changelog

This file preserves the previous `docs/changelog.md` content after cleanup.

The original document had severe encoding corruption and should not be treated as the current
source of truth.

---

# Boundary Circle - 鏇存柊鏃ュ織 (Changelog)

鏈」鐩伒寰樁娈垫€у紑鍙戠瓥鐣ワ紝纭繚杞欢宸ョ▼璇剧▼椤圭洰鑳藉鎸夋椂銆侀珮璐ㄩ噺鍦颁氦浠樸€備互涓嬫槸椤圭洰鐨勬洿鏂拌褰曘€?

## [v0.1.0] - 閲岀▼纰?1 (鏍稿績鍚庣楠ㄦ灦鎼缓) - 2026-02-27

### 鏋舵瀯璋冩暣璇存槑 (Architecture Simplification)
涓轰簡闄嶄綆寮€鍙戦棬妲涖€佸噺灏戠幆澧冮厤缃甫鏉ョ殑涓嶅彲鎺у洜绱狅紝鎴戜滑瀵瑰垵濮?AI 鐢熸垚鐨勫畯澶ф灦鏋勮繘琛屼簡鈥滈檷缁村噺璐熲€濊皟鏁达細
* **绉婚櫎 PostgreSQL**锛屽垏鎹㈣嚦 **SQLite**銆傚疄鐜扳€滃紑绠卞嵆鐢ㄢ€濓紝灏忕粍鎴愬憳鍏嬮殕浠ｇ爜鍚庡彲鐩存帴杩愯锛屾棤闇€閰嶇疆 Docker 鎴栧畨瑁呮湰鍦版暟鎹簱杞欢銆?
* **绉婚櫎澶嶆潅鐨?SQLAlchemy 閰嶇疆**锛屽紩鍏?**SQLModel**銆傜粨鍚?FastAPI 瀹炵幇浜嗘暟鎹ā鍨嬩笌 Pydantic 妯″瀷鐨勫畬缇庣粺涓€锛屽ぇ骞呭噺灏戜簡浠ｇ爜閲忓拰鍑洪敊姒傜巼銆?
* 鏆傛椂鎼佺疆 ChromaDB 鍜屽鏉傜殑 AI 瀵规帴锛屽厛纭繚鍩虹鐨?CRUD 涓氬姟閫昏緫鐣呴€氾紙閲岀▼纰?3 涓啀寮曞叆杞婚噺绾?AI 鍖归厤鏈哄埗锛夈€?

### 鏂板鍔熻兘 (Features)
* 澧炲姞浜?FastAPI 鐨勫簲鐢ㄧ敓鍛藉懆鏈熺鐞嗭紙鍚姩鏃惰嚜鍔ㄥ垱寤?SQLite 鏁版嵁搴撳拰琛級銆?
* **鏁版嵁搴撳眰 (`src/db/database.py`)**: 瀹炵幇浜嗗熀纭€鐨?SQLite 寮曟搸涓?Session 渚濊禆娉ㄥ叆銆?
* **妯″瀷灞?(`src/models/core.py`)**: 瀹氫箟浜?`User` (鐢ㄦ埛) 鍜?`Circle` (鍦堝瓙) 鐨勫熀纭€鏁版嵁妯″瀷锛堝寘鍚?Base, Create, Read 绛夌敤浜庢帴鍙ｆ牎楠岀殑琛嶇敓妯″瀷锛夈€?
* **API 鎺ュ彛 - 鐢ㄦ埛 (`src/api/users.py`)**:
  * `POST /users/`: 娉ㄥ唽鍒涘缓鏂扮敤鎴枫€?
  * `GET /users/`: 鑾峰彇鐢ㄦ埛鍒楄〃锛堟敮鎸佸垎椤碉級銆?
  * `GET /users/{user_id}`: 鏍规嵁 ID 鑾峰彇鐗瑰畾鐢ㄦ埛銆?
* **API 鎺ュ彛 - 鍦堝瓙 (`src/api/circles.py`)**:
  * `POST /circles/`: 鍒涘缓鏂板湀瀛愶紙鏍￠獙鍒涘缓鑰呮槸鍚﹀瓨鍦級銆?
  * `GET /circles/`: 鑾峰彇鍦堝瓙鍒楄〃锛堟敮鎸佸垎椤碉級銆?
  * `GET /circles/{circle_id}`: 鑾峰彇鐗瑰畾鍦堝瓙璇︽儏銆?

### 淇敼椤?(Changed)
* 閲嶅啓浜?`src/main.py`锛屾敞鍐屼簡鐪熸鐨勮矾鐢?`/users` 鍜?`/circles`锛屽苟鎺ョ浜嗗簲鐢ㄧ殑鍚姩浜嬩欢銆?
* 鏇存柊浜?`requirements.txt`锛屾坊鍔犱簡 `sqlmodel`, `pydantic-settings`, `pytest`, `httpx` 绛夊疄闄呰繍琛岄渶瑕佺殑渚濊禆銆?
* 閲嶅啓浜?`README.md`锛屾洿鏂颁簡鎶€鏈爤鎻忚堪锛屽苟鍔犲叆浜嗘竻鏅扮殑鈥滈樁娈垫€у紑鍙戣鍒?(Milestones)鈥濄€?
* 淇浜?`tests/test_main.py`锛屼娇鍩烘湰鐨勯泦鎴愭祴璇曡兘澶熻窇閫氾紝骞跺姞鍏ヤ簡鍦ㄦ祴璇曞墠鍒涘缓娴嬭瘯琛ㄧ殑閫昏緫銆?

### 閬楃暀闂 / 涓嬩竴姝ヨ鍒?(Todo / Next Steps)
* **閲岀▼纰?2**: 寮曞叆 `Tag` 鍜?`Team` 妯″瀷锛屽疄鐜扳€滃姞鍏ュ湀瀛愬～鍐欐爣绛锯€濅互鍙娾€滃彂甯冪粍闃熼渶姹傗€濈殑鍚庣 API銆?
* **鍓嶇闆嗘垚**: 闇€瑕佸墠绔悓瀛︿娇鐢?Streamlit 瀵规帴鐩墠宸茬粡瀹屾垚鐨?`/users` 鍜?`/circles` 鎺ュ彛銆?

