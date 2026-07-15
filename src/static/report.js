const params = new URLSearchParams(window.location.search);
const address = params.get("address");

async function checkStatus() {
    if (!address) {
        console.error("No address was found in the report URL.");
        return;
    }

    try {
        const response = await fetch(
            `/report/status?address=${encodeURIComponent(address)}`
        );

        if (!response.ok) {
            const errorText = await response.text();

            console.error(
                `Status check failed (${response.status}):`,
                errorText
            );

            setTimeout(checkStatus, 2000);
            return;
        }

        const status = await response.json();

        if (status.complete) {
            const reloadKey = `reportReloaded:${address}`;

            if (!sessionStorage.getItem(reloadKey)) {
                sessionStorage.setItem(reloadKey, "true");
                window.location.reload();
                return;
            }
            document.getElementById("loadingState").style.display =
                "none";
            document.getElementById("completeState").style.display =
                "block";
            document.getElementById("reportContent").style.display =
                "block";
            return;
        }

        setTimeout(checkStatus, 2000);
    } catch (error) {
        console.error("Unable to check analysis status:", error);

        setTimeout(checkStatus, 3000);
    }
}

checkStatus();