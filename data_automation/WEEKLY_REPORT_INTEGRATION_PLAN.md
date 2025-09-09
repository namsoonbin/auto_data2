# 주간 리포트 기능 통합 계획서

## 1. 목표

`desktop_app_final.py`에 구현되어 있는 '주간 리포트 생성' 관련 UI 및 로직을 최신 메인 애플리케이션 파일인 `desktop_app.py`에 완전하게 통합한다. 이를 통해 사용자가 최신 Material Design 3 UI에서 모든 기능을 사용할 수 있도록 한다.

## 2. 기술적 원칙

- **단일 책임 원칙 (SRP):** 각 클래스와 메서드는 하나의 기능만 책임지도록 구조를 유지한다.
- **신호와 슬롯 (Signal & Slot):** UI 이벤트와 백그라운드 로직 간의 통신은 PySide6의 표준 신호/슬롯 메커니즘을 사용해 결합도를 낮춘다.
- **UI 반응성 유지:** `QThread`를 사용하여 시간이 오래 걸리는 리포트 생성 작업이 메인 UI 스레드를 차단하지 않도록 한다.
- **코드 일관성:** 새로 추가되는 코드는 `desktop_app.py`의 기존 코드 스타일(클래스 구조, 네이밍 컨벤션, 레이아웃 등)을 따른다.

---

## 3. 상세 실행 계획

### 1단계: 관련 클래스 코드 이전

`desktop_app_final.py`에서 `desktop_app.py`로 주간 리포트 기능에 필요한 두 개의 핵심 클래스를 이전한다.

- **작업 내용:**
  1. `WeeklyReportDialog` 클래스 전체 코드를 복사한다.
  2. `WeeklyWorker` 클래스 전체 코드를 복사한다.
- **배치 위치:** `desktop_app.py` 파일 내에서 다른 Dialog 및 Worker 클래스들이 정의된 곳 근처 (e.g., `ModernRewardDialog` 또는 `ModernManualWorker` 클래스 아래)에 붙여넣는다.
- **기술적 근거:** 관련된 클래스들을 한곳에 모아두면 코드의 가독성이 향상되고, 향후 기능 변경 시 관련 코드를 쉽게 찾을 수 있어 유지보수에 용이하다.

---

### 2단계: UI 요소 통합 및 레이아웃 배치

사용자가 기능을 실행할 수 있도록 '주간 리포트' 버튼을 메인 화면에 추가하고 배치한다.

- **작업 내용:**
  1. `desktop_app_final.py`의 `create_settings_section` 메서드에서 `weekly_report_btn`을 생성하는 코드 라인을 복사한다.
  2. `desktop_app.py`의 `create_settings_section` 메서드 내 `settings_control_layout` (설정 관리 버튼들이 있는 레이아웃)에 해당 코드를 추가한다.
- **참고 코드 (`desktop_app.py` 수정):**
  ```python
  # ... in create_settings_section method ...
  settings_control_layout = QHBoxLayout()
  # ...
  self.reward_btn = AppleStyleButton("리워드 관리", "fa5s.gift" if QTAWESOME_AVAILABLE else None, "#8b5cf6")
  self.reward_btn.clicked.connect(self.show_reward_dialog)
  
  self.purchase_btn = AppleStyleButton("가구매 관리", "fa5s.shopping-cart" if QTAWESOME_AVAILABLE else None, "#f59e0b")
  self.purchase_btn.clicked.connect(self.show_purchase_dialog)

  # <<< 여기에 주간 리포트 버튼 추가 >>>
  self.weekly_report_btn = AppleStyleButton("📅 주간 리포트", "fa5s.calendar-week" if QTAWESOME_AVAILABLE else None, "#10b981")
  self.weekly_report_btn.clicked.connect(self.show_weekly_report_dialog) # 3단계에서 만들 메서드 연결
  
  settings_control_layout.addWidget(self.reward_btn)
  settings_control_layout.addWidget(self.purchase_btn)
  settings_control_layout.addWidget(self.weekly_report_btn) # 레이아웃에 위젯 추가
  settings_control_layout.addStretch()
  ```
- **기술적 근거:** PySide6의 레이아웃 관리자(`QHBoxLayout`)를 사용하면 위젯의 크기나 위치를 직접 계산할 필요 없이 유연하고 반응성 좋은 UI를 만들 수 있다. 이는 애플리케이션 창 크기가 변경되어도 UI가 깨지지 않도록 보장하는 표준적인 방법이다.

