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

const API_BASE_URL = 'http://localhost:8000/api';

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
        <Badge className="bg-green-600">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          성공
        </Badge>
      );
    } else {
      return (
        <Badge variant="destructive">
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-black flex items-center gap-2">
            <History className="h-8 w-8" />
            업로드 히스토리
          </h1>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchHistory}
            disabled={loading}
            title="새로고침"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        <p className="text-muted-foreground mb-6">
          과거 업로드한 파일 목록과 통합 결과를 확인할 수 있습니다
        </p>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {loading ? (
          <Card>
            <CardContent className="flex justify-center items-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </CardContent>
          </Card>
        ) : history.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <History className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold text-muted-foreground mb-2">업로드 기록이 없습니다</h3>
              <p className="text-sm text-muted-foreground">
                파일을 업로드하면 여기에 기록이 표시됩니다
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            <Card>
              <CardContent className="p-0">
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead className="font-bold">업로드 시간</TableHead>
                        <TableHead className="font-bold">판매 파일</TableHead>
                        <TableHead className="font-bold">광고 파일</TableHead>
                        <TableHead className="font-bold">마진 파일</TableHead>
                        <TableHead className="text-center font-bold">총 레코드</TableHead>
                        <TableHead className="text-center font-bold">광고 매칭</TableHead>
                        <TableHead className="text-center font-bold">마진 매칭</TableHead>
                        <TableHead className="text-center font-bold">완전 통합</TableHead>
                        <TableHead className="text-center font-bold">상태</TableHead>
                        <TableHead className="text-center font-bold">작업</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {history.map((upload) => (
                        <TableRow key={upload.id} className="hover:bg-gray-50">
                          <TableCell>{formatDate(upload.uploaded_at)}</TableCell>
                          <TableCell>
                            <div className="max-w-[150px] truncate" title={upload.sales_filename}>
                              {upload.sales_filename}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="max-w-[150px] truncate" title={upload.ads_filename}>
                              {upload.ads_filename}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="max-w-[150px] truncate" title={upload.margin_filename}>
                              {upload.margin_filename}
                            </div>
                          </TableCell>
                          <TableCell className="text-center">{upload.total_records || 0}</TableCell>
                          <TableCell className="text-center">{upload.matched_with_ads || 0}</TableCell>
                          <TableCell className="text-center">{upload.matched_with_margin || 0}</TableCell>
                          <TableCell className="text-center">
                            <span className="font-semibold text-green-600">
                              {upload.fully_integrated || 0}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">{getStatusBadge(upload.status)}</TableCell>
                          <TableCell className="text-center">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
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
              <p className="text-xs text-muted-foreground">총 {history.length}개의 업로드 기록</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default HistoryPage;
