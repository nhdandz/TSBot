import { useState, useEffect } from 'react'
import { Upload, FileText, Trash2, AlertCircle, CheckCircle, Loader2, RefreshCw, Database } from 'lucide-react'
import { adminService } from '@/services/adminService'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface Document {
  filename: string
  chunks: number
  uploaded_by: string
  uploaded_at: string
}

interface IndexStatus {
  type: 'success' | 'error' | 'info' | null
  message: string
  details?: Array<{ file: string; chunks: number }>
  totalChunks?: number
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [reindexing, setReindexing] = useState(false)
  const [loadingJson, setLoadingJson] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | null
    message: string
  }>({ type: null, message: '' })
  const [indexStatus, setIndexStatus] = useState<IndexStatus>({ type: null, message: '' })

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const response = await adminService.getDocuments()
      setDocuments(response.documents)
    } catch (error: any) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
      if (!allowedTypes.includes(file.type)) {
        setUploadStatus({
          type: 'error',
          message: 'Chỉ hỗ trợ file PDF, DOCX, TXT'
        })
        return
      }
      setSelectedFile(file)
      setUploadStatus({ type: null, message: '' })
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    try {
      setUploading(true)
      setUploadStatus({ type: null, message: '' })

      const response = await adminService.uploadDocument(selectedFile)

      setUploadStatus({
        type: 'success',
        message: `Đã upload thành công! ${response.chunks} chunks đã được index.`
      })

      await loadDocuments()

      setSelectedFile(null)
      const fileInput = document.getElementById('file-input') as HTMLInputElement
      if (fileInput) fileInput.value = ''
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.message || 'Lỗi khi upload file'
      })
    } finally {
      setUploading(false)
    }
  }

  const handleReindex = async () => {
    if (!confirm('Re-index sẽ xóa và tạo lại toàn bộ vector database từ thư mục tài liệu. Tiếp tục?')) return

    try {
      setReindexing(true)
      setIndexStatus({ type: null, message: '' })
      const res = await adminService.reindexDocuments()
      setIndexStatus({
        type: 'success',
        message: res.message,
        details: res.files_processed,
        totalChunks: res.total_chunks,
      })
      await loadDocuments()
    } catch (error: any) {
      setIndexStatus({
        type: 'error',
        message: error.message || 'Lỗi khi re-index',
      })
    } finally {
      setReindexing(false)
    }
  }

  const handleLoadJson = async () => {
    try {
      setLoadingJson(true)
      setIndexStatus({ type: null, message: '' })
      const res = await adminService.loadChunksJson()
      setIndexStatus({
        type: 'success',
        message: res.message,
        totalChunks: res.total_chunks,
      })
    } catch (error: any) {
      setIndexStatus({
        type: 'error',
        message: error.message || 'Lỗi khi load chunks.json',
      })
    } finally {
      setLoadingJson(false)
    }
  }

  const handleDelete = async (filename: string) => {
    if (!confirm(`Bạn có chắc muốn xóa "${filename}"?`)) return

    try {
      await adminService.deleteDocument(filename)
      setUploadStatus({
        type: 'success',
        message: `Đã xóa ${filename}`
      })
      await loadDocuments()
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.message || 'Lỗi khi xóa file'
      })
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('vi-VN')
    } catch {
      return dateString
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tighter">Quản lý Văn bản</h1>
        <p className="text-sm text-muted-foreground mt-1">Văn bản pháp quy và tài liệu tuyển sinh</p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base">Upload văn bản mới</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-2xl border-2 border-dashed border-border p-6 text-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-muted/50 flex items-center justify-center">
                <Upload className="w-5 h-5 text-muted-foreground" />
              </div>

              <div className="space-y-1">
                <label
                  htmlFor="file-input"
                  className="text-sm font-medium text-primary cursor-pointer hover:underline"
                >
                  Chọn file để upload
                </label>
                <p className="text-xs text-muted-foreground">Hỗ trợ PDF, DOCX, TXT</p>
              </div>

              <input
                id="file-input"
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileSelect}
                className="hidden"
              />

              {selectedFile && (
                <div className="flex items-center gap-2 text-sm text-foreground bg-muted/40 px-3 py-2 rounded-lg">
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  <span className="font-medium">{selectedFile.name}</span>
                  <span className="text-muted-foreground">
                    ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
              )}

              <Button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                size="sm"
              >
                {uploading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                {uploading ? 'Đang upload...' : 'Upload & Index'}
              </Button>
            </div>
          </div>

          {/* Status Message */}
          {uploadStatus.type && (
            <div
              className={`flex items-center gap-2 p-3 rounded-xl text-sm ${
                uploadStatus.type === 'success'
                  ? 'bg-success/10 text-success'
                  : 'bg-destructive/10 text-destructive'
              }`}
            >
              {uploadStatus.type === 'success' ? (
                <CheckCircle className="w-4 h-4 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0" />
              )}
              {uploadStatus.message}
            </div>
          )}

          <p className="text-xs text-muted-foreground">
            File sẽ được tự động chunking theo cấu trúc (Điều, Khoản...) và index vào vector database
          </p>
        </CardContent>
      </Card>

      {/* Index Management */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Quản lý Index & BM25</CardTitle>
              <CardDescription className="text-xs mt-1">
                Re-index dùng DocxChunker — mỗi điểm a)/b)/c) là chunk riêng, tránh lẫn quy định
              </CardDescription>
            </div>
            <Database className="w-5 h-5 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-3">
            {/* Re-index all */}
            <Button
              variant="default"
              size="sm"
              onClick={handleReindex}
              disabled={reindexing || loadingJson}
            >
              {reindexing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              {reindexing ? 'Đang re-index...' : 'Re-index tất cả'}
            </Button>

            {/* Load chunks.json vào bộ nhớ */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleLoadJson}
              disabled={reindexing || loadingJson}
            >
              {loadingJson ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Database className="w-4 h-4" />
              )}
              {loadingJson ? 'Đang load...' : 'Load JSON vào bộ nhớ'}
            </Button>
          </div>

          {/* Index status */}
          {indexStatus.type && (
            <div
              className={`rounded-xl p-3 text-sm space-y-2 ${
                indexStatus.type === 'success'
                  ? 'bg-success/10 text-success'
                  : indexStatus.type === 'error'
                  ? 'bg-destructive/10 text-destructive'
                  : 'bg-muted/50 text-foreground'
              }`}
            >
              <div className="flex items-center gap-2">
                {indexStatus.type === 'success' ? (
                  <CheckCircle className="w-4 h-4 shrink-0" />
                ) : (
                  <AlertCircle className="w-4 h-4 shrink-0" />
                )}
                <span className="font-medium">{indexStatus.message}</span>
                {indexStatus.totalChunks !== undefined && (
                  <span className="ml-auto font-mono text-xs bg-background/50 px-2 py-0.5 rounded-md shrink-0">
                    {indexStatus.totalChunks} chunks
                  </span>
                )}
              </div>

              {/* Per-file breakdown */}
              {indexStatus.details && indexStatus.details.length > 0 && (
                <div className="pl-6 space-y-1">
                  {indexStatus.details.map((item) => (
                    <div key={item.file} className="flex items-center gap-2 text-xs opacity-80">
                      <FileText className="w-3 h-3 shrink-0" />
                      <span className="font-medium truncate">{item.file}</span>
                      <span className="ml-auto font-mono shrink-0">{item.chunks} chunks</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <p className="text-xs text-muted-foreground">
            <strong>Re-index tất cả</strong> — đọc từ thư mục tài liệu, xây lại vector database và chunks.json.&nbsp;
            <strong>Load JSON vào bộ nhớ</strong> — khởi tạo BM25 từ chunks.json đã có (không cần embedding lại).
          </p>
        </CardContent>
      </Card>

      {/* Documents List */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base">Danh sách ({documents.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center p-8 text-sm text-muted-foreground">
              Chưa có văn bản nào. Hãy upload văn bản đầu tiên!
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tên file</TableHead>
                  <TableHead>Chunks</TableHead>
                  <TableHead>Upload bởi</TableHead>
                  <TableHead>Ngày upload</TableHead>
                  <TableHead className="text-right">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.filename}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                        <span className="font-medium">{doc.filename}</span>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs">{doc.chunks}</TableCell>
                    <TableCell className="text-muted-foreground">{doc.uploaded_by}</TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(doc.uploaded_at)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 rounded-lg text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => handleDelete(doc.filename)}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