---

### 3단계: 신호(Signal)와 슬롯(Slot) 연결

버튼 클릭(신호)에 반응하여 실제 동작(슬롯)이 일어나도록 기능을 연결한다.

- **작업 내용:**
  1. `ModernSalesAutomationApp` 클래스에 `self.weekly_worker = None` 속성을 `__init__`에 추가한다.
  2. `show_weekly_report_dialog` 메서드를 새로 만든다. 이 메서드는 `WeeklyReportDialog`를 생성하고, 사용자가 'OK'를 누르면 `run_weekly_report_creation`을 호출한다.
  3. `run_weekly_report_creation` 메서드를 새로 만든다. 이 메서드는 `WeeklyWorker`를 생성하고 필요한 값(날짜, 폴더 경로)을 전달한 뒤 스레드를 시작시킨다.
  4. `on_weekly_report_finished` 메서드를 새로 만든다. 이 메서드는 `WeeklyWorker`의 `finished_signal`과 연결되어 작업 완료 후 UI를 정리하는 역할을 한다.
- **참고 코드 (`desktop_app.py`에 추가될 메서드):**
  ```python
  # --- Weekly Report Methods ---
  def show_weekly_report_dialog(self):
      if not self.download_folder_path:
          QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
          return

      dialog = WeeklyReportDialog(self)
      if dialog.exec():
          start_date, end_date = dialog.get_dates()
          self.run_weekly_report_creation(start_date, end_date)

  def run_weekly_report_creation(self, start_date, end_date):
      # 4단계: 상태 관리 로직 추가
      self.start_btn.setEnabled(False)
      self.manual_btn.setEnabled(False)
      self.weekly_report_btn.setEnabled(False)
      self.statusBar().showMessage("📅 주간 리포트 생성 중...")

      # Worker 생성 및 신호 연결
      self.weekly_worker = WeeklyWorker(start_date, end_date, self.download_folder_path)
      self.weekly_worker.output_signal.connect(self.update_log)
      self.weekly_worker.finished_signal.connect(self.on_weekly_report_finished)
      self.weekly_worker.start()

  def on_weekly_report_finished(self):
      # 4단계: 상태 관리 로직 추가
      self.start_btn.setEnabled(True)
      self.manual_btn.setEnabled(True)
      self.weekly_report_btn.setEnabled(True)
      self.statusBar().showMessage("✅ 준비됨")
      self.update_log("[INFO] ✅ 주간 리포트 생성이 완료되었습니다.")
      self.weekly_worker = None
  ```
- **기술적 근거:** '신호와 슬롯'은 UI 코드와 로직 코드를 분리(Decoupling)하는 PySide6의 핵심 디자인 패턴이다. 버튼(신호 발생자)은 어떤 객체의 어떤 메서드(슬롯)가 실행될지 알 필요가 없으며, 그저 신호만 보낸다. 이는 코드의 재사용성과 유지보수성을 크게 향상시킨다.

---

### 4단계: UI 상태 관리 강화

주간 리포트 생성 작업이 진행되는 동안 사용자의 다른 입력을 막아 프로그램의 오작동을 방지한다.

- **작업 내용:**
  1. `run_weekly_report_creation` 메서드에서 `WeeklyWorker` 스레드를 시작하기 **전**에, `start_btn`, `manual_btn` 등 다른 주요 버튼을 `setEnabled(False)`로 설정한다.
  2. 상태바 메시지를 "주간 리포트 생성 중..."으로 변경하여 사용자에게 현재 상태를 알린다.
  3. `on_weekly_report_finished` 메서드에서 작업이 끝나면 비활성화했던 버튼들을 다시 `setEnabled(True)`로 설정하고 상태바 메시지를 "준비됨"으로 복원한다.
- **기술적 근거:** 시간이 오래 걸리는 작업 중에는 사용자의 추가적인 입력(예: 다른 버튼 클릭)이 현재 작업과 충돌하거나 예기치 않은 상태를 만들 수 있다. 관련 컨트롤을 비활성화하는 것은 사용자에게 현재 시스템이 다른 작업 중임을 명확히 알리고, 데이터의 정합성과 프로그램의 안정성을 보장하는 필수적인 절차이다.
