(function () {
    function initPublicationPdfViewer(options) {
        const { pdfUrl, workerSrc, annotationsUrl, annotationDetailUrlTemplate } =
            options || {};

        const viewerContainer = document.getElementById("pdf-viewer-container");
        const viewer = document.getElementById("pdf-viewer");
        const errorBox = document.getElementById("pdf-error");
        const annotationPanel = document.getElementById("annotation-panel");
        const commentInput = document.getElementById("annotation-comment");
        const colorInput = document.getElementById("annotation-color");
        const saveButton = document.getElementById("save-annotation");
        const hintLabel = document.getElementById("annotation-hint");
        const annotationList = document.getElementById("annotation-list");

        if (
            !viewerContainer ||
            !viewer ||
            !window.pdfjsLib ||
            !window.pdfjsViewer ||
            !pdfUrl
        ) {
            return;
        }

        let selectionData = null;
        const annotations = [];
        const renderedAnnotationIds = new Set();

        function getCsrfToken() {
            const match = document.cookie.match(/csrftoken=([^;]+)/);
            return match ? decodeURIComponent(match[1]) : "";
        }

        function detailUrl(id) {
            return annotationDetailUrlTemplate
                ? annotationDetailUrlTemplate.replace(/0\/?$/, `${id}/`)
                : null;
        }

        function setHint(text, isWarning) {
            if (!hintLabel) return;
            hintLabel.textContent = text;
            if (isWarning) {
                hintLabel.classList.add("text-danger");
            } else {
                hintLabel.classList.remove("text-danger");
            }
        }

        function clearHighlightSelection() {
            const selection = window.getSelection();
            if (selection) {
                selection.removeAllRanges();
            }
        }

        function resetSelectionState() {
            selectionData = null;
            if (saveButton) {
                saveButton.disabled = true;
            }
            setHint("Text im PDF markieren, um eine neue Markierung anzulegen.");
        }

        function ensureAnnotationLayer(pageElement) {
            let layer = pageElement.querySelector(".slm-annotation-layer");
            if (!layer) {
                layer = document.createElement("div");
                layer.className = "slm-annotation-layer";
                layer.style.position = "absolute";
                layer.style.top = 0;
                layer.style.left = 0;
                layer.style.right = 0;
                layer.style.bottom = 0;
                layer.style.pointerEvents = "none";
                pageElement.appendChild(layer);
            }
            return layer;
        }

        function addAnnotationHighlight(annotation) {
            const pageElement = viewer.querySelector(
                `.page[data-page-number="${annotation.page_number}"]`
            );
            if (!pageElement) return false;

            const layer = ensureAnnotationLayer(pageElement);
            const highlight = document.createElement("div");
            highlight.className = "slm-annotation";
            highlight.style.position = "absolute";
            highlight.style.left = `${annotation.x * 100}%`;
            highlight.style.top = `${annotation.y * 100}%`;
            highlight.style.width = `${annotation.width * 100}%`;
            highlight.style.height = `${annotation.height * 100}%`;
            highlight.style.backgroundColor = annotation.color || "#ffeb3b";
            highlight.style.opacity = "0.35";
            highlight.style.borderRadius = "4px";
            highlight.style.pointerEvents = "auto";
            highlight.title = annotation.comment || "Markierung";
            highlight.dataset.annotationId = annotation.id;

            highlight.addEventListener("click", () => {
                if (annotation.comment) {
                    alert(`Kommentar: ${annotation.comment}`);
                }
            });

            layer.appendChild(highlight);
            return true;
        }

        function renderAnnotationList() {
            if (!annotationList) return;
            annotationList.innerHTML = "";

            if (!annotations.length) {
                const empty = document.createElement("div");
                empty.className = "text-muted small";
                empty.textContent = "Noch keine Markierungen gespeichert.";
                annotationList.appendChild(empty);
                return;
            }

            annotations
                .slice()
                .sort((a, b) => a.page_number - b.page_number)
                .forEach((annotation) => {
                    const item = document.createElement("div");
                    item.className =
                        "list-group-item d-flex justify-content-between align-items-start gap-3";

                    const body = document.createElement("div");
                    const title = document.createElement("div");
                    title.className = "fw-semibold";
                    title.textContent = `Seite ${annotation.page_number}`;

                    const comment = document.createElement("div");
                    comment.className = "small";
                    comment.textContent = annotation.comment || "(kein Kommentar)";

                    const colorBadge = document.createElement("span");
                    colorBadge.style.display = "inline-block";
                    colorBadge.style.width = "16px";
                    colorBadge.style.height = "16px";
                    colorBadge.style.border = "1px solid #ced4da";
                    colorBadge.style.borderRadius = "4px";
                    colorBadge.style.backgroundColor = annotation.color || "#ffeb3b";
                    colorBadge.title = "Markierungsfarbe";

                    body.appendChild(title);
                    body.appendChild(comment);

                    const actions = document.createElement("div");
                    actions.className = "d-flex align-items-center gap-2";
                    actions.appendChild(colorBadge);

                    const deleteButton = document.createElement("button");
                    deleteButton.className = "btn btn-sm btn-outline-danger";
                    deleteButton.textContent = "Löschen";
                    deleteButton.addEventListener("click", () => {
                        if (!confirm("Markierung wirklich löschen?")) return;
                        const url = detailUrl(annotation.id);
                        if (!url) return;

                        fetch(url, {
                            method: "DELETE",
                            headers: {
                                "X-CSRFToken": getCsrfToken(),
                            },
                        })
                            .then((response) => {
                                if (!response.ok) {
                                    throw new Error("Löschen fehlgeschlagen");
                                }
                                const index = annotations.findIndex(
                                    (item) => item.id === annotation.id
                                );
                                if (index >= 0) {
                                    annotations.splice(index, 1);
                                }
                                renderedAnnotationIds.delete(annotation.id);
                                const highlight = viewer.querySelector(
                                    `.slm-annotation[data-annotation-id="${annotation.id}"]`
                                );
                                if (highlight && highlight.parentElement) {
                                    highlight.parentElement.removeChild(highlight);
                                }
                                renderAnnotationList();
                            })
                            .catch((error) => {
                                console.error(error);
                                alert("Die Markierung konnte nicht gelöscht werden.");
                            });
                    });

                    actions.appendChild(deleteButton);

                    item.appendChild(body);
                    item.appendChild(actions);
                    annotationList.appendChild(item);
                });
        }

        function renderAnnotations() {
            annotations.forEach((annotation) => {
                if (!renderedAnnotationIds.has(annotation.id)) {
                    const rendered = addAnnotationHighlight(annotation);
                    if (rendered) {
                        renderedAnnotationIds.add(annotation.id);
                    }
                }
            });
        }

        function handleSelection() {
            const selection = window.getSelection();
            if (!selection || selection.isCollapsed) {
                resetSelectionState();
                return;
            }

            const range = selection.rangeCount ? selection.getRangeAt(0) : null;
            if (!range) {
                resetSelectionState();
                return;
            }

            const pageElement = range.commonAncestorContainer.parentElement.closest(
                ".page"
            );
            if (!pageElement || !pageElement.dataset.pageNumber) {
                resetSelectionState();
                return;
            }

            const rect = range.getBoundingClientRect();
            if (!rect || rect.width === 0 || rect.height === 0) {
                resetSelectionState();
                return;
            }

            const pageRect = pageElement.getBoundingClientRect();
            selectionData = {
                pageNumber: parseInt(pageElement.dataset.pageNumber, 10),
                x: (rect.left - pageRect.left) / pageRect.width,
                y: (rect.top - pageRect.top) / pageRect.height,
                width: rect.width / pageRect.width,
                height: rect.height / pageRect.height,
            };

            if (saveButton) {
                saveButton.disabled = false;
            }
            setHint("Auswahl gefunden. Kommentar hinzufügen und speichern.");
        }

        function saveAnnotation() {
            if (!selectionData || !annotationsUrl) {
                setHint("Bitte zuerst einen Textbereich markieren.", true);
                return;
            }

            const payload = {
                page_number: selectionData.pageNumber,
                x: selectionData.x,
                y: selectionData.y,
                width: selectionData.width,
                height: selectionData.height,
                color: colorInput ? colorInput.value : "#ffeb3b",
                comment: commentInput ? commentInput.value.trim() : "",
            };

            fetch(annotationsUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify(payload),
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("Markierung konnte nicht gespeichert werden");
                    }
                    return response.json();
                })
                .then((annotation) => {
                    annotations.push(annotation);
                    addAnnotationHighlight(annotation);
                    renderedAnnotationIds.add(annotation.id);
                    renderAnnotationList();
                    clearHighlightSelection();
                    if (commentInput) {
                        commentInput.value = "";
                    }
                    resetSelectionState();
                })
                .catch((error) => {
                    console.error(error);
                    setHint("Speichern fehlgeschlagen. Bitte erneut versuchen.", true);
                });
        }

        function loadAnnotations() {
            if (!annotationsUrl) return;
            fetch(annotationsUrl)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("Anmerkungen konnten nicht geladen werden.");
                    }
                    return response.json();
                })
                .then((data) => {
                    annotations.splice(0, annotations.length, ...data);
                    renderAnnotationList();
                    renderAnnotations();
                })
                .catch((error) => {
                    console.error(error);
                    setHint("Markierungen konnten nicht geladen werden.", true);
                });
        }

        if (saveButton) {
            saveButton.addEventListener("click", saveAnnotation);
        }

        viewerContainer.addEventListener("mouseup", () => {
            setTimeout(handleSelection, 50);
        });

        document.addEventListener("selectionchange", () => {
            const selection = window.getSelection();
            if (!selection || selection.isCollapsed) {
                resetSelectionState();
            }
        });

        pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;

        const eventBus = new pdfjsViewer.EventBus();
        const linkService = new pdfjsViewer.PDFLinkService({ eventBus });
        const pdfViewer = new pdfjsViewer.PDFViewer({
            container: viewerContainer,
            viewer,
            eventBus,
            linkService,
            removePageBorders: true,
        });

        linkService.setViewer(pdfViewer);

        eventBus.on("pagesinit", () => {
            pdfViewer.currentScaleValue = "page-width";
        });

        eventBus.on("pagerendered", () => {
            renderAnnotations();
        });

        pdfjsLib
            .getDocument(pdfUrl)
            .promise.then((doc) => {
                pdfViewer.setDocument(doc);
                linkService.setDocument(doc, null);
                loadAnnotations();
            })
            .catch(() => {
                if (errorBox) {
                    errorBox.classList.remove("d-none");
                }
                setHint("PDF konnte nicht geladen werden.", true);
            });
    }

    window.initPublicationPdfViewer = initPublicationPdfViewer;
})();
