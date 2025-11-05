import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";

import { Separator } from "./components/ui/separator";
import { Mail } from "lucide-react";

export default function App() {
  const [formData, setFormData] = useState({
    fullName: "",
    nickName: "",
    shopName: "",
    shopId: "",
    email: "alexarawles@gmail.com"
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Form submitted:", formData);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-black mb-2">프로필 설정</h1>
          <p className="text-gray-600">개인 정보를 관리하고 업데이트하세요</p>
        </div>

        {/* Main Card */}
        <Card className="shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle>기본 정보</CardTitle>
            <CardDescription>프로필에 표시될 기본 정보를 입력해주세요</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Personal Information Section */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Full Name */}
                <div className="space-y-2">
                  <Label htmlFor="fullName" className="text-gray-700">
                    성명 <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="fullName"
                    type="text"
                    placeholder="이름을 입력하세요"
                    value={formData.fullName}
                    onChange={(e) => handleInputChange('fullName', e.target.value)}
                    className="bg-white border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                {/* Nickname */}
                <div className="space-y-2">
                  <Label htmlFor="nickName" className="text-gray-700">
                    닉네임 <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="nickName"
                    type="text"
                    placeholder="닉네임을 입력하세요"
                    value={formData.nickName}
                    onChange={(e) => handleInputChange('nickName', e.target.value)}
                    className="bg-white border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                {/* Shop Name */}
                <div className="space-y-2">
                  <Label htmlFor="shopName" className="text-gray-700">
                    쇼핑몰 이름
                  </Label>
                  <Input
                    id="shopName"
                    type="text"
                    placeholder="쇼핑몰 이름을 입력하세요"
                    value={formData.shopName}
                    onChange={(e) => handleInputChange('shopName', e.target.value)}
                    className="bg-white border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                {/* Shop ID */}
                <div className="space-y-2">
                  <Label htmlFor="shopId" className="text-gray-700">
                    쇼핑몰 ID
                  </Label>
                  <Input
                    id="shopId"
                    type="text"
                    placeholder="쇼핑몰 ID를 입력하세요"
                    value={formData.shopId}
                    onChange={(e) => handleInputChange('shopId', e.target.value)}
                    className="bg-white border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>

              <Separator className="my-8" />

              {/* Email Section */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-black mb-1">이메일 주소</h3>
                  <p className="text-gray-600">계정과 연결된 이메일 주소를 관리하세요</p>
                </div>

                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="bg-blue-100 rounded-full p-3">
                      <Mail className="size-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-black">{formData.email}</p>
                      <p className="text-gray-500">주 이메일</p>
                    </div>
                  </div>
                  <Button variant="ghost" className="text-blue-600 hover:text-blue-700 hover:bg-blue-100">
                    변경
                  </Button>
                </div>

                <Button variant="outline" className="w-full border-dashed border-blue-300 text-blue-600 hover:bg-blue-50 hover:border-blue-400">
                  + 이메일 주소 추가
                </Button>
              </div>

              <Separator className="my-8" />

              {/* Action Buttons */}
              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" className="px-8">
                  취소
                </Button>
                <Button type="submit" className="bg-blue-600 hover:bg-blue-700 px-8">
                  저장하기
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Additional Settings Card */}
        <Card className="mt-6 shadow-lg">
          <CardHeader>
            <CardTitle>계정 설정</CardTitle>
            <CardDescription>비밀번호 및 보안 설정을 관리하세요</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="text-black">비밀번호 변경</p>
                <p className="text-gray-500">계정 비밀번호를 업데이트하세요</p>
              </div>
              <Button variant="outline" className="text-blue-600 hover:bg-blue-50">
                변경
              </Button>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="text-black">2단계 인증</p>
                <p className="text-gray-500">계정 보안을 강화하세요</p>
              </div>
              <Button variant="outline" className="text-blue-600 hover:bg-blue-50">
                설정
              </Button>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-black">계정 삭제</p>
                <p className="text-gray-500">계정을 영구적으로 삭제합니다</p>
              </div>
              <Button variant="outline" className="text-red-600 border-red-200 hover:bg-red-50">
                삭제
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
