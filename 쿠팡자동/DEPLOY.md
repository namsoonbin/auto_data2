# 쿠팡 자동화 서비스 배포 가이드

무료로 Vercel (프론트엔드) + Render (백엔드) + Supabase (데이터베이스)에 배포하는 방법입니다.

## 📋 준비 사항

- GitHub 계정
- Vercel 계정 (https://vercel.com)
- Render 계정 (https://render.com)
- Supabase 계정 (https://supabase.com)

---

## 1️⃣ GitHub 저장소 준비

### 1. GitHub에 코드 푸시

```bash
# 현재 변경사항 커밋
git add .
git commit -m "배포 준비: PostgreSQL 설정 추가"
git push origin main
```

---

## 2️⃣ Supabase 데이터베이스 설정

### 1. Supabase 프로젝트 생성

1. https://supabase.com 접속 후 로그인
2. "New project" 클릭
3. 프로젝트 정보 입력:
   - **Name**: coupang-automation
   - **Database Password**: 강력한 비밀번호 입력 (복사해두기!)
   - **Region**: Northeast Asia (Seoul) 선택
   - **Plan**: Free 선택
4. "Create new project" 클릭 (약 2분 소요)

### 2. 데이터베이스 연결 정보 확인

1. 프로젝트 대시보드에서 **Settings** (⚙️) 클릭
2. 왼쪽 메뉴에서 **Database** 클릭
3. **Connection string** 섹션에서 "URI" 복사
   ```
   postgresql://postgres.프로젝트ID:비밀번호@aws-0-region.pooler.supabase.com:6543/postgres
   ```

---

## 3️⃣ Render 백엔드 배포

### 1. Render 프로젝트 생성

1. https://render.com 접속 후 로그인
2. 대시보드에서 **New +** → **Web Service** 클릭
3. GitHub 저장소 연결:
   - "Connect account" → GitHub 계정 연결
   - 저장소 선택: `auto_data2` (또는 본인 저장소 이름)
   - "Connect" 클릭

### 2. 서비스 설정

다음 정보 입력:

| 항목 | 값 |
|------|-----|
| **Name** | `coupang-automation-api` (원하는 이름) |
| **Region** | Oregon (US West) 또는 Singapore |
| **Branch** | `main` |
| **Root Directory** | `쿠팡자동/backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

### 3. 환경 변수 설정

"Environment Variables" 섹션에서 다음 변수 추가:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Supabase에서 복사한 연결 문자열 |
| `SECRET_KEY` | "Generate" 버튼 클릭 (자동 생성) |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |

### 4. 배포 시작

1. "Create Web Service" 클릭
2. 배포 로그 확인 (약 5-10분 소요)
3. 배포 완료 후 URL 확인:
   ```
   https://coupang-automation-api.onrender.com
   ```
4. **이 URL을 복사해두세요!** (프론트엔드에서 사용)

### 5. 초기 데이터베이스 생성 확인

배포 완료 후 첫 번째 요청 시 자동으로 테이블이 생성됩니다:

```bash
# 테스트 요청 (브라우저에서 접속)
https://coupang-automation-api.onrender.com/
```

"Hello World" 응답이 오면 성공!

---

## 4️⃣ Vercel 프론트엔드 배포

### 1. Vercel 프로젝트 생성

1. https://vercel.com 접속 후 로그인
2. "Add New..." → "Project" 클릭
3. GitHub 저장소 Import:
   - "Import Git Repository" 선택
   - 저장소 선택: `auto_data2`
   - "Import" 클릭

### 2. 프로젝트 설정

다음 정보 입력:

| 항목 | 값 |
|------|-----|
| **Project Name** | `coupang-automation` (원하는 이름) |
| **Framework Preset** | `Vite` |
| **Root Directory** | `쿠팡자동/frontend` (Edit 버튼으로 수정) |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

### 3. 환경 변수 설정

"Environment Variables" 섹션에서 추가:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | Render에서 복사한 백엔드 URL<br>(예: `https://coupang-automation-api.onrender.com`) |

⚠️ **주의**: `VITE_` 접두사를 꼭 포함해야 합니다!

### 4. 배포 시작

1. "Deploy" 클릭
2. 배포 로그 확인 (약 2-3분 소요)
3. 배포 완료 후 URL 확인:
   ```
   https://coupang-automation.vercel.app
   ```

---

## 5️⃣ CORS 설정 (백엔드)

### Render에서 환경변수 추가

Render 대시보드 → 서비스 선택 → Environment:

| Key | Value |
|-----|-------|
| `FRONTEND_URL` | Vercel에서 받은 프론트엔드 URL<br>(예: `https://coupang-automation.vercel.app`) |

추가 후 "Save Changes" → 자동 재배포

---

## 6️⃣ 배포 완료 확인

### 1. 프론트엔드 접속

```
https://coupang-automation.vercel.app
```

### 2. 회원가입 테스트

1. "회원가입" 버튼 클릭
2. 정보 입력 후 가입
3. 자동 로그인 확인

### 3. 데이터 업로드 테스트

1. 대시보드 접속
2. 파일 업로드 테스트

---

## 🎉 배포 완료!

무료로 다음 서비스를 사용 중입니다:

- ✅ **프론트엔드**: Vercel (무료)
- ✅ **백엔드**: Render (무료 750시간/월)
- ✅ **데이터베이스**: Supabase (무료 500MB)

---

## 📝 주의사항

### Render Free Tier 제한

- **15분 비활성 시 Sleep 모드**
  - 첫 요청 시 10-30초 대기
  - 이후 정상 작동
- **750시간/월 제한**
  - 한 달 = 720시간 → 충분!

### Supabase Free Tier 제한

- **7일 비활성 시 일시 중지**
  - 해결책: 매일 한 번 이상 접속
- **500MB 저장소**
  - 데이터가 적으면 수년간 사용 가능

---

## 🔧 문제 해결

### 1. 백엔드 응답 없음

**증상**: 프론트엔드에서 API 호출 시 오류

**해결**:
1. Render 대시보드 → Logs 확인
2. DATABASE_URL 환경변수 확인
3. Supabase 프로젝트 활성 상태 확인

### 2. CORS 오류

**증상**: 브라우저 콘솔에 CORS 에러

**해결**:
1. Render에서 FRONTEND_URL 환경변수 확인
2. 값이 정확한 Vercel URL인지 확인
3. 재배포 (환경변수 변경 시 자동)

### 3. 데이터베이스 연결 실패

**증상**: "Database connection failed"

**해결**:
1. Supabase 대시보드 → Settings → Database
2. Connection string 다시 복사
3. Render에서 DATABASE_URL 업데이트

---

## 🚀 업데이트 배포

코드 수정 후 배포:

```bash
git add .
git commit -m "기능 추가"
git push origin main
```

- Render: 자동 재배포 (3-5분)
- Vercel: 자동 재배포 (1-2분)

---

## 💰 비용 (모두 무료!)

| 서비스 | 무료 플랜 | 초과 시 |
|--------|----------|---------|
| Vercel | 무제한 | 무료 유지 |
| Render | 750시간/월 | $7/월 |
| Supabase | 500MB DB | $25/월 |

**예상**: 소규모 서비스는 계속 무료!

---

## 📚 추가 리소스

- [Vercel 문서](https://vercel.com/docs)
- [Render 문서](https://render.com/docs)
- [Supabase 문서](https://supabase.com/docs)

---

배포 완료를 축하합니다! 🎊
