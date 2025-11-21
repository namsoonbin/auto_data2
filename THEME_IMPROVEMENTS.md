# 테마 시스템 개선 (Theme System Improvements)

> 2025년 1월 - 다크/라이트 모드 전면 개선 및 시스템 테마 감지 구현

## 📋 목차

1. [개요](#개요)
2. [주요 기능](#주요-기능)
3. [변경된 파일 목록](#변경된-파일-목록)
4. [세부 변경사항](#세부-변경사항)
5. [버그 수정](#버그-수정)
6. [기술 스택](#기술-스택)

---

## 개요

쿠팡 판매 자동화 시스템의 사용자 경험을 개선하기 위해 다크/라이트 테마를 전면적으로 재설계했습니다. 시스템 설정을 자동 감지하고, 모든 UI 컴포넌트에 일관된 테마를 적용했습니다.

### 주요 개선 사항
- ✅ 시스템 테마 자동 감지 (prefers-color-scheme)
- ✅ 범용 사이드바 토글 (모바일/데스크톱 공통)
- ✅ 라이트 모드 완전 지원 (헤더, 사이드바, 모든 페이지)
- ✅ 차트 색상 테마 적응
- ✅ 프로필 설정 다이얼로그 테마 지원
- ✅ 접근성 개선 (ARIA 레이블)
- ✅ 메모리 누수 수정
- ✅ 타입 안전성 개선

---

## 주요 기능

### 1. 시스템 테마 자동 감지

**파일**: `coupang-auto/frontend/src/contexts/ThemeContext.tsx`

사용자의 OS 설정(Windows/Mac 다크 모드)을 자동으로 감지하여 첫 방문 시 적절한 테마를 적용합니다.

```typescript
// 우선순위: localStorage → 시스템 설정 → 기본값(light)
const [theme, setThemeState] = useState<Theme>(() => {
  const savedTheme = localStorage.getItem('theme') as Theme;
  if (savedTheme) return savedTheme;

  // 시스템 설정 확인
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
});
```

**동작 방식**:
1. 사용자가 이전에 테마를 선택했다면 → 그 설정 사용
2. 첫 방문이라면 → OS 다크 모드 확인
3. OS가 다크 모드라면 → 다크 테마 적용
4. 그 외 → 라이트 테마 적용

### 2. 범용 사이드바 토글

**파일**: `coupang-auto/frontend/src/App.tsx`

기존의 모바일 전용 메뉴를 제거하고, 모든 화면 크기에서 작동하는 범용 사이드바 토글을 구현했습니다.

**변경 사항**:
- `mobileMenuOpen` → `sidebarOpen` (상태 이름 변경)
- 모바일 오버레이 제거
- 반응형 클래스 제거 (`md:hidden`, `md:translate-x-0`)
- PanelLeftClose/PanelLeft 아이콘 추가
- 메인 컨텐츠 마진 동적 조정: `ml-60` (열림) / `ml-0` (닫힘)

### 3. 라이트 모드 완전 지원

#### 헤더 & 사이드바
- **다크 모드**: Cyan 색상 (#06b6d4), 네온 효과, grain/scan line 효과
- **라이트 모드**: Blue 색상 (#3b82f6), 깔끔한 그림자, 특수 효과 제거

#### 페이지 배경
모든 페이지의 배경을 그라디언트에서 단색으로 통일하여 시각적 일관성 확보:
- **이전**: `bg-gradient-to-br from-blue-50 to-indigo-50`
- **현재**: `bg-gray-50`

**적용된 페이지** (10개):
- HomePage.tsx
- DashboardPage.tsx
- HistoryPage.tsx
- DataManagementPage.tsx
- ExportPage.tsx
- FakePurchaseManagementPage.tsx
- MarginManagementPage.tsx
- ProfileSettingsPage.tsx
- TeamManagementPage.tsx
- LoginPage.tsx

### 4. 차트 테마 적응

**파일**: `coupang-auto/frontend/src/components/SalesChart.tsx`

Recharts 라이브러리를 사용하는 매출 차트가 다크/라이트 모드에 맞게 색상을 자동 변경합니다.

**색상 매핑**:
| 데이터 | 다크 모드 | 라이트 모드 |
|--------|-----------|-------------|
| 매출 | Cyan (#06b6d4) | Blue (#3b82f6) |
| 광고비 | Amber (#f59e0b) | Orange (#f97316) |
| 순이익 | Emerald (#10b981) | Green (#22c55e) |
| 판매량 | Violet (#a78bfa) | Purple (#8b5cf6) |

**폰트 개선**:
- 모든 차트 텍스트의 폰트를 `monospace` → `inherit`로 변경
- 전역 폰트 설정 적용

**적응된 요소**:
- Line 색상 및 두께
- CartesianGrid 색상 및 투명도
- XAxis/YAxis 색상
- Tooltip 배경 및 텍스트
- Legend 아이템 스타일
- Dot 및 ActiveDot 색상

### 5. 프로필 설정 다이얼로그

**파일**:
- `PasswordChangeDialog.tsx` - 비밀번호 변경
- `AccountDeleteDialog.tsx` - 계정 삭제
- `ProfileTab.tsx` - 프로필 정보
- `SecurityTab.tsx` - 보안 설정
- `TenantTab.tsx` - 테넌트 설정

**개선 사항**:
- 다크/라이트 모드 완전 지원
- 일관된 색상 스킴 (cyan/blue)
- Input, Button, Alert 컴포넌트 테마 적응
- 다이얼로그 배경 및 border 색상 조정

---

## 변경된 파일 목록

### 🎨 테마 시스템
- ✨ **NEW**: `coupang-auto/frontend/src/contexts/ThemeContext.tsx`
  - 시스템 테마 자동 감지
  - localStorage 기반 테마 저장

### 📱 레이아웃 & 네비게이션
- `coupang-auto/frontend/src/App.tsx`
  - 범용 사이드바 토글 구현
  - 라이트 모드 헤더/사이드바 스타일링
  - PanelLeftClose/PanelLeft 아이콘 추가

### 📊 차트
- `coupang-auto/frontend/src/components/SalesChart.tsx`
  - 테마별 색상 매핑
  - 폰트 상속 (monospace → inherit)
  - 모든 차트 요소 테마 적응

### 💬 다이얼로그 & 프로필
- `coupang-auto/frontend/src/components/profile/PasswordChangeDialog.tsx`
  - 라이트 모드 지원
  - 메모리 누수 수정
  - ARIA 레이블 추가

- `coupang-auto/frontend/src/components/profile/AccountDeleteDialog.tsx`
  - 라이트 모드 지원
  - 타입 안전성 개선
  - ARIA 레이블 추가

- `coupang-auto/frontend/src/components/profile/ProfileTab.tsx`
- `coupang-auto/frontend/src/components/profile/SecurityTab.tsx`
- `coupang-auto/frontend/src/components/profile/TenantTab.tsx`

### 📄 페이지 컴포넌트 (배경색 통일)
- `coupang-auto/frontend/src/pages/HomePage.tsx`
- `coupang-auto/frontend/src/pages/DashboardPage.tsx`
- `coupang-auto/frontend/src/pages/HistoryPage.tsx`
- `coupang-auto/frontend/src/pages/DataManagementPage.tsx`
- `coupang-auto/frontend/src/pages/ExportPage.tsx`
- `coupang-auto/frontend/src/pages/FakePurchaseManagementPage.tsx`
- `coupang-auto/frontend/src/pages/MarginManagementPage.tsx`
- `coupang-auto/frontend/src/pages/ProfileSettingsPage.tsx`
- `coupang-auto/frontend/src/pages/TeamManagementPage.tsx`
- `coupang-auto/frontend/src/pages/LoginPage.tsx`

### 🎨 UI 컴포넌트
- `coupang-auto/frontend/src/components/ui/radio-group.tsx`
- ✨ **NEW**: `coupang-auto/frontend/src/components/ui/skeleton.tsx`

### ⚙️ 설정 파일
- `coupang-auto/frontend/package.json`
- `coupang-auto/frontend/package-lock.json`
- `coupang-auto/frontend/tailwind.config.js`
- `coupang-auto/frontend/src/main.jsx`

### 🔧 기타
- `.gitignore`
- `.claude/settings.local.json`
- `coupang-auto/backend/routers/metrics.py`

---

## 세부 변경사항

### ThemeContext (시스템 테마 감지)

```typescript
// 이전: 무조건 light 기본값
const [theme, setThemeState] = useState<Theme>(() => {
  const savedTheme = localStorage.getItem('theme') as Theme;
  return savedTheme || 'light';
});

// 현재: 시스템 설정 우선
const [theme, setThemeState] = useState<Theme>(() => {
  const savedTheme = localStorage.getItem('theme') as Theme;
  if (savedTheme) return savedTheme;

  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
});
```

### App.tsx (사이드바 토글)

```typescript
// 이전: 모바일 전용
const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

// 현재: 범용
const [sidebarOpen, setSidebarOpen] = useState(true);

// 사이드바 클래스
className={`
  fixed left-0 top-16 bottom-0 border-r overflow-y-auto z-40
  transition-all duration-300 ease-out
  ${theme === 'dark' ? 'bg-[#0f1115] border-cyan-500/10' : 'bg-white border-gray-200'}
  ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
`}

// 메인 컨텐츠 마진
className={`transition-all duration-300 ${showSidebar ? 'pt-16' : ''} ${
  showSidebar && sidebarOpen ? 'ml-60' : 'ml-0'
} ${theme === 'dark' ? 'bg-[#0f1115]' : 'bg-gray-50'}`}
```

### SalesChart.tsx (차트 테마)

```typescript
// Line 컴포넌트 색상
<Line
  dataKey="매출"
  stroke={theme === 'dark' ? '#06b6d4' : '#3b82f6'}
  dot={{ fill: theme === 'dark' ? '#06b6d4' : '#3b82f6' }}
/>

// 폰트 설정
tick={{
  fill: theme === 'dark' ? '#6b7280' : '#6b7280',
  fontSize: 11,
  fontFamily: 'inherit',  // 'monospace' → 'inherit'
}}

// CartesianGrid
<CartesianGrid
  strokeDasharray="3 3"
  stroke={theme === 'dark' ? '#374151' : '#e5e7eb'}
  opacity={theme === 'dark' ? 0.3 : 0.5}
/>
```

### PasswordChangeDialog.tsx (메모리 누수 수정)

```typescript
// 이전: 메모리 누수 위험
const handlePasswordChange = async () => {
  // ...
  setLocalSuccess('성공');
  setTimeout(() => {
    onOpenChange(false);
  }, 1500);
};

// 현재: useEffect cleanup
useEffect(() => {
  if (!localSuccess) return;

  const timeoutId = setTimeout(() => {
    if (onSuccess) onSuccess('비밀번호가 성공적으로 변경되었습니다');
    onOpenChange(false);
  }, 1500);

  return () => clearTimeout(timeoutId);
}, [localSuccess, onSuccess, onOpenChange]);
```

---

## 버그 수정

### 1. 메모리 누수 (Memory Leak)
**파일**: `PasswordChangeDialog.tsx`

**문제**: setTimeout이 컴포넌트 언마운트 후에도 실행될 수 있음

**해결**: useEffect cleanup 함수로 타이머 정리
```typescript
return () => clearTimeout(timeoutId);
```

### 2. 접근성 (Accessibility)
**파일**: `PasswordChangeDialog.tsx`, `AccountDeleteDialog.tsx`

**문제**: 비밀번호 표시/숨김 버튼에 스크린 리더 지원 없음

**해결**: ARIA 속성 추가
```typescript
<button
  aria-label={showPassword ? "비밀번호 숨기기" : "비밀번호 보기"}
  aria-pressed={showPassword}
>
  <Eye className="w-4 h-4" aria-hidden="true" />
</button>
```

**영향받은 버튼**: 4개
- 현재 비밀번호 토글
- 새 비밀번호 토글
- 새 비밀번호 확인 토글
- 계정 삭제 비밀번호 토글

### 3. 타입 안전성 (Type Safety)
**파일**: `AccountDeleteDialog.tsx`

**문제**: Checkbox의 `checked` 타입이 `boolean | 'indeterminate'`인데 `as boolean` 사용

**해결**: 명시적 비교로 변경
```typescript
// 이전
onCheckedChange={(checked) => setConfirmed(checked as boolean)}

// 현재
onCheckedChange={(checked) => setConfirmed(checked === true)}
```

### 4. 라이트 모드 스타일 누락
**파일**: 여러 다이얼로그 컴포넌트

**문제**: 다크 모드만 스타일링되어 라이트 모드에서 가독성 저하

**해결**: 모든 요소에 라이트 모드 스타일 추가
```typescript
className={theme === 'dark'
  ? 'bg-[#1a1d23] border-gray-800'
  : 'bg-white border-gray-200'
}
```

---

## 기술 스택

### 프론트엔드
- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안전성
- **Vite** - 빌드 도구
- **Tailwind CSS** - 유틸리티 CSS
- **Recharts** - 차트 라이브러리
- **shadcn/ui** - UI 컴포넌트
- **lucide-react** - 아이콘
- **date-fns** - 날짜 포맷팅

### 테마 시스템
- **React Context API** - 전역 상태 관리
- **localStorage** - 테마 설정 저장
- **CSS Media Query** - 시스템 테마 감지
  - `window.matchMedia('(prefers-color-scheme: dark)')`

### 색상 팔레트

#### 다크 모드
- Primary: Cyan (#06b6d4)
- Background: #0f1115, #1a1d23
- Text: White (#ffffff), Gray (#6b7280)
- Accent: Amber (#f59e0b), Emerald (#10b981), Violet (#a78bfa)

#### 라이트 모드
- Primary: Blue (#3b82f6)
- Background: White (#ffffff), Gray-50 (#f9fafb)
- Text: Gray-900 (#111827), Gray-600 (#4b5563)
- Accent: Orange (#f97316), Green (#22c55e), Purple (#8b5cf6)

---

## 사용 방법

### 테마 전환
헤더 우측의 테마 토글 버튼(해/달 아이콘) 클릭

### 사이드바 토글
헤더 좌측의 패널 아이콘 클릭 (PanelLeftClose/PanelLeft)

### 시스템 테마 감지
첫 방문 시 자동으로 OS 설정을 따름. 수동으로 변경하면 해당 설정이 저장됨.

---

## 향후 계획

- [ ] 다크 모드 전용 고대비 테마 추가
- [ ] 사용자 정의 색상 테마 지원
- [ ] 애니메이션 선호도 설정 (prefers-reduced-motion)
- [ ] 시스템 테마 변경 실시간 반영 (matchMedia listener)
- [ ] 테마 프리셋 저장 기능

---

## 참고 자료

- [MDN - prefers-color-scheme](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme)
- [Tailwind CSS Dark Mode](https://tailwindcss.com/docs/dark-mode)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [Recharts Documentation](https://recharts.org/)

---

**Last Updated**: 2025-01-21
**Contributors**: Claude Code Assistant
**Version**: 2.0.0
