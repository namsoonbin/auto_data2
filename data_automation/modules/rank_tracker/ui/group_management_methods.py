"""
GroupManagementTab에 추가할 메서드들 - 자동 순위 표시 관련
"""

def auto_display_ranks(self):
    """현재 그룹의 모든 아이템에 대해 자동으로 순위 표시"""
    if not self.current_group or not self.engine:
        return

    if not self.current_group.items:
        return

    # 기존 워커가 실행 중이면 중지
    if self.rank_display_worker and self.rank_display_thread:
        self.rank_display_worker.stop()
        self.rank_display_thread.quit()
        self.rank_display_thread.wait()

    # 새로운 워커 생성
    if RankDisplayWorker:
        self.rank_display_worker = RankDisplayWorker(
            self.current_group.group_id,
            self.current_group.items.copy(),
            self.engine
        )

        self.rank_display_thread = QThread()
        self.rank_display_worker.moveToThread(self.rank_display_thread)

        # 시그널 연결
        self.rank_display_worker.progress.connect(self.on_rank_display_progress)
        self.rank_display_worker.item_updated.connect(self.on_item_rank_updated)
        self.rank_display_worker.finished.connect(self.on_rank_display_finished)
        self.rank_display_worker.error.connect(self.on_rank_display_error)

        self.rank_display_thread.started.connect(self.rank_display_worker.run)

        # 워커 시작
        self.rank_display_thread.start()

        logging.info(f"그룹 '{self.current_group.name}' 자동 순위 표시 시작")


def on_rank_display_progress(self, percentage, message):
    """자동 순위 표시 진행률 업데이트"""
    # 상태바나 프로그레스 바가 있다면 업데이트
    logging.debug(f"순위 표시 진행률: {percentage}% - {message}")


def on_item_rank_updated(self, item_id, rank_data):
    """개별 아이템 순위 업데이트"""
    if not self.current_group or item_id not in self.current_group.items:
        return

    try:
        # 그룹 내 아이템 업데이트
        item = self.current_group.items[item_id]

        if rank_data['success']:
            item.last_rank = rank_data['rank']
            item.last_error = None
        else:
            item.last_rank = None
            item.last_error = rank_data.get('error_message', '알 수 없는 오류')

        item.last_checked = rank_data.get('search_time',
                                         datetime.now(timezone(timedelta(hours=9))).isoformat())

        # 데이터 저장
        if self.group_manager:
            self.group_manager.save_groups()

        # UI 업데이트 (해당 카드만)
        self.update_item_card_display(item_id)

        logging.debug(f"아이템 {item.title} 순위 업데이트: {item.last_rank}")

    except Exception as e:
        logging.error(f"아이템 순위 업데이트 실패 (ID: {item_id}): {e}")


def on_rank_display_finished(self):
    """자동 순위 표시 완료"""
    logging.info("자동 순위 표시 완료")

    # 스레드 정리
    if self.rank_display_thread:
        self.rank_display_thread.quit()
        self.rank_display_thread.wait()
        self.rank_display_thread = None
        self.rank_display_worker = None


def on_rank_display_error(self, error_message):
    """자동 순위 표시 오류 처리"""
    logging.error(f"자동 순위 표시 오류: {error_message}")

    # 사용자에게 오류 알림 (선택적)
    # QMessageBox.warning(self, "오류", f"자동 순위 표시 중 오류가 발생했습니다: {error_message}")


def update_item_card_display(self, item_id):
    """특정 아이템 카드의 표시를 업데이트"""
    # products_layout에서 해당 아이템 카드를 찾아서 업데이트
    for i in range(self.products_layout.count()):
        widget = self.products_layout.itemAt(i).widget()
        if isinstance(widget, ItemCard) and widget.item_id == item_id:
            # 카드를 새로운 데이터로 다시 생성
            item = self.current_group.items[item_id]
            new_card = ItemCard(item_id, item)
            new_card.remove_requested.connect(self.remove_item_from_group)

            # 기존 카드 제거하고 새 카드 삽입
            self.products_layout.removeWidget(widget)
            widget.deleteLater()
            self.products_layout.insertWidget(i, new_card)
            break


def remove_item_from_group(self, item_id):
    """그룹에서 아이템 제거"""
    if not self.current_group:
        return

    try:
        # 확인 대화상자
        reply = QMessageBox.question(
            self, "확인",
            f"'{self.current_group.items[item_id].title}' 아이템을 제거하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 아이템 제거
            success = self.current_group.remove_item(item_id)

            if success:
                # 데이터 저장
                if self.group_manager:
                    self.group_manager.save_groups()

                # UI 새로고침
                self.refresh_items_display()
                self.update_group_info()

                QMessageBox.information(self, "완료", "아이템이 제거되었습니다.")
            else:
                QMessageBox.warning(self, "오류", "아이템 제거에 실패했습니다.")

    except Exception as e:
        QMessageBox.critical(self, "오류", f"아이템 제거 중 오류가 발생했습니다: {str(e)}")


def refresh_group_list(self):
    """그룹 목록 새로고침"""
    # 기존 groups_tree 위젯이 있다면 업데이트
    if hasattr(self, 'groups_tree') and self.group_manager:
        self.groups_tree.clear()

        for group in self.group_manager.get_all_groups():
            item = QTreeWidgetItem(self.groups_tree)
            item.setText(0, f"{group.name} ({group.get_item_count()}개)")
            item.setData(0, Qt.UserRole, group.group_id)

        logging.info(f"그룹 목록 새로고침: {len(self.group_manager.get_all_groups())}개 그룹")


def set_engine(self, engine):
    """순위 엔진 설정 (부모 창에서 호출)"""
    self.engine = engine
    logging.info("그룹 관리 탭에 순위 엔진 설정됨")