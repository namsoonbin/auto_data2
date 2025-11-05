import { useState } from 'react';
import { Input } from './components/ui/input';
import { Button } from './components/ui/button';
import { Checkbox } from './components/ui/checkbox';
import { Label } from './components/ui/label';
import { Eye, EyeOff, User, Lock, Globe } from 'lucide-react';

export default function App() {
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('로그인 시도:', formData, '로그인 유지:', rememberMe);
    // 실제 로그인 로직을 여기에 구현
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
        <h1 className="text-center text-slate-800 mb-8">슈퍼리스트 로그인</h1>

        {/* 로그인 폼 */}
        <div className="bg-white rounded-2xl p-8 shadow-xl border border-slate-200">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 사용자명 또는 이메일 */}
            <div className="space-y-2">
              <Label htmlFor="username" className="text-slate-700">
                사용자명 또는 이메일
              </Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  id="username"
                  type="text"
                  placeholder="사용자명 또는 이메일"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="pl-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* 비밀번호 */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-slate-700">
                  비밀번호
                </Label>
                <a href="#" className="text-indigo-600 hover:text-indigo-700 transition-colors">
                  비밀번호를 잊으셨나요?
                </a>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="비밀번호"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="pl-10 pr-10 bg-slate-50 border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-indigo-500"
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

            {/* 로그인 유지 */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(checked as boolean)}
                className="border-slate-300 data-[state=checked]:bg-indigo-600 data-[state=checked]:border-indigo-600"
              />
              <Label
                htmlFor="remember"
                className="text-slate-700 cursor-pointer"
              >
                로그인 유지
              </Label>
            </div>

            {/* 로그인 버튼 */}
            <Button
              type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white transition-colors"
            >
              로그인
            </Button>

            {/* 회원가입 링크 */}
            <p className="text-center text-slate-600">
              계정이 없으신가요?{' '}
              <a href="#" className="text-indigo-600 hover:text-indigo-700 transition-colors">
                회원가입
              </a>
            </p>
          </form>
        </div>

        {/* 하단 링크 */}
        <div className="mt-8 flex items-center justify-between text-slate-500">
          <div className="flex items-center space-x-4">
            <a href="#" className="hover:text-slate-700 transition-colors">
              약관
            </a>
            <span>•</span>
            <a href="#" className="hover:text-slate-700 transition-colors">
              개인정보처리방침
            </a>
            <span>•</span>
            <a href="#" className="hover:text-slate-700 transition-colors">
              문서
            </a>
            <span>•</span>
            <a href="#" className="hover:text-slate-700 transition-colors">
              도움말
            </a>
          </div>
          <div className="flex items-center space-x-2">
            <Globe className="w-4 h-4" />
            <span>한국어</span>
          </div>
        </div>
      </div>
    </div>
  );
}
