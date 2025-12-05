(function () {
    function initPublicationPdfViewer(options) {
        const { pdfUrl, workerSrc } = options || {};
        const viewerContainer = document.getElementById("pdf-viewer");
        const errorBox = document.getElementById("pdf-error");

        if (!viewerContainer || !window.pdfjsLib || !window.pdfjsViewer || !pdfUrl) {
            return;
        }

        pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;

        const eventBus = new pdfjsViewer.EventBus();
        const linkService = new pdfjsViewer.PDFLinkService({ eventBus });
        const pdfViewer = new pdfjsViewer.PDFViewer({
            container: viewerContainer,
            eventBus,
            linkService,
            removePageBorders: true,
        });

        linkService.setViewer(pdfViewer);

        eventBus.on("pagesinit", () => {
            pdfViewer.currentScaleValue = "page-width";
        });

        pdfjsLib
            .getDocument(pdfUrl)
            .promise.then((doc) => {
                pdfViewer.setDocument(doc);
                linkService.setDocument(doc, null);
            })
            .catch(() => {
                if (errorBox) {
                    errorBox.classList.remove("d-none");
                }
            });
    }

    window.initPublicationPdfViewer = initPublicationPdfViewer;
})();
