# Supabase RLS 보안 이슈 해결 가이드

## 🚨 문제 상황
- **4개 테이블**에서 RLS (Row Level Security) 미활성화
- PostgREST를 통한 **무제한 데이터 접근** 가능
- 사용자 개인정보 및 예측 데이터 노출 위험

## 📊 영향받는 테이블
| 테이블 | 위험도 | 내용 |
|--------|--------|------|
| `public.users` | 🔴 HIGH | 사용자 식별 정보 |
| `public.predictions` | 🔴 HIGH | 사용자 예측 번호 |
| `public.matches` | 🟡 MEDIUM | 매칭 결과 |
| `public.draws` | 🟡 MEDIUM | 로또 추첨 데이터 |

## 🛡️ 해결 방안

### 1. 기본 RLS 활성화 (모든 테이블)
```sql
-- 모든 테이블에 RLS 활성화
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.draws ENABLE ROW LEVEL SECURITY;
```

### 2. 기본 차단 정책 (보안 우선)
```sql
-- 기본적으로 모든 접근 차단
CREATE POLICY "Default deny all" ON public.users FOR ALL TO public USING (false);
CREATE POLICY "Default deny all" ON public.predictions FOR ALL TO public USING (false);
CREATE POLICY "Default deny all" ON public.matches FOR ALL TO public USING (false);
CREATE POLICY "Default deny all" ON public.draws FOR ALL TO public USING (false);
```

### 3. 애플리케이션별 접근 정책

#### 🔓 public.draws (로또 추첨 데이터)
```sql
-- 모든 사용자가 읽기 가능 (공개 데이터)
CREATE POLICY "Public read access" ON public.draws
FOR SELECT TO public
USING (true);

-- 서비스 계정만 쓰기 가능
CREATE POLICY "Service write access" ON public.draws
FOR INSERT TO authenticated
USING (auth.jwt() ->> 'role' = 'service_role');
```

#### 👤 public.users (사용자 테이블)
```sql
-- 자신의 데이터만 읽기 가능
CREATE POLICY "Users can view own data" ON public.users
FOR SELECT TO authenticated
USING (user_key = (auth.jwt() ->> 'user_key'));

-- 새 사용자 생성 허용
CREATE POLICY "Allow user creation" ON public.users
FOR INSERT TO authenticated
WITH CHECK (user_key = (auth.jwt() ->> 'user_key'));
```

#### 🎯 public.predictions (예측 데이터)
```sql
-- 자신의 예측만 읽기 가능
CREATE POLICY "Users can view own predictions" ON public.predictions
FOR SELECT TO authenticated
USING (user_key = (auth.jwt() ->> 'user_key'));

-- 자신의 예측만 생성 가능
CREATE POLICY "Users can create own predictions" ON public.predictions
FOR INSERT TO authenticated
WITH CHECK (user_key = (auth.jwt() ->> 'user_key'));
```

#### 🏆 public.matches (매칭 결과)
```sql
-- 자신의 매칭 결과만 읽기 가능
CREATE POLICY "Users can view own matches" ON public.matches
FOR SELECT TO authenticated
USING (
  prediction_id IN (
    SELECT id FROM public.predictions 
    WHERE user_key = (auth.jwt() ->> 'user_key')
  )
);

-- 서비스 계정만 매칭 결과 생성 가능
CREATE POLICY "Service can create matches" ON public.matches
FOR INSERT TO authenticated
USING (auth.jwt() ->> 'role' = 'service_role');
```

## ⚠️ 주의사항

### 1. 현재 애플리케이션 영향
- **백엔드 API**: 서비스 키로 접근하므로 영향 없음
- **프론트엔드**: 현재 직접 Supabase 접근 안함
- **크론 작업**: 서비스 키 사용으로 영향 없음

### 2. 단계별 적용 권장
```sql
-- 1단계: RLS 활성화만 (기존 기능 유지)
ALTER TABLE public.draws ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for now" ON public.draws FOR ALL TO public USING (true);

-- 2단계: 점진적 정책 적용
-- 3단계: 최종 보안 정책 적용
```

## 🔧 구현 순서

1. **테스트 환경에서 먼저 적용**
2. **RLS 활성화 + 임시 전체 허용 정책**
3. **애플리케이션 동작 확인**
4. **단계별 보안 정책 적용**
5. **프로덕션 환경 적용**

## 📝 체크리스트

- [ ] 테스트 환경 RLS 활성화
- [ ] 기존 기능 동작 확인
- [ ] 보안 정책 단계별 적용
- [ ] 프로덕션 환경 적용
- [ ] 모니터링 및 로그 확인

## 🚀 즉시 적용 가능한 안전한 방법

```sql
-- 1. RLS 활성화 (모든 테이블)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.draws ENABLE ROW LEVEL SECURITY;

-- 2. 임시 전체 허용 정책 (기존 기능 유지)
CREATE POLICY "Temporary allow all" ON public.users FOR ALL TO public USING (true);
CREATE POLICY "Temporary allow all" ON public.predictions FOR ALL TO public USING (true);
CREATE POLICY "Temporary allow all" ON public.matches FOR ALL TO public USING (true);
CREATE POLICY "Temporary allow all" ON public.draws FOR ALL TO public USING (true);
```

이후 단계별로 보안 정책을 강화해 나가면 됩니다! 🛡️
