document.addEventListener('DOMContentLoaded', function () {
    // Sidebar toggle for mobile
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    // Drag and drop upload
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('id_image');
    const preview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');

    if (uploadZone && fileInput) {
        uploadZone.addEventListener('click', () => fileInput.click());

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
            uploadZone.addEventListener(ev, e => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(ev => {
            uploadZone.addEventListener(ev, () => uploadZone.classList.add('dragover'));
        });
        ['dragleave', 'drop'].forEach(ev => {
            uploadZone.addEventListener(ev, () => uploadZone.classList.remove('dragover'));
        });

        uploadZone.addEventListener('drop', e => {
            const files = e.dataTransfer.files;
            if (files.length) {
                fileInput.files = files;
                showPreview(files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) showPreview(fileInput.files[0]);
        });
    }

    function showPreview(file) {
        if (!file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = e => {
            if (preview && previewImg) {
                previewImg.src = e.target.result;
                preview.classList.remove('d-none');
            }
        };
        reader.readAsDataURL(file);
    }
});
