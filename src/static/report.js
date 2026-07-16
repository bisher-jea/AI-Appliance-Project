const params = new URLSearchParams(window.location.search);

        const batchId = params.get("batch_id");
        const completed = params.get("completed") === "true";

        const loadingState =
            document.getElementById("loadingState");

        const loadingMessage =
            document.getElementById("loadingMessage");

        const completeState =
            document.getElementById("completeState");

        const reportContent =
            document.getElementById("reportContent");

        let reportReloaded = false;
        let pollingTimeout = null;

        function scheduleStatusCheck(delay = 2000) {
            pollingTimeout = window.setTimeout(
                checkStatus,
                delay
            );
        }

        function showLoadingMessage(message) {
            if (loadingMessage) {
                loadingMessage.textContent = message;
            }
        }

        async function checkStatus() {
            if (!batchId) {
                console.error(
                    "No batch ID was found in the report URL."
                );

                showLoadingMessage(
                    "The current submission could not be identified."
                );

                return;
            }

            try {
                const response = await fetch(
                    `/report/status?batch_id=${
                        encodeURIComponent(batchId)
                    }`,
                    {
                        method: "GET",
                        cache: "no-store",
                        headers: {
                            "Accept": "application/json"
                        }
                    }
                );

                if (!response.ok) {
                    const errorText = await response.text();

                    console.error(
                        `Status check failed (${response.status}):`,
                        errorText
                    );

                    showLoadingMessage(
                        "The analysis is still processing."
                    );

                    scheduleStatusCheck(3000);
                    return;
                }

                const status = await response.json();

                if (!status.found) {
                    showLoadingMessage(
                        "Preparing your appliance analysis..."
                    );

                    scheduleStatusCheck(2000);
                    return;
                }

                if (
                    typeof status.completed === "number"
                    &&
                    typeof status.total === "number"
                ) {
                    showLoadingMessage(
                        `Analyzing appliance ${
                            status.completed
                        } of ${
                            status.total
                        }...`
                    );
                }

                if (status.complete && !reportReloaded) {
                    reportReloaded = true;

                    if (loadingState) {
                        loadingState.style.display = "none";
                    }

                    if (completeState) {
                        completeState.style.display = "block";
                    }

                    window.setTimeout(() => {
                        const refreshedUrl =
                            new URL(window.location.href);

                        refreshedUrl.searchParams.set(
                            "completed",
                            "true"
                        );

                        window.location.replace(
                            refreshedUrl.toString()
                        );
                    }, 1000);

                    return;
                }

                scheduleStatusCheck(2000);
            } catch (error) {
                console.error(
                    "Unable to check analysis status:",
                    error
                );

                showLoadingMessage(
                    "The analysis is still processing. "
                    + "This page will continue checking."
                );

                scheduleStatusCheck(3000);
            }
        }

        if (!completed && batchId) {
            checkStatus();
        } else if (completed) {
            if (loadingState) {
                loadingState.style.display = "none";
            }

            if (completeState) {
                completeState.style.display = "none";
            }

            if (reportContent) {
                reportContent.style.display = "block";
            }
        }

        window.addEventListener("beforeunload", () => {
            if (pollingTimeout !== null) {
                window.clearTimeout(pollingTimeout);
            }
        });