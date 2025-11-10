import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { Upload, AlertCircle } from 'lucide-react';
import axios from 'axios';

// Interfaces
interface UploadFormProps {
  title: string;
  type: 'sales' | 'ads' | 'products';
  onUploadComplete?: (data: UploadResult) => void;
  description: string;
}

interface UploadResult {
  status: 'success' | 'error';
  message: string;
  records?: number;
  errors?: string[];
  [key: string]: any;
}

function UploadForm({ title, type, onUploadComplete, description }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('파일을 선택해주세요.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    // 엔드포인트 매핑
    const endpoints: Record<string, string> = {
      sales: '/api/upload/sales',
      ads: '/api/upload/ads',
      products: '/api/upload/products',
    };

    setLoading(true);
    setError(null);

    try {
      const res = await axios.post<UploadResult>(endpoints[type], formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // 업로드 완료 콜백
      if (onUploadComplete) {
        onUploadComplete(res.data);
      }

      // 파일 초기화
      setFile(null);
      // 파일 input 초기화
      const fileInput = document.getElementById(`file-input-${type}`) as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: any) {
      console.error('Upload error', err);
      const errorMessage = err.response?.data?.message || '업로드 중 오류가 발생했습니다.';
      setError(errorMessage);

      if (onUploadComplete) {
        onUploadComplete({
          status: 'error',
          message: errorMessage,
          records: 0,
          errors: [err.message],
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <input
            id={`file-input-${type}`}
            type="file"
            accept=".xlsx, .xls, .csv"
            onChange={handleFileChange}
            className="hidden"
          />
          <Button variant="outline" className="w-full" asChild>
            <label htmlFor={`file-input-${type}`} className="cursor-pointer">
              <Upload className="h-4 w-4 mr-2" />
              파일 선택
            </label>
          </Button>
        </div>

        {file && (
          <p className="text-sm text-muted-foreground">선택된 파일: {file.name}</p>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Button className="w-full" onClick={handleUpload} disabled={!file || loading}>
          {loading ? '업로드 중...' : '업로드'}
        </Button>

        {loading && <Progress value={undefined} className="w-full" />}
      </CardContent>
    </Card>
  );
}

export default UploadForm;
