import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Eye, EyeOff, User, Lock, Mail, Building2, Hash, UserCircle } from 'lucide-react';
import { RegisterData } from '../types';

interface LoginData {
  email: string;
  password: string;
}

interface RegisterFormData extends RegisterData {
  passwordConfirm: string;
}

function LoginPage() {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const { theme } = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);

  // 로그인 폼 상태
  const [loginData, setLoginData] = useState<LoginData>({
    email: '',
    password: ''
  });

  // 회원가입 폼 상태
  const [registerData, setRegisterData] = useState<RegisterFormData>({
    email: '',
    password: '',
    passwordConfirm: '',
    full_name: '',
    phone: '',
    tenant_name: '',
    tenant_slug: ''
  });

  const handleLoginChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLoginData({
      ...loginData,
      [e.target.name]: e.target.value
    });
  };

  const handleRegisterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRegisterData({
      ...registerData,
      [e.target.name]: e.target.value
    });
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
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

  const handleRegisterSubmit = async (e: React.FormEvent) => {
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
        phone: registerData.phone,
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
    <div className={`min-h-screen flex items-center justify-center p-4 relative ${
      theme === 'dark'
        ? 'bg-[#0f1115]'
        : 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50'
    }`}>
      {/* Dark theme grain texture */}
      {theme === 'dark' && (
        <div
          className="fixed inset-0 opacity-[0.015] pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
        />
      )}

      <div className="w-full max-w-md relative z-10">
        {/* 로고 */}
        <div className="flex justify-center mb-8">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-lg ${
            theme === 'dark'
              ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 border border-cyan-500/30'
              : 'bg-yellow-400'
          }`}>
            <div className={`w-6 h-6 rounded-full ${
              theme === 'dark' ? 'bg-cyan-400/30' : 'bg-white'
            }`}></div>
          </div>
        </div>

        {/* 제목 */}
        <h1 className={`text-center text-2xl font-medium mb-8 ${
          theme === 'dark'
            ? 'text-white'
            : 'text-slate-800'
        }`}>
          {theme === 'dark' ? (
            <>
              <span className="text-cyan-400">COUPANG</span>
              <span className="text-gray-500 mx-2">///</span>
              <span className="font-light">DATA SYSTEM</span>
            </>
          ) : (
            '쿠팡 판매 데이터 자동화'
          )}
        </h1>

        {/* 탭 네비게이션 */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => { setTabValue(0); setError(''); }}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-all ${
              theme === 'dark'
                ? tabValue === 0
                  ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.3)] border border-cyan-500/30'
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800/70 border border-gray-700'
                : tabValue === 0
                  ? 'bg-white text-indigo-600 shadow-md'
                  : 'bg-white/50 text-slate-600 hover:bg-white/70'
            }`}
          >
            로그인
          </button>
          <button
            onClick={() => { setTabValue(1); setError(''); }}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-all ${
              theme === 'dark'
                ? tabValue === 1
                  ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.3)] border border-cyan-500/30'
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800/70 border border-gray-700'
                : tabValue === 1
                  ? 'bg-white text-indigo-600 shadow-md'
                  : 'bg-white/50 text-slate-600 hover:bg-white/70'
            }`}
          >
            회원가입
          </button>
        </div>

        {/* 폼 컨테이너 */}
        <div className={`rounded-2xl p-4 shadow-xl ${
          theme === 'dark'
            ? 'bg-[#1a1d23] border border-gray-800'
            : 'bg-white border border-slate-200'
        }`}>
          {/* 에러 메시지 */}
          {error && (
            <div className={`mb-6 p-4 rounded-lg text-sm ${
              theme === 'dark'
                ? 'bg-red-500/10 border border-red-500/30 text-red-400'
                : 'bg-red-50 border border-red-200 text-red-600'
            }`}>
              {error}
            </div>
          )}

          {/* 로그인 폼 */}
          {tabValue === 0 && (
            <form onSubmit={handleLoginSubmit} className="space-y-6">
              {/* 이메일 */}
              <div className="space-y-2">
                <Label htmlFor="email" className={theme === 'dark' ? 'text-gray-300 text-xs' : 'text-slate-700'}>
                  이메일
                </Label>
                <div className="relative">
                  <Mail className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-slate-400'
                  }`} />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="이메일을 입력하세요"
                    value={loginData.email}
                    onChange={handleLoginChange}
                    className={`pl-10 ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:ring-cyan-500/30'
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-indigo-500'
                    }`}
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              {/* 비밀번호 */}
              <div className="space-y-2">
                <Label htmlFor="password" className={theme === 'dark' ? 'text-gray-300 text-xs' : 'text-slate-700'}>
                  비밀번호
                </Label>
                <div className="relative">
                  <Lock className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-slate-400'
                  }`} />
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="비밀번호를 입력하세요"
                    value={loginData.password}
                    onChange={handleLoginChange}
                    className={`pl-10 pr-10 ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:ring-cyan-500/30'
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-indigo-500'
                    }`}
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className={`absolute right-3 top-1/2 -translate-y-1/2 transition-colors ${
                      theme === 'dark'
                        ? 'text-gray-500 hover:text-cyan-400'
                        : 'text-slate-400 hover:text-slate-600'
                    }`}
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
                className={`w-full h-10 ${
                  theme === 'dark'
                    ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                }`}
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
                <Label htmlFor="register-email" className={theme === 'dark' ? 'text-gray-300 text-xs' : 'text-slate-700'}>
                  이메일
                </Label>
                <div className="relative">
                  <Mail className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-slate-400'
                  }`} />
                  <Input
                    id="register-email"
                    name="email"
                    type="email"
                    placeholder="이메일을 입력하세요"
                    value={registerData.email}
                    onChange={handleRegisterChange}
                    className={`pl-10 ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:ring-cyan-500/30'
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400'
                    }`}
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              {/* 이름 */}
              <div className="space-y-2">
                <Label htmlFor="full_name" className={theme === 'dark' ? 'text-gray-300 text-xs' : 'text-slate-700'}>
                  이름
                </Label>
                <div className="relative">
                  <UserCircle className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-slate-400'
                  }`} />
                  <Input
                    id="full_name"
                    name="full_name"
                    type="text"
                    placeholder="이름을 입력하세요"
                    value={registerData.full_name}
                    onChange={handleRegisterChange}
                    className={`pl-10 ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:ring-cyan-500/30'
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400'
                    }`}
                    required
                    autoComplete="name"
                  />
                </div>
              </div>

              {/* 비밀번호 */}
              <div className="space-y-2">
                <Label htmlFor="register-password" className={theme === 'dark' ? 'text-gray-300 text-xs' : 'text-slate-700'}>
                  비밀번호
                </Label>
                <div className="relative">
                  <Lock className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-slate-400'
                  }`} />
                  <Input
                    id="register-password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="비밀번호를 입력하세요 (최소 8자)"
                    value={registerData.password}
                    onChange={handleRegisterChange}
                    className={`pl-10 pr-10 ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:ring-cyan-500/30'
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400'
                    }`}
                    required
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className={`absolute right-3 top-1/2 -translate-y-1/2 transition-colors ${
                      theme === 'dark'
                        ? 'text-gray-500 hover:text-cyan-400'
                        : 'text-slate-400 hover:text-slate-600'
                    }`}
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
                <Label htmlFor="passwordConfirm" className={theme === 'dark' ? 'text-gray-300 text-xs' : 'text-slate-700'}>
                  비밀번호 확인
                </Label>
                <div className="relative">
                  <Lock className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-slate-400'
                  }`} />
                  <Input
                    id="passwordConfirm"
                    name="passwordConfirm"
                    type={showPasswordConfirm ? 'text' : 'password'}
                    placeholder="비밀번호를 다시 입력하세요"
                    value={registerData.passwordConfirm}
                    onChange={handleRegisterChange}
                    className={`pl-10 pr-10 ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:ring-cyan-500/30'
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400'
                    }`}
                    required
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                    className={`absolute right-3 top-1/2 -translate-y-1/2 transition-colors ${
                      theme === 'dark'
                        ? 'text-gray-500 hover:text-cyan-400'
                        : 'text-slate-400 hover:text-slate-600'
                    }`}
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
                <Label htmlFor="tenant_name" className={theme === 'dark' ? 'text-gray-300 text-xs' : 'text-slate-700'}>
                  쇼핑몰 이름
                </Label>
                <div className="relative">
                  <Building2 className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-slate-400'
                  }`} />
                  <Input
                    id="tenant_name"
                    name="tenant_name"
                    type="text"
                    placeholder="예: 마이쇼핑몰"
                    value={registerData.tenant_name}
                    onChange={handleRegisterChange}
                    className={`pl-10 ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:ring-cyan-500/30'
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400'
                    }`}
                    required
                  />
                </div>
              </div>

              {/* 쇼핑몰 ID (선택사항) */}
              <div className="space-y-2">
                <Label htmlFor="tenant_slug" className={theme === 'dark' ? 'text-gray-300 text-xs' : 'text-slate-700'}>
                  쇼핑몰 ID <span className={theme === 'dark' ? 'text-gray-500 text-xs' : 'text-slate-400 text-xs'}>(선택사항)</span>
                </Label>
                <div className="relative">
                  <Hash className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-slate-400'
                  }`} />
                  <Input
                    id="tenant_slug"
                    name="tenant_slug"
                    type="text"
                    placeholder="영문 소문자, 숫자, 하이픈만 사용"
                    value={registerData.tenant_slug}
                    onChange={handleRegisterChange}
                    className={`pl-10 ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:ring-cyan-500/30'
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400'
                    }`}
                  />
                </div>
                <p className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-slate-500'}`}>
                  비워두면 자동으로 생성됩니다
                </p>
              </div>

              {/* 회원가입 버튼 */}
              <Button
                type="submit"
                disabled={loading}
                className={`w-full h-10 ${
                  theme === 'dark'
                    ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                }`}
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
