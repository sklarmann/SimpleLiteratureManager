(function () {
    function initPublicationPdfViewer(options) {
        const { pdfUrl, workerSrc } = options || {};
        const canvas = document.getElementById("pdf-canvas");
        const pageInfo = document.getElementById("pdf-page-info");
        const prevButton = document.getElementById("pdf-prev");
        const nextButton = document.getElementById("pdf-next");
        const errorBox = document.getElementById("pdf-error");

        if (!canvas || !pageInfo || !prevButton || !nextButton || !window.pdfjsLib || !pdfUrl) {
            return;
        }

        const container = canvas.parentElement;
        const context = canvas.getContext("2d");
        let pdfDoc = null;
        let currentPage = 1;
        let isRendering = false;
        let pendingPage = null;

        pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;

        function updateControls(pageNumber, totalPages) {
            pageInfo.textContent = `${pageNumber} / ${totalPages}`;
            prevButton.disabled = pageNumber <= 1;
            nextButton.disabled = pageNumber >= totalPages;
        }

        function renderPage(pageNumber) {
            isRendering = true;
            pdfDoc.getPage(pageNumber).then((page) => {
                const viewport = page.getViewport({ scale: 1 });
                const targetWidth = container.clientWidth || viewport.width;
                const scale = targetWidth / viewport.width;
                const scaledViewport = page.getViewport({ scale });

                canvas.height = scaledViewport.height;
                canvas.width = scaledViewport.width;

                const renderContext = {
                    canvasContext: context,
                    viewport: scaledViewport,
                };

                const renderTask = page.render(renderContext);
                renderTask.promise.then(() => {
                    isRendering = false;
                    updateControls(pageNumber, pdfDoc.numPages);
                    if (pendingPage !== null) {
                        renderPage(pendingPage);
                        pendingPage = null;
                    }
                });
            });
        }

        function queueRenderPage(pageNumber) {
            if (isRendering) {
                pendingPage = pageNumber;
                return;
            }
            renderPage(pageNumber);
        }

        prevButton.addEventListener("click", () => {
            if (currentPage <= 1) return;
            currentPage -= 1;
            queueRenderPage(currentPage);
        });

        nextButton.addEventListener("click", () => {
            if (!pdfDoc || currentPage >= pdfDoc.numPages) return;
            currentPage += 1;
            queueRenderPage(currentPage);
        });

        pdfjsLib
            .getDocument(pdfUrl)
            .promise.then((doc) => {
                pdfDoc = doc;
                updateControls(currentPage, pdfDoc.numPages);
                renderPage(currentPage);
            })
            .catch(() => {
                if (errorBox) {
                    errorBox.classList.remove("d-none");
                }
            });
    }

    window.initPublicationPdfViewer = initPublicationPdfViewer;
})();
