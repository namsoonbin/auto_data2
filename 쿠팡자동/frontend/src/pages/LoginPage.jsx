import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Eye, EyeOff, User, Lock, Mail, Building2, Hash, UserCircle } from 'lucide-react';

function LoginPage() {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);

  // 로그인 폼 상태
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });

  // 회원가입 폼 상태
  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    full_name: '',
    tenant_name: '',
    tenant_slug: ''
  });

  const handleLoginChange = (e) => {
    setLoginData({
      ...loginData,
      [e.target.name]: e.target.value
    });
  };

  const handleRegisterChange = (e) => {
    setRegisterData({
      ...registerData,
      [e.target.name]: e.target.value
    });
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(loginData.email, loginData.password);

      if (result.success) {
        navigate('/dashboard');
      } else {
        setError(result.error || '로그인에 실패했습니다');
      }
    } catch (err) {
      setError('로그인 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // 비밀번호 확인
    if (registerData.password !== registerData.passwordConfirm) {
      setError('비밀번호가 일치하지 않습니다');
      return;
    }

    // 테넌트 슬러그 생성 (자동으로 소문자, 공백을 하이픈으로)
    const tenant_slug = registerData.tenant_slug ||
      registerData.tenant_name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

    setLoading(true);

    try {
      const result = await register({
        email: registerData.email,
        password: registerData.password,
        full_name: registerData.full_name,
        tenant_name: registerData.tenant_name,
        tenant_slug: tenant_slug
      });

      if (result.success) {
        navigate('/dashboard');
      } else {
        setError(result.error || '회원가입에 실패했습니다');
      }
    } catch (err) {
      setError('회원가입 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* 로고 */}
        <div className="flex justify-center mb-8">
          <div className="w-12 h-12 bg-yellow-400 rounded-xl flex items-center justify-center shadow-lg">
            <div className="w-6 h-6 bg-white rounded-full"></div>
          </div>
        </div>

        {/* 제목 */}
        <h1 className="text-center text-slate-800 text-2xl font-medium mb-8">
          쿠팡 판매 데이터 자동화
        </h1>

        {/* 탭 네비게이션 */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => { setTabValue(0); setError(''); }}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-all ${
              tabValue === 0
                ? 'bg-white text-indigo-600 shadow-md'
                : 'bg-white/50 text-slate-600 hover:bg-white/70'
            }`}
          >
            로그인
          </button>
          <button
            onClick={() => { setTabValue(1); setError(''); }}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-all ${
              tabValue === 1
                ? 'bg-white text-indigo-600 shadow-md'
                : 'bg-white/50 text-slate-600 hover:bg-white/70'
            }`}
          >
            회원가입
          </button>
        </div>

        {/* 폼 컨테이너 */}
        <div className="bg-white rounded-2xl p-8 shadow-xl border border-slate-200">
          {/* 에러 메시지 */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* 로그인 폼 */}
          {tabValue === 0 && (
            <form onSubmit={handleLoginSubmit} className="space-y-6">
              {/* 이메일 */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-slate-700">
                  이메일
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="이메일을 입력하세요"
                    value={loginData.email}
                    onChange={handleLoginChange}
                    className="pl-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-indigo-500"
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              {/* 비밀번호 */}
              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-700">
                  비밀번호
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="비밀번호를 입력하세요"
                    value={loginData.password}
                    onChange={handleLoginChange}
                    className="pl-10 pr-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-indigo-500"
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* 로그인 버튼 */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white h-10"
              >
                {loading ? '로그인 중...' : '로그인'}
              </Button>
            </form>
          )}

          {/* 회원가입 폼 */}
          {tabValue === 1 && (
            <form onSubmit={handleRegisterSubmit} className="space-y-6">
              {/* 이메일 */}
              <div className="space-y-2">
                <Label htmlFor="register-email" className="text-slate-700">
                  이메일
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="register-email"
                    name="email"
                    type="email"
                    placeholder="이메일을 입력하세요"
                    value={registerData.email}
                    onChange={handleRegisterChange}
                    className="pl-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400"
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              {/* 이름 */}
              <div className="space-y-2">
                <Label htmlFor="full_name" className="text-slate-700">
                  이름
                </Label>
                <div className="relative">
                  <UserCircle className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="full_name"
                    name="full_name"
                    type="text"
                    placeholder="이름을 입력하세요"
                    value={registerData.full_name}
                    onChange={handleRegisterChange}
                    className="pl-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400"
                    required
                    autoComplete="name"
                  />
                </div>
              </div>

              {/* 비밀번호 */}
              <div className="space-y-2">
                <Label htmlFor="register-password" className="text-slate-700">
                  비밀번호
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="register-password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="비밀번호를 입력하세요 (최소 8자)"
                    value={registerData.password}
                    onChange={handleRegisterChange}
                    className="pl-10 pr-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400"
                    required
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* 비밀번호 확인 */}
              <div className="space-y-2">
                <Label htmlFor="passwordConfirm" className="text-slate-700">
                  비밀번호 확인
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="passwordConfirm"
                    name="passwordConfirm"
                    type={showPasswordConfirm ? 'text' : 'password'}
                    placeholder="비밀번호를 다시 입력하세요"
                    value={registerData.passwordConfirm}
                    onChange={handleRegisterChange}
                    className="pl-10 pr-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400"
                    required
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showPasswordConfirm ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* 쇼핑몰 이름 */}
              <div className="space-y-2">
                <Label htmlFor="tenant_name" className="text-slate-700">
                  쇼핑몰 이름
                </Label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="tenant_name"
                    name="tenant_name"
                    type="text"
                    placeholder="예: 마이쇼핑몰"
                    value={registerData.tenant_name}
                    onChange={handleRegisterChange}
                    className="pl-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400"
                    required
                  />
                </div>
              </div>

              {/* 쇼핑몰 ID (선택사항) */}
              <div className="space-y-2">
                <Label htmlFor="tenant_slug" className="text-slate-700">
                  쇼핑몰 ID <span className="text-slate-400 text-xs">(선택사항)</span>
                </Label>
                <div className="relative">
                  <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="tenant_slug"
                    name="tenant_slug"
                    type="text"
                    placeholder="영문 소문자, 숫자, 하이픈만 사용"
                    value={registerData.tenant_slug}
                    onChange={handleRegisterChange}
                    className="pl-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400"
                  />
                </div>
                <p className="text-xs text-slate-500">
                  비워두면 자동으로 생성됩니다
                </p>
              </div>

              {/* 회원가입 버튼 */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white h-10"
              >
                {loading ? '회원가입 중...' : '회원가입'}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
