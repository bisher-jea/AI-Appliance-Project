const params = new URLSearchParams(
    window.location.search
);

const batchId = params.get("batch_id");
const completed =
    params.get("completed") === "true";

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

function showLoadingMessage(message) {
    if (loadingMessage) {
        loadingMessage.textContent = message;
    }
}

function scheduleStatusCheck(delay = 2000) {
    if (pollingTimeout !== null) {
        window.clearTimeout(pollingTimeout);
    }

    pollingTimeout = window.setTimeout(
        checkStatus,
        delay
    );
}

function loadCompletedReport() {
    if (reportReloaded) {
        return;
    }

    reportReloaded = true;

    if (loadingState) {
        loadingState.style.display = "none";
    }

    if (completeState) {
        completeState.style.display = "block";
    }

    showLoadingMessage(
        "Analysis complete. Loading your report."
    );

    const completedUrl = new URL(
        window.location.href
    );

    completedUrl.searchParams.set(
        "completed",
        "true"
    );

    /*
     * Replace the loading page with a fresh server-rendered
     * report. The server will now include the new analysis.
     */
    window.setTimeout(() => {
        window.location.replace(
            completedUrl.toString()
        );
    }, 700);
}

async function checkStatus() {
    if (!batchId) {
        console.error(
            "No batch ID was found in the report URL."
        );

        showLoadingMessage(
            "The report could not be checked because its batch ID is missing."
        );

        return;
    }

    try {
        const statusUrl = new URL(
            "/report/status",
            window.location.origin
        );

        statusUrl.searchParams.set(
            "batch_id",
            batchId
        );

        const response = await fetch(
            statusUrl.toString(),
            {
                method: "GET",
                cache: "no-store",
                headers: {
                    "Accept": "application/json",
                },
            }
        );

        if (!response.ok) {
            throw new Error(
                `Status request failed with ${response.status}.`
            );
        }

        const status = await response.json();

        if (!status.found) {
            showLoadingMessage(
                "Waiting for the submitted appliance records."
            );

            scheduleStatusCheck();
            return;
        }

        if (status.complete) {
            loadCompletedReport();
            return;
        }

        showLoadingMessage(
            `Analyzing appliance ${status.completed + 1} of ${status.total}.`
        );

        scheduleStatusCheck();
    } catch (error) {
        console.error(
            "Unable to check report status:",
            error
        );

        showLoadingMessage(
            "The analysis is still running. Retrying automatically."
        );

        scheduleStatusCheck(3000);
    }
}

function initializeReport() {
    /*
     * The completed URL was loaded after the analysis finished.
     * The server-rendered report should already be visible.
     */
    if (completed) {
        if (loadingState) {
            loadingState.style.display = "none";
        }

        if (completeState) {
            completeState.style.display = "none";
        }

        if (reportContent) {
            reportContent.style.display = "block";
        }

        return;
    }

    checkStatus();
}

window.addEventListener(
    "DOMContentLoaded",
    initializeReport
);

window.addEventListener(
    "pagehide",
    () => {
        if (pollingTimeout !== null) {
            window.clearTimeout(pollingTimeout);
        }
    }
);