import React, { useState, useEffect, forwardRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Plus,
  Edit,
  Trash2,
  RefreshCw,
  AlertCircle,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Search,
  Loader2,
  X,
} from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import axios from 'axios';
import { Checkbox } from '../components/ui/checkbox';

const API_BASE_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;

// Interfaces
interface FakePurchase {
  id: number;
  option_id: number;
  product_name: string;
  option_name?: string;
  date: string;
  quantity: number;
  unit_price: number;
  calculated_cost: number;
  total_cost: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface FakePurchaseFormData {
  option_id: number | string;
  product_name: string;
  option_name: string;
  date: Date | null;
  quantity: number | string;
  unit_price: number | string;
  notes: string;
}

interface ProductSearchResult {
  option_id: number;
  product_name: string;
  option_name?: string;
}

// Custom input component for DatePicker
const CustomDateInput = forwardRef<HTMLInputElement, { value?: string; onClick?: () => void }>(
  ({ value, onClick }, ref) => (
    <div className="relative">
      <Input
        value={value}
        onClick={onClick}
        ref={ref}
        readOnly
        placeholder="날짜 선택"
        className="cursor-pointer pr-10"
      />
      <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
    </div>
  )
);

CustomDateInput.displayName = 'CustomDateInput';

// Custom header component for DatePicker
const renderCustomHeader = ({
  monthDate,
  decreaseMonth,
  increaseMonth,
  prevMonthButtonDisabled,
  nextMonthButtonDisabled,
}: any) => (
  <div className="flex items-center justify-between px-3 py-2 bg-white">
    <button
      onClick={decreaseMonth}
      disabled={prevMonthButtonDisabled}
      className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
      type="button"
    >
      <ChevronLeft className="h-5 w-5" />
    </button>
    <span className="font-semibold text-lg">
      {format(monthDate, 'yyyy년 M월', { locale: ko })}
    </span>
    <button
      onClick={increaseMonth}
      disabled={nextMonthButtonDisabled}
      className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
      type="button"
    >
      <ChevronRight className="h-5 w-5" />
    </button>
  </div>
);

const FakePurchaseManagementPage: React.FC = () => {
  const [fakePurchases, setFakePurchases] = useState<FakePurchase[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Filter states
  const [filterDateRange, setFilterDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [filterProductName, setFilterProductName] = useState('');

  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isProductSearchDialogOpen, setIsProductSearchDialogOpen] = useState(false);
  const [selectedFakePurchase, setSelectedFakePurchase] = useState<FakePurchase | null>(null);

  // Product search states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<ProductSearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Form data
  const [formData, setFormData] = useState<FakePurchaseFormData>({
    option_id: '',
    product_name: '',
    option_name: '',
    date: null,
    quantity: '',
    unit_price: '',
    notes: '',
  });

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Fetch fake purchases
  const fetchFakePurchases = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('accessToken');
      const params: any = {
        sort_by: 'date',
        sort_order: 'desc',
      };

      if (filterDateRange[0]) {
        params.start_date = format(filterDateRange[0], 'yyyy-MM-dd');
      }
      if (filterDateRange[1]) {
        params.end_date = format(filterDateRange[1], 'yyyy-MM-dd');
      }
      if (filterProductName) {
        params.product_name = filterProductName;
      }

      const response = await axios.get(`${API_BASE_URL}/fake-purchases`, {
        params,
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setFakePurchases(response.data.fake_purchases || []);
    } catch (err: any) {
      console.error('Error fetching fake purchases:', err);
      setError(err.response?.data?.detail || '가구매 데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFakePurchases();
  }, []);

  // Reset form
  const resetForm = () => {
    setFormData({
      option_id: '',
      product_name: '',
      option_name: '',
      date: null,
      quantity: '',
      unit_price: '',
      notes: '',
    });
  };

  // Handle create
  const handleCreate = () => {
    resetForm();
    setIsCreateDialogOpen(true);
  };

  // Handle edit
  const handleEdit = (fakePurchase: FakePurchase) => {
    setSelectedFakePurchase(fakePurchase);
    setFormData({
      option_id: fakePurchase.option_id,
      product_name: fakePurchase.product_name,
      option_name: fakePurchase.option_name || '',
      date: new Date(fakePurchase.date),
      quantity: fakePurchase.quantity,
      unit_price: fakePurchase.unit_price,
      notes: fakePurchase.notes || '',
    });
    setIsEditDialogOpen(true);
  };

  // Handle delete
  const handleDelete = (fakePurchase: FakePurchase) => {
    setSelectedFakePurchase(fakePurchase);
    setIsDeleteDialogOpen(true);
  };

  // Auto-fill product info from option_id
  const autoFillProductInfo = async (optionId: number) => {
    try {
      const token = localStorage.getItem('accessToken');

      // Try to get product info from integrated records
      const response = await axios.get(`${API_BASE_URL}/data/records`, {
        params: {
          option_id: optionId,
          limit: 1,
        },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.data.records && response.data.records.length > 0) {
        const record = response.data.records[0];
        setFormData((prev) => ({
          ...prev,
          product_name: record.product_name || prev.product_name,
          option_name: record.option_name || prev.option_name,
        }));
      }
    } catch (err) {
      console.log('Could not auto-fill product info:', err);
      // Silently fail - user can still enter manually
    }
  };

  // Search products by name
  const handleProductSearch = async () => {
    if (!searchQuery.trim()) {
      setError('검색어를 입력하세요.');
      return;
    }

    setSearchLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('accessToken');
      const response = await axios.get(`${API_BASE_URL}/data/records`, {
        params: {
          product_name: searchQuery,
          limit: 50,
        },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.data.records && response.data.records.length > 0) {
        // Remove duplicates by option_id
        const uniqueProducts = response.data.records.reduce((acc: ProductSearchResult[], record: any) => {
          if (!acc.find((p) => p.option_id === record.option_id)) {
            acc.push({
              option_id: record.option_id,
              product_name: record.product_name,
              option_name: record.option_name,
            });
          }
          return acc;
        }, []);

        setSearchResults(uniqueProducts);
      } else {
        setSearchResults([]);
        setError('검색 결과가 없습니다.');
      }
    } catch (err: any) {
      console.error('Error searching products:', err);
      setError(err.response?.data?.detail || '상품 검색에 실패했습니다.');
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  // Select product from search results
  const handleSelectProduct = (product: ProductSearchResult) => {
    setFormData((prev) => ({
      ...prev,
      option_id: product.option_id,
      product_name: product.product_name,
      option_name: product.option_name || '',
    }));
    setIsProductSearchDialogOpen(false);
    setSearchQuery('');
    setSearchResults([]);
  };

  // Open product search dialog
  const handleOpenProductSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setIsProductSearchDialogOpen(true);
  };

  // Submit create
  const submitCreate = async () => {
    setError(null);

    // Validate required fields
    const missingFields: string[] = [];

    if (!formData.option_id || formData.option_id === '') {
      missingFields.push('옵션ID');
    }
    if (!formData.date) {
      missingFields.push('날짜');
    }
    if (!formData.quantity || formData.quantity === '') {
      missingFields.push('수량');
    }
    if (!formData.unit_price || formData.unit_price === '') {
      missingFields.push('단가');
    }

    if (missingFields.length > 0) {
      setError(`다음 필수 항목을 입력해주세요: ${missingFields.join(', ')}`);
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');

      const payload = {
        option_id: Number(formData.option_id),
        product_name: formData.product_name || null,  // Optional now
        option_name: formData.option_name || null,
        date: formData.date ? format(formData.date, 'yyyy-MM-dd') : null,
        quantity: Number(formData.quantity),
        unit_price: Number(formData.unit_price),
        notes: formData.notes || null,
      };

      await axios.post(`${API_BASE_URL}/fake-purchases`, payload, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setSuccess('가구매가 성공적으로 생성되었습니다.');
      setIsCreateDialogOpen(false);
      resetForm();
      fetchFakePurchases();
    } catch (err: any) {
      console.error('Error creating fake purchase:', err);
      setError(err.response?.data?.detail || '가구매 생성에 실패했습니다.');
    }
  };

  // Submit edit
  const submitEdit = async () => {
    if (!selectedFakePurchase) return;
    setError(null);

    try {
      const token = localStorage.getItem('accessToken');

      const payload: any = {};
      if (formData.quantity !== '') payload.quantity = Number(formData.quantity);
      if (formData.unit_price !== '') payload.unit_price = Number(formData.unit_price);
      if (formData.notes !== '') payload.notes = formData.notes;

      await axios.put(
        `${API_BASE_URL}/fake-purchases/${selectedFakePurchase.id}`,
        payload,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setSuccess('가구매가 성공적으로 수정되었습니다.');
      setIsEditDialogOpen(false);
      setSelectedFakePurchase(null);
      resetForm();
      fetchFakePurchases();
    } catch (err: any) {
      console.error('Error updating fake purchase:', err);
      setError(err.response?.data?.detail || '가구매 수정에 실패했습니다.');
    }
  };

  // Submit delete
  const submitDelete = async () => {
    if (!selectedFakePurchase) return;
    setError(null);

    try {
      const token = localStorage.getItem('accessToken');

      await axios.delete(`${API_BASE_URL}/fake-purchases/${selectedFakePurchase.id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setSuccess('가구매가 성공적으로 삭제되었습니다.');
      setIsDeleteDialogOpen(false);
      setSelectedFakePurchase(null);
      fetchFakePurchases();
    } catch (err: any) {
      console.error('Error deleting fake purchase:', err);
      setError(err.response?.data?.detail || '가구매 삭제에 실패했습니다.');
    }
  };

  // Handle batch delete
  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) {
      setError('삭제할 항목을 선택하세요.');
      return;
    }

    if (!window.confirm(`선택한 ${selectedIds.size}개 항목을 삭제하시겠습니까?`)) {
      return;
    }

    setError(null);

    try {
      const token = localStorage.getItem('accessToken');

      await axios.post(
        `${API_BASE_URL}/fake-purchases/batch-delete`,
        { ids: Array.from(selectedIds) },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setSuccess(`${selectedIds.size}개 항목이 성공적으로 삭제되었습니다.`);
      setSelectedIds(new Set());
      fetchFakePurchases();
    } catch (err: any) {
      console.error('Error batch deleting:', err);
      setError(err.response?.data?.detail || '일괄 삭제에 실패했습니다.');
    }
  };

  // Toggle selection
  const toggleSelection = (id: number) => {
    const newSelectedIds = new Set(selectedIds);
    if (newSelectedIds.has(id)) {
      newSelectedIds.delete(id);
    } else {
      newSelectedIds.add(id);
    }
    setSelectedIds(newSelectedIds);
  };

  // Toggle all selection
  const toggleAllSelection = () => {
    if (selectedIds.size === fakePurchases.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(fakePurchases.map((fp) => fp.id)));
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">가구매 관리</h1>
          <p className="text-muted-foreground mt-2">
            가구매 데이터를 관리하고 비용을 추적합니다
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleCreate} variant="default">
            <Plus className="mr-2 h-4 w-4" />
            가구매 추가
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>오류</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert>
          <AlertTitle>성공</AlertTitle>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {/* Filter Card */}
      <Card>
        <CardHeader>
          <CardTitle>필터</CardTitle>
        </CardHeader>
        <CardContent className="overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-4">
            <div>
              <Label>기간</Label>
              <DatePicker
                selectsRange
                startDate={filterDateRange[0]}
                endDate={filterDateRange[1]}
                onChange={(update: [Date | null, Date | null]) => {
                  setFilterDateRange(update);
                }}
                customInput={<CustomDateInput />}
                renderCustomHeader={renderCustomHeader}
                dateFormat="yyyy-MM-dd"
                locale={ko}
                monthsShown={2}
                isClearable
              />
            </div>
            <div>
              <Label>상품명</Label>
              <Input
                placeholder="상품명으로 검색"
                value={filterProductName}
                onChange={(e) => setFilterProductName(e.target.value)}
              />
            </div>
            <div className="flex items-end gap-2 flex-shrink-0">
              <Button onClick={fetchFakePurchases}>
                <Search className="mr-2 h-4 w-4" />
                검색
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => {
                  setFilterDateRange([null, null]);
                  setFilterProductName('');
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>가구매 목록 ({fakePurchases.length}건)</CardTitle>
            <div className="flex gap-2">
              {selectedIds.size > 0 && (
                <Button variant="destructive" size="sm" onClick={handleBatchDelete}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  선택 삭제 ({selectedIds.size})
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={fetchFakePurchases}>
                <RefreshCw className="mr-2 h-4 w-4" />
                새로고침
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : fakePurchases.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              가구매 데이터가 없습니다
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedIds.size === fakePurchases.length}
                      onCheckedChange={toggleAllSelection}
                    />
                  </TableHead>
                  <TableHead>날짜</TableHead>
                  <TableHead>옵션ID</TableHead>
                  <TableHead>상품정보</TableHead>
                  <TableHead className="text-right">수량</TableHead>
                  <TableHead className="text-right">단가</TableHead>
                  <TableHead className="text-right">단위비용</TableHead>
                  <TableHead className="text-right">총비용</TableHead>
                  <TableHead className="text-right">작업</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fakePurchases.map((fp) => (
                  <TableRow key={fp.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.has(fp.id)}
                        onCheckedChange={() => toggleSelection(fp.id)}
                      />
                    </TableCell>
                    <TableCell>{fp.date}</TableCell>
                    <TableCell>{fp.option_id}</TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <div className="font-medium">{fp.product_name}</div>
                        {fp.option_name && (
                          <div className="text-sm text-muted-foreground">
                            {fp.option_name}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{fp.quantity}</TableCell>
                    <TableCell className="text-right">
                      {fp.unit_price.toLocaleString()}원
                    </TableCell>
                    <TableCell className="text-right">
                      {fp.calculated_cost.toLocaleString()}원
                    </TableCell>
                    <TableCell className="text-right">
                      {fp.total_cost.toLocaleString()}원
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(fp)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(fp)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>가구매 추가</DialogTitle>
            <DialogDescription>
              새로운 가구매 정보를 입력하세요
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="option_id">옵션 ID *</Label>
                <div className="flex gap-2">
                  <Input
                    id="option_id"
                    type="number"
                    value={formData.option_id}
                    onChange={(e) =>
                      setFormData({ ...formData, option_id: e.target.value })
                    }
                    onBlur={(e) => {
                      const optionId = Number(e.target.value);
                      if (optionId && !isNaN(optionId)) {
                        autoFillProductInfo(optionId);
                      }
                    }}
                    placeholder="옵션 ID"
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleOpenProductSearch}
                    title="상품 검색"
                  >
                    <Search className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div>
                <Label htmlFor="date">날짜 *</Label>
                <DatePicker
                  selected={formData.date}
                  onChange={(date) => setFormData({ ...formData, date })}
                  customInput={<CustomDateInput />}
                  renderCustomHeader={renderCustomHeader}
                  dateFormat="yyyy-MM-dd"
                  locale={ko}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="product_name">상품명 *</Label>
              <Input
                id="product_name"
                value={formData.product_name}
                onChange={(e) =>
                  setFormData({ ...formData, product_name: e.target.value })
                }
                placeholder="상품명"
              />
            </div>
            <div>
              <Label htmlFor="option_name">옵션명</Label>
              <Input
                id="option_name"
                value={formData.option_name}
                onChange={(e) =>
                  setFormData({ ...formData, option_name: e.target.value })
                }
                placeholder="옵션명 (선택사항)"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="quantity">가구매 수량 *</Label>
                <Input
                  id="quantity"
                  type="number"
                  value={formData.quantity}
                  onChange={(e) =>
                    setFormData({ ...formData, quantity: e.target.value })
                  }
                  placeholder="수량"
                />
              </div>
              <div>
                <Label htmlFor="unit_price">상품 단가 *</Label>
                <Input
                  id="unit_price"
                  type="number"
                  value={formData.unit_price}
                  onChange={(e) =>
                    setFormData({ ...formData, unit_price: e.target.value })
                  }
                  placeholder="단가 (원)"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="notes">메모</Label>
              <Textarea
                id="notes"
                value={formData.notes}
                onChange={(e) =>
                  setFormData({ ...formData, notes: e.target.value })
                }
                placeholder="메모 (선택사항)"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={submitCreate}>생성</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>가구매 수정</DialogTitle>
            <DialogDescription>
              수량, 단가, 메모만 수정 가능합니다
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_quantity">가구매 수량</Label>
                <Input
                  id="edit_quantity"
                  type="number"
                  value={formData.quantity}
                  onChange={(e) =>
                    setFormData({ ...formData, quantity: e.target.value })
                  }
                  placeholder="수량"
                />
              </div>
              <div>
                <Label htmlFor="edit_unit_price">상품 단가</Label>
                <Input
                  id="edit_unit_price"
                  type="number"
                  value={formData.unit_price}
                  onChange={(e) =>
                    setFormData({ ...formData, unit_price: e.target.value })
                  }
                  placeholder="단가 (원)"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="edit_notes">메모</Label>
              <Textarea
                id="edit_notes"
                value={formData.notes}
                onChange={(e) =>
                  setFormData({ ...formData, notes: e.target.value })
                }
                placeholder="메모 (선택사항)"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={submitEdit}>수정</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>가구매 삭제</DialogTitle>
            <DialogDescription>
              정말로 이 가구매를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </DialogDescription>
          </DialogHeader>
          {selectedFakePurchase && (
            <div className="py-4">
              <p>
                <strong>상품명:</strong> {selectedFakePurchase.product_name}
              </p>
              <p>
                <strong>날짜:</strong> {selectedFakePurchase.date}
              </p>
              <p>
                <strong>수량:</strong> {selectedFakePurchase.quantity}
              </p>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              취소
            </Button>
            <Button variant="destructive" onClick={submitDelete}>
              삭제
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Product Search Dialog */}
      <Dialog open={isProductSearchDialogOpen} onOpenChange={setIsProductSearchDialogOpen}>
        <DialogContent className="sm:max-w-5xl">
          <DialogHeader>
            <DialogTitle>상품 검색</DialogTitle>
            <DialogDescription>
              상품명으로 검색하여 옵션을 선택하세요 (판매량 많은 순으로 정렬됨)
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex gap-2">
              <Input
                placeholder="상품명 입력"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleProductSearch();
                  }
                }}
              />
              <Button onClick={handleProductSearch} disabled={searchLoading}>
                {searchLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                <span className="ml-2">검색</span>
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              검색 결과는 전체 기간 판매량이 많은 순서대로 표시됩니다
            </p>

            {searchResults.length > 0 && (
              <div className="border rounded-lg max-h-96 overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>옵션 ID</TableHead>
                      <TableHead>상품 정보</TableHead>
                      <TableHead className="text-right">선택</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {searchResults.map((product) => (
                      <TableRow key={product.option_id}>
                        <TableCell>{product.option_id}</TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <div className="font-medium">{product.product_name}</div>
                            {product.option_name && (
                              <div className="text-sm text-muted-foreground">
                                {product.option_name}
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => handleSelectProduct(product)}
                          >
                            선택
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {!searchLoading && searchResults.length === 0 && searchQuery && (
              <div className="text-center py-8 text-muted-foreground">
                검색 결과가 없습니다
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsProductSearchDialogOpen(false)}>
              닫기
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FakePurchaseManagementPage;
