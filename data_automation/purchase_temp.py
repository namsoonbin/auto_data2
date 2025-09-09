    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 헤더
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #E1F5FE, stop:1 #81D4FA);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
        """)
        header_layout = QVBoxLayout(header_widget)
        
        title_label = QLabel("🛒 일일 가구매 개수 설정")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 800;
            color: #01579B;
            margin: 0;
        """)
        
        subtitle_label = QLabel("상품별 가구매 개수를 날짜별로 설정하세요")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #0277BD;
            margin-top: 4px;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_widget)
        
        # --- 날짜 선택 및 복사 ---
        date_group = QGroupBox("날짜 선택 및 설정 복사")
        date_layout = QGridLayout()
        
        date_layout.addWidget(QLabel("<b>수정할 날짜:</b>"), 0, 0)
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setDate(QDate.currentDate())
        self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.dateChanged.connect(self.load_purchases_for_date)
        date_layout.addWidget(self.target_date_edit, 0, 1)
        
        date_layout.addWidget(QLabel("<b>설정 복사:</b>"), 1, 0)
        self.source_date_edit = QDateEdit()
        self.source_date_edit.setDate(QDate.currentDate().addDays(-1))
        self.source_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.source_date_edit, 1, 1)
        
        self.copy_button = QPushButton("의 설정 불러오기")
        self.copy_button.clicked.connect(self.copy_purchases)
        date_layout.addWidget(self.copy_button, 1, 2)
        
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # --- 검색 및 일괄 설정 ---
        control_group = QGroupBox("검색 및 일괄 설정")
        control_layout = QGridLayout()
        
        # 첫 번째 줄: 검색
        control_layout.addWidget(QLabel("검색:"), 0, 0)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("상품명으로 검색...")
        self.search_box.textChanged.connect(self.filter_products)
        control_layout.addWidget(self.search_box, 0, 1, 1, 2)
        
        # 두 번째 줄: 선택 관리
        self.select_all_checkbox = QCheckBox("전체 선택/해제")
        self.select_all_checkbox.clicked.connect(self.toggle_all_selection)
        control_layout.addWidget(self.select_all_checkbox, 1, 0)
        
        self.selected_count_label = QLabel("선택됨: 0개")
        self.selected_count_label.setStyleSheet("color: #666; font-size: 12px;")
        control_layout.addWidget(self.selected_count_label, 1, 1)
        
        # 세 번째 줄: 일괄 적용
        control_layout.addWidget(QLabel("선택된 항목에 적용:"), 2, 0)
        
        bulk_layout = QHBoxLayout()
        self.bulk_purchase = QSpinBox()
        self.bulk_purchase.setRange(0, 9999)
        self.bulk_purchase.setSuffix(" 개")
        self.bulk_purchase.setSingleStep(1)
        self.bulk_purchase.setValue(0)
        bulk_layout.addWidget(self.bulk_purchase)
        
        # 빠른 설정 버튼들
        quick_buttons = [
            ("0개", 0),
            ("1개", 1),
            ("3개", 3),
            ("5개", 5),
            ("10개", 10)
        ]
        
        for text, value in quick_buttons:
            btn = QPushButton(text)
            btn.setMaximumWidth(50)
            btn.clicked.connect(lambda checked, v=value: self.bulk_purchase.setValue(v))
            btn.setStyleSheet("font-size: 11px; padding: 4px;")
            bulk_layout.addWidget(btn)
        
        bulk_layout.addStretch()
        control_layout.addLayout(bulk_layout, 2, 1, 1, 2)
        
        # 네 번째 줄: 적용 버튼
        self.apply_selected_button = QPushButton("선택된 항목에 적용")
        self.apply_selected_button.clicked.connect(self.apply_to_selected)
        self.apply_selected_button.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        control_layout.addWidget(self.apply_selected_button, 3, 0, 1, 3)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # --- 상품 테이블 ---
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(['선택', '상품ID', '상품명', '가구매 개수'])
        
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 체크박스
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 상품ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상품명
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 가구매 개수
        
        layout.addWidget(self.product_table)
        
        # --- 저장 버튼 ---
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_purchases)
        self.save_button.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px 16px;")
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)

    def load_data_sources(self):
        """초기 데이터 (상품 목록, 전체 가구매 설정) 로드"""
        try:
            if os.path.exists(self.margin_file):
                df = pd.read_excel(self.margin_file, engine='openpyxl')
                if '상품번호' in df.columns:
                    df = df.rename(columns={'상품번호': '상품ID'})
                if '대표옵션' in df.columns:
                    df['대표옵션'] = df['대표옵션'].astype(str).str.upper().isin(['O', 'Y', 'TRUE'])
                    df = df[df['대표옵션'] == True]
                self.products_df = df[['상품ID', '상품명']].drop_duplicates().sort_values(by='상품명')
            else:
                QMessageBox.warning(self, "경고", "마진정보.xlsx 파일을 찾을 수 없습니다.")

            if os.path.exists(self.purchase_file):
                with open(self.purchase_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content:
                        self.all_purchases_data = json.loads(content)
                    else:
                        self.all_purchases_data = {'purchases': []}
            else:
                self.all_purchases_data = {'purchases': []}
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 소스를 로드하는 중 오류가 발생했습니다:\n{e}")

    def load_purchases_for_date(self, q_date):
        """선택된 날짜의 가구매 정보를 테이블에 로드"""
        target_date_str = q_date.toString("yyyy-MM-dd")
        
        purchase_map = {}
        for entry in self.all_purchases_data.get('purchases', []):
            if entry.get('start_date') == target_date_str and entry.get('end_date') == target_date_str:
                purchase_map[str(entry['product_id'])] = entry['purchase_count']

        self.product_table.setRowCount(0)
        self.product_table.setRowCount(len(self.products_df))
        
        for row, (_, product) in enumerate(self.products_df.iterrows()):
            product_id = str(product['상품ID'])
            
            # 체크박스 (0번 컬럼)
            checkbox = QCheckBox()
            checkbox.clicked.connect(self.update_selected_count)
            self.product_table.setCellWidget(row, 0, checkbox)
            
            # 상품ID (1번 컬럼)
            self.product_table.setItem(row, 1, QTableWidgetItem(product_id))
            
            # 상품명 (2번 컬럼)
            self.product_table.setItem(row, 2, QTableWidgetItem(str(product['상품명'])))
            
            # 가구매 개수 (3번 컬럼)
            spinbox = QSpinBox()
            spinbox.setRange(0, 9999)
            spinbox.setSingleStep(1)
            spinbox.setSuffix(" 개")
            spinbox.setValue(purchase_map.get(product_id, 0))
            self.product_table.setCellWidget(row, 3, spinbox)
        
        self.filter_products()
        self.update_selected_count()

    def copy_purchases(self):
        """선택한 날짜의 설정을 현재 날짜의 테이블에 복사"""
        source_date_str = self.source_date_edit.date().toString("yyyy-MM-dd")
        
        purchase_map = {}
        for entry in self.all_purchases_data.get('purchases', []):
            if entry.get('start_date') == source_date_str:
                purchase_map[str(entry['product_id'])] = entry['purchase_count']
        
        if not purchase_map:
            QMessageBox.information(self, "알림", f"{source_date_str}에 저장된 가구매 설정이 없습니다.")
            return

        for row in range(self.product_table.rowCount()):
            product_id = self.product_table.item(row, 1).text()  # 1번 컬럼으로 변경
            spinbox = self.product_table.cellWidget(row, 3)  # 3번 컬럼으로 변경
            if spinbox and product_id in purchase_map:
                spinbox.setValue(purchase_map[product_id])
        
        QMessageBox.information(self, "완료", f"{source_date_str}의 설정이 현재 테이블로 복사되었습니다.\n저장 버튼을 눌러야 최종 반영됩니다.")

    def toggle_all_selection(self):
        """전체 선택/해제 토글"""
        select_all = self.select_all_checkbox.isChecked()
        for row in range(self.product_table.rowCount()):
            if not self.product_table.isRowHidden(row):  # 보이는 행만
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(select_all)
        self.update_selected_count()
    
    def update_selected_count(self):
        """선택된 항목 개수 업데이트"""
        selected_count = 0
        for row in range(self.product_table.rowCount()):
            checkbox = self.product_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
        
        self.selected_count_label.setText(f"선택됨: {selected_count}개")
        self.apply_selected_button.setEnabled(selected_count > 0)
    
    def apply_to_selected(self):
        """선택된 항목에만 가구매 개수 적용"""
        bulk_value = self.bulk_purchase.value()
        applied_count = 0
        
        for row in range(self.product_table.rowCount()):
            checkbox = self.product_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                spinbox = self.product_table.cellWidget(row, 3)
                if spinbox:
                    spinbox.setValue(bulk_value)
                    applied_count += 1
        
        if applied_count > 0:
            QMessageBox.information(self, "완료", f"{applied_count}개 상품에 {bulk_value}개 가구매가 적용되었습니다.")
        else:
            QMessageBox.information(self, "알림", "선택된 상품이 없습니다.")

    def filter_products(self):
        """상품명으로 필터링"""
        search_text = self.search_box.text().lower()
        for row in range(self.product_table.rowCount()):
            product_name = self.product_table.item(row, 2).text().lower()  # 2번 컬럼으로 변경
            self.product_table.setRowHidden(row, search_text not in product_name)
        self.update_selected_count()  # 필터링 후 선택 개수 업데이트

    def save_purchases(self):
        """현재 날짜의 가구매 설정을 저장 (덮어쓰기 방식)"""
        try:
            target_date_str = self.target_date_edit.date().toString("yyyy-MM-dd")
            
            # 현재 날짜와 다른 날짜의 설정만 유지
            other_days_purchases = [
                entry for entry in self.all_purchases_data.get('purchases', [])
                if entry.get('start_date') != target_date_str
            ]
            
            # 현재 테이블의 설정 추가
            new_purchases_for_date = []
            for row in range(self.product_table.rowCount()):
                spinbox = self.product_table.cellWidget(row, 3)  # 3번 컬럼으로 변경
                if spinbox:
                    entry = {
                        'start_date': target_date_str,
                        'end_date': target_date_str,
                        'product_id': self.product_table.item(row, 1).text(),  # 1번 컬럼으로 변경
                        'purchase_count': spinbox.value()
                    }
                    new_purchases_for_date.append(entry)
            
            self.all_purchases_data['purchases'] = other_days_purchases + new_purchases_for_date
            
            with open(self.purchase_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_purchases_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "완료", f"{target_date_str}의 가구매 설정이 저장되었습니다.")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"가구매 설정 저장 중 오류가 발생했습니다:\n{e}")