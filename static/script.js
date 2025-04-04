document.addEventListener('DOMContentLoaded', () => {
    // 元素引用
    const uploadForm = document.getElementById('uploadForm');
    const uploadResult = document.getElementById('uploadResult');
    const imageUrlInput = document.getElementById('imageUrl');
    const viewImageLink = document.getElementById('viewImage');
    const copyUrlBtn = document.getElementById('copyUrlBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const imageList = document.getElementById('imageList');
    const emptyMessage = document.getElementById('emptyMessage');
    const storageTypeSelect = document.getElementById('storageType');
    const previewModal = document.getElementById('previewModal');
    const previewImage = document.getElementById('previewImage');
    const previewImageUrl = document.getElementById('previewImageUrl');
    const previewCopyUrlBtn = document.getElementById('previewCopyUrlBtn');
    const navbarToggle = document.getElementById('navbarToggle');
    const navbarMenu = document.getElementById('navbarMenu');
    const modalClose = document.getElementById('modalClose');

    // 获取可用的存储类型
    fetchStorageTypes();

    // 加载图片列表
    loadImageList();

    // 绑定事件处理程序
    uploadForm.addEventListener('submit', handleImageUpload);
    refreshBtn.addEventListener('click', loadImageList);
    copyUrlBtn.addEventListener('click', () => copyToClipboard(imageUrlInput));
    previewCopyUrlBtn.addEventListener('click', () => copyToClipboard(previewImageUrl));

    // 导航栏切换
    if (navbarToggle) {
        navbarToggle.addEventListener('click', () => {
            navbarMenu.classList.toggle('show');
        });
    }

    // 模态框关闭
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);

        // 点击模态框背景关闭
        previewModal.addEventListener('click', (e) => {
            if (e.target === previewModal || e.target.classList.contains('modal-overlay')) {
                closeModal();
            }
        });
    }

    // 获取存储类型列表
    async function fetchStorageTypes() {
        try {
            const response = await fetch('/storage-types');
            if (!response.ok) throw new Error('获取存储类型失败');

            const data = await response.json();

            // 清空选择框
            storageTypeSelect.innerHTML = '';

            // 填充存储类型选项
            data.storage_types.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type === 'local' ? '本地存储' : type === 's3' ? 'Amazon S3' : type;
                storageTypeSelect.appendChild(option);
            });
        } catch (error) {
            console.error('获取存储类型出错:', error);
            showToast('获取存储类型失败', 'danger');
        }
    }

    // 处理图片上传
    async function handleImageUpload(e) {
        e.preventDefault();

        const formData = new FormData(uploadForm);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`上传失败: ${errorText}`);
            }

            const data = await response.json();

            // 显示成功结果
            uploadResult.style.display = 'block';

            // 构建完整URL (包含域名)
            const baseUrl = window.location.origin;
            const fullUrl = `${baseUrl}${data.url}`;

            imageUrlInput.value = fullUrl;
            viewImageLink.href = fullUrl;

            // 重新加载图片列表
            loadImageList();

            // 如果是重复图片，显示提示
            if (data.is_duplicate) {
                const alertElement = uploadResult.querySelector('.alert');
                alertElement.classList.remove('alert-success');
                alertElement.classList.add('alert-warning');
                alertElement.querySelector('p').textContent = '图片已存在，返回现有链接';
            } else {
                const alertElement = uploadResult.querySelector('.alert');
                alertElement.classList.remove('alert-warning');
                alertElement.classList.add('alert-success');
                alertElement.querySelector('p').textContent = '上传成功！';
            }
        } catch (error) {
            console.error('上传出错:', error);
            showToast(error.message, 'danger');
            uploadResult.style.display = 'none';
        }
    }

    // 加载图片列表
    async function loadImageList() {
        try {
            const response = await fetch('/list');
            if (!response.ok) throw new Error('获取图片列表失败');

            const data = await response.json();

            // 清空当前列表
            imageList.innerHTML = '';

            if (data.images && data.images.length > 0) {
                // 隐藏空消息，显示表格
                emptyMessage.style.display = 'none';
                imageList.closest('.table-responsive').style.display = '';

                // 渲染图片列表
                data.images.forEach(image => {
                    const row = document.createElement('tr');

                    // 计算文件大小显示
                    const sizeDisplay = formatFileSize(image.size);

                    // 格式化日期显示
                    const uploadDate = new Date(image.upload_time);
                    const dateDisplay = formatDate(uploadDate);

                    // 图片URL
                    const baseUrl = window.location.origin;
                    const imageUrl = `${baseUrl}/images/${image.id}`;

                    row.innerHTML = `
                        <td>
                            <img src="/images/${image.id}" class="thumbnail" 
                                 data-url="${imageUrl}" 
                                 alt="${image.original_filename}">
                        </td>
                        <td>${image.original_filename}</td>
                        <td>${image.storage_type}</td>
                        <td class="file-size">${sizeDisplay}</td>
                        <td class="upload-time">${dateDisplay}</td>
                        <td>
                            <div class="btn-group">
                                <button class="btn btn-small view-btn" data-url="${imageUrl}">
                                    <span class="icon-eye"></span>
                                </button>
                                <button class="btn btn-small copy-btn" data-url="${imageUrl}">
                                    <span class="icon-clipboard"></span>
                                </button>
                                <button class="btn btn-small delete-btn" data-id="${image.id}">
                                    &#10005;
                                </button>
                            </div>
                        </td>
                    `;

                    // 添加行到表格
                    imageList.appendChild(row);

                    // 添加事件处理
                    const thumbnail = row.querySelector('.thumbnail');
                    const viewBtn = row.querySelector('.view-btn');
                    const copyBtn = row.querySelector('.copy-btn');
                    const deleteBtn = row.querySelector('.delete-btn');

                    thumbnail.addEventListener('click', () => {
                        showImagePreview(imageUrl, image.original_filename);
                    });

                    viewBtn.addEventListener('click', () => {
                        showImagePreview(imageUrl, image.original_filename);
                    });

                    copyBtn.addEventListener('click', () => {
                        navigator.clipboard.writeText(imageUrl)
                            .then(() => showToast('链接已复制到剪贴板', 'success'))
                            .catch(() => showToast('复制失败', 'danger'));
                    });

                    deleteBtn.addEventListener('click', () => {
                        if (confirm(`确定要删除图片 ${image.original_filename} 吗？`)) {
                            deleteImage(image.id);
                        }
                    });
                });
            } else {
                // 显示空消息，隐藏表格
                emptyMessage.style.display = 'block';
                imageList.closest('.table-responsive').style.display = 'none';
            }
        } catch (error) {
            console.error('加载图片列表出错:', error);
            showToast('获取图片列表失败', 'danger');
            emptyMessage.style.display = 'block';
            imageList.closest('.table-responsive').style.display = 'none';
        }
    }

    // 显示图片预览
    function showImagePreview(url, title) {
        previewImage.src = url;
        previewImage.alt = title || '预览图片';
        previewImageUrl.value = url;
        previewModal.classList.add('show');
        document.body.style.overflow = 'hidden'; // 防止滚动
    }

    // 关闭模态框
    function closeModal() {
        previewModal.classList.remove('show');
        document.body.style.overflow = ''; // 恢复滚动
    }

    // 删除图片
    async function deleteImage(id) {
        try {
            const response = await fetch(`/images/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`删除失败: ${errorText}`);
            }

            const data = await response.json();
            showToast(data.message, 'success');

            // 重新加载图片列表
            loadImageList();
        } catch (error) {
            console.error('删除图片出错:', error);
            showToast(error.message, 'danger');
        }
    }

    // 复制文本到剪贴板
    function copyToClipboard(inputElement) {
        inputElement.select();

        try {
            // 尝试使用现代API
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(inputElement.value)
                    .then(() => showToast('链接已复制到剪贴板', 'success'))
                    .catch(() => {
                        // 如果失败，回退到旧版API
                        document.execCommand('copy');
                        showToast('链接已复制到剪贴板', 'success');
                    });
            } else {
                // 旧版API
                document.execCommand('copy');
                showToast('链接已复制到剪贴板', 'success');
            }
        } catch (err) {
            showToast('复制失败', 'danger');
        }
    }

    // 格式化文件大小显示
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';

        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 格式化日期显示
    function formatDate(date) {
        const options = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        };
        return date.toLocaleDateString('zh-CN', options).replace(/\//g, '-');
    }

    // 显示提示消息
    function showToast(message, type = 'info') {
        // 创建toast容器
        let toastContainer = document.querySelector('.toast-container');

        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        // 创建toast元素
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const toastBody = document.createElement('div');
        toastBody.className = 'toast-body';
        toastBody.textContent = message;

        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'toast-close';
        closeButton.innerHTML = '&times;';
        closeButton.addEventListener('click', () => {
            toast.remove();
        });

        toast.appendChild(toastBody);
        toast.appendChild(closeButton);
        toastContainer.appendChild(toast);

        // 自动移除
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});

// 全局预览函数（提供给HTML内联onclick使用）
function showPreview(imgElement) {
    const url = imgElement.getAttribute('data-url');
    const alt = imgElement.getAttribute('alt');

    const previewImage = document.getElementById('previewImage');
    const previewImageUrl = document.getElementById('previewImageUrl');
    const previewModal = document.getElementById('previewModal');

    previewImage.src = url;
    previewImage.alt = alt || '预览图片';
    previewImageUrl.value = url;
    previewModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// 关闭模态框的全局函数
function closeModal() {
    const previewModal = document.getElementById('previewModal');
    previewModal.classList.remove('show');
    document.body.style.overflow = '';
}
