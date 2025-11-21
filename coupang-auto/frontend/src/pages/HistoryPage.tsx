import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  History,
  CheckCircle2,
  XCircle,
  Trash2,
  RefreshCw,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import axios from 'axios';
import { useTheme } from '../contexts/ThemeContext';

const API_BASE_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;

// Interfaces
interface UploadHistory {
  id: number;
  sales_filename: string;
  ads_filename: string;
  margin_filename: string;
  total_records: number;
  matched_with_ads: number;
  matched_with_margin: number;
  fully_integrated: number;
  status: 'success' | 'error';
  uploaded_at: string;
}

function HistoryPage() {
  const { theme } = useTheme();
  const [history, setHistory] = useState<UploadHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get<{ uploads: UploadHistory[] }>(`${API_BASE_URL}/upload/history`);
      setHistory(response.data.uploads || []);
    } catch (err: any) {
      setError(err.response?.data?.message || '히스토리 조회 실패');
      console.error('Failed to fetch history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (uploadId: number) => {
    if (!window.confirm('이 업로드 기록을 삭제하시겠습니까?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/upload/history/${uploadId}`);
      fetchHistory(); // Refresh list
    } catch (err: any) {
      alert('삭제 실패: ' + (err.response?.data?.message || err.message));
    }
  };

  const getStatusBadge = (status: 'success' | 'error') => {
    if (status === 'success') {
      return (
        <Badge className={theme === 'dark'
          ? 'bg-green-500/30 text-green-400 border-green-500/50'
          : 'bg-green-600'
        }>
          <CheckCircle2 className="h-3 w-3 mr-1" />
          성공
        </Badge>
      );
    } else {
      return (
        <Badge variant="destructive" className={theme === 'dark'
          ? 'bg-red-500/30 text-red-400 border-red-500/50'
          : ''
        }>
          <XCircle className="h-3 w-3 mr-1" />
          실패
        </Badge>
      );
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className={`min-h-screen p-4 relative ${
      theme === 'dark'
        ? 'bg-[#0f1115]'
        : 'bg-gray-50'
    }`}>
      {/* Grain texture overlay for dark mode */}
      {theme === 'dark' && (
        <div
          className="fixed inset-0 opacity-[0.015] pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
        />
      )}

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className={`flex items-center gap-2 text-3xl font-bold ${
            theme === 'dark' ? 'text-white' : 'text-black'
          }`}>
            <History className={`h-8 w-8 ${theme === 'dark' ? 'text-cyan-400' : ''}`} />
            업로드 히스토리
          </h1>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchHistory}
            disabled={loading}
            title="새로고침"
            className={theme === 'dark'
              ? 'text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10'
              : ''
            }
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        <p className={`mb-6 ${
          theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'
        }`}>
          과거 업로드한 파일 목록과 통합 결과를 확인할 수 있습니다
        </p>

        {error && (
          <Alert variant="destructive" className={`mb-6 ${
            theme === 'dark' ? 'bg-red-950/20 border-red-500/30 text-red-400' : ''
          }`}>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {loading ? (
          <Card className={`shadow-lg ${
            theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
          }`}>
            <CardContent className="flex justify-center items-center py-16">
              <Loader2 className={`h-8 w-8 animate-spin ${
                theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
              }`} />
            </CardContent>
          </Card>
        ) : history.length === 0 ? (
          <Card className={`shadow-lg ${
            theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
          }`}>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <History className={`h-16 w-16 mb-4 ${
                theme === 'dark' ? 'text-gray-600' : 'text-muted-foreground'
              }`} />
              <h3 className={`text-lg font-semibold mb-2 ${
                theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'
              }`}>업로드 기록이 없습니다</h3>
              <p className={`text-sm ${
                theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
              }`}>
                파일을 업로드하면 여기에 기록이 표시됩니다
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            <Card className={`shadow-lg ${
              theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
            }`}>
              <CardContent className="p-0">
                <div className={`rounded-md border ${
                  theme === 'dark' ? 'border-gray-800' : ''
                }`}>
                  <Table>
                    <TableHeader>
                      <TableRow className={theme === 'dark' ? 'bg-gray-900/50 border-gray-700' : 'bg-gray-50'}>
                        <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>업로드 시간</TableHead>
                        <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>판매 파일</TableHead>
                        <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>광고 파일</TableHead>
                        <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>마진 파일</TableHead>
                        <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>총 레코드</TableHead>
                        <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>광고 매칭</TableHead>
                        <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>마진 매칭</TableHead>
                        <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>완전 통합</TableHead>
                        <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>상태</TableHead>
                        <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>작업</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {history.map((upload) => (
                        <TableRow key={upload.id} className={theme === 'dark'
                          ? 'hover:bg-gray-900/30 border-gray-800'
                          : 'hover:bg-gray-50'
                        }>
                          <TableCell className={theme === 'dark' ? 'text-gray-200' : ''}>
                            {formatDate(upload.uploaded_at)}
                          </TableCell>
                          <TableCell>
                            <div className={`max-w-[150px] truncate ${
                              theme === 'dark' ? 'text-white' : ''
                            }`} title={upload.sales_filename}>
                              {upload.sales_filename}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className={`max-w-[150px] truncate ${
                              theme === 'dark' ? 'text-white' : ''
                            }`} title={upload.ads_filename}>
                              {upload.ads_filename}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className={`max-w-[150px] truncate ${
                              theme === 'dark' ? 'text-white' : ''
                            }`} title={upload.margin_filename}>
                              {upload.margin_filename}
                            </div>
                          </TableCell>
                          <TableCell className={`text-center ${theme === 'dark' ? 'text-gray-200' : ''}`}>
                            {upload.total_records || 0}
                          </TableCell>
                          <TableCell className={`text-center ${theme === 'dark' ? 'text-gray-200' : ''}`}>
                            {upload.matched_with_ads || 0}
                          </TableCell>
                          <TableCell className={`text-center ${theme === 'dark' ? 'text-gray-200' : ''}`}>
                            {upload.matched_with_margin || 0}
                          </TableCell>
                          <TableCell className="text-center">
                            <span className={`font-semibold ${
                              theme === 'dark' ? 'text-green-400' : 'text-green-600'
                            }`}>
                              {upload.fully_integrated || 0}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">{getStatusBadge(upload.status)}</TableCell>
                          <TableCell className="text-center">
                            <Button
                              size="sm"
                              variant="ghost"
                              className={theme === 'dark'
                                ? 'text-red-400 hover:text-red-300 hover:bg-red-500/10'
                                : 'text-red-600 hover:text-red-700 hover:bg-red-50'
                              }
                              onClick={() => handleDelete(upload.id)}
                              title="삭제"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            <div className="mt-4">
              <p className={`text-xs ${
                theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
              }`}>총 {history.length}개의 업로드 기록</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default HistoryPage;
