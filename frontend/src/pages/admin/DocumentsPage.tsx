import { useState, useEffect } from 'react'
import { Upload, FileText, Trash2, AlertCircle, CheckCircle } from 'lucide-react'
import { adminService } from '@/services/adminService'

interface Document {
    filename: string
    chunks: number
    uploaded_by: string
    uploaded_at: string
}

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<Document[]>([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [uploadStatus, setUploadStatus] = useState<{
        type: 'success' | 'error' | null
        message: string
    }>({ type: null, message: '' })

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
            // Validate file type
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

            // Reload documents list
            await loadDocuments()

            // Clear selected file
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
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-gray-900">
                    Quản lý Văn bản Pháp quy
                </h1>
            </div>

            {/* Upload Section */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Upload Văn bản mới</h2>

                <div className="space-y-4">
                    <div className="flex items-center gap-4">
                        <label
                            htmlFor="file-input"
                            className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg cursor-pointer hover:bg-blue-100 transition"
                        >
                            <FileText size={20} />
                            Chọn file
                        </label>
                        <input
                            id="file-input"
                            type="file"
                            accept=".pdf,.docx,.txt"
                            onChange={handleFileSelect}
                            className="hidden"
                        />

                        {selectedFile && (
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <FileText size={16} />
                                {selectedFile.name}
                                <span className="text-gray-400">
                                    ({(selectedFile.size / 1024).toFixed(1)} KB)
                                </span>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={handleUpload}
                        disabled={!selectedFile || uploading}
                        className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                    >
                        <Upload size={20} />
                        {uploading ? 'Đang upload...' : 'Upload & Index'}
                    </button>

                    {/* Status Message */}
                    {uploadStatus.type && (
                        <div
                            className={`flex items-center gap-2 p-4 rounded-lg ${uploadStatus.type === 'success'
                                    ? 'bg-green-50 text-green-800'
                                    : 'bg-red-50 text-red-800'
                                }`}
                        >
                            {uploadStatus.type === 'success' ? (
                                <CheckCircle size={20} />
                            ) : (
                                <AlertCircle size={20} />
                            )}
                            {uploadStatus.message}
                        </div>
                    )}
                </div>

                <div className="mt-4 text-sm text-gray-500">
                    <p>Hỗ trợ: PDF, DOCX, TXT</p>
                    <p>File sẽ được tự động chunking theo cấu trúc (Điều, Khoản...) và index vào vector database</p>
                </div>
            </div>

            {/* Documents List */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b">
                    <h2 className="text-lg font-semibold">
                        Danh sách Văn bản ({documents.length})
                    </h2>
                </div>

                {loading ? (
                    <div className="p-8 text-center text-gray-500">
                        Đang tải...
                    </div>
                ) : documents.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                        Chưa có văn bản nào. Hãy upload văn bản đầu tiên!
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Tên file
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Chunks
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Upload bởi
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Ngày upload
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Thao tác
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {documents.map((doc) => (
                                    <tr key={doc.filename} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-2">
                                                <FileText size={16} className="text-blue-600" />
                                                <span className="text-sm font-medium text-gray-900">
                                                    {doc.filename}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {doc.chunks} chunks
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {doc.uploaded_by}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatDate(doc.uploaded_at)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            <button
                                                onClick={() => handleDelete(doc.filename)}
                                                className="text-red-600 hover:text-red-800 transition"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
